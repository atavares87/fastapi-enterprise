"""
Unit tests for telemetry module.

Tests OpenTelemetry initialization and configuration.
"""

from app.infra.telemetry import (
    TelemetryConfig,
    TelemetryManager,
    get_telemetry_manager,
    initialize_telemetry,
)


class TestTelemetryConfig:
    """Test cases for TelemetryConfig."""

    def test_default_config(self, monkeypatch):
        """Test default configuration values."""
        # Clear environment variables
        for key in ["OTEL_EXPORTER_OTLP_ENDPOINT", "TRACE_SAMPLE_RATE", "METRICS_PORT"]:
            monkeypatch.delenv(key, raising=False)

        config = TelemetryConfig()

        assert config.service_name == "fastapi-enterprise"
        assert config.service_version == "1.0.0"
        assert config.deployment_environment == "development"
        assert config.otlp_endpoint == "http://localhost:4317"
        assert config.trace_sample_rate == 0.1
        assert config.metrics_port == 8000

    def test_config_from_environment(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("OTLP_ENDPOINT", "http://custom:4317")
        monkeypatch.setenv("TRACE_SAMPLE_RATE", "0.5")
        monkeypatch.setenv("METRICS_PORT", "9000")
        monkeypatch.setenv("DEPLOYMENT_ENVIRONMENT", "production")

        config = TelemetryConfig()

        assert config.otlp_endpoint == "http://custom:4317"
        assert config.trace_sample_rate == 0.5
        assert config.metrics_port == 9000
        assert config.deployment_environment == "production"


class TestTelemetryManager:
    """Test cases for TelemetryManager."""

    def test_telemetry_manager_initialization(self):
        """Test TelemetryManager initialization."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        assert manager.config == config
        assert manager.tracer_provider is None

    def test_setup_telemetry(self):
        """Test setting up telemetry."""
        config = TelemetryConfig()
        manager = TelemetryManager(config)

        # Should not raise
        manager.setup_telemetry()

        # Resource should be created
        assert manager.resource is not None


class TestTelemetryFunctions:
    """Test cases for telemetry module functions."""

    def test_initialize_telemetry_default(self, monkeypatch):
        """Test initialize_telemetry with default config."""
        # Set test environment
        monkeypatch.setenv("TESTING", "true")

        # Initialize telemetry
        manager = initialize_telemetry()

        assert manager is not None
        assert isinstance(manager, TelemetryManager)

    def test_initialize_telemetry_with_config(self, monkeypatch):
        """Test initialize_telemetry with custom config."""
        monkeypatch.setenv("TESTING", "true")

        config = TelemetryConfig()
        manager = initialize_telemetry(config)

        assert manager is not None
        assert manager.config == config

    def test_get_telemetry_manager(self, monkeypatch):
        """Test get_telemetry_manager."""
        monkeypatch.setenv("TESTING", "true")

        # Initialize first
        initialize_telemetry()

        manager = get_telemetry_manager()
        assert manager is not None
        assert isinstance(manager, TelemetryManager)

    def test_get_telemetry_manager_before_init(self):
        """Test get_telemetry_manager before initialization."""
        # Clear any existing manager
        import app.infra.telemetry as telemetry_module

        telemetry_module._telemetry_manager = None

        manager = get_telemetry_manager()
        assert manager is None
