"""
Unit tests for TelemetryManager.

Tests TelemetryManager initialization, setup, and methods.
"""

from unittest.mock import Mock, patch

import pytest

from app.infrastructure.telemetry import (
    TelemetryConfig,
    TelemetryManager,
    get_telemetry_manager,
    initialize_telemetry,
    shutdown_telemetry,
)


class TestTelemetryManager:
    """Test cases for TelemetryManager."""

    def test_manager_initialization(self):
        """Test TelemetryManager initialization."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        assert manager.config == config
        assert manager.tracer_provider is None

    @patch("app.infrastructure.telemetry.Resource.create")
    @patch("app.infrastructure.telemetry.TracerProvider")
    @patch("app.infrastructure.telemetry.OTLPSpanExporter")
    @patch("app.infrastructure.telemetry.BatchSpanProcessor")
    @patch("app.infrastructure.telemetry.ConsoleSpanExporter")
    @patch("app.infrastructure.telemetry.set_global_textmap")
    @patch("app.infrastructure.telemetry.PymongoInstrumentor")
    @patch("app.infrastructure.telemetry.HTTPXClientInstrumentor")
    @patch("app.infrastructure.telemetry.RedisInstrumentor")
    def test_setup_telemetry(
        self,
        mock_redis,
        mock_httpx,
        mock_pymongo,
        mock_set_global,
        mock_console_exporter,
        mock_batch_processor,
        mock_otlp_exporter,
        mock_tracer_provider,
        mock_resource_create,
    ):
        """Test setup_telemetry."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        # Mock resource
        mock_resource = Mock()
        mock_resource_create.return_value = mock_resource

        # Mock tracer provider
        mock_tracer_provider_instance = Mock()
        mock_tracer_provider.return_value = mock_tracer_provider_instance

        # Mock exporters
        mock_otlp_exporter_instance = Mock()
        mock_otlp_exporter.return_value = mock_otlp_exporter_instance
        mock_console_exporter_instance = Mock()
        mock_console_exporter.return_value = mock_console_exporter_instance

        # Mock processors
        mock_batch_processor_instance = Mock()
        mock_batch_processor.return_value = mock_batch_processor_instance

        # Mock instrumentors
        mock_pymongo_instance = Mock()
        mock_pymongo.return_value = mock_pymongo_instance
        mock_httpx_instance = Mock()
        mock_httpx.return_value = mock_httpx_instance
        mock_redis_instance = Mock()
        mock_redis.return_value = mock_redis_instance

        manager.setup_telemetry()

        # Verify setup was called
        assert manager.tracer_provider is not None
        mock_resource_create.assert_called_once()
        mock_tracer_provider.assert_called_once_with(resource=mock_resource)
        mock_tracer_provider_instance.add_span_processor.assert_called()

    def test_setup_telemetry_with_console_exporter(self, monkeypatch):
        """Test setup_telemetry with console exporter enabled."""
        monkeypatch.setenv("ENABLE_CONSOLE_TRACES", "true")

        with (
            patch("app.infrastructure.telemetry.Resource.create"),
            patch("app.infrastructure.telemetry.TracerProvider"),
            patch("app.infrastructure.telemetry.OTLPSpanExporter"),
            patch("app.infrastructure.telemetry.BatchSpanProcessor"),
            patch("app.infrastructure.telemetry.ConsoleSpanExporter") as mock_console,
            patch("app.infrastructure.telemetry.set_global_textmap"),
            patch("app.infrastructure.telemetry.PymongoInstrumentor"),
            patch("app.infrastructure.telemetry.HTTPXClientInstrumentor"),
            patch("app.infrastructure.telemetry.RedisInstrumentor"),
        ):

            config = TelemetryConfig()
            manager = TelemetryManager(config)
            manager.setup_telemetry()

            # Console exporter should be created if ENABLE_CONSOLE_TRACES is true
            mock_console.assert_called_once()

    @patch("app.infrastructure.telemetry.FastAPIInstrumentor")
    def test_instrument_fastapi(self, mock_instrumentor):
        """Test instrument_fastapi."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager.tracer_provider = Mock()

        mock_app = Mock()
        manager.instrument_fastapi(mock_app)

        mock_instrumentor.instrument_app.assert_called_once_with(
            mock_app,
            tracer_provider=manager.tracer_provider,
        )

    @patch("app.infrastructure.telemetry.trace.get_tracer")
    def test_get_tracer(self, mock_get_tracer):
        """Test get_tracer."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        result = manager.get_tracer("test_module")

        mock_get_tracer.assert_called_once_with("test_module", config.service_version)
        assert result == mock_tracer

    def test_parse_headers(self):
        """Test _parse_headers."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        headers = manager._parse_headers("key1=value1,key2=value2")
        assert headers == {"key1": "value1", "key2": "value2"}

    def test_parse_headers_empty(self):
        """Test _parse_headers with empty string."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        headers = manager._parse_headers("")
        assert headers == {}

    def test_parse_headers_with_spaces(self):
        """Test _parse_headers with spaces."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        headers = manager._parse_headers("key1 = value1 , key2 = value2")
        assert headers == {"key1": "value1", "key2": "value2"}

    def test_shutdown(self):
        """Test shutdown."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager.tracer_provider = Mock()

        manager.shutdown()

        manager.tracer_provider.shutdown.assert_called_once()

    def test_shutdown_no_provider(self):
        """Test shutdown with no tracer provider."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)
        manager.tracer_provider = None

        # Should not raise
        manager.shutdown()

    @patch("app.infrastructure.telemetry.TelemetryManager")
    def test_initialize_telemetry(self, mock_manager_class):
        """Test initialize_telemetry."""
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = initialize_telemetry()

        mock_manager_class.assert_called_once()
        mock_manager.setup_telemetry.assert_called_once()
        assert result == mock_manager

    @patch("app.infrastructure.telemetry.TelemetryManager")
    def test_initialize_telemetry_with_config(self, mock_manager_class):
        """Test initialize_telemetry with custom config."""
        config = TelemetryConfig()
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        result = initialize_telemetry(config)

        mock_manager_class.assert_called_once_with(config)
        mock_manager.setup_telemetry.assert_called_once()
        assert result == mock_manager

    def test_get_telemetry_manager(self, monkeypatch):
        """Test get_telemetry_manager."""
        monkeypatch.setenv("TESTING", "true")

        # Clear any existing manager first
        import app.infrastructure.telemetry as telemetry_module

        telemetry_module._telemetry_manager = None

        # Initially None
        assert get_telemetry_manager() is None

        # After initialization
        manager = initialize_telemetry()
        assert get_telemetry_manager() == manager

    @pytest.mark.asyncio
    async def test_shutdown_telemetry(self):
        """Test shutdown_telemetry."""
        manager = initialize_telemetry()

        with patch.object(manager, "shutdown") as mock_shutdown:
            await shutdown_telemetry()
            mock_shutdown.assert_called_once()
            assert get_telemetry_manager() is None

    @pytest.mark.asyncio
    async def test_shutdown_telemetry_no_manager(self):
        """Test shutdown_telemetry when no manager exists."""
        # Ensure no manager
        import app.infrastructure.telemetry as telemetry_module

        telemetry_module._telemetry_manager = None

        # Should not raise
        await shutdown_telemetry()
