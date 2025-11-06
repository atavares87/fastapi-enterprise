"""
Integration tests for pricing router edge cases.

Tests edge cases and error paths in pricing endpoints.
"""

from fastapi.testclient import TestClient


class TestPricingRouterEdgeCases:
    """Test edge cases in pricing router."""

    def test_pricing_with_none_weight_estimation(self, test_client: TestClient):
        """Test pricing calculation triggers weight estimation when weight not provided."""
        request_data = {
            "material": "aluminum",
            "quantity": 10,
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 3.0,
            "process": "cnc",
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing/calculate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "estimated_weight_kg" in data
        assert data["estimated_weight_kg"] > 0

    def test_pricing_with_all_optional_fields(self, test_client: TestClient):
        """Test pricing calculation with all optional fields."""
        request_data = {
            "material": "steel",
            "quantity": 50,
            "dimensions": {"length_mm": 200, "width_mm": 100, "height_mm": 50},
            "geometric_complexity_score": 4.5,
            "process": "cnc",
            "surface_finish": "polished",
            "tolerance_class": "precision",
            "special_requirements": ["heat_treatment", "anodization"],
            "delivery_timeline": "rush",
            "rush_order": True,
            "customer_tier": "enterprise",
            "shipping_distance_zone": 3,
        }

        response = test_client.post("/api/v1/pricing/calculate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "pricing_tiers" in data
        assert "cost_breakdown" in data
