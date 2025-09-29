"""
Tests for the pricing limits system.

This module tests the pricing limits functionality including:
- Limit enforcement and adjustments
- Violation detection and reporting
- Exception handling for strict validation
- Integration with the pricing service
"""

from decimal import Decimal

import pytest

from app.modules.cost.domain import (
    CostBreakdown,
    ManufacturingProcess,
    Material,
    PartDimensions,
    PartSpecification,
)
from app.modules.pricing.domain import PriceBreakdown, PricingRequest, PricingTier
from app.modules.pricing.exceptions import (
    BelowMinimumPriceError,
    ExcessiveDiscountError,
    InsufficientMarginError,
    NegativePriceError,
)
from app.modules.pricing.limits import (
    LimitViolationType,
    PricingLimitConfigurationFactory,
    PricingLimitEnforcer,
    PricingLimits,
)
from app.modules.pricing.service import PricingService


@pytest.fixture
def sample_cost_breakdown():
    """Create a sample cost breakdown for testing."""
    return CostBreakdown.create(
        material_cost=Decimal("100.00"),
        labor_cost=Decimal("150.00"),
        setup_cost=Decimal("50.00"),
        complexity_adjustment=Decimal("20.00"),
    )


@pytest.fixture
def sample_pricing_request(sample_cost_breakdown):
    """Create a sample pricing request for testing."""
    return PricingRequest(
        cost_breakdown=sample_cost_breakdown,
        geometric_complexity_score=3.0,
        part_weight_kg=0.5,
        part_volume_cm3=125.0,
        quantity=10,
        customer_tier="standard",
        shipping_distance_zone=1,
    )


@pytest.fixture
def sample_price_breakdown():
    """Create a sample price breakdown that might violate limits."""
    return PriceBreakdown.create(
        base_cost=Decimal("350.00"),  # 10 units * $35 cost per unit
        margin=Decimal("105.00"),  # 30% margin
        shipping_cost=Decimal("25.00"),
        volume_discount=Decimal("50.00"),  # Large discount
        complexity_surcharge=Decimal("20.00"),
        final_discount=Decimal("200.00"),  # Very large final discount
    )


class TestPricingLimits:
    """Test pricing limits configuration and validation."""

    def test_pricing_limits_validation(self):
        """Test that pricing limits validate their configuration."""
        # Valid configuration
        limits = PricingLimits(
            minimum_price_per_unit=Decimal("1.00"),
            minimum_margin_percentage=0.10,
            maximum_total_discount_percentage=0.30,
        )
        assert limits.minimum_price_per_unit == Decimal("1.00")

        # Invalid margin percentage
        with pytest.raises(
            ValueError, match="Minimum margin percentage must be non-negative"
        ):
            PricingLimits(minimum_margin_percentage=-0.10)

        # Invalid discount percentage
        with pytest.raises(
            ValueError, match="Maximum discount percentage must be non-negative"
        ):
            PricingLimits(maximum_total_discount_percentage=-0.10)

        # Invalid cost multiplier
        with pytest.raises(
            ValueError, match="Minimum price over cost multiplier must be at least 1.0"
        ):
            PricingLimits(minimum_price_over_cost_multiplier=0.5)

    def test_factory_conservative_limits(self):
        """Test conservative limits factory."""
        limits = PricingLimitConfigurationFactory.conservative_limits()

        assert limits.minimum_price_per_unit == Decimal("1.00")
        assert limits.minimum_total_price == Decimal("25.00")
        assert limits.minimum_margin_percentage == 0.10
        assert limits.maximum_total_discount_percentage == 0.25
        assert limits.minimum_price_over_cost_multiplier == 1.05

    def test_factory_aggressive_limits(self):
        """Test aggressive limits factory."""
        limits = PricingLimitConfigurationFactory.aggressive_limits()

        assert limits.minimum_price_per_unit == Decimal("0.50")
        assert limits.minimum_total_price == Decimal("10.00")
        assert limits.minimum_margin_percentage == 0.05
        assert limits.maximum_total_discount_percentage == 0.35
        assert limits.minimum_price_over_cost_multiplier == 1.02

    def test_factory_custom_limits(self):
        """Test custom limits factory."""
        limits = PricingLimitConfigurationFactory.custom_limits(
            min_price_per_unit=Decimal("2.00"),
            min_margin_pct=0.15,
        )

        assert limits.minimum_price_per_unit == Decimal("2.00")
        assert limits.minimum_margin_percentage == 0.15
        assert limits.minimum_total_price is None  # Not specified


class TestPricingLimitEnforcer:
    """Test the pricing limit enforcer functionality."""

    def test_negative_price_fix(self, sample_pricing_request):
        """Test fixing negative prices by reducing discounts."""
        limits = PricingLimits()
        enforcer = PricingLimitEnforcer(limits)

        # Create a breakdown with excessive discounts leading to negative price
        negative_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("30.00"),
            shipping_cost=Decimal("20.00"),
            volume_discount=Decimal("80.00"),
            final_discount=Decimal("100.00"),  # Total discounts exceed base + margin
        )

        # This should result in a negative price
        assert negative_breakdown.final_price < 0

        # Apply limits should fix the negative price
        result = enforcer.apply_limits(
            negative_breakdown, sample_pricing_request, PricingTier.STANDARD
        )

        assert result.was_adjusted
        assert result.price_breakdown.final_price > 0
        assert len(result.violations) == 1
        assert result.violations[0].violation_type == LimitViolationType.NEGATIVE_PRICE

    def test_minimum_price_per_unit_enforcement(self, sample_pricing_request):
        """Test minimum price per unit enforcement."""
        limits = PricingLimits(minimum_price_per_unit=Decimal("5.00"))
        enforcer = PricingLimitEnforcer(limits)

        # Create breakdown with low per-unit price
        low_price_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),  # $10 per unit for 10 units
            margin=Decimal("20.00"),  # $2 per unit
            shipping_cost=Decimal("15.00"),
            volume_discount=Decimal("10.00"),
        )

        # Per unit price should be ($100 + $20 + $15 - $10) / 10 = $12.50
        per_unit_price = (
            low_price_breakdown.final_price / sample_pricing_request.quantity
        )

        # If we set a higher minimum, it should be adjusted
        if per_unit_price < Decimal("5.00"):
            result = enforcer.apply_limits(
                low_price_breakdown, sample_pricing_request, PricingTier.STANDARD
            )
            assert result.was_adjusted
            assert result.price_breakdown.price_per_unit >= Decimal("5.00")

    def test_minimum_total_price_enforcement(self, sample_pricing_request):
        """Test minimum total price enforcement."""
        limits = PricingLimits(minimum_total_price=Decimal("200.00"))
        enforcer = PricingLimitEnforcer(limits)

        # Create breakdown with low total price
        low_total_breakdown = PriceBreakdown.create(
            base_cost=Decimal("50.00"),
            margin=Decimal("15.00"),
            shipping_cost=Decimal("10.00"),
            volume_discount=Decimal("5.00"),
        )

        # Total should be $70, below our $200 minimum
        assert low_total_breakdown.final_price < Decimal("200.00")

        result = enforcer.apply_limits(
            low_total_breakdown, sample_pricing_request, PricingTier.STANDARD
        )

        assert result.was_adjusted
        assert result.price_breakdown.final_price >= Decimal("200.00")
        assert any(
            v.violation_type == LimitViolationType.MINIMUM_PRICE
            for v in result.violations
        )

    def test_minimum_margin_percentage_enforcement(self, sample_pricing_request):
        """Test minimum margin percentage enforcement."""
        limits = PricingLimits(minimum_margin_percentage=0.25)  # 25% minimum margin
        enforcer = PricingLimitEnforcer(limits)

        # Create breakdown with low margin
        low_margin_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("10.00"),  # Only 10% margin
            shipping_cost=Decimal("20.00"),
            volume_discount=Decimal("15.00"),
            final_discount=Decimal("20.00"),
        )

        result = enforcer.apply_limits(
            low_margin_breakdown, sample_pricing_request, PricingTier.STANDARD
        )

        assert result.was_adjusted
        # Margin should be increased by reducing discounts
        expected_min_margin = Decimal("100.00") * Decimal("0.25")  # 25% of base cost
        assert result.price_breakdown.margin >= expected_min_margin
        assert any(
            v.violation_type == LimitViolationType.MINIMUM_MARGIN
            for v in result.violations
        )

    def test_maximum_discount_enforcement(self, sample_pricing_request):
        """Test maximum discount percentage enforcement."""
        limits = PricingLimits(
            maximum_total_discount_percentage=0.20
        )  # 20% max discount
        enforcer = PricingLimitEnforcer(limits)

        # Create breakdown with excessive discounts
        high_discount_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("50.00"),  # Base + margin = $150
            shipping_cost=Decimal("20.00"),
            volume_discount=Decimal("30.00"),  # 20% of base+margin
            final_discount=Decimal("30.00"),  # Another 20% = 40% total discount
        )

        result = enforcer.apply_limits(
            high_discount_breakdown, sample_pricing_request, PricingTier.STANDARD
        )

        assert result.was_adjusted
        # Total discounts should be reduced to 20% max
        base_plus_margin = (
            result.price_breakdown.base_cost + result.price_breakdown.margin
        )
        total_discounts = (
            result.price_breakdown.volume_discount
            + result.price_breakdown.final_discount
        )
        discount_percentage = float(total_discounts / base_plus_margin)
        assert discount_percentage <= 0.20
        assert any(
            v.violation_type == LimitViolationType.MAXIMUM_DISCOUNT
            for v in result.violations
        )

    def test_cost_basis_protection(self, sample_pricing_request):
        """Test minimum price over cost protection."""
        limits = PricingLimits(
            minimum_price_over_cost_multiplier=1.10
        )  # 110% of cost minimum
        enforcer = PricingLimitEnforcer(limits)

        # Create breakdown where final price is too close to cost
        base_cost = (
            sample_pricing_request.cost_breakdown.total_cost
            * sample_pricing_request.quantity
        )

        low_price_breakdown = PriceBreakdown.create(
            base_cost=base_cost,
            margin=Decimal("10.00"),  # Very low margin
            shipping_cost=Decimal("5.00"),
            volume_discount=Decimal(
                "20.00"
            ),  # Discount that brings us below 110% of cost
        )

        result = enforcer.apply_limits(
            low_price_breakdown, sample_pricing_request, PricingTier.STANDARD
        )

        minimum_price = base_cost * Decimal("1.10")
        if low_price_breakdown.final_price < minimum_price:
            assert result.was_adjusted
            assert result.price_breakdown.final_price >= minimum_price
            assert any(
                v.violation_type == LimitViolationType.MINIMUM_PRICE
                for v in result.violations
            )

    def test_no_violations_when_within_limits(self, sample_pricing_request):
        """Test that no adjustments are made when pricing is within limits."""
        limits = PricingLimits(
            minimum_price_per_unit=Decimal("1.00"),
            minimum_total_price=Decimal("50.00"),
            minimum_margin_percentage=0.10,
            maximum_total_discount_percentage=0.30,
        )
        enforcer = PricingLimitEnforcer(limits)

        # Create a reasonable breakdown within all limits
        good_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("30.00"),  # 30% margin
            shipping_cost=Decimal("20.00"),
            volume_discount=Decimal("15.00"),  # 10% discount
        )

        result = enforcer.apply_limits(
            good_breakdown, sample_pricing_request, PricingTier.STANDARD
        )

        assert not result.was_adjusted
        assert len(result.violations) == 0
        assert result.price_breakdown == good_breakdown


class TestPricingLimitEnforcerStrictValidation:
    """Test strict validation mode that raises exceptions."""

    def test_strict_validation_negative_price(self, sample_pricing_request):
        """Test strict validation raises exception for negative price."""
        limits = PricingLimits()
        enforcer = PricingLimitEnforcer(limits)

        negative_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("30.00"),
            shipping_cost=Decimal("20.00"),
            volume_discount=Decimal("80.00"),
            final_discount=Decimal("100.00"),
        )

        with pytest.raises(NegativePriceError) as exc_info:
            enforcer.validate_limits_strict(
                negative_breakdown, sample_pricing_request, PricingTier.STANDARD
            )

        assert exc_info.value.tier == "standard"
        assert exc_info.value.final_price < 0

    def test_strict_validation_minimum_price(self, sample_pricing_request):
        """Test strict validation raises exception for below minimum price."""
        limits = PricingLimits(minimum_price_per_unit=Decimal("20.00"))
        enforcer = PricingLimitEnforcer(limits)

        low_price_breakdown = PriceBreakdown.create(
            base_cost=Decimal("50.00"),
            margin=Decimal("15.00"),
            shipping_cost=Decimal("10.00"),
        )

        with pytest.raises(BelowMinimumPriceError) as exc_info:
            enforcer.validate_limits_strict(
                low_price_breakdown, sample_pricing_request, PricingTier.STANDARD
            )

        assert exc_info.value.tier == "standard"
        assert exc_info.value.price_type == "per-unit"

    def test_strict_validation_insufficient_margin(self, sample_pricing_request):
        """Test strict validation raises exception for insufficient margin."""
        limits = PricingLimits(minimum_margin_percentage=0.50)  # 50% minimum
        enforcer = PricingLimitEnforcer(limits)

        low_margin_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("20.00"),  # Only 20% margin
            shipping_cost=Decimal("15.00"),
        )

        with pytest.raises(InsufficientMarginError) as exc_info:
            enforcer.validate_limits_strict(
                low_margin_breakdown, sample_pricing_request, PricingTier.STANDARD
            )

        assert exc_info.value.tier == "standard"
        assert exc_info.value.current_margin == Decimal("20.00")

    def test_strict_validation_excessive_discount(self, sample_pricing_request):
        """Test strict validation raises exception for excessive discount."""
        limits = PricingLimits(maximum_total_discount_percentage=0.15)  # 15% max
        enforcer = PricingLimitEnforcer(limits)

        high_discount_breakdown = PriceBreakdown.create(
            base_cost=Decimal("100.00"),
            margin=Decimal("50.00"),
            shipping_cost=Decimal("20.00"),
            volume_discount=Decimal("25.00"),  # ~17% of base+margin
            final_discount=Decimal("10.00"),  # Additional discount exceeds 15%
        )

        with pytest.raises(ExcessiveDiscountError) as exc_info:
            enforcer.validate_limits_strict(
                high_discount_breakdown, sample_pricing_request, PricingTier.STANDARD
            )

        assert exc_info.value.tier == "standard"
        assert exc_info.value.discount_percentage > 0.15


class TestPricingServiceIntegration:
    """Test integration of pricing limits with the pricing service."""

    def test_pricing_service_with_conservative_limits(self):
        """Test pricing service with conservative limits applied."""
        service = PricingService.with_conservative_limits()

        # Create a part specification
        part_spec = PartSpecification(
            material=Material.ALUMINUM,
            process=ManufacturingProcess.CNC,
            dimensions=PartDimensions(length_mm=100, width_mm=50, height_mm=25),
            geometric_complexity_score=3.0,
        )

        # Calculate pricing
        pricing_result = service.calculate_part_pricing(
            part_spec=part_spec,
            part_weight_kg=0.3,
            quantity=100,
            customer_tier="premium",  # Premium tier for additional discounts
        )

        # All prices should be positive and above minimums
        assert pricing_result.expedited.final_price > 0
        assert pricing_result.standard.final_price > 0
        assert pricing_result.economy.final_price > 0
        assert pricing_result.domestic_economy.final_price > 0

        # Per-unit prices should meet minimum ($1.00)
        assert pricing_result.expedited.price_per_unit >= Decimal("1.00")
        assert pricing_result.standard.price_per_unit >= Decimal("1.00")
        assert pricing_result.economy.price_per_unit >= Decimal("1.00")
        assert pricing_result.domestic_economy.price_per_unit >= Decimal("1.00")

    def test_pricing_service_with_limits_info(self):
        """Test pricing service method that returns limit violation information."""
        service = PricingService.with_conservative_limits()

        part_spec = PartSpecification(
            material=Material.ALUMINUM,
            process=ManufacturingProcess.CNC,
            dimensions=PartDimensions(length_mm=50, width_mm=25, height_mm=10),
            geometric_complexity_score=2.0,
        )

        result = service.calculate_part_pricing_with_limits_info(
            part_spec=part_spec,
            part_weight_kg=0.1,
            quantity=1000,
            customer_tier="premium",
        )

        assert "pricing" in result
        assert "limit_violations" in result
        assert "was_adjusted" in result

        # Check that violations are properly formatted
        for tier_name, violations in result["limit_violations"].items():
            assert tier_name in ["expedited", "standard", "economy", "domestic_economy"]
            for violation in violations:
                assert "type" in violation
                assert "message" in violation
                assert "original_value" in violation
                assert "adjusted_value" in violation
                assert "limit_value" in violation

    def test_pricing_service_custom_limits(self):
        """Test pricing service with custom limits."""
        service = PricingService.with_custom_limits(
            min_price_per_unit=Decimal("2.00"),
            min_total_price=Decimal("100.00"),
            min_margin_pct=0.15,  # 15% minimum margin
            max_discount_pct=0.20,  # 20% maximum discount
        )

        part_spec = PartSpecification(
            material=Material.PLASTIC_ABS,
            process=ManufacturingProcess.THREE_D_PRINTING,
            dimensions=PartDimensions(length_mm=30, width_mm=30, height_mm=30),
            geometric_complexity_score=1.5,
        )

        pricing_result = service.calculate_part_pricing(
            part_spec=part_spec,
            part_weight_kg=0.05,
            quantity=50,
        )

        # Custom minimums should be enforced
        assert pricing_result.standard.price_per_unit >= Decimal("2.00")
        assert pricing_result.standard.final_price >= Decimal("100.00")

    def test_pricing_service_without_limits(self):
        """Test pricing service without any limits (baseline)."""
        service = PricingService()  # No limits

        part_spec = PartSpecification(
            material=Material.ALUMINUM,
            process=ManufacturingProcess.CNC,
            dimensions=PartDimensions(length_mm=100, width_mm=50, height_mm=25),
            geometric_complexity_score=3.0,
        )

        # Should calculate normally without any limit adjustments
        pricing_result = service.calculate_part_pricing(
            part_spec=part_spec,
            part_weight_kg=0.3,
            quantity=100,
        )

        # Prices should still be positive (basic business logic)
        assert pricing_result.expedited.final_price > 0
        assert pricing_result.standard.final_price > 0
        assert pricing_result.economy.final_price > 0
        assert pricing_result.domestic_economy.final_price > 0

        # Test limits info method returns no violations
        result = service.calculate_part_pricing_with_limits_info(
            part_spec=part_spec,
            part_weight_kg=0.3,
            quantity=100,
        )

        assert not result["was_adjusted"]
        assert result["limit_violations"] == {}


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
