"""
Unit tests for discount calculations.

Tests volume discount and final discount calculations.
"""

from decimal import Decimal

from app.domain.core.pricing import calculate_final_discount, calculate_volume_discount
from app.domain.model import CostBreakdown, PricingConfiguration, PricingRequest


class TestVolumeDiscount:
    """Test cases for volume discount calculation."""

    def test_calculate_volume_discount_small_quantity(self):
        """Test volume discount for small quantity."""
        config = PricingConfiguration(
            margin_percentage=0.2,
            volume_discount_thresholds={},
            complexity_surcharge_threshold=4.0,
            complexity_surcharge_rate=0.1,
        )
        discount = calculate_volume_discount(
            cost_plus_margin=Decimal("120.00"),
            quantity=10,
            config=config,
        )
        assert discount == Decimal("0.00")

    def test_calculate_volume_discount_with_threshold(self):
        """Test volume discount with threshold."""
        config = PricingConfiguration(
            margin_percentage=0.2,
            volume_discount_thresholds={50: 0.05, 100: 0.10},
            complexity_surcharge_threshold=4.0,
            complexity_surcharge_rate=0.1,
        )
        discount = calculate_volume_discount(
            cost_plus_margin=Decimal("120.00"),
            quantity=75,
            config=config,
        )
        assert discount >= Decimal("0.00")


class TestFinalDiscount:
    """Test cases for final discount calculation."""

    def test_calculate_final_discount_standard_tier(self):
        """Test final discount for standard tier."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("50.00"),
                labor_cost=Decimal("30.00"),
                setup_cost=Decimal("20.00"),
                complexity_adjustment=Decimal("10.00"),
            ),
            part_weight_kg=1.0,
            part_volume_cm3=1000.0,
            quantity=10,
            customer_tier="standard",
            shipping_distance_zone=1,
            geometric_complexity_score=3.0,
        )

        discount = calculate_final_discount(
            request=request,
            base_cost=Decimal("125.00"),
            margin=Decimal("25.00"),
        )
        assert discount >= Decimal("0.00")

    def test_calculate_final_discount_premium_tier(self):
        """Test final discount for premium tier."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("50.00"),
                labor_cost=Decimal("30.00"),
                setup_cost=Decimal("20.00"),
                complexity_adjustment=Decimal("10.00"),
            ),
            part_weight_kg=1.0,
            part_volume_cm3=1000.0,
            quantity=10,
            customer_tier="premium",
            shipping_distance_zone=1,
            geometric_complexity_score=3.0,
        )

        base_cost = request.cost_breakdown.total_cost
        discount = calculate_final_discount(
            request=request,
            base_cost=base_cost,
            margin=Decimal("25.00"),
        )
        assert discount > Decimal("0.00")  # Premium should have discount

    def test_calculate_final_discount_high_quantity(self):
        """Test final discount with high quantity."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("50.00"),
                labor_cost=Decimal("30.00"),
                setup_cost=Decimal("20.00"),
                complexity_adjustment=Decimal("10.00"),
            ),
            part_weight_kg=1.0,
            part_volume_cm3=1000.0,
            quantity=150,  # High quantity
            customer_tier="standard",
            shipping_distance_zone=1,
            geometric_complexity_score=3.0,
        )

        base_cost = request.cost_breakdown.total_cost
        discount = calculate_final_discount(
            request=request,
            base_cost=base_cost,
            margin=Decimal("25.00"),
        )
        assert discount > Decimal("0.00")  # High quantity should have discount
