"""
Cost Data Adapter - IMPERATIVE SHELL

Provides cost data from configuration or database.
All I/O operations isolated here.
"""

from decimal import Decimal

from app.core.domain.cost.models import (
    ManufacturingProcess,
    Material,
    MaterialCost,
    ProcessCost,
)


class CostDataAdapter:
    """
    Adapter that provides cost data.

    Currently uses hardcoded defaults (from old service layer),
    but could load from:
    - Database
    - External API
    - Configuration service
    - Redis cache
    """

    async def get_material_costs(self) -> dict[Material, MaterialCost]:
        """
        Get material costs (I/O operation).

        In production, this might:
        - Query database
        - Call external pricing API
        - Load from cache
        """
        # For now, return defaults (migrated from old CostCalculationService)
        return self._get_default_material_costs()

    async def get_process_costs(self) -> dict[ManufacturingProcess, ProcessCost]:
        """
        Get process costs (I/O operation).

        In production, this might:
        - Query database
        - Load from configuration service
        - Read from cache
        """
        return self._get_default_process_costs()

    def _get_default_material_costs(self) -> dict[Material, MaterialCost]:
        """Load default material costs (migrated from old service)."""
        return {
            Material.ALUMINUM: MaterialCost(
                cost_per_cm3=Decimal("0.15"),
                waste_factor=1.15,
                setup_cost=Decimal("25.00"),
            ),
            Material.STEEL: MaterialCost(
                cost_per_cm3=Decimal("0.08"),
                waste_factor=1.20,
                setup_cost=Decimal("30.00"),
            ),
            Material.STAINLESS_STEEL: MaterialCost(
                cost_per_cm3=Decimal("0.25"),
                waste_factor=1.15,
                setup_cost=Decimal("35.00"),
            ),
            Material.PLASTIC_ABS: MaterialCost(
                cost_per_cm3=Decimal("0.05"),
                waste_factor=1.10,
                setup_cost=Decimal("10.00"),
            ),
            Material.PLASTIC_PLA: MaterialCost(
                cost_per_cm3=Decimal("0.04"),
                waste_factor=1.05,
                setup_cost=Decimal("5.00"),
            ),
            Material.PLASTIC_PETG: MaterialCost(
                cost_per_cm3=Decimal("0.06"),
                waste_factor=1.08,
                setup_cost=Decimal("8.00"),
            ),
            Material.TITANIUM: MaterialCost(
                cost_per_cm3=Decimal("2.50"),
                waste_factor=1.25,
                setup_cost=Decimal("100.00"),
            ),
            Material.BRASS: MaterialCost(
                cost_per_cm3=Decimal("0.35"),
                waste_factor=1.18,
                setup_cost=Decimal("40.00"),
            ),
            Material.COPPER: MaterialCost(
                cost_per_cm3=Decimal("0.45"),
                waste_factor=1.20,
                setup_cost=Decimal("45.00"),
            ),
            Material.CARBON_FIBER: MaterialCost(
                cost_per_cm3=Decimal("1.80"),
                waste_factor=1.30,
                setup_cost=Decimal("80.00"),
            ),
        }

    def _get_default_process_costs(self) -> dict[ManufacturingProcess, ProcessCost]:
        """Load default process costs (migrated from old service)."""
        standard_complexity = {
            1.0: 1.0,
            2.0: 1.3,
            3.0: 1.7,
            4.0: 2.2,
            5.0: 3.0,
        }

        return {
            ManufacturingProcess.CNC: ProcessCost(
                hourly_rate=Decimal("85.00"),
                setup_time_hours=1.5,
                complexity_multiplier=standard_complexity,
            ),
            ManufacturingProcess.THREE_D_PRINTING: ProcessCost(
                hourly_rate=Decimal("25.00"),
                setup_time_hours=0.5,
                complexity_multiplier={
                    1.0: 1.0,
                    2.0: 1.1,
                    3.0: 1.3,
                    4.0: 1.6,
                    5.0: 2.0,
                },
            ),
            ManufacturingProcess.SHEET_CUTTING: ProcessCost(
                hourly_rate=Decimal("65.00"),
                setup_time_hours=0.8,
                complexity_multiplier={
                    1.0: 1.0,
                    2.0: 1.2,
                    3.0: 1.4,
                    4.0: 1.7,
                    5.0: 2.1,
                },
            ),
            ManufacturingProcess.TUBE_BENDING: ProcessCost(
                hourly_rate=Decimal("70.00"),
                setup_time_hours=1.2,
                complexity_multiplier=standard_complexity,
            ),
            ManufacturingProcess.INJECTION_MOLDING: ProcessCost(
                hourly_rate=Decimal("120.00"),
                setup_time_hours=8.0,
                complexity_multiplier={
                    1.0: 1.0,
                    2.0: 1.5,
                    3.0: 2.2,
                    4.0: 3.5,
                    5.0: 5.0,
                },
            ),
            ManufacturingProcess.LASER_CUTTING: ProcessCost(
                hourly_rate=Decimal("75.00"),
                setup_time_hours=0.3,
                complexity_multiplier={
                    1.0: 1.0,
                    2.0: 1.1,
                    3.0: 1.3,
                    4.0: 1.6,
                    5.0: 2.0,
                },
            ),
            ManufacturingProcess.WATERJET_CUTTING: ProcessCost(
                hourly_rate=Decimal("90.00"),
                setup_time_hours=0.5,
                complexity_multiplier={
                    1.0: 1.0,
                    2.0: 1.2,
                    3.0: 1.4,
                    4.0: 1.7,
                    5.0: 2.2,
                },
            ),
        }
