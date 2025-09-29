"""
OpenTelemetry Configuration and Setup

Provides comprehensive observability with traces, metrics, and logs
for monitoring pricing calculations and application performance.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semconv.resource import ResourceAttributes

logger = structlog.get_logger()


class TelemetryConfig:
    """Configuration for OpenTelemetry setup."""

    def __init__(self) -> None:
        self.service_name = os.getenv("SERVICE_NAME", "fastapi-enterprise")
        self.service_version = os.getenv("SERVICE_VERSION", "1.0.0")
        self.deployment_environment = os.getenv("DEPLOYMENT_ENVIRONMENT", "development")

        # OTLP configuration
        self.otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        self.otlp_headers = os.getenv("OTLP_HEADERS", "")

        # Prometheus configuration
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8001"))
        self.enable_prometheus = (
            os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"
        )

        # Console exporters (for development)
        self.enable_console_traces = (
            os.getenv("ENABLE_CONSOLE_TRACES", "false").lower() == "true"
        )

        # Sampling configuration
        self.trace_sample_rate = float(os.getenv("TRACE_SAMPLE_RATE", "0.1"))


class PricingMetrics:
    """Custom metrics for pricing operations."""

    def __init__(self, meter: metrics.Meter) -> None:
        self.meter = meter

        # Counters
        self.pricing_calculations_total = meter.create_counter(
            name="pricing_calculations_total",
            description="Total number of pricing calculations performed",
            unit="1",
        )

        self.pricing_errors_total = meter.create_counter(
            name="pricing_errors_total",
            description="Total number of pricing calculation errors",
            unit="1",
        )

        self.limit_violations_total = meter.create_counter(
            name="pricing_limit_violations_total",
            description="Total number of pricing limit violations",
            unit="1",
        )

        # Histograms
        self.pricing_calculation_duration = meter.create_histogram(
            name="pricing_calculation_duration_seconds",
            description="Duration of pricing calculations",
            unit="s",
        )

        self.pricing_final_prices = meter.create_histogram(
            name="pricing_final_prices",
            description="Final prices calculated",
            unit="USD",
        )

        self.pricing_margins = meter.create_histogram(
            name="pricing_margins", description="Profit margins calculated", unit="USD"
        )

        # Gauges
        self.active_pricing_calculations = meter.create_up_down_counter(
            name="active_pricing_calculations",
            description="Number of pricing calculations currently in progress",
            unit="1",
        )


class TelemetryManager:
    """Manages OpenTelemetry setup and instrumentation."""

    def __init__(self, config: TelemetryConfig):
        self.config = config
        self.tracer_provider: TracerProvider | None = None
        self.meter_provider: MeterProvider | None = None
        self.pricing_metrics: PricingMetrics | None = None

    def setup_telemetry(self) -> None:
        """Set up complete telemetry stack."""
        self._setup_resource()
        self._setup_tracing()
        self._setup_metrics()
        self._setup_propagation()
        self._instrument_libraries()

    def _setup_resource(self) -> None:
        """Create resource with service information."""
        self.resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: self.config.service_name,
                ResourceAttributes.SERVICE_VERSION: self.config.service_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.config.deployment_environment,
            }
        )

    def _setup_tracing(self) -> None:
        """Set up distributed tracing."""
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=self.resource)

        # OTLP exporter for production
        if self.config.otlp_endpoint:
            otlp_span_exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
                headers=self._parse_headers(self.config.otlp_headers),
            )
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_span_exporter)
            )

        # Console exporter for development
        if self.config.enable_console_traces:
            console_exporter = ConsoleSpanExporter()
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )

        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)

    def _setup_metrics(self) -> None:
        """Set up metrics collection."""
        readers: list[MetricReader] = []

        # OTLP metrics exporter
        if self.config.otlp_endpoint:
            otlp_metric_exporter = OTLPMetricExporter(
                endpoint=self.config.otlp_endpoint,
                headers=self._parse_headers(self.config.otlp_headers),
            )
            readers.append(
                PeriodicExportingMetricReader(
                    exporter=otlp_metric_exporter, export_interval_millis=5000
                )
            )

        # Prometheus metrics exporter
        if self.config.enable_prometheus:
            prometheus_reader = PrometheusMetricReader()
            readers.append(prometheus_reader)

            # Note: Don't start separate HTTP server - use FastAPI /metrics endpoint

        # Create meter provider
        self.meter_provider = MeterProvider(
            resource=self.resource, metric_readers=readers
        )

        # Set global meter provider
        metrics.set_meter_provider(self.meter_provider)

        # Create custom pricing metrics
        meter = metrics.get_meter("pricing", self.config.service_version)
        self.pricing_metrics = PricingMetrics(meter)

    def _setup_propagation(self) -> None:
        """Set up trace context propagation."""
        set_global_textmap(B3MultiFormat())

    def _instrument_libraries(self) -> None:
        """Instrument common libraries."""
        # MongoDB instrumentation
        PymongoInstrumentor().instrument()

        # HTTP client instrumentation
        HTTPXClientInstrumentor().instrument()

        # Redis instrumentation (if available)
        try:
            RedisInstrumentor().instrument()
        except Exception as exc:
            logger.warning("Redis instrumentation disabled", error=str(exc))

    def instrument_fastapi(self, app: Any) -> None:
        """Instrument FastAPI application."""
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=self.tracer_provider,
            meter_provider=self.meter_provider,
        )

    def _parse_headers(self, headers_string: str) -> dict[str, str]:
        """Parse OTLP headers from environment variable."""
        if not headers_string:
            return {}

        headers = {}
        for header in headers_string.split(","):
            if "=" in header:
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()

        return headers

    def get_tracer(self, name: str) -> trace.Tracer:
        """Get a tracer for the given name."""
        return trace.get_tracer(name, self.config.service_version)

    def get_meter(self, name: str) -> metrics.Meter:
        """Get a meter for the given name."""
        return metrics.get_meter(name, self.config.service_version)

    def shutdown(self) -> None:
        """Shutdown telemetry providers."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
        if self.meter_provider:
            self.meter_provider.shutdown()


class PricingTelemetry:
    """Specialized telemetry for pricing operations."""

    def __init__(self, telemetry_manager: TelemetryManager) -> None:
        self.tracer = telemetry_manager.get_tracer("pricing")
        if telemetry_manager.pricing_metrics is None:
            raise ValueError("Pricing metrics not initialized")
        self.metrics = telemetry_manager.pricing_metrics

    @asynccontextmanager
    async def trace_pricing_calculation(
        self, material: str, process: str, quantity: int, customer_tier: str
    ) -> AsyncGenerator[trace.Span, None]:
        """Context manager for tracing pricing calculations."""

        with self.tracer.start_as_current_span("pricing_calculation") as span:
            # Set span attributes
            span.set_attributes(
                {
                    "pricing.material": material,
                    "pricing.process": process,
                    "pricing.quantity": quantity,
                    "pricing.customer_tier": customer_tier,
                }
            )

            # Track active calculations
            self.metrics.active_pricing_calculations.add(
                1,
                {
                    "material": material,
                    "process": process,
                    "customer_tier": customer_tier,
                },
            )

            try:
                yield span

                # Record successful calculation
                self.metrics.pricing_calculations_total.add(
                    1,
                    {
                        "material": material,
                        "process": process,
                        "customer_tier": customer_tier,
                        "status": "success",
                    },
                )

            except Exception as e:
                # Record error
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

                self.metrics.pricing_errors_total.add(
                    1,
                    {
                        "material": material,
                        "process": process,
                        "customer_tier": customer_tier,
                        "error_type": type(e).__name__,
                    },
                )

                raise
            finally:
                # Track calculation completion
                self.metrics.active_pricing_calculations.add(
                    -1,
                    {
                        "material": material,
                        "process": process,
                        "customer_tier": customer_tier,
                    },
                )

    def record_pricing_result(
        self,
        duration_seconds: float,
        final_price: float,
        margin: float,
        tier: str,
        limits_applied: bool = False,
        limit_violations: int = 0,
    ) -> None:
        """Record pricing calculation results."""

        attributes = {"tier": tier}

        # Record duration
        self.metrics.pricing_calculation_duration.record(duration_seconds, attributes)

        # Record financial metrics
        self.metrics.pricing_final_prices.record(final_price, attributes)

        self.metrics.pricing_margins.record(margin, attributes)

        # Record limit violations if any
        if limit_violations > 0:
            self.metrics.limit_violations_total.add(
                limit_violations, {**attributes, "limits_applied": str(limits_applied)}
            )

    def trace_cost_calculation(self, material: str, process: str) -> trace.Span:
        """Create a span for cost calculation."""
        span = self.tracer.start_span("cost_calculation")
        span.set_attributes(
            {
                "cost.material": material,
                "cost.process": process,
            }
        )
        return span

    def trace_limit_enforcement(self, tier: str, violations: int) -> trace.Span:
        """Create a span for limit enforcement."""
        span = self.tracer.start_span("limit_enforcement")
        span.set_attributes(
            {
                "limits.tier": tier,
                "limits.violations": violations,
            }
        )
        return span

    def trace_explanation_generation(self, calculation_id: str) -> trace.Span:
        """Create a span for explanation generation."""
        span = self.tracer.start_span("explanation_generation")
        span.set_attributes(
            {
                "explanation.calculation_id": calculation_id,
            }
        )
        return span

    def trace_database_operation(self, operation: str, collection: str) -> trace.Span:
        """Create a span for database operations."""
        span = self.tracer.start_span(f"db_{operation}")
        span.set_attributes(
            {
                "db.operation": operation,
                "db.collection": collection,
            }
        )
        return span


# Global telemetry manager instance
_telemetry_manager: TelemetryManager | None = None


def initialize_telemetry(config: TelemetryConfig | None = None) -> TelemetryManager:
    """Initialize global telemetry manager."""
    global _telemetry_manager

    if config is None:
        config = TelemetryConfig()

    _telemetry_manager = TelemetryManager(config)
    _telemetry_manager.setup_telemetry()

    return _telemetry_manager


def get_telemetry_manager() -> TelemetryManager | None:
    """Get the global telemetry manager."""
    return _telemetry_manager


def get_pricing_telemetry() -> PricingTelemetry | None:
    """Get pricing-specific telemetry."""
    if _telemetry_manager:
        return PricingTelemetry(_telemetry_manager)
    return None


def shutdown_telemetry() -> None:
    """Shutdown global telemetry."""
    global _telemetry_manager
    if _telemetry_manager:
        _telemetry_manager.shutdown()
        _telemetry_manager = None
