"""
Test data factory for integration tests.

Provides standardized test data generation for pricing API tests,
ensuring consistent and comprehensive test coverage.
"""

from typing import Any

import pytest


class PricingTestDataFactory:
    """Factory for generating test data for pricing API tests."""

    @staticmethod
    def create_basic_pricing_request(**overrides) -> dict[str, Any]:
        """Create a basic valid pricing request with optional overrides."""
        base_request = {
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
        base_request.update(overrides)
        return base_request

    @staticmethod
    def create_minimal_pricing_request(**overrides) -> dict[str, Any]:
        """Create a minimal valid pricing request."""
        minimal_request = {
            "material": "aluminum",
            "quantity": 1,
            "dimensions": {"length_mm": 10, "width_mm": 10, "height_mm": 10},
            "geometric_complexity_score": 1.0,
            "process": "3d_printing",
        }
        minimal_request.update(overrides)
        return minimal_request

    @staticmethod
    def create_complex_pricing_request(**overrides) -> dict[str, Any]:
        """Create a complex pricing request with many special requirements."""
        complex_request = {
            "material": "titanium",
            "quantity": 500,
            "dimensions": {"length_mm": 500, "width_mm": 300, "height_mm": 100},
            "geometric_complexity_score": 4.8,
            "process": "cnc",
            "surface_finish": "polished",
            "tolerance_class": "precision",
            "special_requirements": [
                "heat_treatment",
                "custom_packaging",
                "expedited_shipping",
                "quality_certification",
                "custom_tooling",
            ],
            "delivery_timeline": "rush",
            "rush_order": True,
            "customer_tier": "enterprise",
        }
        complex_request.update(overrides)
        return complex_request

    @staticmethod
    def get_all_materials() -> list[str]:
        """Get list of all valid materials."""
        return [
            "aluminum",
            "steel",
            "stainless_steel",
            "plastic_abs",
            "plastic_pla",
            "plastic_petg",
            "titanium",
            "brass",
            "copper",
            "carbon_fiber",
        ]

    @staticmethod
    def get_all_processes() -> list[str]:
        """Get list of all valid manufacturing processes."""
        return [
            "cnc",
            "3d_printing",
            "sheet_cutting",
            "tube_bending",
            "injection_molding",
            "laser_cutting",
            "waterjet_cutting",
        ]

    @staticmethod
    def get_all_surface_finishes() -> list[str]:
        """Get list of all valid surface finishes."""
        return ["standard", "polished", "anodized", "painted"]

    @staticmethod
    def get_all_tolerance_classes() -> list[str]:
        """Get list of all valid tolerance classes."""
        return ["standard", "precision", "ultra_precision"]

    @staticmethod
    def get_all_delivery_timelines() -> list[str]:
        """Get list of all valid delivery timelines."""
        return ["standard", "expedited", "rush"]

    @staticmethod
    def get_all_customer_tiers() -> list[str]:
        """Get list of all valid customer tiers."""
        return ["standard", "premium", "enterprise"]

    @staticmethod
    def get_valid_special_requirements() -> list[str]:
        """Get list of valid special requirements."""
        return [
            "heat_treatment",
            "surface_coating",
            "custom_packaging",
            "expedited_shipping",
            "quality_certification",
            "custom_tooling",
            "assembly_required",
            "testing_required",
        ]

    @classmethod
    def create_requests_for_all_materials(cls) -> list[dict[str, Any]]:
        """Create pricing requests for all materials."""
        requests = []
        for material in cls.get_all_materials():
            request = cls.create_basic_pricing_request(material=material)
            requests.append(request)
        return requests

    @classmethod
    def create_requests_for_all_processes(cls) -> list[dict[str, Any]]:
        """Create pricing requests for all processes."""
        requests = []
        for process in cls.get_all_processes():
            request = cls.create_basic_pricing_request(process=process)
            requests.append(request)
        return requests

    @classmethod
    def create_quantity_variation_requests(cls) -> list[dict[str, Any]]:
        """Create pricing requests with different quantities."""
        quantities = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500]
        requests = []
        for qty in quantities:
            request = cls.create_basic_pricing_request(quantity=qty)
            requests.append(request)
        return requests

    @classmethod
    def create_dimension_variation_requests(cls) -> list[dict[str, Any]]:
        """Create pricing requests with different dimensions."""
        dimension_sets = [
            {"length_mm": 10, "width_mm": 10, "height_mm": 10},  # Small
            {"length_mm": 100, "width_mm": 50, "height_mm": 25},  # Medium
            {"length_mm": 500, "width_mm": 300, "height_mm": 100},  # Large
            {"length_mm": 1000, "width_mm": 10, "height_mm": 5},  # Long and thin
            {"length_mm": 50, "width_mm": 50, "height_mm": 200},  # Tall
        ]
        requests = []
        for dimensions in dimension_sets:
            request = cls.create_basic_pricing_request(dimensions=dimensions)
            requests.append(request)
        return requests

    @classmethod
    def create_complexity_variation_requests(cls) -> list[dict[str, Any]]:
        """Create pricing requests with different complexity scores."""
        complexity_scores = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
        requests = []
        for score in complexity_scores:
            request = cls.create_basic_pricing_request(geometric_complexity_score=score)
            requests.append(request)
        return requests

    @classmethod
    def create_invalid_requests(cls) -> list[dict[str, Any]]:
        """Create invalid pricing requests for validation testing."""
        return [
            # Missing required fields
            {"material": "aluminum"},
            {"quantity": 50},
            {"dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25}},
            # Invalid material
            cls.create_basic_pricing_request(material="invalid_material"),
            # Invalid process
            cls.create_basic_pricing_request(process="invalid_process"),
            # Negative quantity
            cls.create_basic_pricing_request(quantity=-10),
            # Zero quantity
            cls.create_basic_pricing_request(quantity=0),
            # Negative dimensions
            cls.create_basic_pricing_request(
                dimensions={"length_mm": -100, "width_mm": 50, "height_mm": 25}
            ),
            # Zero dimensions
            cls.create_basic_pricing_request(
                dimensions={"length_mm": 0, "width_mm": 50, "height_mm": 25}
            ),
            # Invalid complexity score (too low)
            cls.create_basic_pricing_request(geometric_complexity_score=0.5),
            # Invalid complexity score (too high)
            cls.create_basic_pricing_request(geometric_complexity_score=6.0),
            # Invalid surface finish
            cls.create_basic_pricing_request(surface_finish="invalid_finish"),
            # Invalid tolerance class
            cls.create_basic_pricing_request(tolerance_class="invalid_tolerance"),
            # Invalid delivery timeline
            cls.create_basic_pricing_request(delivery_timeline="invalid_timeline"),
            # Invalid customer tier
            cls.create_basic_pricing_request(customer_tier="invalid_tier"),
        ]


@pytest.mark.integration
@pytest.mark.api
class TestPricingEdgeCases:
    """Edge case tests for pricing API using test data factory."""

    def test_minimal_valid_request(self, test_client):
        """Test pricing with minimal valid request."""
        request_data = PricingTestDataFactory.create_minimal_pricing_request()
        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "cost_breakdown" in data
        assert "pricing_tiers" in data

    def test_maximum_complexity_request(self, test_client):
        """Test pricing with maximum complexity request."""
        request_data = PricingTestDataFactory.create_complex_pricing_request()
        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Complex requests should have higher costs
        cost_breakdown = data["cost_breakdown"]
        assert cost_breakdown["complexity_adjustment"] > 0
        assert cost_breakdown["total_cost"] > 100  # Should be substantial

    def test_all_materials_compatibility(self, test_client):
        """Test that all materials work with all processes."""
        materials = PricingTestDataFactory.get_all_materials()
        processes = PricingTestDataFactory.get_all_processes()

        for material in materials:
            for process in processes:
                request_data = PricingTestDataFactory.create_basic_pricing_request(
                    material=material, process=process
                )
                response = test_client.post("/api/v1/pricing", json=request_data)

                assert response.status_code == 200, f"Failed for {material} + {process}"
                data = response.json()
                assert data["part_specification"]["material"] == material
                assert data["part_specification"]["process"] == process

    def test_extreme_quantities(self, test_client):
        """Test pricing with extreme quantities."""
        extreme_quantities = [1, 10000]

        for quantity in extreme_quantities:
            request_data = PricingTestDataFactory.create_basic_pricing_request(
                quantity=quantity
            )
            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for quantity: {quantity}"
            data = response.json()
            assert data["quantity"] == quantity
            assert data["cost_breakdown"]["total_cost"] > 0

    def test_extreme_dimensions(self, test_client):
        """Test pricing with extreme dimensions."""
        extreme_dimensions = [
            {"length_mm": 1, "width_mm": 1, "height_mm": 1},  # Tiny
            {"length_mm": 2000, "width_mm": 1000, "height_mm": 500},  # Large
        ]

        for dimensions in extreme_dimensions:
            request_data = PricingTestDataFactory.create_basic_pricing_request(
                dimensions=dimensions
            )
            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for dimensions: {dimensions}"
            data = response.json()

            # Verify volume calculation
            spec_dimensions = data["part_specification"]["dimensions"]
            expected_volume = (
                dimensions["length_mm"]
                * dimensions["width_mm"]
                * dimensions["height_mm"]
            ) / 1000  # Convert to cm³
            assert abs(spec_dimensions["volume_cm3"] - expected_volume) < 0.01

    def test_all_combinations_surface_finish_tolerance(self, test_client):
        """Test all combinations of surface finish and tolerance class."""
        finishes = PricingTestDataFactory.get_all_surface_finishes()
        tolerances = PricingTestDataFactory.get_all_tolerance_classes()

        for finish in finishes:
            for tolerance in tolerances:
                request_data = PricingTestDataFactory.create_basic_pricing_request(
                    surface_finish=finish, tolerance_class=tolerance
                )
                response = test_client.post("/api/v1/pricing", json=request_data)

                assert response.status_code == 200, f"Failed for {finish} + {tolerance}"

    def test_all_customer_tiers_with_rush_orders(self, test_client):
        """Test all customer tiers with rush orders."""
        tiers = PricingTestDataFactory.get_all_customer_tiers()

        for tier in tiers:
            # Test with rush order
            request_data = PricingTestDataFactory.create_basic_pricing_request(
                customer_tier=tier, rush_order=True, delivery_timeline="rush"
            )
            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for tier: {tier}"

            # Test without rush order
            request_data = PricingTestDataFactory.create_basic_pricing_request(
                customer_tier=tier, rush_order=False, delivery_timeline="standard"
            )
            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for tier: {tier} (no rush)"

    def test_maximum_special_requirements(self, test_client):
        """Test with maximum number of special requirements."""
        all_requirements = PricingTestDataFactory.get_valid_special_requirements()

        request_data = PricingTestDataFactory.create_basic_pricing_request(
            special_requirements=all_requirements
        )
        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should handle all requirements without error
        assert "cost_breakdown" in data
        assert "pricing_tiers" in data

    def test_boundary_complexity_scores(self, test_client):
        """Test boundary values for complexity scores."""
        boundary_scores = [1.0, 5.0]  # Min and max valid values

        for score in boundary_scores:
            request_data = PricingTestDataFactory.create_basic_pricing_request(
                geometric_complexity_score=score
            )
            response = test_client.post("/api/v1/pricing", json=request_data)

            assert response.status_code == 200, f"Failed for complexity score: {score}"
            data = response.json()
            assert data["part_specification"]["geometric_complexity_score"] == score

    def test_unicode_handling_in_special_requirements(self, test_client):
        """Test handling of Unicode characters in special requirements."""
        unicode_requirements = ["custom_ñame", "spëcial_chärs", "emoji_🔧"]

        request_data = PricingTestDataFactory.create_basic_pricing_request(
            special_requirements=unicode_requirements
        )
        response = test_client.post("/api/v1/pricing", json=request_data)

        # Should handle Unicode gracefully (either accept or reject consistently)
        assert response.status_code in [200, 422]  # Either works or validation error

    def test_empty_special_requirements_list(self, test_client):
        """Test with empty special requirements list."""
        request_data = PricingTestDataFactory.create_basic_pricing_request(
            special_requirements=[]
        )
        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "cost_breakdown" in data

    def test_decimal_precision_dimensions(self, test_client):
        """Test with high precision decimal dimensions."""
        precise_dimensions = {
            "length_mm": 100.12345,
            "width_mm": 50.67890,
            "height_mm": 25.11111,
        }

        request_data = PricingTestDataFactory.create_basic_pricing_request(
            dimensions=precise_dimensions
        )
        response = test_client.post("/api/v1/pricing", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Verify precision is maintained
        spec_dims = data["part_specification"]["dimensions"]
        assert abs(spec_dims["length_mm"] - precise_dimensions["length_mm"]) < 0.0001

    def test_pricing_consistency_multiple_calls(self, test_client):
        """Test that identical requests produce identical results."""
        request_data = PricingTestDataFactory.create_basic_pricing_request()

        responses = []
        for _ in range(3):
            response = test_client.post("/api/v1/pricing", json=request_data)
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical
        first_response = responses[0]
        for response in responses[1:]:
            assert (
                response == first_response
            ), "Pricing should be consistent for identical requests"

    @pytest.mark.parametrize(
        "invalid_request", PricingTestDataFactory.create_invalid_requests()[:5]
    )  # Test first 5
    def test_invalid_request_validation(self, test_client, invalid_request):
        """Test validation of invalid requests."""
        response = test_client.post("/api/v1/pricing", json=invalid_request)

        # API may return 422 (validation) or 400 (domain/ValueError)
        assert response.status_code in [400, 422]
        data = response.json()
        assert "error" in data or "detail" in data
