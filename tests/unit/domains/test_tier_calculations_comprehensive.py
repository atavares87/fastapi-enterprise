"""
Comprehensive unit tests for tier calculations.

Tests tier pricing calculation functions with edge cases.
"""

from decimal import Decimal

from app.domain.core.pricing import calculate_tier_price, calculate_tier_pricing
from app.domain.model import (
    CostBreakdown,
    PricingConfiguration,
    PricingRequest,
    PricingTier,
    ShippingCost,
)


class TestCalculateTierPrice:
    """Test cases for calculate_tier_price function."""

    def test_calculate_tier_price_all_components(self):
        """Test calculate_tier_price includes all pricing components."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("100.00"),
                labor_cost=Decimal("50.00"),
                setup_cost=Decimal("25.00"),
                complexity_adjustment=Decimal("10.00"),
            ),
            geometric_complexity_score=4.5,  # Above threshold
            part_weight_kg=5.0,
            part_volume_cm3=500.0,
            quantity=50,  # High quantity for volume discount
            customer_tier="premium",
            shipping_distance_zone=2,
        )

        config = PricingConfiguration(
            margin_percentage=0.5,
            volume_discount_thresholds={50: 0.05, 100: 0.10},
            complexity_surcharge_threshold=4.0,
            complexity_surcharge_rate=0.15,
        )

        shipping = ShippingCost(
            base_cost=Decimal("20.00"),
            weight_factor=Decimal("2.00"),
            volume_factor=Decimal("0.02"),
        )

        result = calculate_tier_price(
            request=request,
            tier=PricingTier.STANDARD,
            config=config,
            shipping_cost_calc=shipping,
        )

        # Verify all components are present
        assert result.base_cost > 0
        assert result.margin > 0
        assert result.shipping_cost > 0
        assert result.volume_discount >= 0
        assert result.complexity_surcharge >= 0
        assert result.final_discount >= 0
        assert result.subtotal > 0
        assert result.final_price > 0
        assert result.price_per_unit > 0

        # Verify per-unit price is calculated correctly
        expected_per_unit = result.final_price / request.quantity
        assert result.price_per_unit == expected_per_unit

    def test_calculate_tier_price_small_quantity(self):
        """Test calculate_tier_price with small quantity (no volume discount)."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("50.00"),
                labor_cost=Decimal("30.00"),
                setup_cost=Decimal("20.00"),
                complexity_adjustment=Decimal("0.00"),
            ),
            geometric_complexity_score=2.0,  # Below threshold
            part_weight_kg=1.0,
            part_volume_cm3=100.0,
            quantity=5,  # Small quantity
            customer_tier="standard",
            shipping_distance_zone=1,
        )

        config = PricingConfiguration(
            margin_percentage=0.3,
            volume_discount_thresholds={50: 0.05},
            complexity_surcharge_threshold=4.0,
            complexity_surcharge_rate=0.15,
        )

        shipping = ShippingCost(
            base_cost=Decimal("10.00"),
            weight_factor=Decimal("1.00"),
            volume_factor=Decimal("0.01"),
        )

        result = calculate_tier_price(
            request=request,
            tier=PricingTier.ECONOMY,
            config=config,
            shipping_cost_calc=shipping,
        )

        # Should have no volume discount
        assert result.volume_discount == Decimal("0")
        # Should have no complexity surcharge
        assert result.complexity_surcharge == Decimal("0")

    def test_calculate_tier_price_different_tiers(self):
        """Test calculate_tier_price produces different prices for different tiers."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("100.00"),
                labor_cost=Decimal("50.00"),
                setup_cost=Decimal("25.00"),
                complexity_adjustment=Decimal("5.00"),
            ),
            geometric_complexity_score=3.0,
            part_weight_kg=2.0,
            part_volume_cm3=200.0,
            quantity=20,
            customer_tier="standard",
            shipping_distance_zone=1,
        )

        shipping = ShippingCost(
            base_cost=Decimal("15.00"),
            weight_factor=Decimal("1.50"),
            volume_factor=Decimal("0.015"),
        )

        # Standard tier config
        standard_config = PricingConfiguration(
            margin_percentage=0.45,
            volume_discount_thresholds={10: 0.03},
            complexity_surcharge_threshold=4.0,
            complexity_surcharge_rate=0.15,
        )

        # Expedited tier config (higher margin)
        expedited_config = PricingConfiguration(
            margin_percentage=0.65,
            volume_discount_thresholds={10: 0.02},
            complexity_surcharge_threshold=3.5,
            complexity_surcharge_rate=0.20,
        )

        standard_result = calculate_tier_price(
            request=request,
            tier=PricingTier.STANDARD,
            config=standard_config,
            shipping_cost_calc=shipping,
        )

        expedited_result = calculate_tier_price(
            request=request,
            tier=PricingTier.EXPEDITED,
            config=expedited_config,
            shipping_cost_calc=shipping,
        )

        # Expedited should cost more
        assert expedited_result.final_price > standard_result.final_price


class TestCalculateTierPricing:
    """Test cases for calculate_tier_pricing function."""

    def test_calculate_tier_pricing_all_tiers_different_prices(self):
        """Test calculate_tier_pricing produces different prices for each tier."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("100.00"),
                labor_cost=Decimal("50.00"),
                setup_cost=Decimal("25.00"),
                complexity_adjustment=Decimal("10.00"),
            ),
            geometric_complexity_score=3.5,
            part_weight_kg=3.0,
            part_volume_cm3=300.0,
            quantity=25,
            customer_tier="standard",
            shipping_distance_zone=1,
        )

        tier_configs = {
            PricingTier.STANDARD: PricingConfiguration(
                margin_percentage=0.45,
                volume_discount_thresholds={10: 0.03},
                complexity_surcharge_threshold=4.0,
                complexity_surcharge_rate=0.15,
            ),
            PricingTier.EXPEDITED: PricingConfiguration(
                margin_percentage=0.65,
                volume_discount_thresholds={10: 0.02},
                complexity_surcharge_threshold=3.5,
                complexity_surcharge_rate=0.20,
            ),
            PricingTier.ECONOMY: PricingConfiguration(
                margin_percentage=0.30,
                volume_discount_thresholds={10: 0.04},
                complexity_surcharge_threshold=4.5,
                complexity_surcharge_rate=0.10,
            ),
            PricingTier.DOMESTIC_ECONOMY: PricingConfiguration(
                margin_percentage=0.25,
                volume_discount_thresholds={10: 0.05},
                complexity_surcharge_threshold=5.0,
                complexity_surcharge_rate=0.05,
            ),
        }

        shipping_costs = {
            PricingTier.STANDARD: ShippingCost(
                base_cost=Decimal("20.00"),
                weight_factor=Decimal("2.00"),
                volume_factor=Decimal("0.02"),
            ),
            PricingTier.EXPEDITED: ShippingCost(
                base_cost=Decimal("30.00"),
                weight_factor=Decimal("3.00"),
                volume_factor=Decimal("0.03"),
            ),
            PricingTier.ECONOMY: ShippingCost(
                base_cost=Decimal("15.00"),
                weight_factor=Decimal("1.50"),
                volume_factor=Decimal("0.015"),
            ),
            PricingTier.DOMESTIC_ECONOMY: ShippingCost(
                base_cost=Decimal("12.00"),
                weight_factor=Decimal("1.20"),
                volume_factor=Decimal("0.012"),
            ),
        }

        result = calculate_tier_pricing(request, tier_configs, shipping_costs)

        # Verify all tiers are calculated
        assert result.standard.final_price > 0
        assert result.expedited.final_price > 0
        assert result.economy.final_price > 0
        assert result.domestic_economy.final_price > 0

        # Verify price ordering (expedited > standard > economy > domestic_economy)
        assert result.expedited.final_price > result.standard.final_price
        assert result.standard.final_price > result.economy.final_price
        assert result.economy.final_price > result.domestic_economy.final_price

    def test_calculate_tier_pricing_empty_thresholds(self):
        """Test calculate_tier_pricing with no volume discount thresholds."""
        request = PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("50.00"),
                labor_cost=Decimal("30.00"),
                setup_cost=Decimal("20.00"),
                complexity_adjustment=Decimal("0.00"),
            ),
            geometric_complexity_score=2.0,
            part_weight_kg=1.0,
            part_volume_cm3=100.0,
            quantity=10,
            customer_tier="standard",
            shipping_distance_zone=1,
        )

        config = PricingConfiguration(
            margin_percentage=0.4,
            volume_discount_thresholds={},  # No thresholds
            complexity_surcharge_threshold=4.0,
            complexity_surcharge_rate=0.15,
        )

        shipping = ShippingCost(
            base_cost=Decimal("10.00"),
            weight_factor=Decimal("1.00"),
            volume_factor=Decimal("0.01"),
        )

        tier_configs = dict.fromkeys(PricingTier, config)
        shipping_costs = dict.fromkeys(PricingTier, shipping)

        result = calculate_tier_pricing(request, tier_configs, shipping_costs)

        # All tiers should have zero volume discount
        assert result.standard.volume_discount == Decimal("0")
        assert result.expedited.volume_discount == Decimal("0")
        assert result.economy.volume_discount == Decimal("0")
        assert result.domestic_economy.volume_discount == Decimal("0")
