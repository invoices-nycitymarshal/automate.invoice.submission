from __future__ import annotations

from pathlib import Path

import pytesseract

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OCR_CONFIG = "--psm 6"
CLIP_DPI = 350
FULL_PAGE_DPI = 300
OCR_ROTATIONS: tuple[int, ...] = (0, 90, 270, 180)
DEFAULT_CLIP_BOXES: list[tuple[float, float, float, float]] = [
    (0.58, 0.00, 0.99, 0.28),
    (0.50, 0.00, 0.99, 0.34),
    (0.38, 0.00, 0.99, 0.42),
]
SPLIT_OUTPUT_DIRNAME = "split_invoices"
RANGES_CSV_NAME = "invoice_ranges.csv"
DEBUG_CSV_NAME = "invoice_page_debug.csv"


def configure_tesseract(tesseract_cmd: str = TESSERACT_CMD) -> None:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def derive_output_paths(master_pdf: Path) -> dict[str, Path]:
    base_dir = master_pdf.parent
    return {
        "base_dir": base_dir,
        "output_dir": base_dir / SPLIT_OUTPUT_DIRNAME,
        "ranges_csv": base_dir / RANGES_CSV_NAME,
        "debug_csv": base_dir / DEBUG_CSV_NAME,
    }