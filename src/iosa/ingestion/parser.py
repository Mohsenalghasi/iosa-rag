import fitz
from pathlib import Path
from iosa.logger import setup_logger

log = setup_logger("iosa.ingestion.parser")

def parse_pdf(pdf_path: Path) -> dict:
    """Extract text from a pdf file. Returns dict with text and metadata."""
    log.info(f'Parsing PDF: {pdf_path}')
    doc = fitz.open(pdf_path)
    pages = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({
            "page_number": page_num,
            "text": text,
            "char_count": len(text)
        })

    doc.close()
    result = {
        "source": pdf_path.name,
        "total_pages": len(pages),
        "pages": pages
    }

    log.info(f"Parsed {len(pages)} pages from {pdf_path.name}")
    return result

if __name__ == "__main__":
    raw_dir= Path("data/raw")
    test_file = raw_dir / "osha3132.pdf"  # Example PDF file for testing

    result = parse_pdf(test_file)

    print(f"Source: {result['source']}")
    print(f"Total Pages: {result['total_pages']}")  
    print("\n---First page preview---")
    print(result['pages'][0]['text'][:500])  # Print first 500 characters of the first page