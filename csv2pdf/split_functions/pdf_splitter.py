from pathlib import Path
import pandas as pd
import fitz

from .filename_utils import safe_filename_part, normalize_billing_code

def split_pdf_using_rows():
    return 0