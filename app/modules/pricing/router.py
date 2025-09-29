"""
Pricing API Router - Manufacturing Cost & Pricing Calculations

This module provides REST API endpoints for manufacturing pricing calculations.
It follows the hexagonal architecture pattern by handling HTTP concerns while
delegating all business logic to the service layer.

Endpoints:
- POST /pricing: Calculate comprehensive pricing for a manufacturing part
- GET /pricing/materials: List all supported materials
- GET /pricing/processes: List all supported manufacturing processes
- GET /pricing/tiers: List all available service tiers

Features:
- ✅ Multi-tier pricing (expedited, standard, economy, domestic_economy)
- ✅ Material and process cost calculations
- ✅ Volume discounts and complexity surcharges
- ✅ Shipping cost calculations by distance zone
- ✅ Customer tier-based discounts
- ✅ Comprehensive error handling with detailed responses

Example Usage:
    POST /api/v1/pricing
    {
        "dimensions": {"length_mm": 100, "width_mm": 50, "height_mm": 25},
        "material": "aluminum_6061",
        "process": "cnc_machining",
        "quantity": 100,
        "geometric_complexity_score": 0.7,
        "customer_tier": "standard",
        "shipping_distance_zone": "domestic"
    }
"""

import structlog
from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import DomainException
from app.modules.cost.domain import (
    ManufacturingProcess,
    Material,
    PartDimensions,
    PartSpecification,
)
from app.modules.pricing.schemas import (
    CostBreakdownSchema,
    ErrorResponseSchema,
    PriceBreakdownSchema,
    PricingRequestSchema,
    PricingResponseSchema,
    TierPricingSchema,
)
from app.modules.pricing.service import PricingService

# Initialize logger and router
logger = structlog.get_logger(__name__)
router = APIRouter()

# Initialize pricing service
pricing_service = PricingService()


@router.post(
    "/pricing",
    response_model=PricingResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Calculate part pricing",
    description="""
    Calculate pricing for a manufacturing part across all service tiers.

    This endpoint takes part specifications (dimensions, material, process, complexity)
    and returns detailed pricing including:
    - Manufacturing cost breakdown
    - Pricing across all service tiers (expedited, standard, economy, domestic_economy)
    - Shipping costs, margins, discounts, and surcharges

    The pricing calculation includes:
    1. **Cost Calculation**: Material, labor, setup, and overhead costs
    2. **Pricing Tiers**: Different service levels with varying margins and shipping
    3. **Volume Discounts**: Quantity-based discounts
    4. **Complexity Surcharges**: Additional charges for complex geometries
    5. **Customer Discounts**: Tier-based customer discounts
    """,
    responses={
        200: {
            "description": "Successful pricing calculation",
            "model": PricingResponseSchema,
        },
        400: {
            "description": "Invalid request parameters",
            "model": ErrorResponseSchema,
        },
        422: {"description": "Validation error", "model": ErrorResponseSchema},
        500: {"description": "Internal server error", "model": ErrorResponseSchema},
    },
    tags=["Pricing"],
)
async def calculate_pricing(request: PricingRequestSchema) -> PricingResponseSchema:
    """
    Calculate comprehensive pricing for a manufacturing part.

    This is the main pricing endpoint that orchestrates cost calculation
    and pricing logic to provide complete pricing information across
    all available service tiers.

    Args:
        request: Complete pricing request with part specifications

    Returns:
        Detailed pricing breakdown including costs, margins, shipping, and discounts

    Raises:
        HTTPException: For validation errors or calculation failures
    """
    try:
        # Log the incoming request
        logger.info(
            "Processing pricing request",
            material=request.material,
            process=request.process,
            quantity=request.quantity,
            complexity=request.geometric_complexity_score,
        )

        # Convert request to domain objects
        part_dimensions = PartDimensions(
            length_mm=request.dimensions.length_mm,
            width_mm=request.dimensions.width_mm,
            height_mm=request.dimensions.height_mm,
        )

        part_spec = PartSpecification(
            dimensions=part_dimensions,
            geometric_complexity_score=request.geometric_complexity_score,
            material=Material(request.material),
            process=ManufacturingProcess(request.process),
        )

        # Estimate weight if not provided
        estimated_weight = None
        part_weight_kg = request.part_weight_kg

        if part_weight_kg is None:
            part_weight_kg = pricing_service.estimate_weight_from_material_and_volume(
                part_spec
            )
            estimated_weight = part_weight_kg
            logger.info(
                "Estimated part weight",
                estimated_weight_kg=part_weight_kg,
                material=request.material,
                volume_cm3=part_dimensions.volume_cm3,
            )

        # Calculate pricing
        tier_pricing = pricing_service.calculate_part_pricing(
            part_spec=part_spec,
            part_weight_kg=part_weight_kg,
            quantity=request.quantity,
            customer_tier=request.customer_tier,
            shipping_distance_zone=request.shipping_distance_zone,
        )

        # Get cost breakdown for response
        cost_breakdown = pricing_service.cost_service.calculate_manufacturing_cost(
            part_spec
        )

        # Convert domain objects to response schemas
        cost_breakdown_schema = CostBreakdownSchema(
            material_cost=cost_breakdown.material_cost,
            labor_cost=cost_breakdown.labor_cost,
            setup_cost=cost_breakdown.setup_cost,
            complexity_adjustment=cost_breakdown.complexity_adjustment,
            overhead_cost=cost_breakdown.overhead_cost,
            total_cost=cost_breakdown.total_cost,
        )

        tier_pricing_schema = TierPricingSchema(
            expedited=PriceBreakdownSchema(
                base_cost=tier_pricing.expedited.base_cost,
                margin=tier_pricing.expedited.margin,
                shipping_cost=tier_pricing.expedited.shipping_cost,
                volume_discount=tier_pricing.expedited.volume_discount,
                complexity_surcharge=tier_pricing.expedited.complexity_surcharge,
                subtotal=tier_pricing.expedited.subtotal,
                final_discount=tier_pricing.expedited.final_discount,
                final_price=tier_pricing.expedited.final_price,
                price_per_unit=tier_pricing.expedited.price_per_unit,
            ),
            standard=PriceBreakdownSchema(
                base_cost=tier_pricing.standard.base_cost,
                margin=tier_pricing.standard.margin,
                shipping_cost=tier_pricing.standard.shipping_cost,
                volume_discount=tier_pricing.standard.volume_discount,
                complexity_surcharge=tier_pricing.standard.complexity_surcharge,
                subtotal=tier_pricing.standard.subtotal,
                final_discount=tier_pricing.standard.final_discount,
                final_price=tier_pricing.standard.final_price,
                price_per_unit=tier_pricing.standard.price_per_unit,
            ),
            economy=PriceBreakdownSchema(
                base_cost=tier_pricing.economy.base_cost,
                margin=tier_pricing.economy.margin,
                shipping_cost=tier_pricing.economy.shipping_cost,
                volume_discount=tier_pricing.economy.volume_discount,
                complexity_surcharge=tier_pricing.economy.complexity_surcharge,
                subtotal=tier_pricing.economy.subtotal,
                final_discount=tier_pricing.economy.final_discount,
                final_price=tier_pricing.economy.final_price,
                price_per_unit=tier_pricing.economy.price_per_unit,
            ),
            domestic_economy=PriceBreakdownSchema(
                base_cost=tier_pricing.domestic_economy.base_cost,
                margin=tier_pricing.domestic_economy.margin,
                shipping_cost=tier_pricing.domestic_economy.shipping_cost,
                volume_discount=tier_pricing.domestic_economy.volume_discount,
                complexity_surcharge=tier_pricing.domestic_economy.complexity_surcharge,
                subtotal=tier_pricing.domestic_economy.subtotal,
                final_discount=tier_pricing.domestic_economy.final_discount,
                final_price=tier_pricing.domestic_economy.final_price,
                price_per_unit=tier_pricing.domestic_economy.price_per_unit,
            ),
        )

        # Create response
        response = PricingResponseSchema(
            part_specification={
                "dimensions": {
                    "length_mm": part_spec.dimensions.length_mm,
                    "width_mm": part_spec.dimensions.width_mm,
                    "height_mm": part_spec.dimensions.height_mm,
                    "volume_cm3": part_spec.dimensions.volume_cm3,
                },
                "geometric_complexity_score": part_spec.geometric_complexity_score,
                "material": part_spec.material.value,
                "process": part_spec.process.value,
            },
            cost_breakdown=cost_breakdown_schema,
            pricing_tiers=tier_pricing_schema,
            estimated_weight_kg=estimated_weight,
            quantity=request.quantity,
        )

        # Log successful response
        logger.info(
            "Pricing calculation completed",
            expedited_price=float(tier_pricing.expedited.final_price),
            standard_price=float(tier_pricing.standard.final_price),
            economy_price=float(tier_pricing.economy.final_price),
            domestic_economy_price=float(tier_pricing.domestic_economy.final_price),
            quantity=request.quantity,
        )

        return response

    except DomainException as e:
        # Handle domain-specific errors
        logger.warning(
            "Domain error in pricing calculation",
            error_type=type(e).__name__,
            error_message=str(e),
            material=request.material,
            process=request.process,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "details": getattr(e, "details", None),
                }
            },
        )

    except ValueError as e:
        # Handle validation and calculation errors
        logger.warning(
            "Validation error in pricing calculation",
            error_message=str(e),
            material=request.material,
            process=request.process,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {"type": "ValidationError", "message": str(e), "details": None}
            },
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(
            "Unexpected error in pricing calculation",
            error_type=type(e).__name__,
            error_message=str(e),
            material=request.material,
            process=request.process,
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred during pricing calculation",
                    "details": None,
                }
            },
        )


@router.get(
    "/pricing/materials",
    response_model=list[str],
    summary="Get supported materials",
    description="Get a list of all materials supported for pricing calculations.",
    tags=["Pricing"],
)
async def get_supported_materials() -> list[str]:
    """
    Get list of supported materials.

    Returns:
        List of material names that can be used in pricing requests
    """
    try:
        materials = pricing_service.cost_service.get_supported_materials()
        return [material.value for material in materials]

    except Exception as e:
        logger.error("Error getting supported materials", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "InternalServerError",
                    "message": "Failed to retrieve supported materials",
                    "details": None,
                }
            },
        )


@router.get(
    "/pricing/processes",
    response_model=list[str],
    summary="Get supported processes",
    description="Get a list of all manufacturing processes supported for pricing calculations.",
    tags=["Pricing"],
)
async def get_supported_processes() -> list[str]:
    """
    Get list of supported manufacturing processes.

    Returns:
        List of process names that can be used in pricing requests
    """
    try:
        processes = pricing_service.cost_service.get_supported_processes()
        return [process.value for process in processes]

    except Exception as e:
        logger.error("Error getting supported processes", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "InternalServerError",
                    "message": "Failed to retrieve supported processes",
                    "details": None,
                }
            },
        )


@router.get(
    "/pricing/tiers",
    response_model=list[str],
    summary="Get available pricing tiers",
    description="Get a list of all available pricing tiers with different service levels.",
    tags=["Pricing"],
)
async def get_pricing_tiers() -> list[str]:
    """
    Get list of available pricing tiers.

    Returns:
        List of pricing tier names available for pricing calculations
    """
    try:
        tiers = pricing_service.get_available_pricing_tiers()
        return tiers

    except Exception as e:
        logger.error("Error getting pricing tiers", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "InternalServerError",
                    "message": "Failed to retrieve pricing tiers",
                    "details": None,
                }
            },
        )
