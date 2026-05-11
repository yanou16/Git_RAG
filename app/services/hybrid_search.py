import math
import structlog
from rank_bm25 import BM25Okapi

log = structlog.get_logger()


def tokenize(text: str) -> list[str]:
    """Lowercase + split on non-alphanumeric chars."""
    import re
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def reciprocal_rank_fusion(
    semantic_chunks: list[dict],
    bm25_chunks: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Combine semantic search and BM25 results using RRF.

    RRF score = 1/(k + rank_in_semantic) + 1/(k + rank_in_bm25)

    Why RRF works:
      Semantic catches MEANING  → "authenticate user" ≈ "verify credentials"
      BM25 catches EXACT WORDS  → finds "JWT", "bcrypt", specific function names
      Together they cover both cases — and RRF needs no tuning weight.

    k=60 is the standard default from the original RRF paper (Cormack 2009).
    """
    scores: dict[str, float] = {}
    chunk_by_id: dict[str, dict] = {}

    # Assign RRF score from semantic ranking
    for rank, chunk in enumerate(semantic_chunks):
        cid = _chunk_id(chunk)
        chunk_by_id[cid] = chunk
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)

    # Add RRF score from BM25 ranking
    for rank, chunk in enumerate(bm25_chunks):
        cid = _chunk_id(chunk)
        chunk_by_id[cid] = chunk
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)

    result = []
    for cid in sorted_ids:
        chunk = dict(chunk_by_id[cid])
        chunk["rrf_score"] = round(scores[cid], 6)
        result.append(chunk)

    return result


def bm25_search(
    query: str,
    chunks: list[dict],
    top_n: int = 20,
) -> list[dict]:
    """
    BM25 keyword search over a list of chunks.
    Used as the second leg of hybrid search.

    BM25 (Best Match 25) is the algorithm behind Elasticsearch's default
    relevance. It weights rare terms higher and penalizes very long documents.
    """
    if not chunks:
        return []

    corpus = [tokenize(c["text"]) for c in chunks]
    query_tokens = tokenize(query)

    if not query_tokens:
        return chunks[:top_n]

    bm25 = BM25Okapi(corpus)
    raw_scores = bm25.get_scores(query_tokens)

    scored = sorted(
        zip(raw_scores, chunks),
        key=lambda x: x[0],
        reverse=True,
    )

    results = []
    for score, chunk in scored[:top_n]:
        c = dict(chunk)
        c["bm25_score"] = round(float(score), 4)
        results.append(c)

    return results


def _chunk_id(chunk: dict) -> str:
    meta = chunk.get("metadata", {})
    return f"{meta.get('file_path', '')}:{meta.get('start_line', '')}:{meta.get('end_line', '')}"
