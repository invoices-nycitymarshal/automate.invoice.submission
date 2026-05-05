from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz
import pandas as pd


MASTER_PDF = Path("master.pdf")
RANGES_CSV = Path("invoice_ranges.csv")
DEBUG_CSV = Path("invoice_page_debug.csv")


INVOICE_RE = re.compile(r"INVOICE\s*#?\s*:?\s*([0-9]+)", re.IGNORECASE)
PAGE_RE = re.compile(r"PAGE\s*:?\s*([0-9]+)", re.IGNORECASE)
BILLING_RE = re.compile(r"BILLING\s*CODE\s*:?\s*([A-Z0-9]{2,10})", re.IGNORECASE)


@dataclass
class PageRecord:
    absolute_page: int
    invoice_number: str
    invoice_page: Optional[int]
    billing_code: Optional[str]


@dataclass
class InvoiceRange:
    billing_code: str
    invoice_number: str
    absolute_start_page: int
    absolute_end_page: int

    @property
    def page_count(self) -> int:
        return self.absolute_end_page - self.absolute_start_page + 1


def normalize_text(text: str) -> str:
    return text.replace("\u00a0", " ").strip()


def clean_billing_code(code: Optional[str]) -> Optional[str]:
    if not code:
        return None
    cleaned = re.sub(r"[^A-Z0-9]", "", code.upper())
    return cleaned or None


def extract_invoice_fields(text: str) -> tuple[str, Optional[int], Optional[str]]:
    text = normalize_text(text)

    invoice_match = INVOICE_RE.search(text)
    page_match = PAGE_RE.search(text)
    billing_match = BILLING_RE.search(text)

    if not invoice_match:
        raise ValueError("Could not find invoice number on page.")

    invoice_number = invoice_match.group(1)
    invoice_page = int(page_match.group(1)) if page_match else None
    billing_code = clean_billing_code(billing_match.group(1)) if billing_match else None

    return invoice_number, invoice_page, billing_code


def parse_pdf_pages(pdf_path: Path) -> list[PageRecord]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    records: list[PageRecord] = []

    try:
        for i in range(doc.page_count):
            page = doc.load_page(i)
            text = page.get_text("text") or ""

            invoice_number, invoice_page, billing_code = extract_invoice_fields(text)

            records.append(
                PageRecord(
                    absolute_page=i + 1,
                    invoice_number=invoice_number,
                    invoice_page=invoice_page,
                    billing_code=billing_code,
                )
            )
    finally:
        doc.close()

    return records


def fill_missing_billing_codes(records: list[PageRecord]) -> list[PageRecord]:
    invoice_to_billing: dict[str, str] = {}

    for record in records:
        if record.billing_code:
            invoice_to_billing[record.invoice_number] = record.billing_code

    filled: list[PageRecord] = []
    for record in records:
        filled.append(
            PageRecord(
                absolute_page=record.absolute_page,
                invoice_number=record.invoice_number,
                invoice_page=record.invoice_page,
                billing_code=record.billing_code or invoice_to_billing.get(record.invoice_number),
            )
        )

    return filled


def group_invoice_ranges(records: list[PageRecord]) -> list[InvoiceRange]:
    if not records:
        return []

    records = fill_missing_billing_codes(records)

    ranges: list[InvoiceRange] = []

    current_invoice = records[0].invoice_number
    current_billing = records[0].billing_code or "UNKNOWN"
    start_page = records[0].absolute_page
    prev_page = records[0].absolute_page

    for record in records[1:]:
        if record.invoice_number != current_invoice:
            ranges.append(
                InvoiceRange(
                    billing_code=current_billing,
                    invoice_number=current_invoice,
                    absolute_start_page=start_page,
                    absolute_end_page=prev_page,
                )
            )
            current_invoice = record.invoice_number
            current_billing = record.billing_code or "UNKNOWN"
            start_page = record.absolute_page

        prev_page = record.absolute_page

    ranges.append(
        InvoiceRange(
            billing_code=current_billing,
            invoice_number=current_invoice,
            absolute_start_page=start_page,
            absolute_end_page=prev_page,
        )
    )

    return ranges


def write_ranges_csv(ranges: list[InvoiceRange], csv_path: Path) -> None:
    df = pd.DataFrame([
        {
            "Billing Code": r.billing_code,
            "Invoice Number": r.invoice_number,
            "Absolute Start Page": r.absolute_start_page,
            "Absolute End Page": r.absolute_end_page,
            "Page Count": r.page_count,
        }
        for r in ranges
    ])
    df.to_csv(csv_path, index=False)


def write_debug_csv(records: list[PageRecord], csv_path: Path) -> None:
    records = fill_missing_billing_codes(records)

    df = pd.DataFrame([
        {
            "Absolute Page": r.absolute_page,
            "Invoice Number": r.invoice_number,
            "Invoice Page": r.invoice_page,
            "Billing Code": r.billing_code,
        }
        for r in records
    ])
    df.to_csv(csv_path, index=False)


def main() -> None:
    print(f"Reading: {MASTER_PDF.resolve()}")

    records = parse_pdf_pages(MASTER_PDF)
    ranges = group_invoice_ranges(records)

    write_ranges_csv(ranges, RANGES_CSV)
    write_debug_csv(records, DEBUG_CSV)

    print("Done.")
    print(f"Created: {RANGES_CSV.resolve()}")
    print(f"Created: {DEBUG_CSV.resolve()}")


if __name__ == "__main__":
    main()