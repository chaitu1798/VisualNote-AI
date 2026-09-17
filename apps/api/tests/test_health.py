from fastapi.testclient import TestClient
from unittest.mock import patch


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VisualNote AI"
    assert data["status"] == "online"
    assert "/api/v1/health" in data["health"]


def test_health_endpoint_healthy_state(client: TestClient):
    with patch("app.api.v1.endpoints.health.check_db_connection", return_value=True), \
         patch("app.api.v1.endpoints.health.check_redis_connection", return_value=True):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api"] == "healthy"
        assert data["database"] == "healthy"
        assert data["redis"] == "healthy"
        assert data["version"] == "0.1.0"


def test_health_endpoint_degraded_state(client: TestClient):
    # Database healthy, Redis unavailable -> Degraded
    with patch("app.api.v1.endpoints.health.check_db_connection", return_value=True), \
         patch("app.api.v1.endpoints.health.check_redis_connection", return_value=False):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "healthy"
        assert data["redis"] == "unavailable"

    # Both unavailable -> Unhealthy
    with patch("app.api.v1.endpoints.health.check_db_connection", return_value=False), \
         patch("app.api.v1.endpoints.health.check_redis_connection", return_value=False):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "unavailable"
        assert data["redis"] == "unavailable"


def test_health_live_execution(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["api"] == "healthy"
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
