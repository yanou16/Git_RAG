def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "uptime_seconds" in data


def test_metrics_returns_200(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "indexed_repos" in data
    assert "total_chunks" in data
