from pathlib import Path
import pandas as pd

def ensure_file_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found in {path}")

def validate_required_columns(df: pd.DataFrame, required: set[str]) -> None:
    missing = required - set(df.columnns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

def ensure_non_empty_dataframe(df: pd.DataFrame, message: str) -> None:
    if df.empty:
        raise ValueError(message)