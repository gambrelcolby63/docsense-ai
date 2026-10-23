def test_health_reports_mock_provider(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["provider"] == "mock"
    assert body["embedding_provider"] == "local"
    assert body["database"] == "sqlite"
    assert body["model"] is None


def test_root_points_at_docs(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
