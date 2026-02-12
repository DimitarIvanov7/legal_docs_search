from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Set, Tuple
import re
import math
import json
import statistics

from search import tf_idf_search
from domain_entities_normalization import extract_text_from_pdf
from domain_entities_extraction import extract_domain_entities


DECISION_RE = re.compile(r"р\s*е\s*ш\s*и\s*:", re.IGNORECASE)

def extract_decision_part(full_text: str) -> str:
    matches = list(DECISION_RE.finditer(full_text))
    if not matches:
        return ""
    m = matches[-1]
    return full_text[m.end():].strip()


def legal_tokens_from_decision(pdf_path: Path) -> Set[str]:
    full_text = extract_text_from_pdf(pdf_path)
    full_text = re.sub(r"\s+", " ", full_text)

    decision = extract_decision_part(full_text)
    if not decision:
        return set()

    _, legal_tokens = extract_domain_entities(decision)
    return {t for t in legal_tokens if t.startswith("LEGAL:")}


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


_LEVEL_RE = re.compile(r"(чл:|§:|ал:|т:)")

def legal_specificity(token: str) -> float:
    # smooth weight: 1 + log(1+depth)
    body = token[6:] if token.startswith("LEGAL:") else token
    depth = len(_LEVEL_RE.findall(body))
    return 1.0 + math.log1p(depth)

def weighted_jaccard(a: Set[str], b: Set[str]) -> float:
    u = a | b
    if not u:
        return 1.0
    inter = a & b
    num = sum(legal_specificity(t) for t in inter)
    den = sum(legal_specificity(t) for t in u)
    return num / den if den > 0 else 0.0


@dataclass
class QueryEval:
    query_doc: str
    best_match_doc: str
    best_tfidf_score: float
    best_jaccard: float
    best_weighted_jaccard: float
    query_legal_count: int
    best_match_legal_count: int


def evaluate_folder(
    queries_dir: Path,
    documents_dir: Path = Path("Data/Documents"),
    top_k: int = 10,
    use_weighted: bool = True,
) -> List[QueryEval]:

    results: List[QueryEval] = []

    query_files = sorted(list(queries_dir.glob("*.pdf")))
    if not query_files:
        raise RuntimeError(f"No PDFs found in {queries_dir}")

    for qpath in query_files:
        q_legal = legal_tokens_from_decision(qpath)

        retrieved = tf_idf_search(qpath, top_k=top_k)

        best_doc = ""
        best_tfidf = 0.0
        best_j = -1.0
        best_wj = -1.0
        best_doc_legal_count = 0

        for doc_id, tfidf_score in retrieved:
            dpath = documents_dir / doc_id
            if not dpath.exists():
                continue

            d_legal = legal_tokens_from_decision(dpath)

            j = jaccard(q_legal, d_legal)
            wj = weighted_jaccard(q_legal, d_legal)

            print("w_j ", wj, "j ", j)

            metric = wj if use_weighted else j
            best_metric = best_wj if use_weighted else best_j

            if metric > best_metric:
                best_doc = doc_id
                best_tfidf = float(tfidf_score)
                best_j = j
                best_wj = wj
                best_doc_legal_count = len(d_legal)

        results.append(
            QueryEval(
                query_doc=qpath.name,
                best_match_doc=best_doc,
                best_tfidf_score=best_tfidf,
                best_jaccard=max(best_j, 0.0),
                best_weighted_jaccard=max(best_wj, 0.0),
                query_legal_count=len(q_legal),
                best_match_legal_count=best_doc_legal_count,
            )
        )

    return results


def summarize(results: List[QueryEval], use_weighted=True) -> Dict:
    scores = [
        (r.best_weighted_jaccard if use_weighted else r.best_jaccard)
        for r in results
    ]

    summary = {
        "count": len(scores),
        "mean": sum(scores) / len(scores) if scores else 0.0,
    }

    return summary


def main():
    import argparse

    p = argparse.ArgumentParser("Offline evaluation using best Jaccard on decision legal refs")
    p.add_argument("queries_dir", type=str, help="Folder with evaluation query PDFs", default="Data/Documents_Eval")
    p.add_argument("--documents_dir", type=str, default="Data/Documents", help="Corpus folder with PDFs")
    p.add_argument("--top_k", type=int, default=10)
    p.add_argument("--weighted", action="store_true", help="Use weighted Jaccard as primary metric")
    p.add_argument("--out_json", type=str, default="offline_eval_results.json")
    args = p.parse_args()

    queries_dir = Path(args.queries_dir)
    documents_dir = Path(args.documents_dir)

    rows = evaluate_folder(
        queries_dir=queries_dir,
        documents_dir=documents_dir,
        top_k=args.top_k,
        use_weighted=args.weighted
    )

    summary = summarize(rows, use_weighted=args.weighted)

    # print per-query
    print(f"\nEvaluated queries: {len(rows)} | top_k={args.top_k} | metric={'weighted_jaccard' if args.weighted else 'jaccard'}")
    print("query\tbest_doc\tTFIDF\tJ\tWJ\t|Q|\t|D|")
    for r in rows:
        print(
            f"{r.query_doc}\t{r.best_match_doc}\t{r.best_tfidf_score:.4f}\t"
            f"{r.best_jaccard:.4f}\t{r.best_weighted_jaccard:.4f}\t"
            f"{r.query_legal_count}\t{r.best_match_legal_count}"
        )

    # print summary
    print("\nSummary:")
    for k, v in summary.items():
        if k != "hit_at":
            print(f"  {k}: {v}")
    print("  hit_at:")
    for t, v in summary["hit_at"].items():
        print(f"    >= {t}: {v:.3f}")

    # save json
    payload = {
        "summary": summary,
        "rows": [r.__dict__ for r in rows],
    }
    Path(args.out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {args.out_json}")


if __name__ == "__main__":
    main()
