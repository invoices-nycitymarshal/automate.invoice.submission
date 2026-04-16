from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MASTER_PDF = BASE_DIR / "master.pdf"
RANGES_CSV = BASE_DIR / "invoice_ranges.csv"
OUTPUT_DIR = BASE_DIR / "split_invoices"
LETTERHEAD_PDF = BASE_DIR / "Letterhead.pdf"

REQUIRED_COLUMNS = {
    "Source File",
    "Billing Code",
    "Invoice Number",
    "Absolute Start Page",
    "Absolute End Page",
}

CLEAR_OLD_OUTPUTS = False
FILTER_BY_SOURCE_FILE = True

LETTERHEAD_WIDTH = 260
LETTERHEAD_TOP_MARGIN = 18
LETTERHEAD_RECURSIVE = False