"""Pricing DTOs - Request and Response schemas for the pricing API."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

# ============================================================================
# Request DTOs
# ============================================================================


class PartDimensionsDTO(BaseModel):
    """Part dimensions DTO for API requests."""

    length_mm: float = Field(gt=0, description="Length in millimeters")
    width_mm: float = Field(gt=0, description="Width in millimeters")
    height_mm: float = Field(gt=0, description="Height in millimeters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"length_mm": 100.0, "width_mm": 50.0, "height_mm": 25.0}
        }
    )


class PricingRequestDTO(BaseModel):
    """Complete pricing request DTO."""

    dimensions: PartDimensionsDTO
    geometric_complexity_score: float = Field(
        ge=1.0, le=5.0, description="Complexity score from 1.0 to 5.0"
    )
    material: str = Field(description="Material type")
    process: str = Field(description="Manufacturing process")
    quantity: int = Field(gt=0, le=10000, description="Number of parts")
    customer_tier: str = Field(default="standard", description="Customer tier")
    shipping_distance_zone: int = Field(
        ge=1, le=4, default=1, description="Shipping zone (1-4)"
    )
    part_weight_kg: float | None = Field(
        default=None, description="Part weight in kg (estimated if not provided)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
                "geometric_complexity_score": 3.2,
                "material": "aluminum",
                "process": "cnc",
                "quantity": 50,
                "customer_tier": "standard",
                "shipping_distance_zone": 1,
            }
        }
    )


# ============================================================================
# Response DTOs
# ============================================================================


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
