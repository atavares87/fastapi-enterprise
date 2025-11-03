"""
Pricing Domain Ports - Interfaces for Imperative Shell

Ports define how the functional core communicates with the outside world
without depending on specific implementations.
"""

from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol
from uuid import UUID

from app.core.domain.cost.models import PartSpecification
from app.core.domain.pricing.models import (
    PricingConfiguration,
    PricingRequest,
    ShippingCost,
)
from app.core.domain.pricing.tier import PricingTier, TierPricing


class PricingConfigPort(Protocol):
    """
    Port for accessing pricing configuration.

    This interface defines how the functional core requests pricing configs
    without knowing where they come from.
    """

    async def get_tier_configurations(
        self,
    ) -> dict[PricingTier, PricingConfiguration]:
        """
        Get pricing configurations for all tiers.

        Returns:
            Dictionary mapping tiers to their configurations
        """
        ...

    async def get_shipping_costs(self) -> dict[PricingTier, ShippingCost]:
        """
        Get shipping costs for all tiers.

        Returns:
            Dictionary mapping tiers to their shipping costs
        """
        ...


class PricingPersistencePort(Protocol):
    """
    Port for persisting pricing calculations.

    This interface defines how pricing results are saved
    without the functional core knowing the storage mechanism.
    """

    async def save_pricing_result(
        self,
        calculation_id: UUID,
        part_spec: PartSpecification,
        pricing_request: PricingRequest,
        tier_pricing: TierPricing,
        cost_breakdown: Any,
        calculation_duration_ms: int,
        user_id: str | None,
        ip_address: str | None,
    ) -> None:
        """
        Save pricing calculation result.

        Args:
            calculation_id: Unique calculation identifier
            part_spec: Part specification used
            pricing_request: Pricing request parameters
            tier_pricing: Calculated pricing for all tiers
            cost_breakdown: Cost calculation breakdown
            calculation_duration_ms: Time taken for calculation
            user_id: User who performed calculation
            ip_address: User's IP address
        """
        ...


class TelemetryPort(Protocol):
    """
    Port for telemetry operations.

    This interface defines how metrics and tracing are recorded
    without the functional core knowing the implementation.
    """

    async def get_current_time(self) -> float:
        """
        Get current time (side effect).

        Returns:
            Current time as float
        """
        ...

    def trace_pricing_calculation(
        self,
        calculation_id: UUID,
        material: str,
        process: str,
        quantity: int,
        customer_tier: str,
    ) -> AbstractAsyncContextManager[None]:
        """
        Trace pricing calculation (context manager).

        Args:
            calculation_id: Unique calculation ID
            material: Material type
            process: Manufacturing process
            quantity: Part quantity
            customer_tier: Customer tier

        Returns:
            Async context manager for tracing
        """
        ...

    async def record_pricing_metrics(
        self,
        calculation_id: UUID,
        material: str,
        process: str,
        tier_pricing: TierPricing,
        duration_seconds: float,
        quantity: int,
        customer_tier: str,
    ) -> None:
        """
        Record pricing metrics.

        Args:
            calculation_id: Unique calculation ID
            material: Material type
            process: Manufacturing process
            tier_pricing: Calculated tier pricing
            duration_seconds: Calculation duration
            quantity: Part quantity
            customer_tier: Customer tier
        """
        ...

    async def record_error(
        self,
        calculation_id: UUID,
        error: str,
        error_type: str,
        material: str | None = None,
        process: str | None = None,
        customer_tier: str | None = None,
    ) -> None:
        """
        Record error.

        Args:
            calculation_id: Unique calculation ID
            error: Error message
            error_type: Type of error
            material: Material type if available
            process: Process type if available
            customer_tier: Customer tier if available
        """
        ...
