"""Cost Domain Enums - Single Responsibility: Manufacturing process and material enumerations."""

from enum import Enum


class ManufacturingProcess(str, Enum):
    """Manufacturing processes supported by the cost calculation system."""

    CNC = "cnc"
    THREE_D_PRINTING = "3d_printing"
    SHEET_CUTTING = "sheet_cutting"
    TUBE_BENDING = "tube_bending"
    INJECTION_MOLDING = "injection_molding"
    LASER_CUTTING = "laser_cutting"
    WATERJET_CUTTING = "waterjet_cutting"


class Material(str, Enum):
    """Materials supported for manufacturing cost calculations."""

    ALUMINUM = "aluminum"
    STEEL = "steel"
    STAINLESS_STEEL = "stainless_steel"
    PLASTIC_ABS = "plastic_abs"
    PLASTIC_PLA = "plastic_pla"
    PLASTIC_PETG = "plastic_petg"
    TITANIUM = "titanium"
    BRASS = "brass"
    COPPER = "copper"
    CARBON_FIBER = "carbon_fiber"
