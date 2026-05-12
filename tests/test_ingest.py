"""
Integration tests for POST /ingest and DELETE /repos/{repo_id}.

We mock all external services (GitHub, Embedder, VectorStore) so tests
run fast without network calls or a real ChromaDB instance.

Rule: mock at the import location — where the route FILE imports it,
not where the service is defined. That's why we patch
"app.routes.ingest.GitHubService", not "app.services.github.GitHubService".
"""
from unittest.mock import AsyncMock, MagicMock, patch


# ── /ingest success path ───────────────────────────────────────────────────

def test_ingest_success(client):
    """Full happy path: GitHub returns files, embedder embeds, VectorStore stores."""
    fake_chunk = MagicMock()
    fake_chunk.text = "# File: main.py\ndef hello(): pass"

    with patch("app.routes.ingest.GitHubService") as MockGH, \
         patch("app.routes.ingest.EmbedderService") as MockEmb, \
         patch("app.routes.ingest.VectorStore") as MockVS, \
         patch("app.routes.ingest.chunk_file", return_value=[fake_chunk]):

        # GitHub returns one file
        gh = AsyncMock()
        gh.list_files.return_value = [
            {"path": "main.py", "language": "python", "size": 500, "sha": "abc"}
        ]
        gh.get_file_content.return_value = "def hello(): pass"
        MockGH.return_value = gh

        # Embedder returns a single vector
        emb = AsyncMock()
        emb.embed_texts.return_value = [[0.1] * 1536]
        MockEmb.return_value = emb

        # VectorStore: not cached, stores 1 chunk
        vs = MagicMock()
        vs.collection_exists.return_value = False
        vs.upsert_chunks.return_value = 1
        MockVS.return_value = vs

        response = client.post("/ingest", json={
            "repo_url": "https://github.com/test/repo"
        })

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["files_indexed"] == 1
    assert data["chunks_stored"] == 1
    assert data["was_cached"] is False
    assert "repo_id" in data
    assert len(data["repo_id"]) == 12        # sha256 hex truncated to 12 chars


def test_ingest_skips_large_files(client):
    """Files over GITHUB_MAX_FILE_SIZE_KB should be skipped silently."""
    with patch("app.routes.ingest.GitHubService") as MockGH, \
         patch("app.routes.ingest.EmbedderService") as MockEmb, \
         patch("app.routes.ingest.VectorStore") as MockVS:

        gh = AsyncMock()
        gh.list_files.return_value = [
            # 200 KB file — above the 100 KB default limit
            {"path": "huge.py", "language": "python", "size": 200_000, "sha": "xyz"}
        ]
        MockGH.return_value = gh

        emb = AsyncMock()
        emb.embed_texts.return_value = []
        MockEmb.return_value = emb

        vs = MagicMock()
        vs.collection_exists.return_value = False
        vs.upsert_chunks.return_value = 0
        MockVS.return_value = vs

        response = client.post("/ingest", json={
            "repo_url": "https://github.com/test/repo"
        })

    # No files processed → 422 (no content extracted) or 404 (no supported files)
    assert response.status_code in (404, 422)


def test_ingest_cache_hit(client):
    """When repo already indexed and force_reindex=False, return cached result."""
    with patch("app.routes.ingest.VectorStore") as MockVS:
        vs = MagicMock()
        vs.collection_exists.return_value = True   # already in DB
        MockVS.return_value = vs

        response = client.post("/ingest", json={
            "repo_url": "https://github.com/test/repo"
        })

    assert response.status_code == 200
    data = response.json()
    assert data["was_cached"] is True
    assert data["files_indexed"] == 0


def test_ingest_force_reindex(client):
    """force_reindex=True should bypass the cache check."""
    fake_chunk = MagicMock()
    fake_chunk.text = "# File: main.py\ndef hello(): pass"

    with patch("app.routes.ingest.GitHubService") as MockGH, \
         patch("app.routes.ingest.EmbedderService") as MockEmb, \
         patch("app.routes.ingest.VectorStore") as MockVS, \
         patch("app.routes.ingest.chunk_file", return_value=[fake_chunk]):

        gh = AsyncMock()
        gh.list_files.return_value = [
            {"path": "main.py", "language": "python", "size": 500, "sha": "abc"}
        ]
        gh.get_file_content.return_value = "def hello(): pass"
        MockGH.return_value = gh

        emb = AsyncMock()
        emb.embed_texts.return_value = [[0.1] * 1536]
        MockEmb.return_value = emb

        vs = MagicMock()
        vs.collection_exists.return_value = True   # already cached
        vs.upsert_chunks.return_value = 1
        MockVS.return_value = vs

        response = client.post("/ingest", json={
            "repo_url": "https://github.com/test/repo",
            "force_reindex": True              # bypass cache
        })

    assert response.status_code == 200
    data = response.json()
    assert data["was_cached"] is False         # should have re-indexed


def test_ingest_truncates_file_list(client):
    """Repos with more files than max_files should be truncated + warn."""
    fake_chunk = MagicMock()
    fake_chunk.text = "# File: f.py\npass"

    with patch("app.routes.ingest.GitHubService") as MockGH, \
         patch("app.routes.ingest.EmbedderService") as MockEmb, \
         patch("app.routes.ingest.VectorStore") as MockVS, \
         patch("app.routes.ingest.chunk_file", return_value=[fake_chunk]):

        # Return 50 files but max_files=5
        gh = AsyncMock()
        gh.list_files.return_value = [
            {"path": f"file{i}.py", "language": "python", "size": 100, "sha": f"s{i}"}
            for i in range(50)
        ]
        gh.get_file_content.return_value = "def f(): pass"
        MockGH.return_value = gh

        emb = AsyncMock()
        emb.embed_texts.return_value = [[0.1] * 1536] * 5
        MockEmb.return_value = emb

        vs = MagicMock()
        vs.collection_exists.return_value = False
        vs.upsert_chunks.return_value = 5
        MockVS.return_value = vs

        response = client.post("/ingest", json={
            "repo_url": "https://github.com/test/repo",
            "max_files": 5
        })

    assert response.status_code == 200
    data = response.json()
    assert data["files_indexed"] == 5          # truncated to max_files
    assert len(data["warnings"]) >= 1          # warning present
    assert "50" in data["warnings"][0]         # mentions original count


def test_ingest_invalid_url(client):
    """Non-GitHub URLs must be rejected at validation (422)."""
    response = client.post("/ingest", json={
        "repo_url": "https://gitlab.com/test/repo"
    })
    assert response.status_code == 422


def test_ingest_repo_not_found(client):
    """GitHub 404 should surface as HTTP 404 with REPO_NOT_FOUND code."""
    from app.services.github import RepoNotFoundError

    with patch("app.routes.ingest.GitHubService") as MockGH, \
         patch("app.routes.ingest.VectorStore") as MockVS:

        gh = AsyncMock()
        gh.list_files.side_effect = RepoNotFoundError("not found")
        MockGH.return_value = gh

        vs = MagicMock()
        vs.collection_exists.return_value = False
        MockVS.return_value = vs

        response = client.post("/ingest", json={
            "repo_url": "https://github.com/ghost/private-repo"
        })

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "REPO_NOT_FOUND"


# ── DELETE /repos/{repo_id} ────────────────────────────────────────────────

def test_delete_repo_success(client):
    with patch("app.routes.ingest.VectorStore") as MockVS:
        vs = MagicMock()
        vs.collection_exists.return_value = True
        vs.delete_collection.return_value = True
        MockVS.return_value = vs

        response = client.delete("/repos/abc123def456")

    assert response.status_code == 200
    assert response.json()["repo_id"] == "abc123def456"


def test_delete_repo_not_found(client):
    with patch("app.routes.ingest.VectorStore") as MockVS:
        vs = MagicMock()
        vs.collection_exists.return_value = False
        MockVS.return_value = vs

        response = client.delete("/repos/doesnotexist")

    assert response.status_code == 404
