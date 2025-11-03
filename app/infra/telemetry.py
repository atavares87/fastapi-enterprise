"""
OpenTelemetry Configuration - Distributed Tracing (INDUSTRY STANDARD)

Provides:
- Distributed Tracing (request flows across services)
- Structured Logging

Metrics are handled by prometheus-fastapi-instrumentator (the standard for FastAPI).

Reference: https://opentelemetry.io/docs/languages/python/
"""

import os
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
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

        # OTLP configuration (for sending telemetry to collector)
        self.otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
        self.otlp_headers = os.getenv("OTLP_HEADERS", "")

        # Console exporters (for development)
        self.enable_console_traces = (
            os.getenv("ENABLE_CONSOLE_TRACES", "false").lower() == "true"
        )

        # Metrics configuration
        self.metrics_port = int(os.getenv("METRICS_PORT", "8000"))  # Same as app port

        # Sampling configuration
        self.trace_sample_rate = float(os.getenv("TRACE_SAMPLE_RATE", "0.1"))


class TelemetryManager:
    """
    Manages OpenTelemetry distributed tracing.

    Handles:
    - Distributed Tracing (via OTLP exporter)
    - Auto-instrumentation of FastAPI, databases, HTTP clients

    Note: Metrics are handled by prometheus-fastapi-instrumentator (standard approach).
    """

    def __init__(self, config: TelemetryConfig):
        self.config = config
        self.tracer_provider: TracerProvider | None = None

    def setup_telemetry(self) -> None:
        """Set up distributed tracing."""
        self._setup_resource()
        self._setup_tracing()
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
        """Set up distributed tracing with OTLP exporter."""
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=self.resource)

        # OTLP exporter for production (sends traces to collector)
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

        logger.info("✅ OpenTelemetry tracing configured")

    def _setup_propagation(self) -> None:
        """
        Set up trace context propagation using B3 format.

        This allows traces to be propagated across service boundaries.
        """
        set_global_textmap(B3MultiFormat())

    def _instrument_libraries(self) -> None:
        """
        Auto-instrument common libraries for distributed tracing.

        This automatically creates spans for:
        - MongoDB operations
        - HTTP client requests
        - Redis operations
        """
        # MongoDB instrumentation
        try:
            PymongoInstrumentor().instrument()
        except Exception as exc:
            logger.warning("MongoDB instrumentation disabled", error=str(exc))

        # HTTP client instrumentation
        try:
            HTTPXClientInstrumentor().instrument()
        except Exception as exc:
            logger.warning("HTTPX instrumentation disabled", error=str(exc))

        # Redis instrumentation
        try:
            RedisInstrumentor().instrument()
        except Exception as exc:
            logger.warning("Redis instrumentation disabled", error=str(exc))

    def instrument_fastapi(self, app: Any) -> None:
        """
        Instrument FastAPI application for distributed tracing.

        This automatically creates spans for each HTTP request.

        Note: HTTP metrics are handled by prometheus-fastapi-instrumentator.
        """
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=self.tracer_provider,
        )

        logger.info("✅ FastAPI instrumentation enabled (distributed tracing)")

    def get_tracer(self, name: str) -> trace.Tracer:
        """
        Get a tracer for creating custom spans.

        Args:
            name: Name of the tracer (usually module or component name)

        Returns:
            Tracer instance for creating spans
        """
        return trace.get_tracer(name, self.config.service_version)

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

    def shutdown(self) -> None:
        """Shutdown telemetry providers and flush remaining data."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()


# =============================================================================
# GLOBAL SINGLETON
# =============================================================================

_telemetry_manager: TelemetryManager | None = None


def initialize_telemetry(config: TelemetryConfig | None = None) -> TelemetryManager:
    """
    Initialize global telemetry manager.

    Args:
        config: Optional telemetry configuration

    Returns:
        TelemetryManager instance
    """
    global _telemetry_manager

    if config is None:
        config = TelemetryConfig()

    _telemetry_manager = TelemetryManager(config)
    _telemetry_manager.setup_telemetry()

    return _telemetry_manager


def get_telemetry_manager() -> TelemetryManager | None:
    """Get the global telemetry manager."""
    return _telemetry_manager


async def shutdown_telemetry() -> None:
    """Shutdown global telemetry and flush remaining data."""
    global _telemetry_manager
    if _telemetry_manager:
        _telemetry_manager.shutdown()
        _telemetry_manager = None
