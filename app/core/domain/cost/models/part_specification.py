"""Part Specification Model - Single Responsibility: Complete part specification and validation."""

from dataclasses import dataclass

from app.core.domain.cost.models.enums import ManufacturingProcess, Material
from app.core.domain.cost.models.part_dimensions import PartDimensions


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
