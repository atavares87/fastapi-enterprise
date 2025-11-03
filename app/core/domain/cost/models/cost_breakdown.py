"""Cost Breakdown Model - Single Responsibility: Manufacturing cost breakdown calculation and structure."""

from dataclasses import dataclass
from decimal import Decimal


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
