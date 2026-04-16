from .config import (
    MASTER_PDF,
    RANGES_CSV,
    OUTPUT_DIR,
    REQUIRED_COLUMNS,
    CLEAR_OLD_OUTPUTS,
    FILTER_BY_SOURCE_FILE,
)

from .validators    import ensure_file_exists
from .paths         import ensure_out_dir, clear_existing_pdfs
from .csv_reader    import read_ranges_csv, filter_rows_for_master_pdf
from .pdf_splitter  import split_pdf_using_rows


def run_split_workflow() -> None:
    ensure_file_exists(MASTER_PDF, "Master PDF")
    ensure_file_exists(RANGES_CSV, "Ranges CSV")

    rows = read_ranges_csv(RANGES_CSV, REQUIRED_COLUMNS)

    if FILTER_BY_SOURCE_FILE:
        rows = filter_rows_for_master_pdf(rows, MASTER_PDF.name)

    ensure_out_dir(OUTPUT_DIR)

    if CLEAR_OLD_OUTPUTS:
        clear_existing_pdfs(OUTPUT_DIR)

    split_pdf_using_rows(MASTER_PDF, rows, OUTPUT_DIR)

    print("\nAll Done !!")