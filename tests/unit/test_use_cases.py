"""
Unit tests for use cases.

Tests pricing use case initialization and basic functionality.
"""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.application.pricing.use_cases import CalculatePricingUseCase


class TestCalculatePricingUseCase:
    """Test cases for CalculatePricingUseCase."""

    @pytest.fixture
    def mock_cost_port(self):
        """Create mock cost data port."""
        port = Mock()
        port.get_material_costs = AsyncMock(
            return_value={"aluminum": Decimal("10.50"), "steel": Decimal("8.00")}
        )
        port.get_process_costs = AsyncMock(
            return_value={"cnc": Decimal("50.00"), "3d_printing": Decimal("30.00")}
        )
        return port

    @pytest.fixture
    def mock_pricing_port(self):
        """Create mock pricing config port."""
        port = Mock()
        port.get_tier_configurations = AsyncMock(
            return_value={
                "standard": {"margin_multiplier": Decimal("1.2")},
                "premium": {"margin_multiplier": Decimal("1.5")},
                "enterprise": {"margin_multiplier": Decimal("1.8")},
            }
        )
        port.get_shipping_costs = AsyncMock(
            return_value={
                1: Decimal("5.00"),
                2: Decimal("10.00"),
                3: Decimal("15.00"),
                4: Decimal("20.00"),
            }
        )
        return port

    @pytest.fixture
    def mock_telemetry_port(self):
        """Create mock telemetry port."""
        port = AsyncMock()
        port.get_current_time = AsyncMock(return_value=1000.0)
        port.record_error = AsyncMock()
        port.record_pricing_metrics = AsyncMock()
        # Context manager mock
        port.trace_pricing_calculation = AsyncMock()
        port.trace_pricing_calculation.return_value.__aenter__ = AsyncMock(
            return_value=None
        )
        port.trace_pricing_calculation.return_value.__aexit__ = AsyncMock(
            return_value=None
        )
        return port

    def test_use_case_initialization(
        self, mock_cost_port, mock_pricing_port, mock_telemetry_port
    ):
        """Test use case initialization."""
        use_case = CalculatePricingUseCase(
            cost_data_port=mock_cost_port,
            pricing_config_port=mock_pricing_port,
            pricing_persistence_port=None,
            telemetry_port=mock_telemetry_port,
        )

        assert use_case.cost_data_port == mock_cost_port
        assert use_case.pricing_config_port == mock_pricing_port
        assert use_case.telemetry_port == mock_telemetry_port
        assert use_case.pricing_persistence_port is None
