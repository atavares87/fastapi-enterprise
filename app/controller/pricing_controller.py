"""
Pricing Controller - REST API endpoints

Analogous to Spring @RestController - handles HTTP requests/responses.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.model import ManufacturingProcess, Material
from app.dto.request.pricing_request import PricingRequestDTO
from app.dto.response.pricing_response import PricingResponseDTO
from app.exception.domain_exceptions import DomainException
from app.service.pricing_service import PricingService

logger = structlog.get_logger(__name__)

# Create router (analogous to Spring @RestController with @RequestMapping)
router = APIRouter(prefix="/api/v1/pricing", tags=["Pricing"])


# Dependency injection placeholder (will be implemented in config/dependencies.py)
def get_pricing_service() -> PricingService:
    """
    Get pricing service instance.

    In Spring Boot, this would be handled by @Autowired.
    Will be implemented properly in config/dependencies.py.
    """
    from app.config.dependencies import get_pricing_service as _get_service

    return _get_service()


@router.post(
    "/calculate",
    response_model=PricingResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Calculate part pricing",
    description="Calculate pricing for a manufacturing part across all service tiers.",
)
async def calculate_pricing(
    request: PricingRequestDTO,
    pricing_service: PricingService = Depends(get_pricing_service),
) -> PricingResponseDTO:
    """
    Calculate comprehensive pricing for a manufacturing part.

    This endpoint delegates all business logic to the PricingService.
    The controller is ONLY responsible for:
    - HTTP concerns (status codes, headers)
    - Request validation (via Pydantic)
    - Exception handling (converting to HTTP responses)
    - Response formatting

    Args:
        request: Pricing request DTO (validated by Pydantic)
        pricing_service: Injected pricing service

    Returns:
        Pricing response DTO with detailed breakdown

    Raises:
        HTTPException: For validation errors or business rule violations
    """
    try:
        logger.info(
            "Received pricing request",
            material=request.material,
            process=request.process,
            quantity=request.quantity,
        )

        # Delegate to service layer (business logic)
        response = await pricing_service.calculate_pricing(request)

        return response

    except DomainException as e:
        # Business rule violation
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
        # Validation error
        logger.warning("Validation error in pricing calculation", error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"type": "ValidationError", "message": str(e)}},
        )

    except Exception as e:
        # Unexpected error
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
    "/materials",
    response_model=list[str],
    summary="Get supported materials",
    description="Get list of all supported materials for manufacturing.",
)
async def get_supported_materials() -> list[str]:
    """
    Get list of supported materials.

    Simple endpoint - no service layer needed for static data.
    """
    return [material.value for material in Material]


@router.get(
    "/processes",
    response_model=list[str],
    summary="Get supported processes",
    description="Get list of all supported manufacturing processes.",
)
async def get_supported_processes() -> list[str]:
    """
    Get list of supported manufacturing processes.

    Simple endpoint - no service layer needed for static data.
    """
    return [process.value for process in ManufacturingProcess]


@router.get(
    "/tiers",
    response_model=list[str],
    summary="Get pricing tiers",
    description="Get list of all available pricing tiers.",
)
async def get_pricing_tiers() -> list[str]:
    """
    Get list of available pricing tiers.

    Simple endpoint - no service layer needed for static data.
    """
    from app.domain.model import PricingTier

    return [tier.value for tier in PricingTier]


# Legacy routes for backward compatibility
@router.post(
    "",  # Root path: /api/v1/pricing
    response_model=PricingResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Calculate part pricing",
    description="Calculate pricing for a manufacturing part across all service tiers.",
)
async def calculate_pricing_legacy(
    request: PricingRequestDTO,
    pricing_service: PricingService = Depends(get_pricing_service),
) -> PricingResponseDTO:
    """Calculate pricing (legacy route for backward compatibility)."""
    return await calculate_pricing(request, pricing_service)


@router.get(
    "/calculate/materials",
    response_model=list[str],
    summary="Get supported materials (legacy)",
    description="Get list of all supported materials for manufacturing. Legacy endpoint.",
    include_in_schema=False,
)
async def get_supported_materials_legacy() -> list[str]:
    """Get list of supported materials (legacy route for backward compatibility)."""
    return [material.value for material in Material]


@router.get(
    "/calculate/processes",
    response_model=list[str],
    summary="Get supported processes (legacy)",
    description="Get list of all supported manufacturing processes. Legacy endpoint.",
    include_in_schema=False,
)
async def get_supported_processes_legacy() -> list[str]:
    """Get list of supported manufacturing processes (legacy route for backward compatibility)."""
    return [process.value for process in ManufacturingProcess]
