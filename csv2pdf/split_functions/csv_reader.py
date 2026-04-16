from pathlib        import Path
from .validators    import (
    ensure_file_exists,
    validate_required_columns,
    ensure_non_empty_dataframe,
)

import pandas as pd


def read_ranges_csv(csv_path: Path, required_columns: str[str]) -> pd.DataFrame:
    ensure_file_exists(csv_path, "Ranges CSV")
    df = pd.read_csv(csv_path)
    validate_required_columns(df, required_columns)
    return df

def filter_rows_for_master_pdf(df: pd.DataFrame, master_pdf_name: str) -> pd.DataFrame:
    return 0