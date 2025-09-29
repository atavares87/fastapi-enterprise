"""
Pricing API Schemas - Request/Response Models for Manufacturing Pricing API

This module defines Pydantic data models for the pricing API, providing:
- 📝 Strong typing and validation for all API requests and responses
- 📚 Automatic OpenAPI documentation generation with examples
- 🔒 Input sanitization and data validation with meaningful error messages
- 🔄 Consistent JSON serialization for Decimal fields

Schema Architecture:
- Request schemas: Validate and structure incoming API data
- Response schemas: Ensure consistent output format and documentation
- Nested schemas: Compose complex data structures from simpler components
- Validation: Business rule enforcement at the API boundary

Key Features:
- Automatic Decimal → float conversion for JSON compatibility
- Comprehensive field validation with ranges and constraints
- Rich examples for API documentation and testing
- Error schemas for consistent error reporting

Example API Request:
    POST /api/v1/pricing
    {
        "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
        "geometric_complexity_score": 3.2,
        "material": "aluminum",
        "process": "cnc",
        "quantity": 50,
        "customer_tier": "premium"
    }
"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.modules.cost.domain import ManufacturingProcess, Material


class PartDimensionsSchema(BaseModel):
    """
    Part dimensions schema for manufacturing pricing requests.

    Validates physical dimensions of parts to be manufactured, ensuring all
    dimensions are positive values in millimeters. Used as a nested schema
    within pricing requests to maintain clear data structure.

    Validation Rules:
    - All dimensions must be greater than 0 (no negative or zero dimensions)
    - Values are expected in millimeters for consistency
    - Supports decimal precision for precise specifications

    The dimensions are used for:
    - Volume calculations (material cost estimation)
    - Surface area calculations (machining time estimation)
    - Bounding box analysis (machine capability assessment)
    """

    length_mm: float = Field(
        gt=0, description="Length of the part in millimeters", examples=[100.0]
    )
    width_mm: float = Field(
        gt=0, description="Width of the part in millimeters", examples=[50.0]
    )
    height_mm: float = Field(
        gt=0, description="Height of the part in millimeters", examples=[25.0]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"length_mm": 100.0, "width_mm": 50.0, "height_mm": 25.0}
        }
    )


class PricingRequestSchema(BaseModel):
    """
    Complete pricing request schema for manufacturing cost calculations.

    This is the main input schema for the pricing API, containing all information
    needed to calculate manufacturing costs and pricing across service tiers.
    Includes comprehensive validation to ensure data quality and business rules.

    Request Components:
    - Physical specifications: dimensions, material, process
    - Complexity assessment: geometric difficulty rating
    - Order details: quantity, customer tier, shipping requirements
    - Optional data: part weight (estimated if not provided)

    Validation Features:
    - Range validation for numeric fields (complexity 1.0-5.0, quantity 1-10000)
    - Enum validation for materials and processes
    - Customer tier validation against allowed values
    - Shipping zone validation (1-4 for local to international)

    Business Rules Enforced:
    - Geometric complexity must be realistic (1.0-5.0 scale)
    - Quantities limited to reasonable manufacturing batches
    - Customer tiers restricted to valid business categories
    - Part weight validation if provided (must be positive)
    """

    dimensions: PartDimensionsSchema = Field(
        description="Physical dimensions of the part"
    )
    geometric_complexity_score: float = Field(
        ge=1.0,
        le=5.0,
        description="Geometric complexity score from 1.0 (simple) to 5.0 (very complex)",
        examples=[3.0],
    )
    material: Material = Field(description="Material the part will be made from")
    process: ManufacturingProcess = Field(
        description="Manufacturing process to be used"
    )
    part_weight_kg: float | None = Field(
        None,
        gt=0,
        description="Weight of the part in kilograms. If not provided, will be estimated from material and volume",
        examples=[0.5],
    )
    quantity: int = Field(
        1, ge=1, le=10000, description="Number of parts to manufacture", examples=[1]
    )
    customer_tier: str = Field(
        "standard",
        description="Customer tier for discount calculations",
        examples=["standard"],
    )
    shipping_distance_zone: int = Field(
        1,
        ge=1,
        le=4,
        description="Shipping distance zone: 1=local, 2=regional, 3=national, 4=international",
        examples=[1],
    )

    @field_validator("customer_tier")
    @classmethod
    def validate_customer_tier(cls, v: str) -> str:
        """
        Validate customer tier against allowed business categories.

        Ensures customer tier values match valid business classifications
        used for discount calculations and pricing tier access.

        Allowed Tiers:
        - standard: Default tier for new customers
        - premium: Higher volume customers with better rates
        - enterprise: Large customers with negotiated pricing

        Args:
            v: Customer tier string to validate

        Returns:
            Validated customer tier string

        Raises:
            ValueError: If tier is not in allowed list
        """
        allowed_tiers = ["standard", "premium", "enterprise"]
        if v not in allowed_tiers:
            raise ValueError(
                f"Customer tier '{v}' is not valid. Must be one of: {', '.join(allowed_tiers)}"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dimensions": {"length_mm": 100.0, "width_mm": 50.0, "height_mm": 25.0},
                "geometric_complexity_score": 3.0,
                "material": "aluminum",
                "process": "cnc",
                "part_weight_kg": 0.34,
                "quantity": 1,
                "customer_tier": "standard",
                "shipping_distance_zone": 1,
            }
        }
    )


class CostBreakdownSchema(BaseModel):
    """
    Manufacturing cost breakdown schema for transparent pricing responses.

    Provides detailed itemization of all cost components in manufacturing,
    enabling customers to understand pricing structure and internal teams
    to analyze cost drivers. All monetary values use Decimal precision
    internally but are serialized to float for JSON compatibility.

    Cost Components:
    - material_cost: Raw material costs including waste factors
    - labor_cost: Processing time costs with complexity adjustments
    - setup_cost: Machine preparation and tooling costs
    - complexity_adjustment: Additional charges for difficult geometries
    - overhead_cost: Facility overhead (utilities, rent, admin)
    - total_cost: Sum of all cost components

    Financial Transparency:
    - Enables cost analysis and optimization discussions
    - Supports value engineering and design-to-cost initiatives
    - Provides audit trail for pricing decisions
    - Facilitates cost comparison across different configurations
    """

    material_cost: Decimal = Field(
        description="Cost of raw materials including waste factor"
    )
    labor_cost: Decimal = Field(description="Labor cost for manufacturing")
    setup_cost: Decimal = Field(description="Setup costs for materials and processes")
    complexity_adjustment: Decimal = Field(
        description="Additional cost adjustments for part complexity"
    )
    overhead_cost: Decimal = Field(
        description="Overhead costs (facilities, utilities, etc.)"
    )
    total_cost: Decimal = Field(description="Total manufacturing cost")

    model_config = ConfigDict()

    @field_serializer(
        "material_cost",
        "labor_cost",
        "setup_cost",
        "complexity_adjustment",
        "overhead_cost",
        "total_cost",
    )
    def serialize_decimal(self, value: Decimal) -> float:
        """
        Convert Decimal fields to float for JSON serialization.

        Decimal types provide exact arithmetic for financial calculations but
        are not natively JSON serializable. This method converts them to float
        for API responses while maintaining reasonable precision for pricing.

        Note: Some precision may be lost in conversion, but this is acceptable
        for display purposes. Internal calculations maintain full Decimal precision.
        """
        return float(value)


class PriceBreakdownSchema(BaseModel):
    """
    Service tier price breakdown schema for customer pricing transparency.

    Details the complete pricing calculation for a specific service tier,
    showing how base manufacturing costs are transformed into final customer
    pricing through margins, shipping, discounts, and surcharges.

    Pricing Flow:
    1. base_cost: Manufacturing cost from cost calculation engine
    2. margin: Service tier profit margin (varies by tier)
    3. shipping_cost: Logistics costs based on distance zone
    4. volume_discount: Quantity-based price reductions
    5. complexity_surcharge: Additional charges for difficult parts
    6. subtotal: Running total before customer-specific adjustments
    7. final_discount: Customer tier and promotional discounts
    8. final_price: Total order price
    9. price_per_unit: Individual unit price for reference

    Business Value:
    - Complete pricing transparency for customer trust
    - Enables price optimization and negotiation
    - Supports sales team in explaining value proposition
    - Facilitates automated pricing and quoting systems
    """

    base_cost: Decimal = Field(description="Base manufacturing cost")
    margin: Decimal = Field(description="Profit margin added to base cost")
    shipping_cost: Decimal = Field(description="Shipping charges")
    volume_discount: Decimal = Field(description="Discount applied for quantity")
    complexity_surcharge: Decimal = Field(
        description="Surcharge for high-complexity parts"
    )
    subtotal: Decimal = Field(description="Subtotal before final discounts")
    final_discount: Decimal = Field(
        description="Final discounts (customer-specific, promotional)"
    )
    final_price: Decimal = Field(description="Final price for the entire order")
    price_per_unit: Decimal = Field(description="Price per individual unit")

    model_config = ConfigDict()

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
        """
        Convert Decimal pricing fields to float for JSON serialization.

        Maintains consistent serialization behavior across all pricing schemas
        while preserving reasonable precision for customer-facing pricing information.
        All financial calculations use Decimal internally for accuracy.
        """
        return float(value)


class TierPricingSchema(BaseModel):
    """
    Complete multi-tier pricing schema for service level comparison.

    Provides pricing breakdowns across all available service tiers,
    enabling customers to compare options and select the best fit for
    their timeline and budget requirements.

    Service Tiers:
    - expedited: Fastest delivery, highest margin, premium pricing
    - standard: Balanced delivery time and pricing, most popular option
    - economy: Longer lead times, lower pricing for cost-sensitive orders
    - domestic_economy: Optimized for domestic shipping, best value

    Each tier includes complete PriceBreakdownSchema with:
    - Different margin structures reflecting service levels
    - Tier-specific shipping options and costs
    - Consistent volume discounts across tiers
    - Service-appropriate complexity handling

    Use Cases:
    - Customer self-service pricing comparison
    - Sales team option presentation
    - Automated quote generation systems
    - Strategic pricing analysis and optimization
    """

    expedited: PriceBreakdownSchema = Field(
        description="Pricing for expedited service tier"
    )
    standard: PriceBreakdownSchema = Field(
        description="Pricing for standard service tier"
    )
    economy: PriceBreakdownSchema = Field(
        description="Pricing for economy service tier"
    )
    domestic_economy: PriceBreakdownSchema = Field(
        description="Pricing for domestic economy service tier"
    )


class PricingResponseSchema(BaseModel):
    """
    Complete pricing response schema containing all calculation results.

    The master response schema that combines all pricing information into
    a comprehensive result suitable for customer quotes, internal analysis,
    and automated processing systems.

    Response Structure:
    - part_specification: Echo of input for verification and audit
    - cost_breakdown: Detailed manufacturing cost analysis
    - pricing_tiers: Complete pricing across all service levels
    - estimated_weight_kg: Weight estimation if not provided
    - quantity: Confirmed quantity for pricing calculation

    Key Features:
    - Complete pricing transparency with cost and pricing breakdowns
    - Multi-tier comparison for customer choice optimization
    - Input echo for verification and audit trails
    - Estimated parameters clearly marked when calculated
    - Structured format suitable for automated processing

    Use Cases:
    - Customer quote generation and presentation
    - Internal cost analysis and margin review
    - Automated pricing system integration
    - Historical pricing data storage and analysis
    """

    part_specification: dict[str, Any] = Field(
        description="Echo of the part specification used for pricing"
    )
    cost_breakdown: CostBreakdownSchema = Field(
        description="Detailed manufacturing cost breakdown"
    )
    pricing_tiers: TierPricingSchema = Field(
        description="Pricing breakdown for all available service tiers"
    )
    estimated_weight_kg: float | None = Field(
        None, description="Estimated part weight if not provided in request"
    )
    quantity: int = Field(description="Number of parts priced")

    model_config = ConfigDict()


class ErrorResponseSchema(BaseModel):
    """
    Standardized error response schema for consistent API error handling.

    Provides structured error information that enables clients to handle
    errors appropriately and developers to debug issues effectively.
    Follows standard error response patterns for API consistency.

    Error Structure:
    - type: Classification of error (ValidationError, DomainError, etc.)
    - message: Human-readable error description
    - details: Additional context or specific validation failures

    Error Categories:
    - ValidationError: Input validation failures (ranges, types, etc.)
    - DomainError: Business rule violations (unsupported materials, etc.)
    - InternalServerError: System errors and unexpected failures

    Benefits:
    - Consistent error format across all API endpoints
    - Actionable error messages for client developers
    - Structured format suitable for error handling automation
    - Clear separation of error types for appropriate client responses
    """

    error: dict[str, Any] = Field(description="Error information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "type": "ValidationError",
                    "message": "Invalid input parameters",
                    "details": "Geometric complexity score must be between 1.0 and 5.0",
                }
            }
        }
    )
