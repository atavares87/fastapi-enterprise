"""
Tier Subdomain Models - Pricing tiers and tier-specific pricing
"""

from dataclasses import dataclass
from enum import Enum

from app.core.domain.pricing.models import PriceBreakdown


class PricingTier(str, Enum):
    """Available pricing tiers with different service levels."""

    EXPEDITED = "expedited"
    STANDARD = "standard"
    ECONOMY = "economy"
    DOMESTIC_ECONOMY = "domestic_economy"


@dataclass(frozen=True)
class TierPricing:
    """Pricing for all available tiers."""

    expedited: PriceBreakdown
    standard: PriceBreakdown
    economy: PriceBreakdown
    domestic_economy: PriceBreakdown
