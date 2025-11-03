"""
Telemetry Adapter - STANDARD Implementation

Handles all telemetry side effects using STANDARD libraries:
- Business metrics: prometheus_client (STANDARD for Prometheus metrics)
- Distributed tracing: OpenTelemetry (STANDARD for tracing)

HTTP and system metrics are handled by prometheus-fastapi-instrumentator (STANDARD).

Reference: https://github.com/prometheus/client_python#counter
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

import structlog
from opentelemetry import trace
from prometheus_client import Counter, Histogram  # STANDARD Prometheus client library

from app.core.domain.pricing.tier import TierPricing
from app.infra.telemetry import get_telemetry_manager

logger = structlog.get_logger(__name__)


# =============================================================================
# MODULE-LEVEL METRICS (STANDARD prometheus_client pattern)
# =============================================================================
# Metrics are created ONCE at module import time (singleton pattern).
# This is the STANDARD way to use prometheus_client - NOT instance variables!
# Reference: https://github.com/prometheus/client_python#counter

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


class TelemetryAdapter:
    """
    STANDARD implementation of telemetry port.

    Uses prometheus_client for metrics (STANDARD) and OpenTelemetry for tracing.
    All I/O operations isolated here (Imperative Shell).

    Note: Metrics are MODULE-LEVEL singletons (standard prometheus_client pattern).
    """

    def __init__(self) -> None:
        """
        Initialize tracer (metrics are module-level).

        Reference: https://github.com/prometheus/client_python
        """
        # Get tracer for distributed tracing
        telemetry_manager = get_telemetry_manager()
        self.tracer = (
            telemetry_manager.get_tracer("pricing") if telemetry_manager else None
        )

    async def get_current_time(self) -> float:
        """Get current time (side effect)."""
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
        Record pricing metrics using STANDARD prometheus_client.

        Reference: https://github.com/prometheus/client_python#counter
        """
        # Record duration (use module-level metric - STANDARD pattern)
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
            # Record final price (STANDARD API)
            _pricing_final_prices.labels(tier=tier_name).observe(
                float(breakdown.final_price)
            )

            # Record margin (STANDARD API)
            _pricing_margins.labels(tier=tier_name).observe(float(breakdown.margin))

            # Record tier-specific calculation success (STANDARD API)
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
        Record pricing errors using STANDARD prometheus_client.

        Reference: https://github.com/prometheus/client_python#counter
        """
        # Record error metric (use module-level metric - STANDARD pattern)
        _pricing_errors_total.labels(
            material=material or "unknown",
            process=process or "unknown",
            error_type=error_type,
        ).inc()

        # Add error info to current span if available (STANDARD OTEL tracing)
        if self.tracer:
            span = trace.get_current_span()
            if span:
                span.set_status(trace.Status(trace.StatusCode.ERROR, error))
                # Build attributes dict, filtering out None values
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
