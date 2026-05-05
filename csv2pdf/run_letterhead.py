from pathlib import Path
from split_functions.add_letterhead import add_letterhead_to_pdf

PDF_PATH = Path("master.pdf")

def main():
    add_letterhead_to_pdf(PDF_PATH)

if __name__ == "__main__":
    main()