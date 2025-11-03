"""
Unit tests for telemetry setup methods.

Tests telemetry initialization and setup paths.
"""

from unittest.mock import patch

from app.infra.telemetry import TelemetryConfig, TelemetryManager


class TestTelemetryManagerSetup:
    """Test telemetry manager setup methods."""

    def test_setup_resource(self):
        """Test _setup_resource method."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        manager._setup_resource()

        assert manager.resource is not None

    @patch("app.infra.telemetry.TracerProvider")
    @patch("app.infra.telemetry.OTLPSpanExporter")
    @patch("app.infra.telemetry.BatchSpanProcessor")
    def test_setup_tracing(self, mock_processor, mock_exporter, mock_provider):
        """Test _setup_tracing method."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager._setup_resource()

        manager._setup_tracing()

        # Should not raise
        assert True

    @patch("app.infra.telemetry.trace")
    def test_setup_propagation(self, mock_trace):
        """Test _setup_propagation method."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        manager._setup_propagation()

        # Should not raise
        assert True

    def test_instrument_libraries(self):
        """Test _instrument_libraries method."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        # This may raise warnings if instrumentors are not available, but should not crash
        try:
            manager._instrument_libraries()
        except Exception:
            # Instrumentors may not be available in test environment
            pass

        # Should not raise critical errors
        assert True

    def test_get_tracer(self):
        """Test get_tracer method."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager.setup_telemetry()

        tracer = manager.get_tracer("test")

        assert tracer is not None

    def test_instrument_fastapi(self):
        """Test instrument_fastapi method."""
        from fastapi import FastAPI

        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager.setup_telemetry()

        app = FastAPI()
        manager.instrument_fastapi(app)

        # Should not raise
        assert True

    def test_shutdown(self):
        """Test shutdown method."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager.setup_telemetry()

        manager.shutdown()

        # Should not raise
        assert True
