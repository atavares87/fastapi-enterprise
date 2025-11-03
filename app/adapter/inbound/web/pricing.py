"""
Pricing API Router - Manufacturing Cost & Pricing Calculations

Clean API layer following hexagonal architecture.
HTTP concerns only - delegates business logic to use cases.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.adapter.inbound.web.dependencies import get_pricing_use_case
from app.adapter.inbound.web.schemas import (
    CostBreakdownSchema,
    PriceBreakdownSchema,
    PricingRequestSchema,
    PricingResponseSchema,
    TierPricingSchema,
)
from app.core.application.pricing.use_cases import CalculatePricingUseCase
from app.core.domain.cost.models import (
    ManufacturingProcess,
    Material,
    PartDimensions,
    PartSpecification,
)
from app.core.domain.pricing import calculations as pricing_calculations
from app.core.exceptions import DomainException

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post(
    "/pricing",
    response_model=PricingResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Calculate part pricing",
    description="Calculate pricing for a manufacturing part across all service tiers.",
    tags=["Pricing"],
)
async def calculate_pricing(
    request: PricingRequestSchema,
    pricing_use_case: CalculatePricingUseCase = Depends(get_pricing_use_case),
) -> PricingResponseSchema:
    """
    Calculate comprehensive pricing for a manufacturing part.

    This endpoint orchestrates pricing calculation across all tiers using
    the hexagonal architecture with functional core and imperative shell.

    Args:
        request: Complete pricing request with part specifications
        pricing_use_case: Injected pricing use case (orchestration layer)

    Returns:
        Detailed pricing breakdown including costs, margins, shipping, and discounts

    Raises:
        HTTPException: For validation errors or calculation failures
    """
    try:
        logger.info(
            "Processing pricing request",
            material=request.material,
            process=request.process,
            quantity=request.quantity,
        )

        # Convert HTTP request to domain objects
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
            part_weight_kg = (
                pricing_calculations.estimate_weight_from_material_and_volume(
                    material=request.material,
                    volume_cm3=part_dimensions.volume_cm3,
                )
            )
            estimated_weight = part_weight_kg
            logger.info("Estimated part weight", weight_kg=part_weight_kg)

        # Execute use case (orchestrates functional core with imperative shell)
        result = await pricing_use_case.execute(
            part_spec=part_spec,
            part_weight_kg=part_weight_kg,
            quantity=request.quantity,
            customer_tier=request.customer_tier,
            shipping_distance_zone=request.shipping_distance_zone,
            save_to_db=False,  # Not saving for now
        )

        # Extract results
        tier_pricing = result["pricing"]
        cost_breakdown = result["cost_breakdown"]

        # Convert domain objects to HTTP response schemas
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

        # Create HTTP response
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

        logger.info(
            "Pricing calculation completed",
            expedited_price=float(tier_pricing.expedited.final_price),
            standard_price=float(tier_pricing.standard.final_price),
            economy_price=float(tier_pricing.economy.final_price),
        )

        return response

    except DomainException as e:
        # Domain errors are already recorded by use case via TelemetryAdapter
        logger.warning(
            "Domain error in pricing calculation",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"type": type(e).__name__, "message": str(e)}},
        )

    except ValueError as e:
        # Validation errors are already recorded by use case via TelemetryAdapter
        logger.warning("Validation error in pricing calculation", error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"type": "ValidationError", "message": str(e)}},
        )

    except Exception as e:
        # Unexpected errors are already recorded by use case via TelemetryAdapter
        logger.error(
            "Unexpected error in pricing calculation",
            error_type=type(e).__name__,
            error_message=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred during pricing calculation",
                }
            },
        )


@router.get(
    "/pricing/materials",
    response_model=list[str],
    summary="Get supported materials",
    tags=["Pricing"],
)
async def get_supported_materials() -> list[str]:
    """Get list of supported materials."""
    return [material.value for material in Material]


@router.get(
    "/pricing/processes",
    response_model=list[str],
    summary="Get supported processes",
    tags=["Pricing"],
)
async def get_supported_processes() -> list[str]:
    """Get list of supported manufacturing processes."""
    return [process.value for process in ManufacturingProcess]
