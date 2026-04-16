from pathlib import Path
import pandas as pd
import fitz

from .filename_utils import safe_filename_part, normalize_billing_code

def split_pdf_using_rows(
        master_pdf_path: Path,
        rows: pd.DataFrame,
        output_dir: Path,       ) -> None:
    
    src = fitz.open(master_pdf_path)
    try:
        for _, row in rows.iterrows():
            billing = safe_filename_part(
                normalize_billing_code(row["Billing Code"])
            )    
            invoice = safe_filename_part(str(row["Invoice Number"]).strip())
            start_page = int(row["Absolute Start Page"])
            end_page = int(row["Absolute End Page"])

            new_doc = fitz.open()

    finally:
        src.close()
    