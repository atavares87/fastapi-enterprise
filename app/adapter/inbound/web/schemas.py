"""
API Schemas - Request/Response Models for HTTP Interface

Pydantic models for API validation and serialization.
These are HTTP DTOs, not domain models.
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PartDimensionsSchema(BaseModel):
    """Part dimensions schema for API requests."""

    length_mm: float = Field(gt=0, description="Length in millimeters")
    width_mm: float = Field(gt=0, description="Width in millimeters")
    height_mm: float = Field(gt=0, description="Height in millimeters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"length_mm": 100.0, "width_mm": 50.0, "height_mm": 25.0}
        }
    )


class PricingRequestSchema(BaseModel):
    """Complete pricing request schema."""

    dimensions: PartDimensionsSchema
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


class CostBreakdownSchema(BaseModel):
    """Cost breakdown schema for API responses."""

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


class PriceBreakdownSchema(BaseModel):
    """Price breakdown schema for API responses."""

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


class TierPricingSchema(BaseModel):
    """Pricing for all tiers schema for API responses."""

    expedited: PriceBreakdownSchema
    standard: PriceBreakdownSchema
    economy: PriceBreakdownSchema
    domestic_economy: PriceBreakdownSchema


class PricingResponseSchema(BaseModel):
    """Complete pricing response schema."""

    part_specification: dict[str, Any]
    cost_breakdown: CostBreakdownSchema
    pricing_tiers: TierPricingSchema
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
                        "volume_cm3": 125.0,
                    },
                    "geometric_complexity_score": 3.2,
                    "material": "aluminum",
                    "process": "cnc",
                },
                "cost_breakdown": {
                    "material_cost": 18.75,
                    "labor_cost": 85.5,
                    "setup_cost": 152.5,
                    "complexity_adjustment": 8.55,
                    "overhead_cost": 39.795,
                    "total_cost": 305.095,
                },
                "pricing_tiers": {
                    "expedited": {
                        "base_cost": 15254.75,
                        "margin": 9915.59,
                        "shipping_cost": 52.0,
                        "volume_discount": 756.51,
                        "complexity_surcharge": 5034.07,
                        "subtotal": 29499.9,
                        "final_discount": 0.0,
                        "final_price": 29499.9,
                        "price_per_unit": 589.998,
                    },
                    "standard": {"...": "..."},
                    "economy": {"...": "..."},
                    "domestic_economy": {"...": "..."},
                },
                "estimated_weight_kg": 0.38,
                "quantity": 50,
            }
        }
    )


class ErrorResponseSchema(BaseModel):
    """Error response schema."""

    error: dict[str, Any]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "type": "ValidationError",
                    "message": "Material 'unknown' is not supported",
                    "details": None,
                }
            }
        }
    )
