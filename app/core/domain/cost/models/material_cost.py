"""Material Cost Model - Single Responsibility: Material cost information and validation."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MaterialCost:
    """Cost information for a specific material."""

    cost_per_cm3: Decimal
    waste_factor: float
    setup_cost: Decimal

    def __post_init__(self) -> None:
        """Validate material cost parameters."""
        if self.cost_per_cm3 < 0:
            raise ValueError("Cost per cm3 must be non-negative")
        if self.waste_factor < 1.0:
            raise ValueError("Waste factor must be >= 1.0")
        if self.setup_cost < 0:
            raise ValueError("Setup cost must be non-negative")
