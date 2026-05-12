"""
Unit tests for BM25 hybrid search and RRF fusion.

These are pure unit tests — no network, no ChromaDB, no LLM.
They validate the search algorithms themselves.
"""
from app.services.hybrid_search import bm25_search, reciprocal_rank_fusion, tokenize


# ── tokenizer ─────────────────────────────────────────────────────────────

def test_tokenize_basic():
    tokens = tokenize("def login(user, password):")
    assert "def" in tokens
    assert "login" in tokens
    assert "user" in tokens
    assert "password" in tokens

def test_tokenize_lowercases():
    tokens = tokenize("UserAuth JWT_TOKEN")
    assert "userauth" in tokens
    assert "jwt_token" in tokens

def test_tokenize_ignores_punctuation():
    tokens = tokenize("hello, world! (foo)")
    assert "hello" in tokens
    assert "world" in tokens
    assert "foo" in tokens
    # Punctuation should not appear
    assert "," not in tokens
    assert "!" not in tokens


# ── BM25 search ───────────────────────────────────────────────────────────

CHUNKS = [
    {
        "text": "# File: auth.py\ndef login(username, password):\n    return verify(username, password)",
        "metadata": {"file_path": "auth.py", "start_line": 1, "end_line": 3},
        "score": 0.9,
    },
    {
        "text": "# File: shipping.py\ndef calculate_shipping(weight, distance):\n    return weight * distance * 0.05",
        "metadata": {"file_path": "shipping.py", "start_line": 10, "end_line": 13},
        "score": 0.5,
    },
    {
        "text": "# File: auth.py\ndef logout(session_id):\n    sessions.pop(session_id)",
        "metadata": {"file_path": "auth.py", "start_line": 20, "end_line": 22},
        "score": 0.7,
    },
]

def test_bm25_returns_all_chunks_by_default():
    results = bm25_search("login", CHUNKS, top_n=10)
    assert len(results) == len(CHUNKS)

def test_bm25_top_n_limits_results():
    results = bm25_search("login", CHUNKS, top_n=1)
    assert len(results) == 1

def test_bm25_ranks_relevant_chunk_first():
    """
    'login authentication' should rank auth.py login() #1.
    shipping.py and logout() both score 0 (no matching tokens) —
    their relative order is undefined, so we only assert the winner.
    """
    results = bm25_search("login authentication", CHUNKS, top_n=3)
    assert len(results) == 3
    # The login chunk must be ranked first
    first = results[0]["metadata"]
    assert first["file_path"] == "auth.py"
    assert first["start_line"] == 1          # the login chunk, not logout
    # login chunk must score strictly higher than the others
    assert results[0]["bm25_score"] > results[1]["bm25_score"]

def test_bm25_adds_bm25_score_field():
    results = bm25_search("login", CHUNKS)
    for r in results:
        assert "bm25_score" in r

def test_bm25_empty_chunks():
    results = bm25_search("anything", [], top_n=5)
    assert results == []

def test_bm25_empty_query_returns_chunks():
    """Empty query = no BM25 discrimination → returns chunks as-is."""
    results = bm25_search("", CHUNKS, top_n=5)
    assert len(results) == len(CHUNKS)


# ── RRF fusion ────────────────────────────────────────────────────────────

def test_rrf_combines_both_lists():
    """RRF output should contain items from both semantic and BM25."""
    semantic = [CHUNKS[0], CHUNKS[1]]   # auth.py login, shipping.py
    bm25     = [CHUNKS[2], CHUNKS[0]]   # auth.py logout, auth.py login

    result = reciprocal_rank_fusion(semantic, bm25)
    files = [r["metadata"]["file_path"] for r in result]

    # All 3 unique chunks should be present
    assert len(result) == 3

def test_rrf_adds_rrf_score_field():
    result = reciprocal_rank_fusion(CHUNKS[:2], CHUNKS[:2])
    for r in result:
        assert "rrf_score" in r

def test_rrf_item_in_both_lists_scores_higher():
    """
    A chunk that ranks well in BOTH semantic and BM25 should score higher
    than a chunk that only appears in one list.
    """
    # CHUNKS[0] appears first in both lists → should win
    semantic = [CHUNKS[0], CHUNKS[1]]
    bm25     = [CHUNKS[0], CHUNKS[2]]

    result = reciprocal_rank_fusion(semantic, bm25)
    # First result should be CHUNKS[0] (auth.py login)
    assert result[0]["metadata"]["file_path"] == "auth.py"
    assert result[0]["metadata"]["start_line"] == 1    # the login chunk, not logout

def test_rrf_empty_inputs():
    assert reciprocal_rank_fusion([], []) == []

def test_rrf_one_empty_list():
    result = reciprocal_rank_fusion(CHUNKS[:2], [])
    assert len(result) == 2
