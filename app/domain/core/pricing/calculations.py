"""
Pure Pricing Calculation Functions - FUNCTIONAL CORE (Base)

These functions contain pure business logic with NO side effects.
"""

from decimal import Decimal

from app.domain.model import PricingConfiguration


def calculate_complexity_surcharge(
    cost_plus_margin: Decimal,
    complexity_score: float,
    config: PricingConfiguration,
) -> Decimal:
    """
    Pure function: Calculate complexity surcharge.

    Args:
        cost_plus_margin: Base cost plus margin
        complexity_score: Geometric complexity score
        config: Pricing configuration

    Returns:
        Complexity surcharge amount
    """
    if complexity_score >= config.complexity_surcharge_threshold:
        surcharge_rate = Decimal(str(config.complexity_surcharge_rate))
        return cost_plus_margin * surcharge_rate
    return Decimal("0")


def estimate_weight_from_material_and_volume(material: str, volume_cm3: float) -> float:
    """
    Pure function: Estimate part weight based on material density.

    Args:
        material: Material type
        volume_cm3: Part volume in cubic centimeters

    Returns:
        Estimated weight in kilograms
    """
    material_densities = {
        "aluminum": 0.00270,
        "steel": 0.00785,
        "stainless_steel": 0.00800,
        "plastic_abs": 0.00105,
        "plastic_pla": 0.00124,
        "plastic_petg": 0.00127,
        "titanium": 0.00451,
        "brass": 0.00850,
        "copper": 0.00896,
        "carbon_fiber": 0.00155,
    }

    density = material_densities.get(material, 0.00270)
    weight_factor = 1.15  # Buffer for features

    return volume_cm3 * density * weight_factor
