"""
Pricing Service - Business logic orchestration

Analogous to Spring @Service - coordinates business workflows.
Orchestrates repositories and domain core functions.
"""

from uuid import uuid4

import structlog

from app.cost.core.calculations import calculate_manufacturing_cost
from app.cost.models import CostBreakdown, PartDimensions, PartSpecification
from app.cost.repository import CostRepository
from app.pricing.core.calculations import estimate_weight_from_material_and_volume
from app.pricing.core.tier_calculations import calculate_tier_pricing
from app.pricing.dto import (
    CostBreakdownDTO,
    PriceBreakdownDTO,
    PricingRequestDTO,
    PricingResponseDTO,
    TierPricingDTO,
)
from app.pricing.models import PricingRequest, TierPricing
from app.pricing.repository import PricingRepository
from app.shared.config_repository import ConfigRepository
from app.shared.enums import ManufacturingProcess, Material
from app.shared.metrics_repository import MetricsRepository

logger = structlog.get_logger(__name__)


class PricingService:
    """
    Pricing Service - Business logic orchestration.

    In Spring Boot, this would be annotated with @Service.

    Responsibilities:
    - Orchestrate pricing calculation workflow
    - Coordinate between repositories
    - Call domain core functions for business logic
    - Handle transaction boundaries
    - NO HTTP concerns (that's the controller's job)
    """

    def __init__(
        self,
        cost_repository: CostRepository,
        config_repository: ConfigRepository,
        pricing_repository: PricingRepository,
        metrics_repository: MetricsRepository,
    ):
        """
        Initialize service with repository dependencies.

        In Spring Boot, these would be injected via @Autowired or constructor injection.

        Args:
            cost_repository: Repository for cost data
            config_repository: Repository for configuration data
            pricing_repository: Repository for pricing persistence
            metrics_repository: Repository for metrics and tracing
        """
        self.cost_repository = cost_repository
        self.config_repository = config_repository
        self.pricing_repository = pricing_repository
        self.metrics_repository = metrics_repository

    async def calculate_pricing(
        self,
        request: PricingRequestDTO,
        save_to_db: bool = False,
        user_id: str | None = None,
        ip_address: str | None = None,
    ) -> PricingResponseDTO:
        """
        Calculate pricing for a manufacturing part.

        This is the main business method. It orchestrates:
        1. Data retrieval from repositories
        2. Business logic execution (domain core)
        3. Data persistence
        4. Metrics recording

        Args:
            request: Pricing request DTO from API
            save_to_db: Whether to save results to database
            user_id: User making the request (optional)
            ip_address: Request IP address (optional)

        Returns:
            Pricing response DTO for API

        Raises:
            ValueError: For invalid inputs
            Exception: For unexpected errors
        """
        calculation_id = uuid4()
        start_time = await self.metrics_repository.get_current_time()

        logger.info(
            "Processing pricing request",
            calculation_id=str(calculation_id),
            material=request.material,
            process=request.process,
            quantity=request.quantity,
        )

        # Start distributed tracing
        async with self.metrics_repository.trace_pricing_calculation(
            calculation_id=calculation_id,
            material=request.material,
            process=request.process,
            quantity=request.quantity,
            customer_tier=request.customer_tier,
        ):
            try:
                # STEP 1: FETCH DATA (Repository Layer)
                material_costs = await self.cost_repository.get_material_costs()
                process_costs = await self.cost_repository.get_process_costs()
                tier_configs = await self.config_repository.get_tier_configurations()
                shipping_costs = await self.config_repository.get_shipping_costs()

                # STEP 2: CONVERT DTO TO DOMAIN MODELS
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
                    part_weight_kg = estimate_weight_from_material_and_volume(
                        material=request.material,
                        volume_cm3=part_dimensions.volume_cm3,
                    )
                    estimated_weight = part_weight_kg
                    logger.info("Estimated part weight", weight_kg=part_weight_kg)

                # STEP 3: EXECUTE BUSINESS LOGIC (Domain Core - Pure Functions)
                # Calculate manufacturing cost
                cost_breakdown = calculate_manufacturing_cost(
                    spec=part_spec,
                    material_costs=material_costs,
                    process_costs=process_costs,
                )

                # Create pricing request domain model
                pricing_request = PricingRequest(
                    cost_breakdown=cost_breakdown,
                    geometric_complexity_score=part_spec.geometric_complexity_score,
                    part_weight_kg=part_weight_kg,
                    part_volume_cm3=part_spec.dimensions.volume_cm3,
                    quantity=request.quantity,
                    customer_tier=request.customer_tier,
                    shipping_distance_zone=request.shipping_distance_zone,
                )

                # Calculate pricing for all tiers
                tier_pricing = calculate_tier_pricing(
                    request=pricing_request,
                    tier_configurations=tier_configs,
                    tier_shipping_costs=shipping_costs,
                )

                # STEP 4: PERSIST RESULTS (Repository Layer)
                end_time = await self.metrics_repository.get_current_time()
                calculation_duration_ms = int((end_time - start_time) * 1000)

                if save_to_db:
                    await self.pricing_repository.save_pricing_result(
                        calculation_id=calculation_id,
                        part_spec=part_spec,
                        pricing_request=pricing_request,
                        tier_pricing=tier_pricing,
                        cost_breakdown=cost_breakdown,
                        calculation_duration_ms=calculation_duration_ms,
                        user_id=user_id,
                        ip_address=ip_address,
                    )

                # STEP 5: RECORD METRICS (Repository Layer)
                await self.metrics_repository.record_pricing_metrics(
                    calculation_id=calculation_id,
                    material=request.material,
                    process=request.process,
                    tier_pricing=tier_pricing,
                    duration_seconds=(end_time - start_time),
                    quantity=request.quantity,
                    customer_tier=request.customer_tier,
                )

                # STEP 6: CONVERT DOMAIN MODELS TO RESPONSE DTO
                response_dto = self._convert_to_response_dto(
                    part_spec=part_spec,
                    cost_breakdown=cost_breakdown,
                    tier_pricing=tier_pricing,
                    estimated_weight=estimated_weight,
                    quantity=request.quantity,
                )

                logger.info(
                    "Pricing calculation completed",
                    calculation_id=str(calculation_id),
                    duration_ms=calculation_duration_ms,
                    expedited_price=float(tier_pricing.expedited.final_price),
                    standard_price=float(tier_pricing.standard.final_price),
                )

                return response_dto

            except Exception as e:
                # Record error through metrics repository
                await self.metrics_repository.record_error(
                    calculation_id=calculation_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    material=request.material,
                    process=request.process,
                    customer_tier=request.customer_tier,
                )
                logger.error(
                    "Pricing calculation failed",
                    calculation_id=str(calculation_id),
                    error=str(e),
                    exc_info=True,
                )
                raise

    def _convert_to_response_dto(
        self,
        part_spec: PartSpecification,
        cost_breakdown: CostBreakdown,
        tier_pricing: TierPricing,
        estimated_weight: float | None,
        quantity: int,
    ) -> PricingResponseDTO:
        """
        Convert domain models to response DTO.

        Private helper method for DTO conversion.
        Keeps the main service method focused on business logic.
        """
        cost_breakdown_dto = CostBreakdownDTO(
            material_cost=cost_breakdown.material_cost,
            labor_cost=cost_breakdown.labor_cost,
            setup_cost=cost_breakdown.setup_cost,
            complexity_adjustment=cost_breakdown.complexity_adjustment,
            overhead_cost=cost_breakdown.overhead_cost,
            total_cost=cost_breakdown.total_cost,
        )

        tier_pricing_dto = TierPricingDTO(
            expedited=PriceBreakdownDTO(
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
            standard=PriceBreakdownDTO(
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
            economy=PriceBreakdownDTO(
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
            domestic_economy=PriceBreakdownDTO(
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

        return PricingResponseDTO(
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
            cost_breakdown=cost_breakdown_dto,
            pricing_tiers=tier_pricing_dto,
            estimated_weight_kg=estimated_weight,
            quantity=quantity,
        )
