from pathlib import Path
import pandas as pd

def ensure_file_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found in {path}")

def validate_required_columns(df: pd.DataFrame, required: set[str]) -> None:
    return 0

def ensure_non_empty_dataframe():
    return 0