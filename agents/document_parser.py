import fitz  # PyMuPDF

def parse_pdf(file_path: str) -> str:
    """Extract raw text from a typed PDF, page by page with markers."""
    doc = fitz.open(file_path)
    full_text = ""

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        full_text += f"\n--- PAGE {page_num} ---\n{text}"

    doc.close()
    return full_text