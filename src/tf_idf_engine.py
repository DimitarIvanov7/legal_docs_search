import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple


# =========================
# TF / IDF CORE
# =========================

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
        idf[token] = math.log10(N / doc_freq)

    return idf


def compute_tfidf_vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    """
    TF-IDF sparse vector: token -> weight
    """
    tf = compute_tf(tokens)
    tfidf = {}

    for token, tf_value in tf.items():
        if token in idf:
            tfidf[token] = tf_value * idf[token]

    return tfidf


# =========================
# COSINE SIMILARITY
# =========================

def cosine_similarity_sparse(
    v1: Dict[str, float],
    v2: Dict[str, float]
) -> float:
    """
    Cosine similarity for sparse vectors (dicts)
    """
    common_tokens = set(v1.keys()) & set(v2.keys())

    numerator = sum(v1[t] * v2[t] for t in common_tokens)

    norm_v1 = math.sqrt(sum(v ** 2 for v in v1.values()))
    norm_v2 = math.sqrt(sum(v ** 2 for v in v2.values()))

    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    return numerator / (norm_v1 * norm_v2)


# =========================
# INDEX BUILDING
# =========================

class TfidfSearchEngine:
    def __init__(self):
        self.documents_tokens: Dict[str, List[str]] = {}
        self.idf: Dict[str, float] = {}
        self.tfidf_docs: Dict[str, Dict[str, float]] = {}

    def build_index(self, documents_tokens: Dict[str, List[str]]):
        """
        Build TF-IDF index from documents
        """
        self.documents_tokens = documents_tokens
        self.idf = compute_idf(documents_tokens)

        self.tfidf_docs = {
            doc_id: compute_tfidf_vector(tokens, self.idf)
            for doc_id, tokens in documents_tokens.items()
        }

    def vectorize_query(self, query_tokens: List[str]) -> Dict[str, float]:
        """
        TF-IDF vector for query
        """
        return compute_tfidf_vector(query_tokens, self.idf)

    def search(
        self,
        query_tokens: List[str],
        top_k: int = 5,
        min_score: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Return top_k most similar documents
        """
        query_vec = self.vectorize_query(query_tokens)

        scores = []
        for doc_id, doc_vec in self.tfidf_docs.items():
            score = cosine_similarity_sparse(query_vec, doc_vec)
            if score >= min_score:
                scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# =========================
# EXAMPLE USAGE
# =========================

if __name__ == "__main__":
    # --------------------------------------------------
    # Example documents (replace with your real pipeline)
    # --------------------------------------------------

    documents_tokens = {
        "doc1.pdf": [
            "чл_45", "ззд", "непозволен", "увреждан",
            "вред", "обезщетен", "вред"
        ],
        "doc2.pdf": [
            "чл_49", "ззд", "отговорност",
            "възложител", "вред"
        ],
        "doc3.pdf": [
            "договор", "неизпълнен",
            "обезщетен", "вред"
        ],
    }

    # Simulate legal boost
    LEGAL_BOOST = 5
    documents_tokens["doc1.pdf"].extend(["чл_45_ззд"] * LEGAL_BOOST)
    documents_tokens["doc2.pdf"].extend(["чл_49_ззд"] * LEGAL_BOOST)

    # --------------------------------------------------
    # Build index
    # --------------------------------------------------

    engine = TfidfSearchEngine()
    engine.build_index(documents_tokens)

    # --------------------------------------------------
    # Query
    # --------------------------------------------------

    query_tokens = [
        "чл_45", "ззд", "обезщетен", "вред"
    ]
    query_tokens.extend(["чл_45_ззд"] * LEGAL_BOOST)

    results = engine.search(query_tokens, top_k=3)

    print("Query results:")
    for doc_id, score in results:
        print(doc_id, round(score, 4))
