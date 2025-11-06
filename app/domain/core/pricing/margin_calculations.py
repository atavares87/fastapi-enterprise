"""
Pure Margin Calculation Functions - FUNCTIONAL CORE
"""

from decimal import Decimal

from app.domain.model import PricingConfiguration


def calculate_margin(base_cost: Decimal, config: PricingConfiguration) -> Decimal:
    """
    Pure function: Calculate profit margin.

    Args:
        base_cost: Base manufacturing cost
        config: Pricing configuration with margin percentage

    Returns:
        Calculated margin amount
    """
    margin_rate = Decimal(str(config.margin_percentage))
    return base_cost * margin_rate
