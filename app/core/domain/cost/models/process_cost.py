"""Process Cost Model - Single Responsibility: Manufacturing process cost information and validation."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ProcessCost:
    """Cost information for a specific manufacturing process."""

    hourly_rate: Decimal
    setup_time_hours: float
    complexity_multiplier: dict[float, float]

    def __post_init__(self) -> None:
        """Validate process cost parameters."""
        if self.hourly_rate < 0:
            raise ValueError("Hourly rate must be non-negative")
        if self.setup_time_hours < 0:
            raise ValueError("Setup time must be non-negative")
