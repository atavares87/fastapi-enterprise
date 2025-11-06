"""Cost Domain Models - Manufacturing cost entities and value objects."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.model.enums import ManufacturingProcess, Material


@dataclass(frozen=True)
class PartDimensions:
    """Physical dimensions of a manufacturing part with automatic calculations."""

    length_mm: float
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        """Validate dimensions are positive."""
        if any(dim <= 0 for dim in [self.length_mm, self.width_mm, self.height_mm]):
            raise ValueError("All dimensions must be positive")

    @property
    def volume_cm3(self) -> float:
        """Calculate part volume in cubic centimeters."""
        return (self.length_mm * self.width_mm * self.height_mm) / 1000

    @property
    def surface_area_cm2(self) -> float:
        """Calculate total surface area in square centimeters."""
        length, width, height = (
            self.length_mm / 10,
            self.width_mm / 10,
            self.height_mm / 10,
        )
        return 2 * (length * width + length * height + width * height)

    @property
    def bounding_box_diagonal_mm(self) -> float:
        """Calculate 3D diagonal of the part's bounding box."""
        return float((self.length_mm**2 + self.width_mm**2 + self.height_mm**2) ** 0.5)


@dataclass(frozen=True)
class PartSpecification:
    """Complete specification defining a part for manufacturing cost calculation."""

    dimensions: PartDimensions
    geometric_complexity_score: float
    material: Material
    process: ManufacturingProcess

    def __post_init__(self) -> None:
        """Validate part specification."""
        if not (1.0 <= self.geometric_complexity_score <= 5.0):
            raise ValueError("Geometric complexity score must be between 1.0 and 5.0")


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


@dataclass(frozen=True)
class CostBreakdown:
    """Complete breakdown of manufacturing costs with itemized components."""

    material_cost: Decimal
    labor_cost: Decimal
    setup_cost: Decimal
    complexity_adjustment: Decimal
    overhead_cost: Decimal
    total_cost: Decimal

    @classmethod
    def create(
        cls,
        material_cost: Decimal,
        labor_cost: Decimal,
        setup_cost: Decimal,
        complexity_adjustment: Decimal,
        overhead_rate: float = 0.15,
    ) -> "CostBreakdown":
        """Create cost breakdown with calculated totals."""
        base_cost = material_cost + labor_cost + setup_cost + complexity_adjustment
        overhead_cost = base_cost * Decimal(str(overhead_rate))
        total_cost = base_cost + overhead_cost

        return cls(
            material_cost=material_cost,
            labor_cost=labor_cost,
            setup_cost=setup_cost,
            complexity_adjustment=complexity_adjustment,
            overhead_cost=overhead_cost,
            total_cost=total_cost,
        )
