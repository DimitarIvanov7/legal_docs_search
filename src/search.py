from pathlib import Path
import json

from text_preprocessing import process_pdf
from tf_idf_engine import TfidfSearchEngine


BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "index"


def load_engine() -> TfidfSearchEngine:
    engine = TfidfSearchEngine()

    with (INDEX_DIR / "documents_tokens.json").open(encoding="utf-8") as f:
        engine.documents_tokens = json.load(f)

    with (INDEX_DIR / "idf.json").open(encoding="utf-8") as f:
        engine.idf = {k: float(v) for k, v in json.load(f).items()}

    with (INDEX_DIR / "tfidf_docs.json").open(encoding="utf-8") as f:
        engine.tfidf_docs = {
            doc_id: {k: float(v) for k, v in vec.items()}
            for doc_id, vec in json.load(f).items()
        }

    return engine


# Load ONCE at startup
ENGINE = load_engine()


def tf_idf_search(query_pdf_path: Path, top_k: int = 5):
    query_tokens = process_pdf(query_pdf_path)
    return ENGINE.search(query_tokens, top_k=top_k)
