import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple


# Колко тежи legal similarity спрямо text similarity
LEGAL_LAMBDA = 1.8

# Нормализирани тегла (сумират се до 1)
W_TEXT = 1.0 / (1.0 + LEGAL_LAMBDA)
W_LEGAL = LEGAL_LAMBDA / (1.0 + LEGAL_LAMBDA)

# boost по специфичност за LEGAL:* токени
LEGAL_SPEC_LOG_WEIGHT = 0.8
_LEGAL_LEVEL_RE = re.compile(r"(чл:|§:|ал:|т:)")


def token_boost_legal(token: str) -> float:
    if not token.startswith("LEGAL:"):
        return 1.0
    body = token[6:]
    depth = len(_LEGAL_LEVEL_RE.findall(body))
    return 1.0 + LEGAL_SPEC_LOG_WEIGHT * math.log1p(depth)


def compute_tf(tokens: List[str]) -> Dict[str, float]:
    """
    TF = 1 + log10(freq)
    """
    freq = Counter(tokens)
    tf = {}
    for token, count in freq.items():
        tf[token] = 1 + math.log10(count)
    return tf


def compute_idf(documents_tokens: Dict[str, List[str]]) -> Dict[str, float]:
    """
    IDF = log10(N / df)
    """
    df = defaultdict(int)
    N = len(documents_tokens)

    for tokens in documents_tokens.values():
        for token in set(tokens):
            df[token] += 1

    idf = {}
    for token, doc_freq in df.items():
        # защита при doc_freq==0 не е нужна, но пазим формулата стабилна
        idf[token] = math.log10(N / doc_freq) if doc_freq else 0.0

    return idf


def compute_tfidf_vector(
    tokens: List[str],
    idf: Dict[str, float],
    *,
    is_legal_field: bool = False
) -> Dict[str, float]:
    """
    TF-IDF sparse vector: token -> weight
    """
    tf = compute_tf(tokens)
    tfidf = {}

    for token, tf_value in tf.items():
        if token in idf:
            w = tf_value * idf[token]
            if is_legal_field:
                w *= token_boost_legal(token)
            tfidf[token] = w

    return tfidf


def cosine_similarity_sparse(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    common_tokens = set(v1.keys()) & set(v2.keys())
    numerator = sum(v1[t] * v2[t] for t in common_tokens)

    norm_v1 = math.sqrt(sum(v ** 2 for v in v1.values()))
    norm_v2 = math.sqrt(sum(v ** 2 for v in v2.values()))

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    return numerator / (norm_v1 * norm_v2)


class TfidfSearchEngine:
    def __init__(self):
        # doc_id -> tokens
        self.documents_text_tokens: Dict[str, List[str]] = {}
        self.documents_legal_tokens: Dict[str, List[str]] = {}

        # separate idf per field
        self.idf_text: Dict[str, float] = {}
        self.idf_legal: Dict[str, float] = {}

        # doc_id -> tfidf vector
        self.tfidf_docs_text: Dict[str, Dict[str, float]] = {}
        self.tfidf_docs_legal: Dict[str, Dict[str, float]] = {}

    def build_index(
        self,
        documents_text_tokens: Dict[str, List[str]],
        documents_legal_tokens: Dict[str, List[str]]
    ):
        self.documents_text_tokens = documents_text_tokens
        self.documents_legal_tokens = documents_legal_tokens

        self.idf_text = compute_idf(documents_text_tokens)
        self.idf_legal = compute_idf(documents_legal_tokens)

        self.tfidf_docs_text = {
            doc_id: compute_tfidf_vector(tokens, self.idf_text, is_legal_field=False)
            for doc_id, tokens in documents_text_tokens.items()
        }

        self.tfidf_docs_legal = {
            doc_id: compute_tfidf_vector(tokens, self.idf_legal, is_legal_field=True)
            for doc_id, tokens in documents_legal_tokens.items()
        }

    def vectorize_query(self, text_tokens: List[str], legal_tokens: List[str]) -> Tuple[Dict[str, float], Dict[str, float]]:
        q_text = compute_tfidf_vector(text_tokens, self.idf_text, is_legal_field=False)
        q_legal = compute_tfidf_vector(legal_tokens, self.idf_legal, is_legal_field=True)
        return q_text, q_legal

    def search(
        self,
        query_text_tokens: List[str],
        query_legal_tokens: List[str],
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Tuple[str, float]]:
        q_text_vec, q_legal_vec = self.vectorize_query(query_text_tokens, query_legal_tokens)

        scores = []
        for doc_id in self.tfidf_docs_text.keys():
            d_text_vec = self.tfidf_docs_text.get(doc_id, {})
            d_legal_vec = self.tfidf_docs_legal.get(doc_id, {})

            s_text = cosine_similarity_sparse(q_text_vec, d_text_vec)
            s_legal = cosine_similarity_sparse(q_legal_vec, d_legal_vec)

            score = (W_TEXT * s_text) + (W_LEGAL * s_legal)

            if score >= min_score:
                scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
