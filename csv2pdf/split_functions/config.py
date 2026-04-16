from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MASTER_PDF = BASE_DIR / "master.pdf"
RANGES_CSV = BASE_DIR / "invoice_ranges.csv"
OUTPUT_DIR = BASE_DIR / "split_invoices"

REQUIRED_COLUMNS = {
    "Source File",
    "Billing Code",
    "Invoice Number",
    "Absolute Start Page",
    "Absolute End Page"
}

CLEAR_OLD_OUTPUTS = False
FILTER_BY_SOURCE_FILE = True