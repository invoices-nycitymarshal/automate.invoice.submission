from pathlib import Path


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clear_existing_pdfs(path: Path) -> None:
    for old_pdf in path.glob("*.pdf"):
        old_pdf.unlink()