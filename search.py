from pathlib import Path
import json

from text_preprocessing import process_pdf
from tf_idf_engine import TfidfSearchEngine

BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "index"


def load_engine() -> TfidfSearchEngine:
    engine = TfidfSearchEngine()

    with (INDEX_DIR / "documents_text_tokens.json").open(encoding="utf-8") as f:
        engine.documents_text_tokens = json.load(f)

    with (INDEX_DIR / "documents_legal_tokens.json").open(encoding="utf-8") as f:
        engine.documents_legal_tokens = json.load(f)

    with (INDEX_DIR / "idf_text.json").open(encoding="utf-8") as f:
        engine.idf_text = {k: float(v) for k, v in json.load(f).items()}

    with (INDEX_DIR / "idf_legal.json").open(encoding="utf-8") as f:
        engine.idf_legal = {k: float(v) for k, v in json.load(f).items()}

    with (INDEX_DIR / "tfidf_docs_text.json").open(encoding="utf-8") as f:
        engine.tfidf_docs_text = {
            doc_id: {k: float(v) for k, v in vec.items()}
            for doc_id, vec in json.load(f).items()
        }

    with (INDEX_DIR / "tfidf_docs_legal.json").open(encoding="utf-8") as f:
        engine.tfidf_docs_legal = {
            doc_id: {k: float(v) for k, v in vec.items()}
            for doc_id, vec in json.load(f).items()
        }

    return engine


# Load ONCE at startup
ENGINE = load_engine()


def tf_idf_search(query_pdf_path: Path, top_k: int = 5):
    query_text_tokens, query_legal_tokens = process_pdf(query_pdf_path)
    return ENGINE.search(query_text_tokens, query_legal_tokens, top_k=top_k)
