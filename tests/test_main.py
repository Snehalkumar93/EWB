def test_root_endpoint(test_client):
    """Verify GET / returns 200 and expected welcome message."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "Welcome" in data["message"]


def test_health_endpoint(test_client):
    """Verify GET /health returns 200 and healthy status."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
