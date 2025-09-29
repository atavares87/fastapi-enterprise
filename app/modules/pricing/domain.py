"""
Pricing Domain Models

Pure domain models for pricing calculation. These contain business logic
for calculating final prices including shipping, margins, and discounts.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.modules.cost.domain import CostBreakdown


class PricingTier(str, Enum):
    """Available pricing tiers with different service levels."""

    EXPEDITED = "expedited"  # Fastest delivery, highest price
    STANDARD = "standard"  # Standard delivery and price
    ECONOMY = "economy"  # Longer delivery, lower price
    DOMESTIC_ECONOMY = "domestic_economy"  # Domestic only, lowest price


class ShippingMethod(str, Enum):
    """Available shipping methods."""

    OVERNIGHT = "overnight"
    TWO_DAY = "two_day"
    GROUND = "ground"
    ECONOMY_GROUND = "economy_ground"
    FREIGHT = "freight"


@dataclass(frozen=True)
class ShippingCost:
    """Shipping cost calculation based on part characteristics."""

    base_cost: Decimal
    weight_factor: Decimal  # Cost per kg
    volume_factor: Decimal  # Cost per cm³ for large items
    distance_multiplier: float = 1.0  # Multiplier based on shipping distance

    def calculate_shipping_cost(
        self,
        weight_kg: float,
        volume_cm3: float,
        distance_zone: int = 1,  # 1=local, 2=regional, 3=national, 4=international
    ) -> Decimal:
        """
        Calculate shipping cost based on weight, volume, and distance.

        Args:
            weight_kg: Weight of the part in kilograms
            volume_cm3: Volume of the part in cubic centimeters
            distance_zone: Shipping distance zone (1-4)

        Returns:
            Total shipping cost
        """
        weight_cost = Decimal(str(weight_kg)) * self.weight_factor
        volume_cost = Decimal(str(volume_cm3)) * self.volume_factor

        # Use the higher of weight-based or volume-based pricing
        shipping_cost = self.base_cost + max(weight_cost, volume_cost)

        # Apply distance multiplier
        distance_multipliers = {1: 1.0, 2: 1.3, 3: 1.8, 4: 2.5}
        multiplier = distance_multipliers.get(distance_zone, 1.0)

        return shipping_cost * Decimal(str(multiplier))


@dataclass(frozen=True)
class PricingConfiguration:
    """Configuration for pricing calculations including margins and discounts."""

    margin_percentage: float  # Profit margin (e.g., 0.40 = 40%)
    volume_discount_thresholds: dict[int, float]  # Quantity -> discount percentage
    complexity_surcharge_threshold: float  # Complexity score where surcharge kicks in
    complexity_surcharge_rate: float  # Additional margin for complex parts

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
class PricingRequest:
    """Request for pricing calculation including part specs and business parameters."""

    cost_breakdown: CostBreakdown
    geometric_complexity_score: float
    part_weight_kg: float
    part_volume_cm3: float
    quantity: int = 1
    customer_tier: str = "standard"  # Could affect discounts
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

    base_cost: Decimal  # Manufacturing cost
    margin: Decimal  # Profit margin
    shipping_cost: Decimal  # Shipping charges
    volume_discount: Decimal  # Discount for quantity
    complexity_surcharge: Decimal  # Surcharge for complex parts
    subtotal: Decimal  # Before final adjustments
    final_discount: Decimal  # Any additional discounts
    final_price: Decimal  # Total price customer pays
    price_per_unit: Decimal  # Price per individual unit

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
            price_per_unit=final_price,  # Will be adjusted for quantity in service layer
        )


@dataclass(frozen=True)
class TierPricing:
    """Pricing for all available tiers."""

    expedited: PriceBreakdown
    standard: PriceBreakdown
    economy: PriceBreakdown
    domestic_economy: PriceBreakdown


class PricingEngine:
    """
    Core business logic for calculating final prices.

    This engine takes manufacturing costs and applies business rules
    for margins, shipping, discounts, and pricing tiers.
    """

    def __init__(
        self,
        tier_configurations: dict[PricingTier, PricingConfiguration],
        tier_shipping_costs: dict[PricingTier, ShippingCost],
        pricing_limits_enforcer: "PricingLimitEnforcer" = None,
    ):
        """
        Initialize pricing engine with configuration.

        Args:
            tier_configurations: Pricing config for each tier
            tier_shipping_costs: Shipping costs for each tier
            pricing_limits_enforcer: Optional enforcer for pricing limits
        """
        self.tier_configurations = tier_configurations
        self.tier_shipping_costs = tier_shipping_costs
        self.limits_enforcer = pricing_limits_enforcer

    def calculate_tier_pricing(self, request: PricingRequest) -> TierPricing:
        """
        Calculate pricing for all tiers.

        Args:
            request: Complete pricing request with costs and parameters

        Returns:
            Pricing breakdown for all available tiers
        """
        tier_prices = {}

        for tier in PricingTier:
            price_breakdown = self._calculate_tier_price(request, tier)
            tier_prices[tier.value] = price_breakdown

        return TierPricing(
            expedited=tier_prices["expedited"],
            standard=tier_prices["standard"],
            economy=tier_prices["economy"],
            domestic_economy=tier_prices["domestic_economy"],
        )

    def _calculate_tier_price(
        self, request: PricingRequest, tier: PricingTier
    ) -> PriceBreakdown:
        """Calculate price for a specific tier."""
        config = self.tier_configurations[tier]
        shipping_cost_calc = self.tier_shipping_costs[tier]

        # Base cost from manufacturing
        base_cost = request.cost_breakdown.total_cost * request.quantity

        # Calculate margin
        margin = self._calculate_margin(base_cost, config, request)

        # Calculate shipping
        shipping_cost = shipping_cost_calc.calculate_shipping_cost(
            weight_kg=request.part_weight_kg * request.quantity,
            volume_cm3=request.part_volume_cm3 * request.quantity,
            distance_zone=request.shipping_distance_zone,
        )

        # Calculate volume discount
        volume_discount = self._calculate_volume_discount(
            base_cost + margin, request.quantity, config
        )

        # Calculate complexity surcharge
        complexity_surcharge = self._calculate_complexity_surcharge(
            base_cost + margin, request.geometric_complexity_score, config
        )

        # Calculate final discount (customer-specific, promotional, etc.)
        final_discount = self._calculate_final_discount(request, tier)

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

        original_breakdown = PriceBreakdown(
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

        # Apply pricing limits if enforcer is configured
        if self.limits_enforcer is not None:
            limited_result = self.limits_enforcer.apply_limits(
                original_breakdown, request, tier
            )
            return limited_result.price_breakdown

        return original_breakdown

    def _calculate_margin(
        self, base_cost: Decimal, config: PricingConfiguration, request: PricingRequest
    ) -> Decimal:
        """Calculate profit margin based on configuration."""
        margin_rate = Decimal(str(config.margin_percentage))
        return base_cost * margin_rate

    def _calculate_volume_discount(
        self, cost_plus_margin: Decimal, quantity: int, config: PricingConfiguration
    ) -> Decimal:
        """Calculate discount based on order quantity."""
        # Find applicable discount rate
        discount_rate = Decimal("0")

        for threshold in sorted(config.volume_discount_thresholds.keys(), reverse=True):
            if quantity >= threshold:
                discount_rate = Decimal(
                    str(config.volume_discount_thresholds[threshold])
                )
                break

        return cost_plus_margin * discount_rate

    def _calculate_complexity_surcharge(
        self,
        cost_plus_margin: Decimal,
        complexity_score: float,
        config: PricingConfiguration,
    ) -> Decimal:
        """Calculate surcharge for high-complexity parts."""
        if complexity_score >= config.complexity_surcharge_threshold:
            surcharge_rate = Decimal(str(config.complexity_surcharge_rate))
            return cost_plus_margin * surcharge_rate

        return Decimal("0")

    def _calculate_final_discount(
        self, request: PricingRequest, tier: PricingTier
    ) -> Decimal:
        """
        Calculate final discounts (customer-specific, promotional, etc.).

        This would typically integrate with a customer management system
        or promotional engine. For now, we implement basic logic.
        """
        discount = Decimal("0")

        # Example: Premium customers get additional discount
        if request.customer_tier == "premium":
            discount += Decimal("0.05")  # 5% discount

        # Example: Large orders get additional discount
        if request.quantity >= 100:
            discount += Decimal("0.02")  # 2% additional discount

        # Apply discount to base cost + margin only (not shipping)
        base_amount = request.cost_breakdown.total_cost * request.quantity
        margin = base_amount * Decimal(
            str(self.tier_configurations[tier].margin_percentage)
        )

        return (base_amount + margin) * discount
