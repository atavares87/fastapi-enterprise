"""
Pricing Domain - Manufacturing part pricing with subdomains

Subdomains:
- tier: Pricing tier management and tier-specific pricing
- discount: Volume discounts and customer discounts
- margin: Profit margin calculations
"""

from app.core.domain.pricing.calculations import (
    calculate_complexity_surcharge,
    estimate_weight_from_material_and_volume,
)

# Discount subdomain
from app.core.domain.pricing.discount import (
    calculate_final_discount,
    calculate_volume_discount,
)

# Margin subdomain
from app.core.domain.pricing.margin import calculate_margin

# Base pricing models and calculations
from app.core.domain.pricing.models import (
    PriceBreakdown,
    PricingConfiguration,
    PricingRequest,
    ShippingCost,
)

# Tier subdomain
from app.core.domain.pricing.tier import (
    PricingTier,
    TierPricing,
    calculate_tier_price,
    calculate_tier_pricing,
)

__all__ = [
    # Base pricing
    "PriceBreakdown",
    "PricingConfiguration",
    "PricingRequest",
    "ShippingCost",
    "calculate_complexity_surcharge",
    "estimate_weight_from_material_and_volume",
    # Tier subdomain
    "PricingTier",
    "TierPricing",
    "calculate_tier_pricing",
    "calculate_tier_price",
    # Discount subdomain
    "calculate_volume_discount",
    "calculate_final_discount",
    # Margin subdomain
    "calculate_margin",
]
