"""
Metrics Repository - Data access for telemetry and metrics

Analogous to Spring @Repository - handles metrics and tracing.
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

import structlog
from opentelemetry import trace
from prometheus_client import Counter, Histogram

from app.domain.model import TierPricing
from app.infrastructure.telemetry import get_telemetry_manager

logger = structlog.get_logger(__name__)


# Module-level metrics (Prometheus standard pattern)
_pricing_calculations_total = Counter(
    name="pricing_calculations_total",
    documentation="Total pricing calculations",
    labelnames=["material", "process", "tier", "status"],
)

_pricing_errors_total = Counter(
    name="pricing_errors_total",
    documentation="Total pricing errors",
    labelnames=["material", "process", "error_type"],
)

_pricing_calculation_duration = Histogram(
    name="pricing_calculation_duration_seconds",
    documentation="Pricing calculation duration in seconds",
    labelnames=["material", "process", "tier"],
)

_pricing_final_prices = Histogram(
    name="pricing_final_prices_usd",
    documentation="Final prices calculated in USD",
    labelnames=["tier"],
)

_pricing_margins = Histogram(
    name="pricing_margins_usd",
    documentation="Profit margins calculated in USD",
    labelnames=["tier"],
)


class MetricsRepository:
    """
    Repository for metrics and telemetry data access.

    In Spring Boot, this would be analogous to a metrics publisher.
    Handles all observability concerns (metrics, tracing, logging).
    """

    def __init__(self) -> None:
        """Initialize tracer for distributed tracing."""
        telemetry_manager = get_telemetry_manager()
        self.tracer = (
            telemetry_manager.get_tracer("pricing") if telemetry_manager else None
        )

    async def get_current_time(self) -> float:
        """Get current time (side effect for timing calculations)."""
        return time.time()

    @asynccontextmanager
    async def trace_pricing_calculation(
        self,
        calculation_id: UUID,
        material: str,
        process: str,
        quantity: int,
        customer_tier: str,
    ) -> AsyncGenerator[None, None]:
        """
        Trace pricing calculation using OpenTelemetry.

        Creates a distributed tracing span for the calculation.
        """
        if self.tracer:
            with self.tracer.start_as_current_span(
                "pricing.calculate",
                attributes={
                    "pricing.calculation_id": str(calculation_id),
                    "pricing.material": material,
                    "pricing.process": process,
                    "pricing.quantity": quantity,
                    "pricing.customer_tier": customer_tier,
                },
            ):
                yield
        else:
            yield

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
        Record pricing metrics using Prometheus.

        Records duration, prices, margins, and success counts.
        """
        # Record calculation duration
        _pricing_calculation_duration.labels(
            material=material,
            process=process,
            tier=customer_tier,
        ).observe(duration_seconds)

        # Record prices and margins for each tier
        for tier_name, breakdown in [
            ("expedited", tier_pricing.expedited),
            ("standard", tier_pricing.standard),
            ("economy", tier_pricing.economy),
            ("domestic_economy", tier_pricing.domestic_economy),
        ]:
            # Record final price
            _pricing_final_prices.labels(tier=tier_name).observe(
                float(breakdown.final_price)
            )

            # Record margin
            _pricing_margins.labels(tier=tier_name).observe(float(breakdown.margin))

            # Record successful calculation
            _pricing_calculations_total.labels(
                material=material,
                process=process,
                tier=tier_name,
                status="success",
            ).inc()

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
        Record pricing errors.

        Increments error counter and adds error information to tracing span.
        """
        # Record error metric
        _pricing_errors_total.labels(
            material=material or "unknown",
            process=process or "unknown",
            error_type=error_type,
        ).inc()

        # Add error info to current span if available
        if self.tracer:
            span = trace.get_current_span()
            if span:
                span.set_status(trace.Status(trace.StatusCode.ERROR, error))
                attributes: dict[str, str] = {
                    "pricing.calculation_id": str(calculation_id),
                    "pricing.error": error,
                    "pricing.error_type": error_type,
                }
                if material is not None:
                    attributes["pricing.material"] = material
                if process is not None:
                    attributes["pricing.process"] = process
                if customer_tier is not None:
                    attributes["pricing.customer_tier"] = customer_tier
                span.set_attributes(attributes)
