from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz


INVOICE_RE = re.compile(r"INVOICE\s*#\s*:\s*([0-9]+)", re.IGNORECASE)
PAGE_RE = re.compile(r"PAGE\s*:\s*([0-9]+)", re.IGNORECASE)


@dataclass
class PageRecord:
    absolute_page: int
    invoice_number: str
    invoice_page: Optional[int]


@dataclass
class InvoiceRange:
    invoice_number: str
    absolute_start_page: int
    absolute_end_page: int

    @property
    def page_count(self) -> int:
        return self.absolute_end_page - self.absolute_start_page + 1


def extract_invoice_and_page(text: str) -> tuple[str, Optional[int]]:
    invoice_match = INVOICE_RE.search(text)
    page_match = PAGE_RE.search(text)

    if not invoice_match:
        raise ValueError("Could not find 'INVOICE #' on page.")

    invoice_number = invoice_match.group(1)
    invoice_page = int(page_match.group(1)) if page_match else None
    return invoice_number, invoice_page


def parse_pdf_pages(pdf_path: str | Path) -> list[PageRecord]:
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    records: list[PageRecord] = []

    for i in range(doc.page_count):
        text = doc.load_page(i).get_text("text") or ""
        text = text.replace("\u00a0", " ")

        invoice_number, invoice_page = extract_invoice_and_page(text)
        records.append(PageRecord(i + 1, invoice_number, invoice_page))

    doc.close()
    return records


def group_into_invoice_ranges(records: list[PageRecord]) -> list[InvoiceRange]:
    if not records:
        return []

    ranges: list[InvoiceRange] = []
    current_invoice = records[0].invoice_number
    start_page = records[0].absolute_page
    prev_page = records[0].absolute_page

    for record in records[1:]:
        if record.invoice_number != current_invoice:
            ranges.append(InvoiceRange(current_invoice, start_page, prev_page))
            current_invoice = record.invoice_number
            start_page = record.absolute_page
        prev_page = record.absolute_page

    ranges.append(InvoiceRange(current_invoice, start_page, prev_page))
    return ranges


def write_csv(ranges: list[InvoiceRange], csv_path: str | Path) -> None:
    csv_path = Path(csv_path)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "invoice_number",
            "absolute_start_page",
            "absolute_end_page",
            "page_count",
        ])
        for r in ranges:
            writer.writerow([
                r.invoice_number,
                r.absolute_start_page,
                r.absolute_end_page,
                r.page_count,
            ])


def split_pdf(master_pdf_path: str | Path, ranges: list[InvoiceRange], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    src = fitz.open(master_pdf_path)

    for r in ranges:
        new_doc = fitz.open()
        new_doc.insert_pdf(
            src,
            from_page=r.absolute_start_page - 1,
            to_page=r.absolute_end_page - 1,
        )
        out_path = output_dir / f"invoice_{r.invoice_number}.pdf"
        new_doc.save(out_path)
        new_doc.close()

    src.close()


def main() -> None:
    master_pdf = "master.pdf"
    output_csv = "invoice_ranges.csv"
    output_dir = "split_invoices"

    records = parse_pdf_pages(master_pdf)
    ranges = group_into_invoice_ranges(records)
    write_csv(ranges, output_csv)
    split_pdf(master_pdf, ranges, output_dir)

    print(f"CSV written to: {output_csv}")
    print(f"Split PDFs written to: {output_dir}")


if __name__ == "__main__":
    main()