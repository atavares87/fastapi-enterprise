"""Pricing Configuration Model - Single Responsibility: Pricing configuration and validation."""

from dataclasses import dataclass


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
