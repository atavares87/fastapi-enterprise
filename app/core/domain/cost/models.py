"""
Cost Domain Models - DEPRECATED: Use app.core.domain.cost.models.* instead

This file now re-exports from the new SRP-compliant structure where each model
has its own file. Import directly from models package:

    from app.core.domain.cost.models import CostBreakdown, PartSpecification

Each model now has its own file following Single Responsibility Principle.
"""

# Re-export from new structure for backwards compatibility
from app.core.domain.cost.models.cost_breakdown import CostBreakdown
from app.core.domain.cost.models.enums import ManufacturingProcess, Material
from app.core.domain.cost.models.material_cost import MaterialCost
from app.core.domain.cost.models.part_dimensions import PartDimensions
from app.core.domain.cost.models.part_specification import PartSpecification
from app.core.domain.cost.models.process_cost import ProcessCost

__all__ = [
    "CostBreakdown",
    "ManufacturingProcess",
    "Material",
    "MaterialCost",
    "PartDimensions",
    "PartSpecification",
    "ProcessCost",
]
