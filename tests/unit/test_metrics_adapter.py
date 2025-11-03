"""
Unit tests for metrics adapter.

Tests business metrics recording using prometheus_client.
"""

from uuid import uuid4

import pytest

from app.adapter.outbound.telemetry.metrics_adapter import TelemetryAdapter
from app.core.domain.pricing.models.price_breakdown import PriceBreakdown
from app.core.domain.pricing.tier import TierPricing


class TestTelemetryAdapter:
    """Test cases for TelemetryAdapter."""

    def test_adapter_initialization(self):
        """Test TelemetryAdapter initialization."""
        adapter = TelemetryAdapter()
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_get_current_time(self):
        """Test get_current_time returns float."""
        adapter = TelemetryAdapter()
        time_value = await adapter.get_current_time()
        assert isinstance(time_value, float)
        assert time_value > 0

    @pytest.mark.asyncio
    async def test_trace_pricing_calculation(self):
        """Test trace_pricing_calculation context manager."""
        adapter = TelemetryAdapter()
        calculation_id = uuid4()

        async with adapter.trace_pricing_calculation(
            calculation_id=calculation_id,
            material="aluminum",
            process="cnc",
            quantity=10,
            customer_tier="standard",
        ):
            # Should not raise
            pass

    @pytest.mark.asyncio
    async def test_record_pricing_metrics(self):
        """Test record_pricing_metrics."""
        adapter = TelemetryAdapter()
        calculation_id = uuid4()

        # Create mock tier pricing
        breakdown = PriceBreakdown(
            base_cost=100.0,
            margin=20.0,
            shipping_cost=10.0,
            volume_discount=5.0,
            complexity_surcharge=15.0,
            subtotal=120.0,
            final_discount=2.0,
            final_price=118.0,
            price_per_unit=11.8,
        )

        tier_pricing = TierPricing(
            expedited=breakdown,
            standard=breakdown,
            economy=breakdown,
            domestic_economy=breakdown,
        )

        await adapter.record_pricing_metrics(
            calculation_id=calculation_id,
            material="aluminum",
            process="cnc",
            tier_pricing=tier_pricing,
            duration_seconds=0.5,
            quantity=10,
            customer_tier="standard",
        )

        # Should not raise
        assert True

    @pytest.mark.asyncio
    async def test_record_error(self):
        """Test record_error."""
        adapter = TelemetryAdapter()
        calculation_id = uuid4()

        await adapter.record_error(
            calculation_id=calculation_id,
            error="Test error",
            error_type="TestError",
            material="aluminum",
            process="cnc",
            customer_tier="standard",
        )

        # Should not raise
        assert True
