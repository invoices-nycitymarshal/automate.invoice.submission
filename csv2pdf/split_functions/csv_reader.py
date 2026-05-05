from pathlib import Path
import pandas as pd

from .validators import (
    ensure_file_exists,
    validate_required_columns,
    ensure_non_empty_dataframe,
)


COLUMN_ALIASES = {
    "Source File":          ["Source File", "source_file"],
    "Billing Code":         ["Billing Code", "billing_code"],
    "Invoice Number":       ["Invoice Number", "invoice_number"],
    "Absolute Start Page":  ["Absolute Start Page", "absolute_start_page"],
    "Absolute End Page":    ["Absolute End Page", "absolute_end_page"],
    "Page Count":           ["Page Count", "page_count"],
}


def normalize_range_columns(
    df: pd.DataFrame, 
    master_pdf_name: str
    ) -> pd.DataFrame:

    df = df.copy()

    rename_map = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                rename_map[alias] = canonical
                break

    df = df.rename(columns=rename_map)

    if "Source File" not in df.columns:
        df["Source File"] = master_pdf_name

    return df


def read_ranges_csv(
    csv_path: Path,
    required_columns: set[str],
    master_pdf_name: str,
) -> pd.DataFrame:
    
    ensure_file_exists(csv_path, "Ranges CSV")
    df = pd.read_csv(csv_path)
    df = normalize_range_columns(df, master_pdf_name)
    validate_required_columns(df, required_columns)
    return df


def filter_rows_for_master_pdf(df: pd.DataFrame, master_pdf_name: str) -> pd.DataFrame:
    filtered = df[df["Source File"].astype(str).str.strip() == master_pdf_name].copy()

    ensure_non_empty_dataframe(
        filtered,
        f"No rows found in invoice_ranges.csv for source file '{master_pdf_name}'.",
    )
    return filtered