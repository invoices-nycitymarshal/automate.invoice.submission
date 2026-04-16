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
        return 0
    
    finally:
        src.close()
    