from unittest.mock import AsyncMock, patch, MagicMock


@patch("app.routes.ingest.GitHubService")
@patch("app.routes.ingest.EmbedderService")
@patch("app.routes.ingest.VectorStore")
def test_ingest_success(mock_vs, mock_emb, mock_gh, client):
    mock_gh_instance = AsyncMock()
    mock_gh_instance.list_files.return_value = [
        {"path": "main.py", "language": "python", "size": 1000, "sha": "abc"}
    ]
    mock_gh_instance.get_file_content.return_value = "def hello(): pass"
    mock_gh.return_value = mock_gh_instance

    mock_emb_instance = AsyncMock()
    mock_emb_instance.embed_texts.return_value = [[0.1] * 1536]
    mock_emb.return_value = mock_emb_instance

    mock_vs_instance = MagicMock()
    mock_vs_instance.collection_exists.return_value = False
    mock_vs_instance.upsert_chunks.return_value = 1
    mock_vs.return_value = mock_vs_instance

    response = client.post("/ingest", json={
        "repo_url": "https://github.com/test/repo"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["files_indexed"] == 1
    assert "repo_id" in data
    assert data["was_cached"] is False


@patch("app.routes.ingest.VectorStore")
def test_ingest_cache_hit(mock_vs, client):
    mock_vs_instance = MagicMock()
    mock_vs_instance.collection_exists.return_value = True
    mock_vs.return_value = mock_vs_instance

    response = client.post("/ingest", json={
        "repo_url": "https://github.com/test/repo"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["was_cached"] is True


def test_ingest_invalid_url(client):
    response = client.post("/ingest", json={
        "repo_url": "https://gitlab.com/test/repo"
    })
    assert response.status_code == 422
