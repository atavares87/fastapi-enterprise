"""Domain Enums - Manufacturing processes, materials, and pricing tiers."""

from enum import Enum


class ManufacturingProcess(str, Enum):
    """Manufacturing processes supported by the system."""

    CNC = "cnc"
    THREE_D_PRINTING = "3d_printing"
    SHEET_CUTTING = "sheet_cutting"
    TUBE_BENDING = "tube_bending"
    INJECTION_MOLDING = "injection_molding"
    LASER_CUTTING = "laser_cutting"
    WATERJET_CUTTING = "waterjet_cutting"


class Material(str, Enum):
    """Materials supported for manufacturing."""

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


class PricingTier(str, Enum):
    """Pricing tiers for different service levels."""

    EXPEDITED = "expedited"
    STANDARD = "standard"
    ECONOMY = "economy"
    DOMESTIC_ECONOMY = "domestic_economy"
