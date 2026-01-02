from pathlib import Path
import PyPDF2


def extract_text_from_pdf(pdf_path: Path) -> str:
    chunks = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                chunks.append(text)
    return "\n".join(chunks)
