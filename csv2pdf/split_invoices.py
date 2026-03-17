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
from PIL import Image


# Set this if pytesseract cannot find tesseract automatically
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

INVOICE_RE = re.compile(r"INVOICE\s*#\s*:?\s*([0-9]+)", re.IGNORECASE)
PAGE_RE = re.compile(r"PAGE\s*:?\s*([0-9]+)", re.IGNORECASE)


@dataclass
class PageRecord:
    absolute_page: int
    invoice_number: str
    invoice_page: Optional[int]
    source: str  # "text" or "ocr"


@dataclass
class InvoiceRange:
    invoice_number: str
    absolute_start_page: int
    absolute_end_page: int

    @property
    def page_count(self) -> int:
        return self.absolute_end_page - self.absolute_start_page + 1


def extract_invoice_and_page(text: str) -> tuple[str, Optional[int]]:
    text = text.replace("\u00a0", " ")

    invoice_match = INVOICE_RE.search(text)
    page_match = PAGE_RE.search(text)

    if not invoice_match:
        raise ValueError("Could not find 'INVOICE #' on page.")

    invoice_number = invoice_match.group(1)
    invoice_page = int(page_match.group(1)) if page_match else None
    return invoice_number, invoice_page


def page_to_ocr_text(page: fitz.Page, dpi: int = 300) -> str:
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return pytesseract.image_to_string(img)


def parse_pdf_pages(pdf_path: Path) -> list[PageRecord]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    records: list[PageRecord] = []

    try:
        for i in range(doc.page_count):
            page = doc.load_page(i)

            # Try normal text extraction first
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

            # Fall back to OCR
            ocr_text = page_to_ocr_text(page)

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
                preview = ocr_text[:500].replace("\n", " ")
                raise ValueError(
                    f"Could not find 'INVOICE #' on absolute page {i + 1}, "
                    f"even after OCR.\nOCR preview: {preview}"
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