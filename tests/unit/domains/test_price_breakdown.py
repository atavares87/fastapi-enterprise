"""
Unit tests for PriceBreakdown model.

Tests PriceBreakdown.create factory method.
"""

from decimal import Decimal

from app.core.domain.pricing.models.price_breakdown import PriceBreakdown


class TestPriceBreakdown:
    """Test cases for PriceBreakdown."""

    def test_price_breakdown_create(self):
        """Test PriceBreakdown.create factory method."""
        breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("20.00"),
            shipping_cost=Decimal("10.00"),
            volume_discount=Decimal("5.00"),
            complexity_surcharge=Decimal("15.00"),
            final_discount=Decimal("2.00"),
        )

        assert breakdown.base_cost == Decimal("100.00")
        assert breakdown.margin == Decimal("20.00")
        assert breakdown.shipping_cost == Decimal("10.00")
        assert breakdown.volume_discount == Decimal("5.00")
        assert breakdown.complexity_surcharge == Decimal("15.00")
        assert breakdown.final_discount == Decimal("2.00")
        assert breakdown.subtotal > 0
        assert breakdown.final_price > 0
        # Note: price_per_unit is set separately in tier calculations, not in create()

    def test_price_breakdown_calculations(self):
        """Test PriceBreakdown calculations."""
        breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("20.00"),
            shipping_cost=Decimal("10.00"),
            volume_discount=Decimal("5.00"),
            complexity_surcharge=Decimal("15.00"),
            final_discount=Decimal("2.00"),
        )

        # Verify calculations
        # subtotal = base_cost + margin + shipping_cost + complexity_surcharge - volume_discount
        expected_subtotal = (
            Decimal("100.00")
            + Decimal("20.00")
            + Decimal("10.00")
            + Decimal("15.00")
            - Decimal("5.00")
        )
        assert breakdown.subtotal == expected_subtotal

        # final_price = subtotal - final_discount
        expected_final = expected_subtotal - Decimal("2.00")
        assert breakdown.final_price == expected_final
