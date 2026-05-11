from unittest.mock import AsyncMock, patch, MagicMock


@patch("app.routes.query.VectorStore")
def test_query_repo_not_indexed(mock_vs, client):
    mock_vs_instance = MagicMock()
    mock_vs_instance.collection_exists.return_value = False
    mock_vs.return_value = mock_vs_instance

    response = client.post("/query", json={
        "repo_url": "https://github.com/test/repo",
        "question": "How does authentication work?"
    })

    assert response.status_code == 404


@patch("app.routes.query.LLMService")
@patch("app.routes.query.VectorStore")
@patch("app.routes.query.EmbedderService")
def test_query_success(mock_emb, mock_vs, mock_llm, client):
    mock_emb_instance = AsyncMock()
    mock_emb_instance.embed_query.return_value = [0.1] * 1536
    mock_emb.return_value = mock_emb_instance

    mock_vs_instance = MagicMock()
    mock_vs_instance.collection_exists.return_value = True
    mock_vs_instance.similarity_search.return_value = [
        {
            "text": "# File: main.py\ndef hello(): pass",
            "metadata": {
                "file_path": "main.py",
                "language": "python",
                "start_line": 1,
                "end_line": 2,
                "repo_id": "abc123"
            },
            "score": 0.92
        }
    ]
    mock_vs.return_value = mock_vs_instance

    mock_llm_instance = AsyncMock()
    mock_llm_instance.generate_answer.return_value = ("The hello function greets users.", 42)
    mock_llm.return_value = mock_llm_instance

    response = client.post("/query", json={
        "repo_url": "https://github.com/test/repo",
        "question": "What does hello do?"
    })

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["sources"]) == 1
    assert data["tokens_used"] == 42
