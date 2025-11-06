"""Pricing Request DTO - API request schema for pricing calculations."""

from pydantic import BaseModel, ConfigDict, Field


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
