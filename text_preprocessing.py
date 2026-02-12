from pathlib import Path

import unicodedata
import json
import re

from domain_entities_extraction import extract_domain_entities
from domain_entities_normalization import extract_text_from_pdf

from stemmer.bulgarian_stemmer import BulgarianStemmer

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"

stemmer = (
    BulgarianStemmer(r"C:\Projects\PycharmProjects\legal_docs_search\stemmer\stem_rules_context_1.txt"
)) 


SENSITIVE_MARKERS = [
    "еик",
    "егн",
    "населено място",
    "улица",
    "жк",
    "банкова сметка",
    "дата на раждане",
    "жилищен адрес",
    "електронна поща",
    "телефонен номер",
    "номер",
]

MARKERS_REGEX = re.compile(
    r"\[?\s*(?:"
    + "|".join(map(re.escape, SENSITIVE_MARKERS))
    + r")\s*\]?",
    re.IGNORECASE
)

LEGAL_BOOST = 5

DATE_REGEX = re.compile(
    r"""
    \b
    (?:0?[1-9]|[12][0-9]|3[01])      # ден
    \s*[.\-/]\s*
    (?:0?[1-9]|1[0-2])               # месец
    \s*[.\-/]\s*
    (?:19|20)\d{2}                   # година
    (?:\s*г\.?)?                     # опционално "г." / "г"
    \b
    """,
    re.VERBOSE
)


MONEY_REGEX = r"""
(?:€|\$|лв\.?|лева|bgn)\s*\d{1,3}(?:[ .]\d{3})*(?:[,.]\d+)?
|
\d{1,3}(?:[ .]\d{3})*(?:[,.]\d+)?\s*(?:лв\.?|лева|bgn|€|\$)
"""

WORD_REGEX = r"[а-яa-z0-9]+"


def remove_text_before_marker_safe(text: str, marker: str = "следното:") -> str:
    lower = text.lower()
    idx = lower.find(marker.lower())
    if idx == -1:
        return text
    return text[idx + len(marker):].strip()

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return text.lower()


def remove_dates(text: str) -> str:
    return DATE_REGEX.sub(" ", text)

def remove_sensitive_markers(text: str) -> str:
    return MARKERS_REGEX.sub(" ", text)


TOKEN_REGEX = re.compile(
    f"|{MONEY_REGEX}"
    f"|{WORD_REGEX}",
    re.IGNORECASE | re.VERBOSE
)

def tokenize(text: str) -> list[str]:
    return [t.strip() for t in TOKEN_REGEX.findall(text)]

def preprocess(text: str) -> list[str]:
    text = normalize_text(text)
    text = remove_dates(text)
    text = remove_sensitive_markers(text)
    tokens = tokenize(text)

    stop_words = load_json(str(DATA_DIR / "stopwords.json"))

    cleaned = []
    for token in tokens:
        if token in stop_words["common"]:
            continue
        if token in stop_words["domain_specific"]:
            continue
        cleaned.append(token)

    return cleaned


def process_pdf(pdf_file: Path) -> list[str]:
    raw_text = extract_text_from_pdf(pdf_file)
    trimmed_text = remove_text_before_marker_safe(raw_text)

    text, legal_tokens = extract_domain_entities(trimmed_text)

    tokens = preprocess(text)
    tokens = [t for t in tokens if len(t) > 2 and not t.isdigit()]
    tokens = [stemmer(t) for t in tokens]

    tokens.extend(legal_tokens * LEGAL_BOOST)
    return tokens

def process_query(query: str) -> list[str]:
    trimmed_text = remove_text_before_marker_safe(query)

    text, legal_tokens = extract_domain_entities(trimmed_text)

    tokens = preprocess(text)
    tokens = [t for t in tokens if len(t) > 2 and not t.isdigit()]
    tokens = [stemmer(t) for t in tokens]

    tokens.extend(legal_tokens * LEGAL_BOOST)
    return tokens


# testing
if __name__ == "__main__":
    pdf_path = "./Data/Documents/"

    PDF_DIR = Path("Data/Documents")

    for pdf_file in PDF_DIR.glob("*.pdf"):
        tokens = process_pdf(pdf_file)

        print(f"Total tokens: {len(tokens)}")
        print(pdf_file.name)
        print(f"{tokens}\n ")

