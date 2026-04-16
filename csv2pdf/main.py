from split_functions.workflow import run_split_workflow
from split_functions.add_letterhead import add_letterhead_pdf_to_folder
from split_functions.config import (
    OUTPUT_DIR,
    LETTERHEAD_PDF,
    LETTERHEAD_WIDTH,
    LETTERHEAD_TOP_MARGIN,
    LETTERHEAD_RECURSIVE,
)


def main():
    run_split_workflow()

    add_letterhead_pdf_to_folder(
        folder_path=OUTPUT_DIR,
        letterhead_pdf_path=LETTERHEAD_PDF,
        recursive=LETTERHEAD_RECURSIVE,
        width=LETTERHEAD_WIDTH,
        top_margin=LETTERHEAD_TOP_MARGIN,
    )


if __name__ == "__main__":
    main()