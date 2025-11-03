"""
Tests for Pricing Calculation Functions - FUNCTIONAL CORE

Testing pure functions is simple - no mocks needed!
"""

from decimal import Decimal

from app.core.domain.cost.models import CostBreakdown
from app.core.domain.pricing.calculations import (
    calculate_complexity_surcharge,
    estimate_weight_from_material_and_volume,
)
from app.core.domain.pricing.discount import (
    calculate_final_discount,
    calculate_volume_discount,
)
from app.core.domain.pricing.margin import calculate_margin
from app.core.domain.pricing.models import (
    PricingConfiguration,
    PricingRequest,
    ShippingCost,
)
from app.core.domain.pricing.tier import PricingTier, calculate_tier_pricing


def test_calculate_margin():
    """Test pure margin calculation."""
    base_cost = Decimal("100.00")
    config = PricingConfiguration(
        margin_percentage=0.45,
        volume_discount_thresholds={},
        complexity_surcharge_threshold=4.0,
        complexity_surcharge_rate=0.15,
    )

    result = calculate_margin(base_cost, config)

    assert result == Decimal("45.00")  # 45% of 100


def test_calculate_volume_discount():
    """Test volume discount calculation."""
    cost_plus_margin = Decimal("145.00")
    config = PricingConfiguration(
        margin_percentage=0.45,
        volume_discount_thresholds={
            10: 0.03,
            25: 0.06,
            50: 0.09,
            100: 0.12,
        },
        complexity_surcharge_threshold=4.0,
        complexity_surcharge_rate=0.15,
    )

    # Test with 50 units (should get 9% discount)
    result = calculate_volume_discount(cost_plus_margin, 50, config)
    assert result == Decimal("13.05")  # 9% of 145

    # Test with 5 units (should get 0% discount)
    result_no_discount = calculate_volume_discount(cost_plus_margin, 5, config)
    assert result_no_discount == Decimal("0")


def test_calculate_complexity_surcharge():
    """Test complexity surcharge calculation."""
    cost_plus_margin = Decimal("145.00")

    # High complexity (above threshold)
    config_high = PricingConfiguration(
        margin_percentage=0.45,
        volume_discount_thresholds={},
        complexity_surcharge_threshold=3.5,
        complexity_surcharge_rate=0.20,
    )

    result_high = calculate_complexity_surcharge(cost_plus_margin, 4.0, config_high)
    assert result_high == Decimal("29.00")  # 20% of 145

    # Low complexity (below threshold)
    result_low = calculate_complexity_surcharge(cost_plus_margin, 2.0, config_high)
    assert result_low == Decimal("0")


def test_calculate_final_discount():
    """Test final discount calculation."""
    base_cost = Decimal("100.00")
    margin = Decimal("45.00")

    # Premium customer with large quantity
    request_premium = PricingRequest(
        cost_breakdown=CostBreakdown.create(
            material_cost=Decimal("50"),
            labor_cost=Decimal("30"),
            setup_cost=Decimal("20"),
            complexity_adjustment=Decimal("0"),
        ),
        geometric_complexity_score=2.5,
        part_weight_kg=1.0,
        part_volume_cm3=125.0,
        quantity=150,  # >= 100
        customer_tier="premium",
        shipping_distance_zone=1,
    )

    result = calculate_final_discount(request_premium, base_cost, margin)
    # Should be 5% (premium) + 2% (quantity) = 7% of 145
    assert result == Decimal("10.15")

    # Standard customer with small quantity
    request_standard = PricingRequest(
        cost_breakdown=CostBreakdown.create(
            material_cost=Decimal("50"),
            labor_cost=Decimal("30"),
            setup_cost=Decimal("20"),
            complexity_adjustment=Decimal("0"),
        ),
        geometric_complexity_score=2.5,
        part_weight_kg=1.0,
        part_volume_cm3=125.0,
        quantity=10,
        customer_tier="standard",
        shipping_distance_zone=1,
    )

    result_standard = calculate_final_discount(request_standard, base_cost, margin)
    assert result_standard == Decimal("0")  # No discounts


def test_estimate_weight_from_material_and_volume():
    """Test weight estimation function."""
    # Aluminum has density of 0.00270 kg/cm³
    volume_cm3 = 1000.0  # 1000 cm³

    result = estimate_weight_from_material_and_volume("aluminum", volume_cm3)

    expected = 1000.0 * 0.00270 * 1.15
    assert result == expected


def test_calculate_tier_pricing():
    """Test tier pricing calculation with all components."""
    # Create a simple pricing request
    request = PricingRequest(
        cost_breakdown=CostBreakdown.create(
            material_cost=Decimal("30"),
            labor_cost=Decimal("50"),
            setup_cost=Decimal("20"),
            complexity_adjustment=Decimal("10"),
        ),
        geometric_complexity_score=3.0,
        part_weight_kg=2.0,
        part_volume_cm3=200.0,
        quantity=10,
        customer_tier="standard",
        shipping_distance_zone=1,
    )

    # Simple configs
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
        tier: ShippingCost(
            base_cost=Decimal("10.00"),
            weight_factor=Decimal("5.00"),
            volume_factor=Decimal("0.01"),
        )
        for tier in PricingTier
    }

    # Calculate pricing for all tiers
    result = calculate_tier_pricing(request, tier_configs, shipping_costs)

    # Verify we got pricing for all tiers
    assert result.standard.final_price > 0
    assert result.expedited.final_price > 0
    assert result.economy.final_price > 0
    assert result.domestic_economy.final_price > 0

    # Verify expedited is most expensive (highest margin)
    assert result.expedited.final_price > result.standard.final_price
    assert result.standard.final_price > result.economy.final_price
