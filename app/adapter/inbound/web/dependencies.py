"""
API Dependencies - Dependency Injection for FastAPI

This module provides dependency injection functions for FastAPI endpoints.
It wires together adapters and use cases.
"""

from app.adapter.outbound.persistence.cost_data_adapter import CostDataAdapter
from app.adapter.outbound.persistence.pricing_config_adapter import PricingConfigAdapter
from app.adapter.outbound.telemetry.metrics_adapter import TelemetryAdapter
from app.core.application.pricing.use_cases import CalculatePricingUseCase


def get_pricing_use_case() -> CalculatePricingUseCase:
    """
    Get pricing use case with wired dependencies.

    This function creates and wires all the adapters needed for the pricing use case.
    In production, these might be singletons or managed by a dependency injection container.

    Returns:
        Configured pricing use case
    """
    # Create adapters (imperative shell)
    cost_data_adapter = CostDataAdapter()
    pricing_config_adapter = PricingConfigAdapter()
    telemetry_adapter = TelemetryAdapter()

    # Create and wire use case
    return CalculatePricingUseCase(
        cost_data_port=cost_data_adapter,
        pricing_config_port=pricing_config_adapter,
        pricing_persistence_port=None,  # TODO: Add when needed
        telemetry_port=telemetry_adapter,
    )
