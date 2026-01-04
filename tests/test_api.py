"""Tests for FastAPI API endpoints."""

from fastapi.testclient import TestClient

from hn_herald import __version__


class TestHealthEndpoint:
    """Tests for the /api/health endpoint."""

    def test_health_returns_200(self, test_client: TestClient) -> None:
        """Health endpoint should return 200 OK."""
        response = test_client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, test_client: TestClient) -> None:
        """Health endpoint should return healthy status."""
        response = test_client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_returns_version(self, test_client: TestClient) -> None:
        """Health endpoint should return correct version."""
        response = test_client.get("/api/health")
        data = response.json()
        assert data["version"] == __version__

    def test_health_returns_environment(self, test_client: TestClient) -> None:
        """Health endpoint should return environment."""
        response = test_client.get("/api/health")
        data = response.json()
        assert "environment" in data
        assert data["environment"] in ["development", "production"]

    def test_health_response_structure(self, test_client: TestClient) -> None:
        """Health endpoint should return expected JSON structure."""
        response = test_client.get("/api/health")
        data = response.json()
        assert set(data.keys()) == {"status", "version", "environment"}


class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root_returns_200(self, test_client: TestClient) -> None:
        """Root endpoint should return 200 OK."""
        response = test_client.get("/")
        assert response.status_code == 200

    def test_root_returns_welcome_message(self, test_client: TestClient) -> None:
        """Root endpoint should return welcome message."""
        response = test_client.get("/")
        data = response.json()
        assert data["message"] == "Welcome to HN Herald"

    def test_root_returns_version(self, test_client: TestClient) -> None:
        """Root endpoint should return version."""
        response = test_client.get("/")
        data = response.json()
        assert data["version"] == __version__
