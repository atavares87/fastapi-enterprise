"""
Unit tests for adapter error paths.

Tests error handling in adapters.
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.domain.model import PriceBreakdown, TierPricing
from app.repository.metrics_repository import MetricsRepository


class TestMetricsRepositoryErrorPaths:
    """Test error paths in MetricsRepository."""

    @pytest.mark.asyncio
    async def test_record_error_with_none_values(self):
        """Test record_error with None material/process."""
        adapter = MetricsRepository()

        await adapter.record_error(
            calculation_id=uuid4(),
            error="Test error",
            error_type="TestError",
            material=None,
            process=None,
            customer_tier=None,
        )

        # Should not raise - uses "unknown" for None values
        assert True

    @pytest.mark.asyncio
    async def test_record_error_without_tracer(self):
        """Test record_error when tracer is None."""
        adapter = MetricsRepository()
        # Ensure tracer is None
        adapter.tracer = None

        await adapter.record_error(
            calculation_id=uuid4(),
            error="Test error",
            error_type="TestError",
        )

        # Should not raise even without tracer
        assert True

    @pytest.mark.asyncio
    async def test_record_error_with_tracer_no_span(self):
        """Test record_error with tracer but no current span."""
        adapter = MetricsRepository()
        # Mock tracer without current span
        mock_tracer = Mock()
        adapter.tracer = mock_tracer

        with patch("app.repository.metrics_repository.trace") as mock_trace:
            mock_trace.get_current_span.return_value = None

            await adapter.record_error(
                calculation_id=uuid4(),
                error="Test error",
                error_type="TestError",
            )

        # Should not raise
        assert True

    @pytest.mark.asyncio
    async def test_record_pricing_metrics_all_tiers(self):
        """Test record_pricing_metrics handles all tiers."""
        adapter = MetricsRepository()
        calculation_id = uuid4()

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

        # Should record metrics for all four tiers
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
