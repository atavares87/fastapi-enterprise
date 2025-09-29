"""
Pricing Limits Module

Provides configurable limits and safeguards for the pricing system to prevent
negative or zero final prices, control minimum margins, and enforce business rules.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.modules.pricing.domain import PriceBreakdown, PricingRequest, PricingTier


class LimitViolationType(str, Enum):
    """Types of pricing limit violations."""

    MINIMUM_PRICE = "minimum_price"
    MINIMUM_MARGIN = "minimum_margin"
    MAXIMUM_DISCOUNT = "maximum_discount"
    MINIMUM_PART_TOTAL = "minimum_part_total"
    NEGATIVE_PRICE = "negative_price"


@dataclass(frozen=True)
class PricingLimits:
    """Configuration for pricing limits and safeguards."""

    # Price floor limits
    minimum_price_per_unit: Decimal | None = (
        None  # Minimum price per unit (e.g., $1.00)
    )
    minimum_total_price: Decimal | None = (
        None  # Minimum total order price (e.g., $50.00)
    )
    minimum_part_total: Decimal | None = (
        None  # Minimum for part cost before shipping (e.g., $25.00)
    )

    # Margin protection
    minimum_margin_percentage: float | None = (
        None  # Minimum margin % (e.g., 0.10 = 10%)
    )
    minimum_margin_amount: Decimal | None = None  # Minimum margin $ amount

    # Discount limits
    maximum_total_discount_percentage: float | None = (
        None  # Max total discount (e.g., 0.30 = 30%)
    )
    maximum_volume_discount_percentage: float | None = (
        None  # Max volume discount specifically
    )

    # Cost basis protection
    minimum_price_over_cost_multiplier: float | None = (
        None  # Minimum price as multiple of cost (e.g., 1.1 = 110% of cost)
    )

    def __post_init__(self) -> None:
        """Validate pricing limits configuration."""
        if (
            self.minimum_margin_percentage is not None
            and self.minimum_margin_percentage < 0
        ):
            raise ValueError("Minimum margin percentage must be non-negative")

        if (
            self.maximum_total_discount_percentage is not None
            and self.maximum_total_discount_percentage < 0
        ):
            raise ValueError("Maximum discount percentage must be non-negative")

        if (
            self.minimum_price_over_cost_multiplier is not None
            and self.minimum_price_over_cost_multiplier < 1.0
        ):
            raise ValueError("Minimum price over cost multiplier must be at least 1.0")


@dataclass(frozen=True)
class LimitViolation:
    """Details of a pricing limit violation."""

    violation_type: LimitViolationType
    message: str
    original_value: Decimal
    adjusted_value: Decimal
    limit_value: Decimal


@dataclass(frozen=True)
class LimitedPriceBreakdown:
    """Price breakdown with applied limits and violation information."""

    price_breakdown: PriceBreakdown
    violations: list[LimitViolation]
    was_adjusted: bool

    @property
    def has_violations(self) -> bool:
        """Check if any limits were violated."""
        return len(self.violations) > 0


class PricingLimitEnforcer:
    """
    Service for enforcing pricing limits and safeguards.

    This service applies configurable limits to pricing calculations to prevent
    business-critical issues like negative prices or insufficient margins.
    """

    def __init__(self, limits: PricingLimits):
        """
        Initialize the limit enforcer with configuration.

        Args:
            limits: Pricing limits configuration
        """
        self.limits = limits

    def apply_limits(
        self,
        price_breakdown: PriceBreakdown,
        request: PricingRequest,
        tier: PricingTier,
    ) -> LimitedPriceBreakdown:
        """
        Apply pricing limits to a price breakdown.

        Args:
            price_breakdown: Original price breakdown to check and adjust
            request: Original pricing request for context
            tier: Pricing tier being calculated

        Returns:
            Limited price breakdown with violation details
        """
        violations = []
        adjusted_breakdown = price_breakdown
        violation: LimitViolation | None  # Type hint for violation variable used below

        # Check for negative or zero price (critical error)
        if price_breakdown.final_price <= 0:
            violation, adjusted_breakdown = self._fix_negative_price(
                adjusted_breakdown, request, tier
            )
            violations.append(violation)

        # Apply minimum price limits
        violation, adjusted_breakdown = self._apply_minimum_price_limits(
            adjusted_breakdown, request
        )
        if violation:
            violations.append(violation)

        # Apply minimum margin limits
        violation, adjusted_breakdown = self._apply_minimum_margin_limits(
            adjusted_breakdown, request
        )
        if violation:
            violations.append(violation)

        # Apply maximum discount limits
        violation, adjusted_breakdown = self._apply_maximum_discount_limits(
            adjusted_breakdown, request
        )
        if violation:
            violations.append(violation)

        # Apply cost basis protection
        violation, adjusted_breakdown = self._apply_cost_basis_protection(
            adjusted_breakdown, request
        )
        if violation:
            violations.append(violation)

        return LimitedPriceBreakdown(
            price_breakdown=adjusted_breakdown,
            violations=violations,
            was_adjusted=len(violations) > 0,
        )

    def validate_limits_strict(
        self,
        price_breakdown: PriceBreakdown,
        request: PricingRequest,
        tier: PricingTier,
    ) -> None:
        """
        Validate pricing limits strictly, raising exceptions for any violations.

        This method performs the same checks as apply_limits but raises
        specific exceptions instead of automatically adjusting prices.
        Useful for validation-only scenarios or when adjustments are not desired.

        Args:
            price_breakdown: Price breakdown to validate
            request: Original pricing request for context
            tier: Pricing tier being validated

        Raises:
            NegativePriceError: If final price is negative or zero
            BelowMinimumPriceError: If price falls below minimums
            InsufficientMarginError: If margin is below requirements
            ExcessiveDiscountError: If discounts exceed limits
        """
        from app.modules.pricing.exceptions import (
            BelowMinimumPriceError,
            ExcessiveDiscountError,
            InsufficientMarginError,
            NegativePriceError,
        )

        # Check for negative or zero price (critical error)
        if price_breakdown.final_price <= 0:
            raise NegativePriceError(price_breakdown.final_price, tier.value)

        # Check minimum price per unit
        actual_price_per_unit = price_breakdown.final_price / request.quantity
        if (
            self.limits.minimum_price_per_unit is not None
            and actual_price_per_unit < self.limits.minimum_price_per_unit
        ):
            raise BelowMinimumPriceError(
                actual_price_per_unit,
                self.limits.minimum_price_per_unit,
                tier.value,
                "per-unit",
            )

        # Check minimum total price
        if (
            self.limits.minimum_total_price is not None
            and price_breakdown.final_price < self.limits.minimum_total_price
        ):
            raise BelowMinimumPriceError(
                price_breakdown.final_price,
                self.limits.minimum_total_price,
                tier.value,
                "total",
            )

        # Check minimum margin percentage
        if self.limits.minimum_margin_percentage is not None:
            required_margin = price_breakdown.base_cost * Decimal(
                str(self.limits.minimum_margin_percentage)
            )
            if price_breakdown.margin < required_margin:
                raise InsufficientMarginError(
                    price_breakdown.margin, required_margin, tier.value
                )

        # Check minimum margin amount
        if (
            self.limits.minimum_margin_amount is not None
            and price_breakdown.margin < self.limits.minimum_margin_amount
        ):
            raise InsufficientMarginError(
                price_breakdown.margin, self.limits.minimum_margin_amount, tier.value
            )

        # Check maximum total discount
        if self.limits.maximum_total_discount_percentage is not None:
            base_amount = price_breakdown.base_cost + price_breakdown.margin
            if base_amount > 0:
                total_discount_amount = (
                    price_breakdown.volume_discount + price_breakdown.final_discount
                )
                total_discount_percentage = float(total_discount_amount / base_amount)

                if (
                    total_discount_percentage
                    > self.limits.maximum_total_discount_percentage
                ):
                    raise ExcessiveDiscountError(
                        total_discount_percentage,
                        self.limits.maximum_total_discount_percentage,
                        tier.value,
                    )

        # Check cost basis protection
        if self.limits.minimum_price_over_cost_multiplier is not None:
            base_cost = request.cost_breakdown.total_cost * request.quantity
            minimum_price = base_cost * Decimal(
                str(self.limits.minimum_price_over_cost_multiplier)
            )

            if price_breakdown.final_price < minimum_price:
                raise BelowMinimumPriceError(
                    price_breakdown.final_price,
                    minimum_price,
                    tier.value,
                    f"{self.limits.minimum_price_over_cost_multiplier}x cost",
                )

    def _fix_negative_price(
        self, breakdown: PriceBreakdown, request: PricingRequest, tier: PricingTier
    ) -> tuple[LimitViolation, PriceBreakdown]:
        """Fix negative or zero final price by reducing discounts."""
        original_price = breakdown.final_price

        # Calculate the minimum positive price
        min_price = Decimal("0.01")  # 1 cent minimum

        # Reduce discounts to achieve minimum price
        required_price_increase = min_price - original_price

        # First, reduce final discount
        available_final_discount = breakdown.final_discount
        final_discount_reduction = min(
            available_final_discount, required_price_increase
        )
        remaining_increase = required_price_increase - final_discount_reduction

        # Then reduce volume discount if needed
        available_volume_discount = breakdown.volume_discount
        volume_discount_reduction = min(available_volume_discount, remaining_increase)

        new_final_discount = breakdown.final_discount - final_discount_reduction
        new_volume_discount = breakdown.volume_discount - volume_discount_reduction

        # Recalculate subtotal and final price
        new_subtotal = (
            breakdown.base_cost
            + breakdown.margin
            + breakdown.shipping_cost
            + breakdown.complexity_surcharge
            - new_volume_discount
        )
        new_final_price = new_subtotal - new_final_discount
        new_price_per_unit = new_final_price / request.quantity

        adjusted_breakdown = PriceBreakdown(
            base_cost=breakdown.base_cost,
            margin=breakdown.margin,
            shipping_cost=breakdown.shipping_cost,
            volume_discount=new_volume_discount,
            complexity_surcharge=breakdown.complexity_surcharge,
            subtotal=new_subtotal,
            final_discount=new_final_discount,
            final_price=new_final_price,
            price_per_unit=new_price_per_unit,
        )

        violation = LimitViolation(
            violation_type=LimitViolationType.NEGATIVE_PRICE,
            message=f"Price was negative/zero (${original_price}), adjusted to minimum ${new_final_price}",
            original_value=original_price,
            adjusted_value=new_final_price,
            limit_value=min_price,
        )

        return violation, adjusted_breakdown

    def _apply_minimum_price_limits(
        self, breakdown: PriceBreakdown, request: PricingRequest
    ) -> tuple[LimitViolation | None, PriceBreakdown]:
        """Apply minimum price limits."""
        violation = None
        adjusted_breakdown = breakdown

        # Check minimum price per unit
        if (
            self.limits.minimum_price_per_unit is not None
            and breakdown.price_per_unit < self.limits.minimum_price_per_unit
        ):
            required_total = self.limits.minimum_price_per_unit * request.quantity
            adjustment = required_total - breakdown.final_price

            # Reduce discounts to meet minimum
            new_final_discount = max(
                Decimal("0"), breakdown.final_discount - adjustment
            )
            new_final_price = breakdown.subtotal - new_final_discount
            new_price_per_unit = new_final_price / request.quantity

            adjusted_breakdown = PriceBreakdown(
                base_cost=breakdown.base_cost,
                margin=breakdown.margin,
                shipping_cost=breakdown.shipping_cost,
                volume_discount=breakdown.volume_discount,
                complexity_surcharge=breakdown.complexity_surcharge,
                subtotal=breakdown.subtotal,
                final_discount=new_final_discount,
                final_price=new_final_price,
                price_per_unit=new_price_per_unit,
            )

            violation = LimitViolation(
                violation_type=LimitViolationType.MINIMUM_PRICE,
                message=f"Price per unit below minimum ${self.limits.minimum_price_per_unit}",
                original_value=breakdown.price_per_unit,
                adjusted_value=new_price_per_unit,
                limit_value=self.limits.minimum_price_per_unit,
            )

        # Check minimum total price (using the potentially adjusted breakdown)
        if (
            self.limits.minimum_total_price is not None
            and adjusted_breakdown.final_price < self.limits.minimum_total_price
        ):
            original_price_before_total_adjustment = adjusted_breakdown.final_price
            adjustment_needed = (
                self.limits.minimum_total_price - adjusted_breakdown.final_price
            )

            # Try to achieve minimum by reducing discounts first
            available_discount_reduction = (
                adjusted_breakdown.final_discount + adjusted_breakdown.volume_discount
            )
            discount_reduction = min(available_discount_reduction, adjustment_needed)
            remaining_adjustment = adjustment_needed - discount_reduction

            # Reduce discounts (final discount first, then volume discount)
            final_discount_reduction = min(
                adjusted_breakdown.final_discount, discount_reduction
            )
            volume_discount_reduction = discount_reduction - final_discount_reduction

            new_final_discount = (
                adjusted_breakdown.final_discount - final_discount_reduction
            )
            new_volume_discount = (
                adjusted_breakdown.volume_discount - volume_discount_reduction
            )

            # If still need more adjustment, increase the margin
            new_margin = adjusted_breakdown.margin + remaining_adjustment

            # Recalculate subtotal and final price
            new_subtotal = (
                adjusted_breakdown.base_cost
                + new_margin
                + adjusted_breakdown.shipping_cost
                + adjusted_breakdown.complexity_surcharge
                - new_volume_discount
            )
            new_final_price = new_subtotal - new_final_discount
            new_price_per_unit = new_final_price / request.quantity

            adjusted_breakdown = PriceBreakdown(
                base_cost=adjusted_breakdown.base_cost,
                margin=new_margin,
                shipping_cost=adjusted_breakdown.shipping_cost,
                volume_discount=new_volume_discount,
                complexity_surcharge=adjusted_breakdown.complexity_surcharge,
                subtotal=new_subtotal,
                final_discount=new_final_discount,
                final_price=new_final_price,
                price_per_unit=new_price_per_unit,
            )

            violation = LimitViolation(
                violation_type=LimitViolationType.MINIMUM_PRICE,
                message=f"Total price below minimum ${self.limits.minimum_total_price}",
                original_value=original_price_before_total_adjustment,
                adjusted_value=new_final_price,
                limit_value=self.limits.minimum_total_price,
            )

        return violation, adjusted_breakdown

    def _apply_minimum_margin_limits(
        self, breakdown: PriceBreakdown, request: PricingRequest
    ) -> tuple[LimitViolation | None, PriceBreakdown]:
        """Apply minimum margin limits."""
        violation = None
        adjusted_breakdown = breakdown

        current_margin_amount = breakdown.margin
        base_cost = breakdown.base_cost

        # Check minimum margin percentage
        if self.limits.minimum_margin_percentage is not None:
            required_margin = base_cost * Decimal(
                str(self.limits.minimum_margin_percentage)
            )

            if current_margin_amount < required_margin:
                margin_increase = required_margin - current_margin_amount

                # Reduce discounts to preserve margin
                total_discounts = breakdown.volume_discount + breakdown.final_discount
                max_discount_reduction = min(total_discounts, margin_increase)

                # Reduce final discount first, then volume discount
                final_discount_reduction = min(
                    breakdown.final_discount, max_discount_reduction
                )
                volume_discount_reduction = (
                    max_discount_reduction - final_discount_reduction
                )

                new_final_discount = breakdown.final_discount - final_discount_reduction
                new_volume_discount = (
                    breakdown.volume_discount - volume_discount_reduction
                )
                new_margin = breakdown.margin + max_discount_reduction

                new_subtotal = (
                    breakdown.base_cost
                    + new_margin
                    + breakdown.shipping_cost
                    + breakdown.complexity_surcharge
                    - new_volume_discount
                )
                new_final_price = new_subtotal - new_final_discount
                new_price_per_unit = new_final_price / request.quantity

                adjusted_breakdown = PriceBreakdown(
                    base_cost=breakdown.base_cost,
                    margin=new_margin,
                    shipping_cost=breakdown.shipping_cost,
                    volume_discount=new_volume_discount,
                    complexity_surcharge=breakdown.complexity_surcharge,
                    subtotal=new_subtotal,
                    final_discount=new_final_discount,
                    final_price=new_final_price,
                    price_per_unit=new_price_per_unit,
                )

                violation = LimitViolation(
                    violation_type=LimitViolationType.MINIMUM_MARGIN,
                    message=f"Margin below minimum {self.limits.minimum_margin_percentage*100}%",
                    original_value=current_margin_amount,
                    adjusted_value=new_margin,
                    limit_value=required_margin,
                )

        # Check minimum margin amount
        if (
            self.limits.minimum_margin_amount is not None
            and current_margin_amount < self.limits.minimum_margin_amount
        ):
            margin_increase = self.limits.minimum_margin_amount - current_margin_amount

            # Similar logic as above
            total_discounts = breakdown.volume_discount + breakdown.final_discount
            max_discount_reduction = min(total_discounts, margin_increase)

            final_discount_reduction = min(
                breakdown.final_discount, max_discount_reduction
            )
            volume_discount_reduction = (
                max_discount_reduction - final_discount_reduction
            )

            new_final_discount = breakdown.final_discount - final_discount_reduction
            new_volume_discount = breakdown.volume_discount - volume_discount_reduction
            new_margin = breakdown.margin + max_discount_reduction

            new_subtotal = (
                breakdown.base_cost
                + new_margin
                + breakdown.shipping_cost
                + breakdown.complexity_surcharge
                - new_volume_discount
            )
            new_final_price = new_subtotal - new_final_discount
            new_price_per_unit = new_final_price / request.quantity

            adjusted_breakdown = PriceBreakdown(
                base_cost=breakdown.base_cost,
                margin=new_margin,
                shipping_cost=breakdown.shipping_cost,
                volume_discount=new_volume_discount,
                complexity_surcharge=breakdown.complexity_surcharge,
                subtotal=new_subtotal,
                final_discount=new_final_discount,
                final_price=new_final_price,
                price_per_unit=new_price_per_unit,
            )

            violation = LimitViolation(
                violation_type=LimitViolationType.MINIMUM_MARGIN,
                message=f"Margin amount below minimum ${self.limits.minimum_margin_amount}",
                original_value=current_margin_amount,
                adjusted_value=new_margin,
                limit_value=self.limits.minimum_margin_amount,
            )

        return violation, adjusted_breakdown

    def _apply_maximum_discount_limits(
        self, breakdown: PriceBreakdown, request: PricingRequest
    ) -> tuple[LimitViolation | None, PriceBreakdown]:
        """Apply maximum discount limits."""
        violation = None
        adjusted_breakdown = breakdown

        # Calculate total discount percentage
        base_amount = breakdown.base_cost + breakdown.margin
        total_discount_amount = breakdown.volume_discount + breakdown.final_discount

        if base_amount > 0:
            total_discount_percentage = float(total_discount_amount / base_amount)

            # Check maximum total discount
            if (
                self.limits.maximum_total_discount_percentage is not None
                and total_discount_percentage
                > self.limits.maximum_total_discount_percentage
            ):
                max_discount_amount = base_amount * Decimal(
                    str(self.limits.maximum_total_discount_percentage)
                )
                discount_reduction = total_discount_amount - max_discount_amount

                # Reduce final discount first, then volume discount
                final_discount_reduction = min(
                    breakdown.final_discount, discount_reduction
                )
                volume_discount_reduction = (
                    discount_reduction - final_discount_reduction
                )

                new_final_discount = breakdown.final_discount - final_discount_reduction
                new_volume_discount = (
                    breakdown.volume_discount - volume_discount_reduction
                )

                new_subtotal = (
                    breakdown.base_cost
                    + breakdown.margin
                    + breakdown.shipping_cost
                    + breakdown.complexity_surcharge
                    - new_volume_discount
                )
                new_final_price = new_subtotal - new_final_discount
                new_price_per_unit = new_final_price / request.quantity

                adjusted_breakdown = PriceBreakdown(
                    base_cost=breakdown.base_cost,
                    margin=breakdown.margin,
                    shipping_cost=breakdown.shipping_cost,
                    volume_discount=new_volume_discount,
                    complexity_surcharge=breakdown.complexity_surcharge,
                    subtotal=new_subtotal,
                    final_discount=new_final_discount,
                    final_price=new_final_price,
                    price_per_unit=new_price_per_unit,
                )

                violation = LimitViolation(
                    violation_type=LimitViolationType.MAXIMUM_DISCOUNT,
                    message=f"Total discount exceeded maximum {self.limits.maximum_total_discount_percentage*100}%",
                    original_value=Decimal(str(total_discount_percentage)),
                    adjusted_value=Decimal(
                        str(self.limits.maximum_total_discount_percentage)
                    ),
                    limit_value=Decimal(
                        str(self.limits.maximum_total_discount_percentage)
                    ),
                )

        return violation, adjusted_breakdown

    def _apply_cost_basis_protection(
        self, breakdown: PriceBreakdown, request: PricingRequest
    ) -> tuple[LimitViolation | None, PriceBreakdown]:
        """Apply cost basis protection (minimum price over cost)."""
        violation = None
        adjusted_breakdown = breakdown

        if self.limits.minimum_price_over_cost_multiplier is not None:
            base_cost = request.cost_breakdown.total_cost * request.quantity
            minimum_price = base_cost * Decimal(
                str(self.limits.minimum_price_over_cost_multiplier)
            )

            if breakdown.final_price < minimum_price:
                price_increase_needed = minimum_price - breakdown.final_price

                # Try to achieve minimum by reducing discounts first
                available_discount_reduction = (
                    breakdown.final_discount + breakdown.volume_discount
                )
                discount_reduction = min(
                    available_discount_reduction, price_increase_needed
                )
                remaining_increase = price_increase_needed - discount_reduction

                # Reduce discounts (final discount first, then volume discount)
                final_discount_reduction = min(
                    breakdown.final_discount, discount_reduction
                )
                volume_discount_reduction = (
                    discount_reduction - final_discount_reduction
                )

                new_final_discount = breakdown.final_discount - final_discount_reduction
                new_volume_discount = (
                    breakdown.volume_discount - volume_discount_reduction
                )

                # If still need more adjustment, increase the margin
                new_margin = breakdown.margin + remaining_increase

                # Recalculate subtotal and final price
                new_subtotal = (
                    breakdown.base_cost
                    + new_margin
                    + breakdown.shipping_cost
                    + breakdown.complexity_surcharge
                    - new_volume_discount
                )
                new_final_price = new_subtotal - new_final_discount
                new_price_per_unit = new_final_price / request.quantity

                adjusted_breakdown = PriceBreakdown(
                    base_cost=breakdown.base_cost,
                    margin=new_margin,
                    shipping_cost=breakdown.shipping_cost,
                    volume_discount=new_volume_discount,
                    complexity_surcharge=breakdown.complexity_surcharge,
                    subtotal=new_subtotal,
                    final_discount=new_final_discount,
                    final_price=new_final_price,
                    price_per_unit=new_price_per_unit,
                )

                violation = LimitViolation(
                    violation_type=LimitViolationType.MINIMUM_PRICE,
                    message=f"Price below {self.limits.minimum_price_over_cost_multiplier}x cost requirement",
                    original_value=breakdown.final_price,
                    adjusted_value=new_final_price,
                    limit_value=minimum_price,
                )

        return violation, adjusted_breakdown


class PricingLimitConfigurationFactory:
    """Factory for creating common pricing limit configurations."""

    @staticmethod
    def conservative_limits() -> PricingLimits:
        """Conservative limits for business protection."""
        return PricingLimits(
            minimum_price_per_unit=Decimal("1.00"),  # $1 minimum per unit
            minimum_total_price=Decimal("25.00"),  # $25 minimum order
            minimum_margin_percentage=0.10,  # 10% minimum margin
            maximum_total_discount_percentage=0.25,  # 25% max total discount
            minimum_price_over_cost_multiplier=1.05,  # 105% of cost minimum
        )

    @staticmethod
    def aggressive_limits() -> PricingLimits:
        """More aggressive limits allowing competitive pricing."""
        return PricingLimits(
            minimum_price_per_unit=Decimal("0.50"),  # $0.50 minimum per unit
            minimum_total_price=Decimal("10.00"),  # $10 minimum order
            minimum_margin_percentage=0.05,  # 5% minimum margin
            maximum_total_discount_percentage=0.35,  # 35% max total discount
            minimum_price_over_cost_multiplier=1.02,  # 102% of cost minimum
        )

    @staticmethod
    def custom_limits(
        min_price_per_unit: Decimal | None = None,
        min_total_price: Decimal | None = None,
        min_margin_pct: float | None = None,
        max_discount_pct: float | None = None,
        min_price_over_cost: float | None = None,
    ) -> PricingLimits:
        """Create custom pricing limits."""
        return PricingLimits(
            minimum_price_per_unit=min_price_per_unit,
            minimum_total_price=min_total_price,
            minimum_margin_percentage=min_margin_pct,
            maximum_total_discount_percentage=max_discount_pct,
            minimum_price_over_cost_multiplier=min_price_over_cost,
        )
