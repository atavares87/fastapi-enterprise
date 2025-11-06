"""Pricing Domain Models - Pricing entities and value objects."""

from dataclasses import dataclass
from decimal import Decimal

from app.cost.models import CostBreakdown


@dataclass(frozen=True)
class PricingConfiguration:
    """Configuration for pricing calculations including margins and discounts."""

    margin_percentage: float
    volume_discount_thresholds: dict[int, float]
    complexity_surcharge_threshold: float
    complexity_surcharge_rate: float

    def __post_init__(self) -> None:
        """Validate pricing configuration."""
        if self.margin_percentage < 0:
            raise ValueError("Margin percentage must be non-negative")
        if (
            self.complexity_surcharge_threshold < 1.0
            or self.complexity_surcharge_threshold > 5.0
        ):
            raise ValueError("Complexity threshold must be between 1.0 and 5.0")
        if self.complexity_surcharge_rate < 0:
            raise ValueError("Complexity surcharge rate must be non-negative")


@dataclass(frozen=True)
class ShippingCost:
    """Shipping cost calculation based on part characteristics."""

    base_cost: Decimal
    weight_factor: Decimal
    volume_factor: Decimal
    distance_multiplier: float = 1.0

    def calculate_shipping_cost(
        self,
        weight_kg: float,
        volume_cm3: float,
        distance_zone: int = 1,
    ) -> Decimal:
        """
        Pure function: Calculate shipping cost based on weight, volume, and distance.

        Args:
            weight_kg: Weight of the part in kilograms
            volume_cm3: Volume of the part in cubic centimeters
            distance_zone: Shipping distance zone (1-4)

        Returns:
            Total shipping cost
        """
        weight_cost = Decimal(str(weight_kg)) * self.weight_factor
        volume_cost = Decimal(str(volume_cm3)) * self.volume_factor

        shipping_cost = self.base_cost + max(weight_cost, volume_cost)

        distance_multipliers = {1: 1.0, 2: 1.3, 3: 1.8, 4: 2.5}
        multiplier = distance_multipliers.get(distance_zone, 1.0)

        return shipping_cost * Decimal(str(multiplier))


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


@dataclass(frozen=True)
class PriceBreakdown:
    """Detailed breakdown of final pricing including all components."""

    base_cost: Decimal
    margin: Decimal
    shipping_cost: Decimal
    volume_discount: Decimal
    complexity_surcharge: Decimal
    subtotal: Decimal
    final_discount: Decimal
    final_price: Decimal
    price_per_unit: Decimal

    @classmethod
    def create(
        cls,
        base_cost: Decimal,
        margin: Decimal,
        shipping_cost: Decimal,
        volume_discount: Decimal = Decimal("0"),
        complexity_surcharge: Decimal = Decimal("0"),
        final_discount: Decimal = Decimal("0"),
    ) -> "PriceBreakdown":
        """Create price breakdown with calculated totals."""
        subtotal = (
            base_cost + margin + shipping_cost + complexity_surcharge - volume_discount
        )
        final_price = subtotal - final_discount

        return cls(
            base_cost=base_cost,
            margin=margin,
            shipping_cost=shipping_cost,
            volume_discount=volume_discount,
            complexity_surcharge=complexity_surcharge,
            subtotal=subtotal,
            final_discount=final_discount,
            final_price=final_price,
            price_per_unit=final_price,
        )


@dataclass(frozen=True)
class TierPricing:
    """Pricing for all available tiers."""

    expedited: PriceBreakdown
    standard: PriceBreakdown
    economy: PriceBreakdown
    domestic_economy: PriceBreakdown
