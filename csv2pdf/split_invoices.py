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

# Change this only if Tesseract is installed somewhere else
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

INVOICE_RE = re.compile(
    r"INVOI\s*CE\s*#?\s*:?\s*([0-9]+)|INVOICE\s*#?\s*:?\s*([0-9]+)|CE\s*#?\s*:?\s*([0-9]{4,})",
    re.IGNORECASE,
)
PAGE_RE = re.compile(r"PAGE\s*:?[\s]*([0-9]+)", re.IGNORECASE)


@dataclass
class PageRecord:
    absolute_page: int
    invoice_number: str
    invoice_page: Optional[int]
    source: str


@dataclass
class InvoiceRange:
    invoice_number: str
    absolute_start_page: int
    absolute_end_page: int

    @property
    def page_count(self) -> int:
        return self.absolute_end_page - self.absolute_start_page + 1


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_invoice_and_page(text: str) -> tuple[str, Optional[int]]:
    text = normalize_text(text)

    invoice_match = INVOICE_RE.search(text)
    page_match = PAGE_RE.search(text)

    if not invoice_match:
        raise ValueError("Could not find 'INVOICE #' on page.")

    invoice_number = (
        invoice_match.group(1)
        or invoice_match.group(2)
        or invoice_match.group(3)
    )
    invoice_page = int(page_match.group(1)) if page_match else None
    return invoice_number, invoice_page


def pil_preprocess(img: Image.Image) -> Image.Image:
    # grayscale
    img = img.convert("L")
    # slightly sharpen
    img = img.filter(ImageFilter.SHARPEN)
    # autocontrast
    img = ImageOps.autocontrast(img)

    # simple threshold to improve OCR on scans
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

    # Several progressively broader attempts
    clips = [
        fitz.Rect(rect.width * 0.62, rect.height * 0.00, rect.width * 0.99, rect.height * 0.22),  # tight top-right
        fitz.Rect(rect.width * 0.52, rect.height * 0.00, rect.width * 0.99, rect.height * 0.28),  # larger top-right
        fitz.Rect(rect.width * 0.40, rect.height * 0.00, rect.width * 0.99, rect.height * 0.35),  # much larger
    ]

    attempts: list[tuple[str, str]] = []

    # Try cropped regions first
    for idx, clip in enumerate(clips, start=1):
        base_img = render_clip(page, clip, dpi=350)

        for rotation in (0, 90, 270, 180):
            img = base_img.rotate(rotation, expand=True) if rotation else base_img
            text = ocr_pil_image(img)
            attempts.append((f"crop{idx}_rot{rotation}", text))
            try:
                extract_invoice_and_page(text)
                return text
            except ValueError:
                pass

    # Then try full page
    full_img = render_full_page(page, dpi=300)
    for rotation in (0, 90, 270, 180):
        img = full_img.rotate(rotation, expand=True) if rotation else full_img
        text = ocr_pil_image(img)
        attempts.append((f"full_rot{rotation}", text))
        try:
            extract_invoice_and_page(text)
            return text
        except ValueError:
            pass

    # If everything fails, return the "best" looking attempt for debugging
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

            # 1) Try built-in text extraction
            text = page.get_text("text") or ""
            try:
                invoice_number, invoice_page = extract_invoice_and_page(text)
                records.append(
                    PageRecord(
                        absolute_page=i + 1,
                        invoice_number=invoice_number,
                        invoice_page=invoice_page,
                        source="text",
                    )
                )
                continue
            except ValueError:
                pass

            # 2) OCR fallback with multiple strategies
            ocr_text = try_ocr_variants(page)
            try:
                invoice_number, invoice_page = extract_invoice_and_page(ocr_text)
                records.append(
                    PageRecord(
                        absolute_page=i + 1,
                        invoice_number=invoice_number,
                        invoice_page=invoice_page,
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


def group_invoice_ranges(records: list[PageRecord]) -> list[InvoiceRange]:
    if not records:
        return []

    ranges: list[InvoiceRange] = []
    current_invoice = records[0].invoice_number
    start_page = records[0].absolute_page
    prev_page = records[0].absolute_page

    for record in records[1:]:
        if record.invoice_number != current_invoice:
            ranges.append(
                InvoiceRange(
                    invoice_number=current_invoice,
                    absolute_start_page=start_page,
                    absolute_end_page=prev_page,
                )
            )
            current_invoice = record.invoice_number
            start_page = record.absolute_page

        prev_page = record.absolute_page

    ranges.append(
        InvoiceRange(
            invoice_number=current_invoice,
            absolute_start_page=start_page,
            absolute_end_page=prev_page,
        )
    )

    return ranges


def write_csv(ranges: list[InvoiceRange], csv_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
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
    with debug_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["absolute_page", "invoice_number", "invoice_page", "source"])
        for r in records:
            writer.writerow([r.absolute_page, r.invoice_number, r.invoice_page, r.source])


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
                out_path = output_dir / f"invoice_{r.invoice_number}.pdf"
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