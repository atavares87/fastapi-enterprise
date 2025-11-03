"""
Pricing Use Cases - ORCHESTRATION LAYER

Use cases orchestrate the functional core with the imperative shell:
1. Gather all data needed (imperative shell - I/O)
2. Call pure business logic (functional core - pure functions)
3. Persist results (imperative shell - I/O)
4. Record metrics (imperative shell - I/O)
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.domain.cost import calculations as cost_calculations
from app.core.domain.cost.models import PartSpecification
from app.core.domain.pricing import calculate_tier_pricing
from app.core.domain.pricing.models import PricingRequest
from app.core.port.outbound.cost_ports import CostDataPort
from app.core.port.outbound.pricing_ports import (
    PricingConfigPort,
    PricingPersistencePort,
    TelemetryPort,
)


class CalculatePricingUseCase:
    """
    Use case: Calculate pricing for a manufacturing part.

    Orchestrates functional core with imperative shell without mixing concerns.
    """

    def __init__(
        self,
        cost_data_port: CostDataPort,
        pricing_config_port: PricingConfigPort,
        pricing_persistence_port: PricingPersistencePort | None,
        telemetry_port: TelemetryPort,
    ):
        """
        Initialize use case with ports (interfaces to imperative shell).

        Args:
            cost_data_port: Provides cost data (materials, processes)
            pricing_config_port: Provides pricing configurations
            pricing_persistence_port: Handles pricing data persistence (optional)
            telemetry_port: Handles metrics and tracing
        """
        self.cost_data_port = cost_data_port
        self.pricing_config_port = pricing_config_port
        self.pricing_persistence_port = pricing_persistence_port
        self.telemetry_port = telemetry_port

    async def execute(
        self,
        part_spec: PartSpecification,
        part_weight_kg: float,
        quantity: int = 1,
        customer_tier: str = "standard",
        shipping_distance_zone: int = 1,
        save_to_db: bool = False,
        user_id: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute pricing calculation use case.

        This method orchestrates all steps:
        1. Gather data from imperative shell
        2. Execute functional core (pure calculations)
        3. Persist results to imperative shell
        4. Record metrics to imperative shell

        Args:
            part_spec: Part specification
            part_weight_kg: Part weight in kg
            quantity: Number of parts
            customer_tier: Customer tier for discounts
            shipping_distance_zone: Shipping zone (1-4)
            save_to_db: Whether to persist results
            user_id: User performing calculation
            ip_address: User's IP address

        Returns:
            Complete pricing result with explanation
        """
        calculation_id = uuid4()
        start_time = await self.telemetry_port.get_current_time()

        # Start telemetry tracing
        async with self.telemetry_port.trace_pricing_calculation(
            calculation_id=calculation_id,
            material=part_spec.material.value,
            process=part_spec.process.value,
            quantity=quantity,
            customer_tier=customer_tier,
        ):
            try:
                # STEP 1: GATHER DATA (Imperative Shell - I/O)
                material_costs = await self.cost_data_port.get_material_costs()
                process_costs = await self.cost_data_port.get_process_costs()
                tier_configs = await self.pricing_config_port.get_tier_configurations()
                shipping_costs = await self.pricing_config_port.get_shipping_costs()

                # STEP 2: EXECUTE FUNCTIONAL CORE (Pure Calculations - NO I/O)
                # All business logic is pure functions - no side effects!

                # 2a. Calculate manufacturing cost
                cost_breakdown = cost_calculations.calculate_manufacturing_cost(
                    spec=part_spec,
                    material_costs=material_costs,
                    process_costs=process_costs,
                )

                # 2b. Create pricing request
                pricing_request = PricingRequest(
                    cost_breakdown=cost_breakdown,
                    geometric_complexity_score=part_spec.geometric_complexity_score,
                    part_weight_kg=part_weight_kg,
                    part_volume_cm3=part_spec.dimensions.volume_cm3,
                    quantity=quantity,
                    customer_tier=customer_tier,
                    shipping_distance_zone=shipping_distance_zone,
                )

                # 2c. Calculate pricing for all tiers
                tier_pricing = calculate_tier_pricing(
                    request=pricing_request,
                    tier_configurations=tier_configs,
                    tier_shipping_costs=shipping_costs,
                )

                # STEP 3: PERSIST RESULTS (Imperative Shell - I/O)
                end_time = await self.telemetry_port.get_current_time()
                calculation_duration_ms = int((end_time - start_time) * 1000)

                if save_to_db and self.pricing_persistence_port:
                    await self.pricing_persistence_port.save_pricing_result(
                        calculation_id=calculation_id,
                        part_spec=part_spec,
                        pricing_request=pricing_request,
                        tier_pricing=tier_pricing,
                        cost_breakdown=cost_breakdown,
                        calculation_duration_ms=calculation_duration_ms,
                        user_id=user_id,
                        ip_address=ip_address,
                    )

                # STEP 4: RECORD METRICS (Imperative Shell - I/O)
                await self.telemetry_port.record_pricing_metrics(
                    calculation_id=calculation_id,
                    material=part_spec.material.value,
                    process=part_spec.process.value,
                    tier_pricing=tier_pricing,
                    duration_seconds=(end_time - start_time),
                    quantity=quantity,
                    customer_tier=customer_tier,
                )

                # STEP 5: RETURN RESULTS
                return {
                    "calculation_id": str(calculation_id),
                    "pricing": tier_pricing,
                    "cost_breakdown": cost_breakdown,
                    "metadata": {
                        "calculation_duration_ms": calculation_duration_ms,
                        "saved_to_db": save_to_db
                        and self.pricing_persistence_port is not None,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

            except Exception as e:
                # Log error through telemetry port
                await self.telemetry_port.record_error(
                    calculation_id=calculation_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    material=part_spec.material.value,
                    process=part_spec.process.value,
                    customer_tier=customer_tier,
                )
                raise
