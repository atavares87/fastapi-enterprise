"""
Pricing Domain Models - DEPRECATED: Use app.core.domain.pricing.models.* instead

This file now re-exports from the new SRP-compliant structure where each model
has its own file. Import directly from models package:

    from app.core.domain.pricing.models import PriceBreakdown, PricingRequest

Each model now has its own file following Single Responsibility Principle.
"""

# Re-export from new structure for backwards compatibility
from app.core.domain.pricing.models.price_breakdown import PriceBreakdown
from app.core.domain.pricing.models.pricing_configuration import PricingConfiguration
from app.core.domain.pricing.models.pricing_request import PricingRequest
from app.core.domain.pricing.models.shipping_cost import ShippingCost

__all__ = [
    "PriceBreakdown",
    "PricingConfiguration",
    "PricingRequest",
    "ShippingCost",
]
