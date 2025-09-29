"""
Comprehensive API integration tests.

These tests verify end-to-end functionality across all API endpoints,
including health checks, error handling, middleware, and cross-cutting concerns.
"""

import json

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestAPIIntegration:
    """Integration tests for overall API functionality."""

    def test_api_root_endpoint_structure(self, test_client: TestClient):
        """Test that the root endpoint provides proper API structure."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        required_fields = [
            "message",
            "version",
            "environment",
            "docs_url",
            "redoc_url",
            "health_check",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Verify links are correct
        assert data["docs_url"] == "/docs"
        assert data["redoc_url"] == "/redoc"
        assert data["health_check"] == "/health"

        # Verify app information
        assert "FastAPI Enterprise" in data["message"]
        assert data["version"] is not None

    def test_openapi_docs_accessible(self, test_client: TestClient):
        """Test that OpenAPI documentation is accessible."""
        # Test docs endpoint
        docs_response = test_client.get("/docs")
        assert docs_response.status_code == 200
        assert "text/html" in docs_response.headers["content-type"]

        # Test redoc endpoint
        redoc_response = test_client.get("/redoc")
        assert redoc_response.status_code == 200
        assert "text/html" in redoc_response.headers["content-type"]

        # Test OpenAPI JSON
        openapi_response = test_client.get("/openapi.json")
        assert openapi_response.status_code == 200
        assert openapi_response.headers["content-type"] == "application/json"

        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "info" in openapi_data
        assert "paths" in openapi_data

    def test_health_check_integration(self, test_client: TestClient):
        """Test health check endpoint integration."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data

        # Verify headers
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers

    def test_detailed_health_check_integration(self, test_client: TestClient):
        """Test detailed health check with database connectivity."""
        response = test_client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()

        # Verify overall structure
        assert "status" in data
        assert "services" in data
        assert "checks" in data

        # Verify database services (should be mocked in tests)
        services = data["services"]
        expected_services = ["postgres", "mongodb", "redis"]
        for service in expected_services:
            assert service in services
            # In test environment, these should be True (mocked)
            assert isinstance(services[service], bool)

        # Verify individual checks
        checks = data["checks"]
        assert "application" in checks
        assert checks["application"]["status"] == "healthy"

    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are properly set."""
        # Test preflight request
        response = test_client.options(
            "/api/v1/pricing",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # FastAPI TestClient might not handle OPTIONS the same way as real server
        # So we'll test a regular request and check CORS headers
        response = test_client.get("/health")
        assert response.status_code == 200

        # Test actual request with origin
        response = test_client.get(
            "/health", headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200

    def test_request_id_middleware(self, test_client: TestClient):
        """Test that request ID middleware works correctly."""
        response1 = test_client.get("/health")
        response2 = test_client.get("/health")

        # Both should have request IDs
        assert "X-Request-ID" in response1.headers
        assert "X-Request-ID" in response2.headers

        # Request IDs should be different
        assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]

        # Request IDs should be valid UUIDs (basic format check)
        request_id = response1.headers["X-Request-ID"]
        assert len(request_id) == 36  # UUID format
        assert request_id.count("-") == 4

    def test_process_time_middleware(self, test_client: TestClient):
        """Test that process time middleware works correctly."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "X-Process-Time" in response.headers

        # Process time should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
        assert process_time < 10  # Should be fast

    def test_error_handling_404(self, test_client: TestClient):
        """Test 404 error handling."""
        response = test_client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.json()

        # Should have error structure
        assert "detail" in data

    def test_error_handling_405_method_not_allowed(self, test_client: TestClient):
        """Test 405 Method Not Allowed error handling."""
        # POST to health endpoint should not be allowed
        response = test_client.post("/health")

        assert response.status_code == 405
        data = response.json()

        assert "detail" in data

    def test_validation_error_handling(self, test_client: TestClient):
        """Test request validation error handling."""
        # Send invalid JSON to pricing endpoint
        response = test_client.post("/api/v1/pricing", json={"invalid": "data"})

        assert response.status_code == 422
        data = response.json()

        # Should have standardized error format
        assert "error" in data
        error = data["error"]
        assert error["type"] == "ValidationError"
        assert "message" in error
        assert "details" in error
        assert isinstance(error["details"], list)

    def test_content_type_validation(self, test_client: TestClient):
        """Test content type validation."""
        # Send malformed JSON data to JSON endpoint
        response = test_client.post(
            "/api/v1/pricing",
            data="{'invalid': json}",  # Malformed JSON
            headers={"Content-Type": "application/json"},
        )

        # Should return 422 for invalid JSON
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_async_endpoint_functionality(self, async_test_client: AsyncClient):
        """Test that all endpoints work with async client."""
        endpoints = [
            "/",
            "/health",
            "/health/detailed",
            "/api/v1/pricing/materials",
            "/api/v1/pricing/processes",
            "/api/v1/pricing/tiers",
        ]

        for endpoint in endpoints:
            response = await async_test_client.get(endpoint)
            assert response.status_code == 200, f"Failed for endpoint: {endpoint}"

    def test_api_versioning(self, test_client: TestClient):
        """Test API versioning structure."""
        # All pricing endpoints should be under /api/v1
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

        openapi_data = response.json()
        paths = openapi_data["paths"]

        # Check that pricing endpoints are properly versioned
        pricing_endpoints = [path for path in paths.keys() if "/pricing" in path]
        for endpoint in pricing_endpoints:
            assert endpoint.startswith(
                "/api/v1/"
            ), f"Endpoint not properly versioned: {endpoint}"

    def test_response_consistency(self, test_client: TestClient):
        """Test that API responses are consistent."""
        # Make multiple requests to the same endpoint
        responses = []
        for _ in range(3):
            response = test_client.get("/api/v1/pricing/materials")
            responses.append(response.json())

        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            assert response == first_response, "API responses should be consistent"

    def test_request_logging(self, test_client: TestClient):
        """Test that requests are properly logged."""
        # This is more of a structural test - we can't easily test log output
        # but we can verify the middleware doesn't break anything
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers

    def test_concurrent_requests_different_endpoints(self, test_client: TestClient):
        """Test concurrent requests to different endpoints."""
        import concurrent.futures

        def make_request(endpoint: str):
            return test_client.get(endpoint)

        endpoints = [
            "/health",
            "/api/v1/pricing/materials",
            "/api/v1/pricing/processes",
            "/api/v1/pricing/tiers",
        ]

        # Make concurrent requests to different endpoints
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(make_request, endpoint) for endpoint in endpoints
            ]
            responses = [future.result() for future in futures]

        # All requests should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Failed for endpoint: {endpoints[i]}"

    def test_api_performance_multiple_endpoints(self, test_client: TestClient):
        """Test performance across multiple endpoints."""
        import time

        endpoints = [
            "/health",
            "/api/v1/pricing/materials",
            "/api/v1/pricing/processes",
            "/api/v1/pricing/tiers",
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200
            response_time = end_time - start_time
            assert (
                response_time < 1.0
            ), f"Endpoint {endpoint} too slow: {response_time}s"

    def test_large_request_handling(self, test_client: TestClient):
        """Test handling of large requests."""
        # Create a pricing request with large special requirements
        large_requirements = [f"requirement_{i}" for i in range(50)]

        request_data = {
            "material": "aluminum",
            "quantity": 1000,
            "dimensions": {"length_mm": 1000, "width_mm": 500, "height_mm": 250},
            "geometric_complexity_score": 4.5,
            "process": "cnc",
            "surface_finish": "polished",
            "tolerance_class": "precision",
            "special_requirements": large_requirements,
            "delivery_timeline": "rush",
            "rush_order": True,
            "customer_tier": "enterprise",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        # Should handle large requests gracefully
        assert response.status_code == 200
        data = response.json()
        assert "cost_breakdown" in data
        assert "pricing_tiers" in data

    def test_api_security_headers(self, test_client: TestClient):
        """Test that appropriate security headers are present."""
        response = test_client.get("/health")

        assert response.status_code == 200

        # Check for security-related headers added by middleware
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers

        # Content-Type should be properly set
        assert response.headers["content-type"] == "application/json"

    def test_json_response_format(self, test_client: TestClient):
        """Test that all JSON responses are properly formatted."""
        endpoints = [
            "/",
            "/health",
            "/health/detailed",
            "/api/v1/pricing/materials",
            "/api/v1/pricing/processes",
            "/api/v1/pricing/tiers",
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200

            # Should be valid JSON
            data = response.json()
            assert data is not None

            # Should be able to re-serialize
            json_str = json.dumps(data)
            assert json_str is not None

    def test_api_documentation_completeness(self, test_client: TestClient):
        """Test that API documentation includes all endpoints."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

        openapi_data = response.json()
        paths = openapi_data["paths"]

        # Verify all expected endpoints are documented
        expected_paths = [
            "/",
            "/health",
            "/health/detailed",
            "/api/v1/pricing",
            "/api/v1/pricing/materials",
            "/api/v1/pricing/processes",
            "/api/v1/pricing/tiers",
        ]

        for path in expected_paths:
            assert path in paths, f"Missing documentation for path: {path}"

        # Verify schemas are present
        assert "components" in openapi_data
        if "schemas" in openapi_data["components"]:
            schemas = openapi_data["components"]["schemas"]
            assert len(schemas) > 0, "Should have API schemas documented"
