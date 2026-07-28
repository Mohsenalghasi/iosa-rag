import fitz
import json
from pathlib import Path
from datetime import datetime, timezone
from iosa.logger import setup_logger

log = setup_logger("iosa.ingestion.parser")


def parse_pdf(pdf_path: Path, document_type: str = "unknown", access_level: str = "public") -> dict:
    """Extract text from a pdf file. Returns dict with text and metadata."""
    log.info(f"Parsing PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    pages = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        pages.append({
            "page_number": page_num,
            "text": text,
            "char_count": len(text),
            "word_count": len(text.split())
        })

    doc.close()

    total_words = sum(p["word_count"] for p in pages)

    result = {
        "source": pdf_path.name,
        "file_path": str(pdf_path),
        "document_type": document_type,
        "access_level": access_level,
        "language": "en",
        "parsed_at": datetime.now(timezone.utc).isoformat(),
        "total_pages": len(pages),
        "total_word_count": total_words,
        "pages": pages
    }

    log.info(f"Parsed {len(pages)} pages from {pdf_path.name}")
    return result


if __name__ == "__main__":
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(exist_ok=True)

    doc_types = {
        "osha3132.pdf": "OSHA guide",
        "OSHA3514.pdf": "OSHA guide",
        "OSHA3165.pdf": "OSHA guide",
        "csbfinalreportbp.pdf": "CSB incident report",
        "2005-149.pdf": "NIOSH pocket guide"
    }

    pdf_files = sorted(raw_dir.glob("*.pdf"))

    for pdf_file in pdf_files:
        doc_type = doc_types.get(pdf_file.name, "unknown")
        result = parse_pdf(pdf_file, document_type=doc_type)

        print(f"Source: {result['source']}")
        print(f"Type: {result['document_type']}")
        print(f"Total pages: {result['total_pages']}")
        print(f"Total words: {result['total_word_count']}")
        print("---")

        output_path = processed_dir / f"{pdf_file.stem}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)