"""
Pure Discount Calculation Functions - FUNCTIONAL CORE
"""

from decimal import Decimal

from app.pricing.models import PricingConfiguration, PricingRequest


def calculate_volume_discount(
    cost_plus_margin: Decimal, quantity: int, config: PricingConfiguration
) -> Decimal:
    """
    Pure function: Calculate volume discount based on quantity thresholds.

    Args:
        cost_plus_margin: Base cost plus margin
        quantity: Number of units
        config: Pricing configuration with discount thresholds

    Returns:
        Volume discount amount
    """
    discount_rate = Decimal("0")

    for threshold in sorted(config.volume_discount_thresholds.keys(), reverse=True):
        if quantity >= threshold:
            discount_rate = Decimal(str(config.volume_discount_thresholds[threshold]))
            break

    return cost_plus_margin * discount_rate


def calculate_final_discount(
    request: PricingRequest, base_cost: Decimal, margin: Decimal
) -> Decimal:
    """
    Pure function: Calculate final discounts based on customer tier and quantity.

    Args:
        request: Pricing request with customer information
        base_cost: Base manufacturing cost
        margin: Calculated margin

    Returns:
        Final discount amount
    """
    discount = Decimal("0")

    # Premium customer discount
    if request.customer_tier == "premium":
        discount += Decimal("0.05")

    # High quantity discount
    if request.quantity >= 100:
        discount += Decimal("0.02")

    return (base_cost + margin) * discount
