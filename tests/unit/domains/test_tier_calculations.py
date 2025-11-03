"""
Unit tests for tier calculations.

Tests tier pricing calculation functions.
"""

from decimal import Decimal

import pytest

from app.core.domain.cost.models import CostBreakdown
from app.core.domain.pricing.models import (
    PricingConfiguration,
    PricingRequest,
    ShippingCost,
)
from app.core.domain.pricing.tier.calculations import (
    calculate_tier_price,
    calculate_tier_pricing,
)
from app.core.domain.pricing.tier.models import PricingTier


class TestTierCalculations:
    """Test cases for tier calculation functions."""

    @pytest.fixture
    def base_request(self):
        """Create base pricing request."""
        return PricingRequest(
            cost_breakdown=CostBreakdown.create(
                material_cost=Decimal("50.00"),
                labor_cost=Decimal("30.00"),
                setup_cost=Decimal("20.00"),
                complexity_adjustment=Decimal("10.00"),
            ),
            geometric_complexity_score=3.0,
            part_weight_kg=2.0,
            part_volume_cm3=200.0,
            quantity=10,
            customer_tier="standard",
            shipping_distance_zone=1,
        )

    @pytest.fixture
    def base_config(self):
        """Create base pricing configuration."""
        return PricingConfiguration(
            margin_percentage=0.45,
            volume_discount_thresholds={10: 0.03},
            complexity_surcharge_threshold=4.0,
            complexity_surcharge_rate=0.15,
        )

    @pytest.fixture
    def base_shipping(self):
        """Create base shipping cost."""
        return ShippingCost(
            base_cost=Decimal("10.00"),
            weight_factor=Decimal("5.00"),
            volume_factor=Decimal("0.01"),
        )

    def test_calculate_tier_price_standard(
        self, base_request, base_config, base_shipping
    ):
        """Test calculate_tier_price for standard tier."""
        result = calculate_tier_price(
            request=base_request,
            tier=PricingTier.STANDARD,
            config=base_config,
            shipping_cost_calc=base_shipping,
        )

        assert result.final_price > 0
        assert result.price_per_unit > 0
        assert result.base_cost > 0

    def test_calculate_tier_pricing_all_tiers(
        self, base_request, base_config, base_shipping
    ):
        """Test calculate_tier_pricing for all tiers."""
        tier_configs = {
            PricingTier.STANDARD: base_config,
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

        shipping_costs = dict.fromkeys(PricingTier, base_shipping)

        result = calculate_tier_pricing(base_request, tier_configs, shipping_costs)

        assert result.standard.final_price > 0
        assert result.expedited.final_price > 0
        assert result.economy.final_price > 0
        assert result.domestic_economy.final_price > 0
