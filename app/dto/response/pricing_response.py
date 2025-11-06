"""Pricing Response DTO - API response schema for pricing calculations."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class CostBreakdownDTO(BaseModel):
    """Cost breakdown DTO for API responses."""

    material_cost: Decimal
    labor_cost: Decimal
    setup_cost: Decimal
    complexity_adjustment: Decimal
    overhead_cost: Decimal
    total_cost: Decimal

    @field_serializer(
        "material_cost",
        "labor_cost",
        "setup_cost",
        "complexity_adjustment",
        "overhead_cost",
        "total_cost",
    )
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class PriceBreakdownDTO(BaseModel):
    """Price breakdown DTO for API responses."""

    base_cost: Decimal
    margin: Decimal
    shipping_cost: Decimal
    volume_discount: Decimal
    complexity_surcharge: Decimal
    subtotal: Decimal
    final_discount: Decimal
    final_price: Decimal
    price_per_unit: Decimal

    @field_serializer(
        "base_cost",
        "margin",
        "shipping_cost",
        "volume_discount",
        "complexity_surcharge",
        "subtotal",
        "final_discount",
        "final_price",
        "price_per_unit",
    )
    def serialize_decimal(self, value: Decimal) -> float:
        """Convert Decimal to float for JSON serialization."""
        return float(value)


class TierPricingDTO(BaseModel):
    """Pricing for all tiers DTO."""

    expedited: PriceBreakdownDTO
    standard: PriceBreakdownDTO
    economy: PriceBreakdownDTO
    domestic_economy: PriceBreakdownDTO


class PricingResponseDTO(BaseModel):
    """Complete pricing response DTO."""

    part_specification: dict[str, Any]
    cost_breakdown: CostBreakdownDTO
    pricing_tiers: TierPricingDTO
    estimated_weight_kg: float | None = None
    quantity: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "part_specification": {
                    "dimensions": {
                        "length_mm": 100,
                        "width_mm": 50,
                        "height_mm": 25,
                        "volume_cm3": 125,
                    },
                    "geometric_complexity_score": 3.2,
                    "material": "aluminum",
                    "process": "cnc",
                },
                "cost_breakdown": {
                    "material_cost": 5.25,
                    "labor_cost": 42.50,
                    "setup_cost": 152.50,
                    "complexity_adjustment": 4.25,
                    "overhead_cost": 30.68,
                    "total_cost": 235.18,
                },
                "quantity": 50,
            }
        }
    )
