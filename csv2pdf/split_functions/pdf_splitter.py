from pathlib import Path

import fitz
import pandas as pd

from .filename_utils import safe_filename_part, normalize_billing_code


def split_pdf_from_rows(
    master_pdf_path: Path,
    rows: pd.DataFrame,
    output_dir: Path,
) -> None:
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
            try:
                new_doc.insert_pdf(
                    src,
                    from_page=start_page - 1,
                    to_page=end_page - 1,
                )

                output_path = output_dir / f"{billing}_{invoice}.pdf"
                new_doc.save(output_path)
                print(f"Created: {output_path.name}")
            finally:
                new_doc.close()
    finally:
        src.close()