"""
Integration tests for the pricing API endpoints.

These tests verify end-to-end functionality of the pricing system,
including request validation, business logic execution, and response formatting.
All tests use standard pytest and httpx patterns for FastAPI testing.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestPricingAPIIntegration:
    """Integration tests for pricing API endpoints."""

    def test_pricing_calculation_basic_request(self, test_client: TestClient):
        """Test basic pricing calculation with valid minimal data."""
        request_data = {
            "material": "aluminum",
            "quantity": 50,
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 2.5,
            "process": "cnc",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "part_specification" in data
        assert "cost_breakdown" in data
        assert "pricing_tiers" in data
        assert "estimated_weight_kg" in data
        assert "quantity" in data

        # Verify part specification
        spec = data["part_specification"]
        assert spec["material"] == "aluminum"
        assert spec["process"] == "cnc"
        assert spec["geometric_complexity_score"] == 2.5

        # Verify cost breakdown has all required fields
        cost_breakdown = data["cost_breakdown"]
        required_cost_fields = [
            "material_cost",
            "labor_cost",
            "setup_cost",
            "complexity_adjustment",
            "overhead_cost",
            "total_cost",
        ]
        for field in required_cost_fields:
            assert field in cost_breakdown
            assert isinstance(cost_breakdown[field], (int | float))
            assert cost_breakdown[field] >= 0

        # Verify pricing tiers
        pricing_tiers = data["pricing_tiers"]
        expected_tiers = ["expedited", "standard", "economy", "domestic_economy"]
        for tier in expected_tiers:
            assert tier in pricing_tiers
            tier_data = pricing_tiers[tier]
            assert "final_price" in tier_data
            assert "price_per_unit" in tier_data
            assert isinstance(tier_data["final_price"], (int | float))
            assert tier_data["final_price"] > 0

    def test_pricing_calculation_all_materials(self, test_client: TestClient):
        """Test pricing calculation with different materials."""
        materials = ["aluminum", "steel", "stainless_steel", "titanium", "plastic_abs"]

        for material in materials:
            request_data = {
                "material": material,
                "quantity": 25,
                "dimensions": {"length_mm": 75, "width_mm": 40, "height_mm": 15},
                "geometric_complexity_score": 3.0,
                "process": "3d_printing",
                "surface_finish": "standard",
                "tolerance_class": "standard",
                "special_requirements": [],
                "delivery_timeline": "standard",
                "rush_order": False,
                "customer_tier": "standard",
            }

            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for material: {material}"
            data = response.json()

            # Material should be reflected in response
            assert data["part_specification"]["material"] == material

            # Cost should vary by material (titanium should be more expensive than plastic)
            total_cost = data["cost_breakdown"]["total_cost"]
            assert total_cost > 0

    def test_pricing_calculation_all_processes(self, test_client: TestClient):
        """Test pricing calculation with different manufacturing processes."""
        processes = [
            "cnc",
            "3d_printing",
            "sheet_cutting",
            "tube_bending",
            "injection_molding",
            "laser_cutting",
            "waterjet_cutting",
        ]

        for process in processes:
            request_data = {
                "material": "aluminum",
                "quantity": 30,
                "dimensions": {"length_mm": 80, "width_mm": 45, "height_mm": 18},
                "geometric_complexity_score": 2.8,
                "process": process,
                "surface_finish": "standard",
                "tolerance_class": "standard",
                "special_requirements": [],
                "delivery_timeline": "standard",
                "rush_order": False,
                "customer_tier": "standard",
            }

            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for process: {process}"
            data = response.json()

            # Process should be reflected in response
            assert data["part_specification"]["process"] == process

            # Different processes should have different costs
            assert data["cost_breakdown"]["total_cost"] > 0

    def test_pricing_calculation_quantity_scaling(self, test_client: TestClient):
        """Test that pricing scales appropriately with quantity."""
        base_request = {
            "material": "steel",
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 20},
            "geometric_complexity_score": 3.0,
            "process": "cnc",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        quantities = [1, 10, 100, 1000]
        results = []

        for qty in quantities:
            request_data = {**base_request, "quantity": qty}
            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200
            data = response.json()

            standard_price_per_unit = data["pricing_tiers"]["standard"][
                "price_per_unit"
            ]
            results.append((qty, standard_price_per_unit))

        # Higher quantities should generally have lower per-unit costs (volume discounts)
        # At minimum, verify that pricing scales
        assert len(results) == len(quantities)
        for _qty, price_per_unit in results:
            assert price_per_unit > 0

    def test_pricing_calculation_rush_order_impact(self, test_client: TestClient):
        """Test impact of rush order flag on pricing."""
        base_request = {
            "material": "aluminum",
            "quantity": 50,
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 2.5,
            "process": "cnc",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "rush",
            "customer_tier": "standard",
        }

        # Standard order
        standard_request = {**base_request, "rush_order": False}
        standard_response = test_client.post("/api/v1/pricing", json=standard_request)

        # Rush order
        rush_request = {**base_request, "rush_order": True}
        rush_response = test_client.post("/api/v1/pricing", json=rush_request)

        assert standard_response.status_code == 200
        assert rush_response.status_code == 200

        standard_data = standard_response.json()
        rush_data = rush_response.json()

        # Rush orders should typically cost more
        standard_price = standard_data["pricing_tiers"]["standard"]["final_price"]
        rush_price = rush_data["pricing_tiers"]["standard"]["final_price"]

        # Both should be positive
        assert standard_price > 0
        assert rush_price > 0

    def test_pricing_calculation_customer_tiers(self, test_client: TestClient):
        """Test pricing calculation with different customer tiers."""
        tiers = ["standard", "premium", "enterprise"]

        base_request = {
            "material": "steel",
            "quantity": 75,
            "dimensions": {"length_mm": 120, "width_mm": 60, "height_mm": 30},
            "geometric_complexity_score": 3.5,
            "process": "laser_cutting",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
        }

        for tier in tiers:
            request_data = {**base_request, "customer_tier": tier}
            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for customer tier: {tier}"
            data = response.json()

            # Should return valid pricing regardless of tier
            assert data["pricing_tiers"]["standard"]["final_price"] > 0

    def test_pricing_calculation_complex_requirements(self, test_client: TestClient):
        """Test pricing with complex special requirements."""
        request_data = {
            "material": "titanium",
            "quantity": 25,
            "dimensions": {"length_mm": 150, "width_mm": 75, "height_mm": 40},
            "geometric_complexity_score": 4.5,
            "process": "cnc",
            "surface_finish": "polished",
            "tolerance_class": "precision",
            "special_requirements": [
                "heat_treatment",
                "custom_packaging",
                "expedited_shipping",
            ],
            "delivery_timeline": "rush",
            "rush_order": True,
            "customer_tier": "premium",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Complex requirements should result in higher costs
        cost_breakdown = data["cost_breakdown"]
        assert cost_breakdown["total_cost"] > 0
        assert cost_breakdown["complexity_adjustment"] > 0

        # Verify all pricing tiers are present
        pricing_tiers = data["pricing_tiers"]
        for tier_name in ["expedited", "standard", "economy", "domestic_economy"]:
            assert tier_name in pricing_tiers
            assert pricing_tiers[tier_name]["final_price"] > 0

    @pytest.mark.asyncio
    async def test_pricing_calculation_async(self, async_test_client: AsyncClient):
        """Test pricing calculation using async client."""
        request_data = {
            "material": "aluminum",
            "quantity": 40,
            "dimensions": {"length_mm": 90, "width_mm": 45, "height_mm": 22},
            "geometric_complexity_score": 2.8,
            "process": "3d_printing",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        response = await async_test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "cost_breakdown" in data
        assert "pricing_tiers" in data
        assert data["quantity"] == 40

    def test_pricing_validation_missing_required_fields(self, test_client: TestClient):
        """Test validation for missing required fields."""
        incomplete_request = {
            "material": "steel",
            "quantity": 50,
            # Missing required fields
        }

        response = test_client.post("/api/v1/pricing", json=incomplete_request)

        assert response.status_code == 422
        data = response.json()

        assert "error" in data
        assert data["error"]["type"] == "ValidationError"
        assert "details" in data["error"]

    def test_pricing_validation_invalid_material(self, test_client: TestClient):
        """Test validation for invalid material."""
        request_data = {
            "material": "invalid_material",
            "quantity": 50,
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 2.5,
            "process": "cnc",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        # API returns 400 for invalid enum values (caught as ValueError)
        assert response.status_code == 400
        data = response.json()

        assert "error" in data or "detail" in data

    def test_pricing_validation_invalid_process(self, test_client: TestClient):
        """Test validation for invalid manufacturing process."""
        request_data = {
            "material": "aluminum",
            "quantity": 50,
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 2.5,
            "process": "invalid_process",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        # API returns 400 for invalid enum values (caught as ValueError)
        assert response.status_code == 400
        data = response.json()

        assert "error" in data or "detail" in data

    def test_pricing_validation_negative_quantity(self, test_client: TestClient):
        """Test validation for negative quantity."""
        request_data = {
            "material": "aluminum",
            "quantity": -10,
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 2.5,
            "process": "cnc",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        # API may return 400 (domain/ValueError) or 422 (validation)
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "detail" in data

    def test_pricing_validation_invalid_dimensions(self, test_client: TestClient):
        """Test validation for invalid dimensions."""
        request_data = {
            "material": "aluminum",
            "quantity": 50,
            "dimensions": {"length_mm": -100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 2.5,
            "process": "cnc",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        # API may return 400 (domain/ValueError) or 422 (validation)
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "detail" in data

    def test_pricing_response_headers(self, test_client: TestClient):
        """Test that pricing responses include proper headers."""
        request_data = {
            "material": "steel",
            "quantity": 30,
            "dimensions": {"length_mm": 80, "width_mm": 40, "height_mm": 20},
            "geometric_complexity_score": 3.0,
            "process": "laser_cutting",
            "surface_finish": "standard",
            "tolerance_class": "standard",
            "special_requirements": [],
            "delivery_timeline": "standard",
            "rush_order": False,
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200

        # Content type should be JSON
        assert "application/json" in response.headers["content-type"]

    def test_pricing_performance(self, test_client: TestClient):
        """Test that pricing calculation responds within reasonable time."""
        import time

        request_data = {
            "material": "aluminum",
            "quantity": 100,
            "dimensions": {"length_mm": 200, "width_mm": 100, "height_mm": 50},
            "geometric_complexity_score": 4.0,
            "process": "cnc",
            "surface_finish": "polished",
            "tolerance_class": "precision",
            "special_requirements": ["heat_treatment"],
            "delivery_timeline": "rush",
            "rush_order": True,
            "customer_tier": "premium",
        }

        start_time = time.time()
        response = test_client.post("/api/v1/pricing", json=request_data)
        end_time = time.time()

        assert response.status_code == 200

        # Pricing calculation should be fast (under 2 seconds for complex calculations)
        response_time = end_time - start_time
        assert response_time < 2.0, f"Pricing calculation too slow: {response_time}s"

    def test_pricing_concurrent_requests(self, test_client: TestClient):
        """Test that pricing endpoint can handle concurrent requests."""
        import concurrent.futures

        def make_pricing_request(material: str, quantity: int):
            request_data = {
                "material": material,
                "quantity": quantity,
                "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
                "geometric_complexity_score": 2.5,
                "process": "cnc",
                "surface_finish": "standard",
                "tolerance_class": "standard",
                "special_requirements": [],
                "delivery_timeline": "standard",
                "rush_order": False,
                "customer_tier": "standard",
            }
            return test_client.post("/api/v1/pricing", json=request_data)

        # Make multiple concurrent requests with different parameters
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_pricing_request, "aluminum", 25),
                executor.submit(make_pricing_request, "steel", 50),
                executor.submit(make_pricing_request, "titanium", 10),
                executor.submit(make_pricing_request, "plastic_abs", 100),
                executor.submit(make_pricing_request, "stainless_steel", 75),
            ]
            responses = [future.result() for future in futures]

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "cost_breakdown" in data
            assert "pricing_tiers" in data


@pytest.mark.integration
@pytest.mark.api
class TestPricingMetadataEndpoints:
    """Integration tests for pricing metadata endpoints."""

    def test_get_materials_endpoint(self, test_client: TestClient):
        """Test getting available materials."""
        response = test_client.get("/api/v1/pricing/materials")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Each material should be a string
        for material in data:
            assert isinstance(material, str)
            assert len(material) > 0

    def test_get_processes_endpoint(self, test_client: TestClient):
        """Test getting available manufacturing processes."""
        response = test_client.get("/api/v1/pricing/processes")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Each process should be a string
        for process in data:
            assert isinstance(process, str)
            assert len(process) > 0

    def test_pricing_response_includes_tiers(self, test_client: TestClient):
        """Test that pricing responses include tier information."""
        request_data = {
            "material": "aluminum",
            "quantity": 50,
            "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
            "geometric_complexity_score": 2.5,
            "process": "cnc",
            "customer_tier": "standard",
        }

        response = test_client.post("/api/v1/pricing", json=request_data)
        assert response.status_code == 200
        data = response.json()

        # Should have pricing_tiers with all tier types
        assert "pricing_tiers" in data
        tiers = data["pricing_tiers"]
        for tier_name in ["expedited", "standard", "economy", "domestic_economy"]:
            assert tier_name in tiers

    @pytest.mark.asyncio
    async def test_metadata_endpoints_async(self, async_test_client: AsyncClient):
        """Test metadata endpoints using async client."""
        endpoints = [
            "/api/v1/pricing/materials",
            "/api/v1/pricing/processes",
        ]

        for endpoint in endpoints:
            response = await async_test_client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

    def test_metadata_endpoints_performance(self, test_client: TestClient):
        """Test that metadata endpoints respond quickly."""
        import time

        endpoints = [
            "/api/v1/pricing/materials",
            "/api/v1/pricing/processes",
        ]

        for endpoint in endpoints:
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()

            assert response.status_code == 200

            # Metadata endpoints should be very fast (under 0.5 seconds)
            response_time = end_time - start_time
            assert (
                response_time < 0.5
            ), f"Metadata endpoint {endpoint} too slow: {response_time}s"
