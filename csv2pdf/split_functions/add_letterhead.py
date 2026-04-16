from pathlib import Path
import fitz  # PyMuPDF


def add_letterhead_pdf_to_pdf(
    pdf_path,
    letterhead_pdf_path,
    output_path=None,
    width=260,
    top_margin=18
): 
    pdf_path = Path(pdf_path)
    letterhead_pdf_path = Path(letterhead_pdf_path)
    output_path = Path(output_path) if output_path else pdf_path

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if not letterhead_pdf_path.exists():
        raise FileNotFoundError(f"Letterhead PDF not found: {letterhead_pdf_path}")
    
    src_doc = fitz.open(pdf_path)
    letterhead_doc = fitz.open(letterhead_pdf_path)

    try:
        if len(letterhead_doc) == 0:
            raise ValueError("Letterhead PDF has no pages.")

        lh_page = letterhead_doc[0]
        lh_rect = lh_page.rect

        lh_width = lh_rect.width
        lh_height = lh_rect.height

        scale = width / lh_width
        scaled_height = lh_height * scale
        
        for page in src_doc:
            page_width = page.rect.width

            x0 = (page_width - width) / 2
            y0 = top_margin
            x1 = x0 + width
            y1 = y0 + scaled_height

            target_rect = fitz.Rect(x0, y0, x1, y1)

            page.show_pdf_page(
                target_rect,
                letterhead_doc,
                0,
                overlay=True
            )

        if output_path == pdf_path:
            temp_output = pdf_path.with_name(f"{pdf_path.stem}__tmp{pdf_path.suffix}")
            src_doc.save(temp_output)
            src_doc.close()
            letterhead_doc.close()
            temp_output.replace(pdf_path)
        else:
            src_doc.save(output_path)

    finally:
        if not src_doc.is_closed:
            src_doc.close()
        if not letterhead_doc.is_closed:
            letterhead_doc.close()

def add_letterhead_pdf_to_folder(
    folder_path,
    letterhead_pdf_path,
    recursive=False,
    width=260,
    top_margin=18
):
    folder = Path(folder_path)
    letterhead_pdf_path = Path(letterhead_pdf_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder}")

    pdf_paths = folder.rglob("*.pdf") if recursive else folder.glob("*.pdf")

    processed = 0
    for pdf_path in pdf_paths:
        add_letterhead_pdf_to_pdf(
            pdf_path=pdf_path,
            letterhead_pdf_path=letterhead_pdf_path,
            output_path=None,
            width=width,
            top_margin=top_margin
        )
        processed += 1
        print(f"Added letterhead to: {pdf_path.name}")

    print(f"Done. Processed {processed} PDF(s).")