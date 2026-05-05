from pathlib import Path
import fitz  # PyMuPDF

LETTERHEAD_PDF = Path(__file__).resolve().parent.parent / "letterhead.pdf"
LETTERHEAD_TOP_MARGIN = 20

def add_letterhead_to_pdf(pdf_path):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    src_doc = fitz.open(pdf_path)
    letterhead_doc = fitz.open(LETTERHEAD_PDF)

    try:
        letterhead_page = letterhead_doc[0]
        letterhead_rect = letterhead_page.rect

        original_width = letterhead_rect.width
        original_height = letterhead_rect.height

        for page in src_doc:
            page_width = page.rect.width

            target_width = page_width * 0.9  # your tuned value
            scale = target_width / original_width
            scaled_height = original_height * scale

            x0 = (page_width - target_width) / 2
            y0 = LETTERHEAD_TOP_MARGIN
            x1 = x0 + target_width
            y1 = y0 + scaled_height

            rect = fitz.Rect(x0, y0, x1, y1)

            page.show_pdf_page(rect, letterhead_doc, 0, overlay=True)

        temp = pdf_path.with_name(f"{pdf_path.stem}__tmp.pdf")
        src_doc.save(temp)
        src_doc.close()
        letterhead_doc.close()
        temp.replace(pdf_path)

    finally:
        if not src_doc.is_closed:
            src_doc.close()
        if not letterhead_doc.is_closed:
            letterhead_doc.close()