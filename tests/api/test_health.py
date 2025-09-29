"""
API tests for health check endpoints.

These tests verify that the health check endpoints work correctly
and return appropriate status information.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    def test_basic_health_check(self, test_client: TestClient):
        """Test the basic health check endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data

    def test_detailed_health_check(self, test_client: TestClient):
        """Test the detailed health check endpoint."""
        response = test_client.get("/health/detailed")

        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data
        assert "checks" in data

        # Should include database health checks
        checks = data["checks"]
        assert "application" in checks
        assert checks["application"]["status"] == "healthy"

    def test_health_check_response_format(self, test_client: TestClient):
        """Test that health check responses have the correct format."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # Required fields
        required_fields = ["status", "app_name", "version", "environment"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            assert data[field] is not None, f"Field {field} is None"

    def test_health_check_status_values(self, test_client: TestClient):
        """Test that health check status has valid values."""
        response = test_client.get("/health")

        assert response.status_code == 200

        data = response.json()

        # Status should be either "healthy" or "unhealthy"
        assert data["status"] in ["healthy", "unhealthy"]

    def test_detailed_health_includes_database_info(self, test_client: TestClient):
        """Test that detailed health check includes database information."""
        response = test_client.get("/health/detailed")

        assert response.status_code == 200

        data = response.json()
        checks = data["checks"]

        # Should have database checks (mocked in tests)
        # The exact databases present depend on the test configuration
        assert isinstance(checks, dict)
        assert len(checks) > 0

    @pytest.mark.asyncio
    async def test_health_check_with_async_client(self, async_test_client):
        """Test health check with async client."""
        response = await async_test_client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"

    def test_health_check_consistent_response(self, test_client: TestClient):
        """Test that health check returns consistent responses."""
        # Make multiple requests
        responses = []
        for _ in range(3):
            response = test_client.get("/health")
            responses.append(response.json())

        # All responses should have the same status
        statuses = [r["status"] for r in responses]
        assert len(set(statuses)) == 1, "Health check status should be consistent"

        # App name and version should be consistent
        app_names = [r["app_name"] for r in responses]
        versions = [r["version"] for r in responses]

        assert len(set(app_names)) == 1, "App name should be consistent"
        assert len(set(versions)) == 1, "Version should be consistent"

    def test_health_check_headers(self, test_client: TestClient):
        """Test that health check includes appropriate headers."""
        response = test_client.get("/health")

        assert response.status_code == 200

        # Should have request ID header (added by middleware)
        assert "X-Request-ID" in response.headers

        # Should have process time header (added by middleware)
        assert "X-Process-Time" in response.headers

        # Content type should be JSON
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_performance(self, test_client: TestClient):
        """Test that health endpoint responds quickly."""
        import time

        start_time = time.time()
        response = test_client.get("/health")
        end_time = time.time()

        assert response.status_code == 200

        # Health check should be fast (under 1 second)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health check too slow: {response_time}s"

    def test_health_endpoint_multiple_concurrent_requests(
        self, test_client: TestClient
    ):
        """Test health endpoint can handle concurrent requests."""
        import concurrent.futures

        def make_request():
            return test_client.get("/health")

        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    def test_root_endpoint(self, test_client: TestClient):
        """Test the root endpoint provides basic app information."""
        response = test_client.get("/")

        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "health_check" in data

        # Health check URL should be provided
        assert data["health_check"] == "/health"

    def test_root_endpoint_links(self, test_client: TestClient):
        """Test that root endpoint provides correct links."""
        response = test_client.get("/")

        assert response.status_code == 200

        data = response.json()

        # Should reference health check endpoint
        assert data["health_check"] == "/health"

        # In development mode, should include docs URL
        if "docs_url" in data and data["docs_url"] is not None:
            assert data["docs_url"] == "/docs"
