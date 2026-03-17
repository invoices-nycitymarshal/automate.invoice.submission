from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz
import pandas as pd
import pytesseract
from PIL import Image, ImageOps, ImageFilter

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

INVOICE_RE = re.compile(
    r"INVOI\s*CE\s*#?\s*:?\s*([0-9]+)|INVOICE\s*#?\s*:?\s*([0-9]+)|CE\s*#?\s*:?\s*([0-9]{4,})",
    re.IGNORECASE,
)

PAGE_RE = re.compile(r"PAGE\s*:?[\s]*([0-9]+)", re.IGNORECASE)

# More forgiving billing code regex
BILLING_CODE_RE = re.compile(
    r"""
    BILLING\s*
    C[O0Q]D[E3]?\s*   # CODE / C0DE / CQDE / COD / etc
    :?\s*
    ([A-Z0-9]{2,10})
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass
class PageRecord:
    absolute_page: int
    invoice_number: str
    invoice_page: Optional[int]
    billing_code: Optional[str]
    source: str


@dataclass
class InvoiceRange:
    invoice_number: str
    billing_code: str
    absolute_start_page: int
    absolute_end_page: int

    @property
    def page_count(self) -> int:
        return self.absolute_end_page - self.absolute_start_page + 1


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_billing_code(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    code = re.sub(r"[^A-Z0-9]", "", code.upper())
    if not code:
        return None
    return code


def safe_filename_part(value: str) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "_", value)


def extract_invoice_page_and_billing(text: str) -> tuple[str, Optional[int], Optional[str]]:
    text = normalize_text(text)

    invoice_match = INVOICE_RE.search(text)
    page_match = PAGE_RE.search(text)
    billing_match = BILLING_CODE_RE.search(text)

    if not invoice_match:
        raise ValueError("Could not find 'INVOICE #' on page.")

    invoice_number = (
        invoice_match.group(1)
        or invoice_match.group(2)
        or invoice_match.group(3)
    )
    invoice_page = int(page_match.group(1)) if page_match else None
    billing_code = clean_billing_code(billing_match.group(1)) if billing_match else None

    return invoice_number, invoice_page, billing_code


def pil_preprocess(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageOps.autocontrast(img)
    img = img.point(lambda p: 255 if p > 160 else 0)
    return img


def ocr_pil_image(img: Image.Image) -> str:
    img = pil_preprocess(img)
    return pytesseract.image_to_string(img, config="--psm 6")


def render_clip(page: fitz.Page, clip: fitz.Rect, dpi: int = 300) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def render_full_page(page: fitz.Page, dpi: int = 300) -> Image.Image:
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def try_ocr_variants(page: fitz.Page) -> str:
    rect = page.rect

    clips = [
        fitz.Rect(rect.width * 0.58, rect.height * 0.00, rect.width * 0.99, rect.height * 0.28),
        fitz.Rect(rect.width * 0.50, rect.height * 0.00, rect.width * 0.99, rect.height * 0.34),
        fitz.Rect(rect.width * 0.38, rect.height * 0.00, rect.width * 0.99, rect.height * 0.42),
    ]

    attempts: list[tuple[str, str]] = []

    for idx, clip in enumerate(clips, start=1):
        base_img = render_clip(page, clip, dpi=350)

        for rotation in (0, 90, 270, 180):
            img = base_img.rotate(rotation, expand=True) if rotation else base_img
            text = ocr_pil_image(img)
            attempts.append((f"crop{idx}_rot{rotation}", text))
            try:
                extract_invoice_page_and_billing(text)
                return text
            except ValueError:
                pass

    full_img = render_full_page(page, dpi=300)
    for rotation in (0, 90, 270, 180):
        img = full_img.rotate(rotation, expand=True) if rotation else full_img
        text = ocr_pil_image(img)
        attempts.append((f"full_rot{rotation}", text))
        try:
            extract_invoice_page_and_billing(text)
            return text
        except ValueError:
            pass

    best_name, best_text = max(attempts, key=lambda x: len(normalize_text(x[1])))
    return f"[best_attempt={best_name}] {best_text}"


def parse_pdf_pages(pdf_path: Path) -> list[PageRecord]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    records: list[PageRecord] = []

    try:
        for i in range(doc.page_count):
            page = doc.load_page(i)

            text = page.get_text("text") or ""
            try:
                invoice_number, invoice_page, billing_code = extract_invoice_page_and_billing(text)
                records.append(
                    PageRecord(
                        absolute_page=i + 1,
                        invoice_number=invoice_number,
                        invoice_page=invoice_page,
                        billing_code=billing_code,
                        source="text",
                    )
                )
                continue
            except ValueError:
                pass

            ocr_text = try_ocr_variants(page)
            try:
                invoice_number, invoice_page, billing_code = extract_invoice_page_and_billing(ocr_text)
                records.append(
                    PageRecord(
                        absolute_page=i + 1,
                        invoice_number=invoice_number,
                        invoice_page=invoice_page,
                        billing_code=billing_code,
                        source="ocr",
                    )
                )
            except ValueError:
                preview = normalize_text(ocr_text)[:500]
                raise ValueError(
                    f"Could not find invoice data on absolute page {i + 1}, even after multi-pass OCR. "
                    f"OCR preview: {preview}"
                )

    finally:
        doc.close()

    return records


def fill_missing_billing_codes(records: list[PageRecord]) -> list[PageRecord]:
    """
    If one page in an invoice block has the billing code, use it for all pages
    of that same invoice number.
    """
    invoice_to_billing: dict[str, str] = {}

    # first pass: collect known billing codes
    for r in records:
        if r.billing_code:
            invoice_to_billing[r.invoice_number] = r.billing_code

    # second pass: fill missing
    filled: list[PageRecord] = []
    for r in records:
        filled.append(
            PageRecord(
                absolute_page=r.absolute_page,
                invoice_number=r.invoice_number,
                invoice_page=r.invoice_page,
                billing_code=r.billing_code or invoice_to_billing.get(r.invoice_number),
                source=r.source,
            )
        )

    return filled


def group_invoice_ranges(records: list[PageRecord]) -> list[InvoiceRange]:
    if not records:
        return []

    records = fill_missing_billing_codes(records)

    ranges: list[InvoiceRange] = []
    current_invoice = records[0].invoice_number
    current_billing_code = records[0].billing_code or "UNKNOWN"
    start_page = records[0].absolute_page
    prev_page = records[0].absolute_page

    for record in records[1:]:
        if record.invoice_number != current_invoice:
            ranges.append(
                InvoiceRange(
                    invoice_number=current_invoice,
                    billing_code=current_billing_code,
                    absolute_start_page=start_page,
                    absolute_end_page=prev_page,
                )
            )
            current_invoice = record.invoice_number
            current_billing_code = record.billing_code or "UNKNOWN"
            start_page = record.absolute_page

        prev_page = record.absolute_page

    ranges.append(
        InvoiceRange(
            invoice_number=current_invoice,
            billing_code=current_billing_code,
            absolute_start_page=start_page,
            absolute_end_page=prev_page,
        )
    )

    return ranges


def write_csv(ranges: list[InvoiceRange], csv_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "billing_code": r.billing_code,
                "invoice_number": r.invoice_number,
                "absolute_start_page": r.absolute_start_page,
                "absolute_end_page": r.absolute_end_page,
                "page_count": r.page_count,
            }
            for r in ranges
        ]
    )
    df.to_csv(csv_path, index=False)


def write_debug_csv(records: list[PageRecord], debug_csv_path: Path) -> None:
    records = fill_missing_billing_codes(records)

    with debug_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["absolute_page", "invoice_number", "invoice_page", "billing_code", "source"])
        for r in records:
            writer.writerow([r.absolute_page, r.invoice_number, r.invoice_page, r.billing_code, r.source])


def split_pdf(master_pdf_path: Path, ranges: list[InvoiceRange], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    src = fitz.open(master_pdf_path)
    try:
        for r in ranges:
            new_doc = fitz.open()
            try:
                new_doc.insert_pdf(
                    src,
                    from_page=r.absolute_start_page - 1,
                    to_page=r.absolute_end_page - 1,
                )
                billing = safe_filename_part(r.billing_code)
                invoice = safe_filename_part(r.invoice_number)
                out_path = output_dir / f"{billing}_{invoice}.pdf"
                new_doc.save(out_path)
                print(f"Created: {out_path.name}")
            finally:
                new_doc.close()
    finally:
        src.close()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python split_invoices.py <master.pdf>")
        sys.exit(1)

    master_pdf = Path(sys.argv[1]).resolve()
    base_dir = master_pdf.parent
    output_dir = base_dir / "split_invoices"
    csv_path = base_dir / "invoice_ranges.csv"
    debug_csv_path = base_dir / "invoice_page_debug.csv"

    print(f"Reading: {master_pdf}")
    records = parse_pdf_pages(master_pdf)
    records = fill_missing_billing_codes(records)
    ranges = group_invoice_ranges(records)

    write_csv(ranges, csv_path)
    write_debug_csv(records, debug_csv_path)
    split_pdf(master_pdf, ranges, output_dir)

    print("\nDone.")
    print(f"Invoice table: {csv_path}")
    print(f"Debug file: {debug_csv_path}")
    print(f"Split PDFs folder: {output_dir}")


if __name__ == "__main__":
    main()