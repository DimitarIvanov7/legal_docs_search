import json
from pathlib import Path
from tf_idf_engine import TfidfSearchEngine
from text_preprocessing import process_pdf

PDF_DIR = Path("Data/Documents")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(exist_ok=True)

documents_tokens = {}
counter = 1

for pdf_file in PDF_DIR.glob("*.pdf"):
    tokens = process_pdf(pdf_file)
    documents_tokens[pdf_file.name] = tokens
    print(counter)
    counter += 1

print(f"Indexed {len(documents_tokens)} documents")

# Build TF-IDF
engine = TfidfSearchEngine()
engine.build_index(documents_tokens)

# Save JSONs
with open(INDEX_DIR / "documents_tokens.json", "w", encoding="utf-8") as f:
    json.dump(documents_tokens, f, ensure_ascii=False)

with open(INDEX_DIR / "idf.json", "w", encoding="utf-8") as f:
    json.dump(engine.idf, f, ensure_ascii=False)

with open(INDEX_DIR / "tfidf_docs.json", "w", encoding="utf-8") as f:
    json.dump(engine.tfidf_docs, f, ensure_ascii=False)

print("TF-IDF index saved.")
