"""
Pure Tier Calculation Functions - FUNCTIONAL CORE
"""

from app.domain.core.pricing.calculations import calculate_complexity_surcharge
from app.domain.core.pricing.discount_calculations import (
    calculate_final_discount,
    calculate_volume_discount,
)
from app.domain.core.pricing.margin_calculations import calculate_margin
from app.domain.model import (
    PriceBreakdown,
    PricingConfiguration,
    PricingRequest,
    PricingTier,
    ShippingCost,
    TierPricing,
)


def calculate_tier_pricing(
    request: PricingRequest,
    tier_configurations: dict[PricingTier, PricingConfiguration],
    tier_shipping_costs: dict[PricingTier, ShippingCost],
) -> TierPricing:
    """
    Pure function: Calculate pricing for all tiers.

    Args:
        request: Pricing request with all necessary data
        tier_configurations: Pricing config for each tier
        tier_shipping_costs: Shipping costs for each tier

    Returns:
        Pricing breakdown for all tiers
    """
    tier_prices = {}

    for tier in PricingTier:
        price_breakdown = calculate_tier_price(
            request,
            tier,
            tier_configurations[tier],
            tier_shipping_costs[tier],
        )
        tier_prices[tier.value] = price_breakdown

    return TierPricing(
        expedited=tier_prices["expedited"],
        standard=tier_prices["standard"],
        economy=tier_prices["economy"],
        domestic_economy=tier_prices["domestic_economy"],
    )


def calculate_tier_price(
    request: PricingRequest,
    tier: PricingTier,  # noqa: ARG001
    config: PricingConfiguration,
    shipping_cost_calc: ShippingCost,
) -> PriceBreakdown:
    """Pure function: Calculate price for a specific tier.

    Args:
        request: Pricing request with all necessary data
        tier: Pricing tier (not used directly but kept for API consistency)
        config: Pricing configuration for this tier
        shipping_cost_calc: Shipping cost calculator
    """
    # Base cost from manufacturing
    base_cost = request.cost_breakdown.total_cost * request.quantity

    # Calculate margin
    margin = calculate_margin(base_cost, config)

    # Calculate shipping
    shipping_cost = shipping_cost_calc.calculate_shipping_cost(
        weight_kg=request.part_weight_kg * request.quantity,
        volume_cm3=request.part_volume_cm3 * request.quantity,
        distance_zone=request.shipping_distance_zone,
    )

    # Calculate volume discount
    volume_discount = calculate_volume_discount(
        base_cost + margin, request.quantity, config
    )

    # Calculate complexity surcharge
    complexity_surcharge = calculate_complexity_surcharge(
        base_cost + margin, request.geometric_complexity_score, config
    )

    # Calculate final discount
    final_discount = calculate_final_discount(request, base_cost, margin)

    price_breakdown = PriceBreakdown.create(
        base_cost=base_cost,
        margin=margin,
        shipping_cost=shipping_cost,
        volume_discount=volume_discount,
        complexity_surcharge=complexity_surcharge,
        final_discount=final_discount,
    )

    # Calculate per-unit price
    per_unit_price = price_breakdown.final_price / request.quantity

    return PriceBreakdown(
        base_cost=price_breakdown.base_cost,
        margin=price_breakdown.margin,
        shipping_cost=price_breakdown.shipping_cost,
        volume_discount=price_breakdown.volume_discount,
        complexity_surcharge=price_breakdown.complexity_surcharge,
        subtotal=price_breakdown.subtotal,
        final_discount=price_breakdown.final_discount,
        final_price=price_breakdown.final_price,
        price_per_unit=per_unit_price,
    )
