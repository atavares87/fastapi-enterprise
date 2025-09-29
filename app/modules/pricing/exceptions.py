"""
Pricing-specific exceptions for better error handling and user feedback.
"""

from decimal import Decimal

from app.modules.pricing.limits import LimitViolation


class PricingError(Exception):
    """Base exception for pricing-related errors."""

    pass


class PricingLimitViolationError(PricingError):
    """Raised when pricing limits are violated and cannot be automatically corrected."""

    def __init__(self, message: str, violations: list[LimitViolation]):
        super().__init__(message)
        self.violations = violations

    def __str__(self) -> str:
        violation_details = []
        for violation in self.violations:
            violation_details.append(
                f"  - {violation.violation_type.value}: {violation.message}"
            )

        details = "\n".join(violation_details)
        return f"{super().__str__()}\nViolations:\n{details}"


class InvalidPricingConfigurationError(PricingError):
    """Raised when pricing configuration is invalid."""

    pass


class NegativePriceError(PricingError):
    """Raised when pricing calculation results in negative price that cannot be corrected."""

    def __init__(self, final_price: Decimal, tier: str):
        self.final_price = final_price
        self.tier = tier
        super().__init__(
            f"Pricing calculation for tier '{tier}' resulted in negative price: ${final_price}. "
            f"This indicates discounts exceed the base cost + margin. Consider adjusting discount policies."
        )


class InsufficientMarginError(PricingError):
    """Raised when margin requirements cannot be met."""

    def __init__(self, current_margin: Decimal, required_margin: Decimal, tier: str):
        self.current_margin = current_margin
        self.required_margin = required_margin
        self.tier = tier
        super().__init__(
            f"Tier '{tier}' margin ${current_margin} is below required minimum ${required_margin}. "
            f"Consider reducing discounts or increasing base margins."
        )


class ExcessiveDiscountError(PricingError):
    """Raised when discount limits are exceeded."""

    def __init__(self, discount_percentage: float, max_allowed: float, tier: str):
        self.discount_percentage = discount_percentage
        self.max_allowed = max_allowed
        self.tier = tier
        super().__init__(
            f"Tier '{tier}' total discount {discount_percentage:.1%} exceeds maximum allowed {max_allowed:.1%}. "
            f"Review discount policies to ensure profitability."
        )


class BelowMinimumPriceError(PricingError):
    """Raised when price falls below configured minimums."""

    def __init__(
        self,
        current_price: Decimal,
        minimum_price: Decimal,
        tier: str,
        price_type: str = "total",
    ):
        self.current_price = current_price
        self.minimum_price = minimum_price
        self.tier = tier
        self.price_type = price_type
        super().__init__(
            f"Tier '{tier}' {price_type} price ${current_price} is below minimum ${minimum_price}. "
            f"Consider adjusting pricing strategy or minimum price requirements."
        )
