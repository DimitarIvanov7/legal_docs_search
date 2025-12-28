import re
import string
from nltk.tokenize import TweetTokenizer, WhitespaceTokenizer, WordPunctTokenizer, TreebankWordTokenizer
import unicodedata
from PyPDF2 import PdfReader
import json
import re

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


DATE_REGEX = re.compile(
    r"\b(0[1-9]|[12][0-9]|3[01])\."
    r"(0[1-9]|1[0-2])\."
    r"(19|20)\d{2}\b"
)

MONEY_REGEX = r"""
(?:€|\$|лв\.?|лева|bgn)\s*\d{1,3}(?:[ .]\d{3})*(?:[,.]\d+)?
|
\d{1,3}(?:[ .]\d{3})*(?:[,.]\d+)?\s*(?:лв\.?|лева|bgn|€|\$)
"""

LEGAL_ARTICLE_REGEX = r"""
(?:чл\.?\s*\d+(?:\s*[–-]\s*\d+)?        # чл.156–161
 (?:\s*,?\s*ал\.?\s*\d+)?               # ал.1
 (?:\s*,?\s*т\.?\s*\d+(?:\.\d+)?)?      # т.1 или т.5.1
 (?:\s*(?:и|вр\.)\s*
     чл\.?\s*\d+(?:\s*,?\s*ал\.?\s*\d+)?
     (?:\s*,?\s*т\.?\s*\d+(?:\.\d+)?)?
 )*
|
 т\.?\s*\d+\s*на\s*чл\.?\s*\d+           # т.2 на чл.6
|
 чл\.?\s*\d+(?:\s*,?\s*\d+)*(?:\s*и\s*\d+)*  # чл.3, 5 и 6
)
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

def load_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    text = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)

    return "\n".join(text)

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return text.lower()


def remove_dates(text: str) -> str:
    return DATE_REGEX.sub(" ", text)

def remove_sensitive_markers(text: str) -> str:
    return MARKERS_REGEX.sub(" ", text)


TOKEN_REGEX = re.compile(
    f"{LEGAL_ARTICLE_REGEX}"
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

    stop_words = load_json("./Data/stopwords.json")

    cleaned = []
    for token in tokens:
        if token in stop_words["common"]:
            continue
        if token in stop_words["domain_specific"]:
            continue
        cleaned.append(token)

    return cleaned

if __name__ == "__main__":
    pdf_path = "./Data/Documents/"

    raw_text = load_pdf_text(pdf_path + "Act_Content_0.pdf")
    trimmed_text = remove_text_before_marker_safe(raw_text)

    tokens = preprocess(trimmed_text)

    print(tokens[:100])
    print(f"\nTotal tokens: {len(tokens)}")
