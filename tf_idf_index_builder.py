import json
from pathlib import Path
from tf_idf_engine import TfidfSearchEngine
from text_preprocessing import process_pdf

PDF_DIR = Path("Data/Documents")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(exist_ok=True)

documents_text_tokens = {}
documents_legal_tokens = {}

counter = 1

for pdf_file in PDF_DIR.glob("*.pdf"):
    text_tokens, legal_tokens = process_pdf(pdf_file)

    documents_text_tokens[pdf_file.name] = text_tokens
    documents_legal_tokens[pdf_file.name] = legal_tokens

    print(counter)
    counter += 1

print(f"Indexed {len(documents_text_tokens)} documents")

engine = TfidfSearchEngine()
engine.build_index(documents_text_tokens, documents_legal_tokens)

with open(INDEX_DIR / "documents_text_tokens.json", "w", encoding="utf-8") as f:
    json.dump(documents_text_tokens, f, ensure_ascii=False)

with open(INDEX_DIR / "documents_legal_tokens.json", "w", encoding="utf-8") as f:
    json.dump(documents_legal_tokens, f, ensure_ascii=False)

with open(INDEX_DIR / "idf_text.json", "w", encoding="utf-8") as f:
    json.dump(engine.idf_text, f, ensure_ascii=False)

with open(INDEX_DIR / "idf_legal.json", "w", encoding="utf-8") as f:
    json.dump(engine.idf_legal, f, ensure_ascii=False)

with open(INDEX_DIR / "tfidf_docs_text.json", "w", encoding="utf-8") as f:
    json.dump(engine.tfidf_docs_text, f, ensure_ascii=False)

with open(INDEX_DIR / "tfidf_docs_legal.json", "w", encoding="utf-8") as f:
    json.dump(engine.tfidf_docs_legal, f, ensure_ascii=False)

print("TF-IDF index saved (text + legal).")
