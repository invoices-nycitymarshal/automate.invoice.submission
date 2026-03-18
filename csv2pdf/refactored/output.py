from __future__ import annotations

import csv
import re
from pathlib import Path

import fitz
import pandas as pd

from models import InvoiceRange, PageRecord
from transform import fill_missing_billing_codes

def safe_filename_part(value: str) -> str:
    return re.sub(r'[<>:"/\|?*]+', "_", value)

def write_ranges_csv(ranges: list[InvoiceRange], csv_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "billing_code": item.billing_code,
                "invoice_number": item.invoice_number,
                "absolute_start_page": item.absolute_start_page,
                "absolute_end_page": item.absolute_end_page,
                "page_count": item.page_count,
            }
            for item in ranges
        ]
    )
    df.to_csv(csv_path, index=False)
