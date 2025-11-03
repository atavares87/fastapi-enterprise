"""Pricing Request Model - Single Responsibility: Pricing request data and validation."""

from dataclasses import dataclass

from app.core.domain.cost.models import CostBreakdown


@dataclass(frozen=True)
class PricingRequest:
    """Request for pricing calculation including part specs and business parameters."""

    cost_breakdown: CostBreakdown
    geometric_complexity_score: float
    part_weight_kg: float
    part_volume_cm3: float
    quantity: int = 1
    customer_tier: str = "standard"
    shipping_distance_zone: int = 1

    def __post_init__(self) -> None:
        """Validate pricing request."""
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.part_weight_kg <= 0:
            raise ValueError("Part weight must be positive")
        if self.part_volume_cm3 <= 0:
            raise ValueError("Part volume must be positive")
        if self.shipping_distance_zone not in [1, 2, 3, 4]:
            raise ValueError("Shipping distance zone must be 1-4")
