from pathlib import Path
from split_functions.workflow import run_split_workflow
from split_functions.add_letterhead import add_letterhead_to_pdf

OUTPUT_DIR = Path("split_invoices")

def main():
    run_split_workflow()

    for pdf_path in OUTPUT_DIR.glob("*.pdf"):
        add_letterhead_to_pdf(pdf_path)

if __name__ == "__main__":
    main()