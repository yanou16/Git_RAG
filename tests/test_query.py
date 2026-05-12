"""
Integration tests for POST /query.

The pipeline is now: semantic search → BM25 hybrid → Cohere rerank → LLM.
We mock every external call so tests are deterministic and instant.

Key things we test:
- 404 when repo not indexed
- Full pipeline (hybrid + rerank) returns correct response shape
- Pipeline label in response reflects what was used
- Graceful fallback when reranker is unavailable
- Empty retrieval returns a sensible "no results" answer
"""
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


# Shared fake chunk used across tests
FAKE_CHUNK = {
    "text": "# File: app/auth.py\ndef login(user, password):\n    return verify(user, password)",
    "metadata": {
        "file_path": "app/auth.py",
        "language": "python",
        "start_line": 10,
        "end_line": 20,
        "repo_id": "abc123def456",
    },
    "score": 0.92,
}


# ── 404 when repo not indexed ──────────────────────────────────────────────

def test_query_repo_not_indexed(client):
    """If repo was never ingested, return 404 with REPO_NOT_INDEXED code."""
    with patch("app.routes.query.VectorStore") as MockVS:
        vs = MagicMock()
        vs.collection_exists.return_value = False
        MockVS.return_value = vs

        response = client.post("/query", json={
            "repo_url": "https://github.com/test/repo",
            "question": "How does auth work?",
        })

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "REPO_NOT_INDEXED"


# ── Full happy path: hybrid + rerank ──────────────────────────────────────

def test_query_full_pipeline(client):
    """
    Happy path: semantic search → RRF hybrid → Cohere rerank → LLM answer.
    Verifies: 200, correct fields, pipeline label, rerank_score in sources.
    """
    reranked_chunk = dict(FAKE_CHUNK, rerank_score=0.94, score=0.94)

    with patch("app.routes.query.EmbedderService") as MockEmb, \
         patch("app.routes.query.VectorStore") as MockVS, \
         patch("app.routes.query.RerankerService") as MockRR, \
         patch("app.routes.query.LLMService") as MockLLM, \
         patch("app.routes.query.bm25_search", return_value=[FAKE_CHUNK]), \
         patch("app.routes.query.reciprocal_rank_fusion", return_value=[FAKE_CHUNK]):

        emb = AsyncMock()
        emb.embed_query.return_value = [0.1] * 1536
        MockEmb.return_value = emb

        vs = MagicMock()
        vs.collection_exists.return_value = True
        vs.similarity_search.return_value = [FAKE_CHUNK]
        MockVS.return_value = vs

        rr = AsyncMock()
        rr.available = True
        rr.rerank.return_value = [reranked_chunk]
        MockRR.return_value = rr

        llm = AsyncMock()
        llm.generate_answer.return_value = ("Login calls verify().", 128)
        MockLLM.return_value = llm

        response = client.post("/query", json={
            "repo_url": "https://github.com/test/repo",
            "question": "How does login work?",
            "k": 1,
            "use_hybrid": True,
            "use_reranking": True,
        })

    assert response.status_code == 200, response.text
    data = response.json()

    # Core fields
    assert data["answer"] == "Login calls verify()."
    assert data["tokens_used"] == 128
    assert data["k_retrieved"] == 1
    assert "hybrid" in data["pipeline"]
    assert "rerank" in data["pipeline"]

    # Source fields
    src = data["sources"][0]
    assert src["file_path"] == "app/auth.py"
    assert src["start_line"] == 10
    assert src["rerank_score"] == 0.94
    assert src["language"] == "python"
    assert len(src["excerpt"]) <= 200


# ── Semantic-only pipeline (no hybrid, no rerank) ─────────────────────────

def test_query_semantic_only_pipeline(client):
    """
    With use_hybrid=False and use_reranking=False, pipeline = 'semantic'.
    """
    with patch("app.routes.query.EmbedderService") as MockEmb, \
         patch("app.routes.query.VectorStore") as MockVS, \
         patch("app.routes.query.RerankerService") as MockRR, \
         patch("app.routes.query.LLMService") as MockLLM:

        emb = AsyncMock()
        emb.embed_query.return_value = [0.1] * 1536
        MockEmb.return_value = emb

        vs = MagicMock()
        vs.collection_exists.return_value = True
        vs.similarity_search.return_value = [FAKE_CHUNK]
        MockVS.return_value = vs

        rr = AsyncMock()
        rr.available = False
        MockRR.return_value = rr

        llm = AsyncMock()
        llm.generate_answer.return_value = ("Answer.", 50)
        MockLLM.return_value = llm

        response = client.post("/query", json={
            "repo_url": "https://github.com/test/repo",
            "question": "What is this repo?",
            "use_hybrid": False,
            "use_reranking": False,
        })

    assert response.status_code == 200
    assert response.json()["pipeline"] == "semantic"


# ── Reranker unavailable → graceful fallback ──────────────────────────────

def test_query_reranker_unavailable_fallback(client):
    """
    If RerankerService.available is False (no COHERE_API_KEY),
    the pipeline silently falls back to hybrid without reranking.
    """
    with patch("app.routes.query.EmbedderService") as MockEmb, \
         patch("app.routes.query.VectorStore") as MockVS, \
         patch("app.routes.query.RerankerService") as MockRR, \
         patch("app.routes.query.LLMService") as MockLLM, \
         patch("app.routes.query.bm25_search", return_value=[FAKE_CHUNK]), \
         patch("app.routes.query.reciprocal_rank_fusion", return_value=[FAKE_CHUNK]):

        emb = AsyncMock()
        emb.embed_query.return_value = [0.1] * 1536
        MockEmb.return_value = emb

        vs = MagicMock()
        vs.collection_exists.return_value = True
        vs.similarity_search.return_value = [FAKE_CHUNK]
        MockVS.return_value = vs

        # Reranker has no API key
        rr = MagicMock()
        rr.available = False
        MockRR.return_value = rr

        llm = AsyncMock()
        llm.generate_answer.return_value = ("Answer.", 60)
        MockLLM.return_value = llm

        response = client.post("/query", json={
            "repo_url": "https://github.com/test/repo",
            "question": "What is this?",
            "use_reranking": True,   # requested but no key
        })

    assert response.status_code == 200
    data = response.json()
    assert "rerank" not in data["pipeline"]    # reranking not used
    assert "hybrid" in data["pipeline"]        # but hybrid still ran


# ── Empty retrieval ────────────────────────────────────────────────────────

def test_query_no_chunks_found(client):
    """
    When ChromaDB returns zero chunks, we return a no-results message
    without calling the LLM (saves tokens).
    """
    with patch("app.routes.query.EmbedderService") as MockEmb, \
         patch("app.routes.query.VectorStore") as MockVS, \
         patch("app.routes.query.RerankerService") as MockRR, \
         patch("app.routes.query.LLMService") as MockLLM:

        emb = AsyncMock()
        emb.embed_query.return_value = [0.1] * 1536
        MockEmb.return_value = emb

        vs = MagicMock()
        vs.collection_exists.return_value = True
        vs.similarity_search.return_value = []   # nothing found
        MockVS.return_value = vs

        MockRR.return_value = MagicMock(available=False)

        llm = AsyncMock()
        MockLLM.return_value = llm

        response = client.post("/query", json={
            "repo_url": "https://github.com/test/repo",
            "question": "Where is the flux capacitor?",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["k_retrieved"] == 0
    assert data["tokens_used"] == 0             # LLM was NOT called
    assert data["sources"] == []
    llm.generate_answer.assert_not_called()


# ── Validation ────────────────────────────────────────────────────────────

def test_query_question_too_short(client):
    """Questions under 3 chars should be rejected at validation level."""
    response = client.post("/query", json={
        "repo_url": "https://github.com/test/repo",
        "question": "Hi",
    })
    assert response.status_code == 422


def test_query_k_out_of_range(client):
    """k must be between 1 and 20."""
    response = client.post("/query", json={
        "repo_url": "https://github.com/test/repo",
        "question": "How does auth work?",
        "k": 99,
    })
    assert response.status_code == 422
