"""
Cost Domain Ports - Interfaces for Imperative Shell

Ports define how the functional core communicates with the outside world
without depending on specific implementations.
"""

from typing import Protocol

from app.core.domain.cost.models import (
    ManufacturingProcess,
    Material,
    MaterialCost,
    ProcessCost,
)


class CostDataPort(Protocol):
    """
    Port for accessing cost data.

    This interface defines how the functional core requests cost data
    without knowing where it comes from (database, API, config, etc.).
    """

    async def get_material_costs(self) -> dict[Material, MaterialCost]:
        """
        Get material costs from data source.

        Returns:
            Dictionary mapping materials to their cost information
        """
        ...

    async def get_process_costs(self) -> dict[ManufacturingProcess, ProcessCost]:
        """
        Get process costs from data source.

        Returns:
            Dictionary mapping processes to their cost information
        """
        ...
