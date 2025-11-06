"""
Unit tests for telemetry tracing paths.

Tests conditional tracing setup paths.
"""

from app.infrastructure.telemetry import TelemetryConfig, TelemetryManager


class TestTelemetryTracingPaths:
    """Test conditional paths in tracing setup."""

    def test_setup_tracing_with_console_exporter(self, monkeypatch):
        """Test tracing setup with console exporter enabled."""
        monkeypatch.setenv("ENABLE_CONSOLE_TRACES", "true")

        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager._setup_resource()

        # Should not raise
        manager._setup_tracing()
        assert manager.tracer_provider is not None

    def test_setup_tracing_basic(self):
        """Test basic tracing setup."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager._setup_resource()

        # Should not raise
        manager._setup_tracing()
        assert manager.tracer_provider is not None
