from __future__ import annotations
import sys
from pathlib import Path

from config import configure_tesseract, derive_output_paths
from extract import parse_pdf_pages
from output import split_pdf, write_debug_csv, write_ranges_csv
from transform import fill_missing_billing_codes, group_invoice_ranges

def process_master_pdf(master_pdf: Path) -> dict[str, Path]:
    configure_tesseract()

    master_pdf = master_pdf.resolve()
    paths = derive_output_paths(master_pdf)

    print(f"Reading: {master_pdf}")
    records = parse_pdf_pages(master_pdf)
    normalized_records = fill_missing_billing_codes(records)
    ranges = group_invoice_ranges(normalized_records)

    write_ranges_csv(ranges, paths["ranges_csv"])
    write_debug_csv(normalized_records, paths["debug_csv"])
    split_pdf(master_pdf, ranges, paths["output_dir"])

    return {
        "master_pdf": master_pdf,
        **paths,
    }