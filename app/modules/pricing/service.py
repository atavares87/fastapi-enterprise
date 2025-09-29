"""
Pricing Service Layer

Application services for pricing calculation. This layer orchestrates
both cost and pricing domain objects to provide complete pricing solutions.
"""

import time
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from prometheus_client import Counter, Gauge, Histogram

from app.core.telemetry import get_pricing_telemetry
from app.modules.cost.domain import PartSpecification
from app.modules.cost.service import CostCalculationService
from app.modules.pricing.domain import (
    PricingConfiguration,
    PricingEngine,
    PricingRequest,
    PricingTier,
    ShippingCost,
    TierPricing,
)
from app.modules.pricing.explainability import PricingExplainer
from app.modules.pricing.limits import (
    PricingLimitConfigurationFactory,
    PricingLimitEnforcer,
    PricingLimits,
)
from app.modules.pricing.repository import PricingRepository

# Prometheus metrics for pricing operations
pricing_calculations_total = Counter(
    "pricing_calculations_total",
    "Total pricing calculations",
    ["material", "process", "tier", "status"],
)
pricing_calculation_duration = Histogram(
    "pricing_calculation_duration_seconds", "Pricing calculation duration"
)
pricing_final_prices = Histogram(
    "pricing_final_prices_usd", "Final pricing amounts", ["tier"]
)
pricing_margins = Histogram("pricing_margins_usd", "Profit margins", ["tier"])
limit_violations_total = Counter(
    "pricing_limit_violations_total", "Pricing limit violations", ["tier"]
)
active_calculations = Gauge(
    "active_pricing_calculations", "Active pricing calculations"
)


class PricingService:
    """
    Application service for pricing calculations.

    This service coordinates between the cost calculation service
    and the pricing engine to provide complete pricing solutions.
    """

    def __init__(
        self,
        pricing_limits: PricingLimits | None = None,
        repository: PricingRepository | None = None,
        explainer: PricingExplainer | None = None,
    ) -> None:
        """Initialize service with cost service and pricing engine."""
        self.cost_service = CostCalculationService()
        self.repository = repository
        self.explainer = explainer or PricingExplainer()
        self.telemetry = get_pricing_telemetry()

        # Configure pricing limits enforcer if limits are provided
        limits_enforcer = None
        if pricing_limits is not None:
            limits_enforcer = PricingLimitEnforcer(pricing_limits)

        self.pricing_engine = PricingEngine(
            tier_configurations=self._get_default_tier_configurations(),
            tier_shipping_costs=self._get_default_shipping_costs(),
            pricing_limits_enforcer=limits_enforcer,
        )
        self.limits_enforcer = limits_enforcer

    def calculate_part_pricing(
        self,
        part_spec: PartSpecification,
        part_weight_kg: float,
        quantity: int = 1,
        customer_tier: str = "standard",
        shipping_distance_zone: int = 1,
    ) -> TierPricing:
        """
        Calculate pricing for a part across all pricing tiers.

        This is the main use case that combines cost calculation
        with pricing logic to provide complete pricing information.

        Args:
            part_spec: Complete part specification for manufacturing
            part_weight_kg: Weight of the part in kilograms
            quantity: Number of parts to manufacture
            customer_tier: Customer tier for discount calculations
            shipping_distance_zone: Shipping distance (1=local to 4=international)

        Returns:
            Complete pricing breakdown for all tiers

        Raises:
            ValueError: If inputs are invalid or cost calculation fails
        """
        import time

        start_time = time.time()

        try:
            # Track active calculation
            active_calculations.inc()

            # Calculate manufacturing cost
            cost_breakdown = self.cost_service.calculate_manufacturing_cost(part_spec)

            # Create pricing request
            pricing_request = PricingRequest(
                cost_breakdown=cost_breakdown,
                geometric_complexity_score=part_spec.geometric_complexity_score,
                part_weight_kg=part_weight_kg,
                part_volume_cm3=part_spec.dimensions.volume_cm3,
                quantity=quantity,
                customer_tier=customer_tier,
                shipping_distance_zone=shipping_distance_zone,
            )

            # Calculate pricing for all tiers
            tier_pricing = self.pricing_engine.calculate_tier_pricing(pricing_request)

            # Record metrics
            duration = time.time() - start_time
            pricing_calculation_duration.observe(duration)

            # Record pricing metrics for each tier
            tiers = ["standard", "expedited", "economy", "domestic_economy"]
            for tier_name in tiers:
                tier_data = getattr(tier_pricing, tier_name)
                pricing_final_prices.labels(tier=tier_name).observe(
                    float(tier_data.final_price)
                )
                pricing_margins.labels(tier=tier_name).observe(float(tier_data.margin))

            # Record successful calculation
            pricing_calculations_total.labels(
                material=part_spec.material.value,
                process=part_spec.process.value,
                tier=customer_tier,
                status="success",
            ).inc()

            return tier_pricing

        except ValueError as e:
            # Record error metrics
            pricing_calculations_total.labels(
                material=part_spec.material.value,
                process=part_spec.process.value,
                tier=customer_tier,
                status="error",
            ).inc()
            raise ValueError(f"Pricing calculation failed: {str(e)}") from e
        finally:
            # Always decrement active calculations
            active_calculations.dec()

    def estimate_weight_from_material_and_volume(
        self, part_spec: PartSpecification
    ) -> float:
        """
        Estimate part weight based on material and volume.

        This provides a reasonable weight estimate when actual weight
        is not known, using material density data.

        Args:
            part_spec: Part specification including material and dimensions

        Returns:
            Estimated weight in kilograms
        """
        # Material density in kg/cm³ (approximate values)
        material_densities = {
            "aluminum": 0.00270,
            "steel": 0.00785,
            "stainless_steel": 0.00800,
            "plastic_abs": 0.00105,
            "plastic_pla": 0.00124,
            "plastic_petg": 0.00127,
            "titanium": 0.00451,
            "brass": 0.00850,
            "copper": 0.00896,
            "carbon_fiber": 0.00155,
        }

        density = material_densities.get(
            part_spec.material.value, 0.00270
        )  # Default to aluminum
        volume_cm3 = part_spec.dimensions.volume_cm3

        # Add some buffer for features, threads, etc. (typically 10-20% more than solid volume)
        weight_factor = 1.15

        return volume_cm3 * density * weight_factor

    def get_available_pricing_tiers(self) -> list[str]:
        """
        Get list of available pricing tiers.

        Returns:
            List of pricing tier names
        """
        return [tier.value for tier in PricingTier]

    def calculate_part_pricing_with_limits_info(
        self,
        part_spec: PartSpecification,
        part_weight_kg: float,
        quantity: int = 1,
        customer_tier: str = "standard",
        shipping_distance_zone: int = 1,
    ) -> dict[str, Any]:
        """
        Calculate pricing with detailed limit violation information.

        Returns both the pricing result and any limit violations that occurred.

        Args:
            part_spec: Complete part specification for manufacturing
            part_weight_kg: Weight of the part in kilograms
            quantity: Number of parts to manufacture
            customer_tier: Customer tier for discount calculations
            shipping_distance_zone: Shipping distance (1=local to 4=international)

        Returns:
            Dictionary containing pricing results and limit violation details
        """
        if self.limits_enforcer is None:
            # No limits configured, return normal pricing
            pricing = self.calculate_part_pricing(
                part_spec,
                part_weight_kg,
                quantity,
                customer_tier,
                shipping_distance_zone,
            )
            return {"pricing": pricing, "limit_violations": {}, "was_adjusted": False}

        try:
            # Calculate manufacturing cost
            cost_breakdown = self.cost_service.calculate_manufacturing_cost(part_spec)

            # Create pricing request
            pricing_request = PricingRequest(
                cost_breakdown=cost_breakdown,
                geometric_complexity_score=part_spec.geometric_complexity_score,
                part_weight_kg=part_weight_kg,
                part_volume_cm3=part_spec.dimensions.volume_cm3,
                quantity=quantity,
                customer_tier=customer_tier,
                shipping_distance_zone=shipping_distance_zone,
            )

            # Calculate pricing for all tiers and collect violation info
            tier_prices = {}
            tier_violations = {}
            any_adjustments = False

            for tier in PricingTier:
                # Calculate original price for this tier
                config = self.pricing_engine.tier_configurations[tier]
                shipping_cost_calc = self.pricing_engine.tier_shipping_costs[tier]

                # Base cost from manufacturing
                base_cost = (
                    pricing_request.cost_breakdown.total_cost * pricing_request.quantity
                )

                # Calculate components (same logic as in domain)
                margin = base_cost * Decimal(str(config.margin_percentage))

                shipping_cost = shipping_cost_calc.calculate_shipping_cost(
                    weight_kg=pricing_request.part_weight_kg * pricing_request.quantity,
                    volume_cm3=pricing_request.part_volume_cm3
                    * pricing_request.quantity,
                    distance_zone=pricing_request.shipping_distance_zone,
                )

                # Volume discount logic
                discount_rate = Decimal("0")
                for threshold in sorted(
                    config.volume_discount_thresholds.keys(), reverse=True
                ):
                    if pricing_request.quantity >= threshold:
                        discount_rate = Decimal(
                            str(config.volume_discount_thresholds[threshold])
                        )
                        break
                volume_discount = (base_cost + margin) * discount_rate

                # Complexity surcharge
                complexity_surcharge = Decimal("0")
                if (
                    pricing_request.geometric_complexity_score
                    >= config.complexity_surcharge_threshold
                ):
                    surcharge_rate = Decimal(str(config.complexity_surcharge_rate))
                    complexity_surcharge = (base_cost + margin) * surcharge_rate

                # Final discount (basic logic)
                final_discount = Decimal("0")
                if pricing_request.customer_tier == "premium":
                    final_discount += (base_cost + margin) * Decimal("0.05")
                if pricing_request.quantity >= 100:
                    final_discount += (base_cost + margin) * Decimal("0.02")

                from app.modules.pricing.domain import PriceBreakdown

                original_breakdown = PriceBreakdown.create(
                    base_cost=base_cost,
                    margin=margin,
                    shipping_cost=shipping_cost,
                    volume_discount=volume_discount,
                    complexity_surcharge=complexity_surcharge,
                    final_discount=final_discount,
                )

                # Adjust per-unit price
                per_unit_price = (
                    original_breakdown.final_price / pricing_request.quantity
                )
                original_breakdown = PriceBreakdown(
                    base_cost=original_breakdown.base_cost,
                    margin=original_breakdown.margin,
                    shipping_cost=original_breakdown.shipping_cost,
                    volume_discount=original_breakdown.volume_discount,
                    complexity_surcharge=original_breakdown.complexity_surcharge,
                    subtotal=original_breakdown.subtotal,
                    final_discount=original_breakdown.final_discount,
                    final_price=original_breakdown.final_price,
                    price_per_unit=per_unit_price,
                )

                # Apply limits and get violation info
                limited_result = self.limits_enforcer.apply_limits(
                    original_breakdown, pricing_request, tier
                )

                tier_prices[tier.value] = limited_result.price_breakdown
                tier_violations[tier.value] = [
                    {
                        "type": violation.violation_type.value,
                        "message": violation.message,
                        "original_value": float(violation.original_value),
                        "adjusted_value": float(violation.adjusted_value),
                        "limit_value": float(violation.limit_value),
                    }
                    for violation in limited_result.violations
                ]

                if limited_result.was_adjusted:
                    any_adjustments = True

            pricing_result = TierPricing(
                expedited=tier_prices["expedited"],
                standard=tier_prices["standard"],
                economy=tier_prices["economy"],
                domestic_economy=tier_prices["domestic_economy"],
            )

            return {
                "pricing": pricing_result,
                "limit_violations": tier_violations,
                "was_adjusted": any_adjustments,
            }

        except ValueError as e:
            raise ValueError(f"Pricing calculation failed: {str(e)}") from e

    @classmethod
    def with_conservative_limits(cls) -> "PricingService":
        """Create pricing service with conservative limits for business protection."""
        return cls(
            pricing_limits=PricingLimitConfigurationFactory.conservative_limits()
        )

    @classmethod
    def with_aggressive_limits(cls) -> "PricingService":
        """Create pricing service with aggressive limits for competitive pricing."""
        return cls(pricing_limits=PricingLimitConfigurationFactory.aggressive_limits())

    @classmethod
    def with_custom_limits(
        cls,
        min_price_per_unit: Decimal | None = None,
        min_total_price: Decimal | None = None,
        min_margin_pct: float | None = None,
        max_discount_pct: float | None = None,
        min_price_over_cost: float | None = None,
    ) -> "PricingService":
        """Create pricing service with custom limits."""
        limits = PricingLimitConfigurationFactory.custom_limits(
            min_price_per_unit=min_price_per_unit,
            min_total_price=min_total_price,
            min_margin_pct=min_margin_pct,
            max_discount_pct=max_discount_pct,
            min_price_over_cost=min_price_over_cost,
        )
        return cls(pricing_limits=limits)

    async def calculate_part_pricing_with_explanation(
        self,
        part_spec: PartSpecification,
        part_weight_kg: float,
        quantity: int = 1,
        customer_tier: str = "standard",
        shipping_distance_zone: int = 1,
        save_to_db: bool = True,
        user_id: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate pricing with complete explainability and optional database storage.

        This is the comprehensive method that business users should use when they
        need full transparency into pricing calculations.

        Args:
            part_spec: Complete part specification for manufacturing
            part_weight_kg: Weight of the part in kilograms
            quantity: Number of parts to manufacture
            customer_tier: Customer tier for discount calculations
            shipping_distance_zone: Shipping distance (1=local to 4=international)
            save_to_db: Whether to save explanation to database
            user_id: User performing the calculation (for audit)
            ip_address: User's IP address (for audit)

        Returns:
            Dictionary containing pricing, explanation, and metadata
        """
        from time import time
        from uuid import uuid4

        calculation_id = uuid4()
        start_time = time()

        # Set up telemetry context
        if self.telemetry:
            async with self.telemetry.trace_pricing_calculation(
                material=part_spec.material.value,
                process=part_spec.process.value,
                quantity=quantity,
                customer_tier=customer_tier,
            ) as span:
                span.set_attribute("calculation_id", str(calculation_id))
                return await self._perform_pricing_calculation(
                    calculation_id,
                    start_time,
                    part_spec,
                    part_weight_kg,
                    quantity,
                    customer_tier,
                    shipping_distance_zone,
                    save_to_db,
                    user_id,
                    ip_address,
                    span,
                )
        else:
            return await self._perform_pricing_calculation(
                calculation_id,
                start_time,
                part_spec,
                part_weight_kg,
                quantity,
                customer_tier,
                shipping_distance_zone,
                save_to_db,
                user_id,
                ip_address,
            )

    async def _perform_pricing_calculation(
        self,
        calculation_id: UUID,
        start_time: float,
        part_spec: PartSpecification,
        part_weight_kg: float,
        quantity: int,
        customer_tier: str,
        shipping_distance_zone: int,
        save_to_db: bool,
        user_id: str | None,
        ip_address: str | None,
        span: Any = None,
    ) -> dict[str, Any]:
        """Internal method to perform the actual pricing calculation."""
        try:
            # Calculate manufacturing cost
            cost_breakdown = self.cost_service.calculate_manufacturing_cost(part_spec)

            # Create pricing request
            pricing_request = PricingRequest(
                cost_breakdown=cost_breakdown,
                geometric_complexity_score=part_spec.geometric_complexity_score,
                part_weight_kg=part_weight_kg,
                part_volume_cm3=part_spec.dimensions.volume_cm3,
                quantity=quantity,
                customer_tier=customer_tier,
                shipping_distance_zone=shipping_distance_zone,
            )

            # Calculate pricing for all tiers
            tier_pricing = self.pricing_engine.calculate_tier_pricing(pricing_request)

            # Calculate duration
            calculation_duration_ms = int((time.time() - start_time) * 1000)
            calculation_duration_seconds = time.time() - start_time

            # Get limit violations if enforcer is present
            limit_violations = {}
            if self.limits_enforcer:
                for tier in PricingTier:
                    # Get original breakdown to check for violations
                    config = self.pricing_engine.tier_configurations[tier]
                    shipping_cost_calc = self.pricing_engine.tier_shipping_costs[tier]

                    # Calculate original price
                    base_cost = (
                        pricing_request.cost_breakdown.total_cost
                        * pricing_request.quantity
                    )
                    margin = base_cost * Decimal(str(config.margin_percentage))
                    shipping_cost = shipping_cost_calc.calculate_shipping_cost(
                        weight_kg=pricing_request.part_weight_kg
                        * pricing_request.quantity,
                        volume_cm3=pricing_request.part_volume_cm3
                        * pricing_request.quantity,
                        distance_zone=pricing_request.shipping_distance_zone,
                    )

                    # Calculate discounts and surcharges
                    discount_rate = Decimal("0")
                    for threshold in sorted(
                        config.volume_discount_thresholds.keys(), reverse=True
                    ):
                        if pricing_request.quantity >= threshold:
                            discount_rate = Decimal(
                                str(config.volume_discount_thresholds[threshold])
                            )
                            break
                    volume_discount = (base_cost + margin) * discount_rate

                    complexity_surcharge = Decimal("0")
                    if (
                        pricing_request.geometric_complexity_score
                        >= config.complexity_surcharge_threshold
                    ):
                        surcharge_rate = Decimal(str(config.complexity_surcharge_rate))
                        complexity_surcharge = (base_cost + margin) * surcharge_rate

                    final_discount = Decimal("0")
                    if pricing_request.customer_tier == "premium":
                        final_discount += (base_cost + margin) * Decimal("0.05")
                    if pricing_request.quantity >= 100:
                        final_discount += (base_cost + margin) * Decimal("0.02")

                    from app.modules.pricing.domain import PriceBreakdown

                    original_breakdown = PriceBreakdown.create(
                        base_cost=base_cost,
                        margin=margin,
                        shipping_cost=shipping_cost,
                        volume_discount=volume_discount,
                        complexity_surcharge=complexity_surcharge,
                        final_discount=final_discount,
                    )

                    # Apply limits and collect violations
                    limited_result = self.limits_enforcer.apply_limits(
                        original_breakdown, pricing_request, tier
                    )
                    limit_violations[tier.value] = limited_result.violations

            # Create comprehensive explanation
            explanation = self.explainer.create_full_explanation(
                calculation_id=calculation_id,
                part_spec=part_spec,
                pricing_request=pricing_request,
                cost_breakdown=cost_breakdown,
                tier_pricing=tier_pricing,
                tier_configs=self.pricing_engine.tier_configurations,
                shipping_configs=self.pricing_engine.tier_shipping_costs,
                limit_violations=limit_violations,
                calculation_duration_ms=calculation_duration_ms,
            )

            # Record telemetry metrics
            if self.telemetry:
                # Record metrics for each tier
                for tier_name, breakdown in [
                    ("expedited", tier_pricing.expedited),
                    ("standard", tier_pricing.standard),
                    ("economy", tier_pricing.economy),
                    ("domestic_economy", tier_pricing.domestic_economy),
                ]:
                    violations_count = len(limit_violations.get(tier_name, []))
                    self.telemetry.record_pricing_result(
                        duration_seconds=calculation_duration_seconds,
                        final_price=float(breakdown.final_price),
                        margin=float(breakdown.margin),
                        tier=tier_name,
                        limits_applied=explanation.limits_applied,
                        limit_violations=violations_count,
                    )

                # Add span attributes
                if span:
                    span.set_attributes(
                        {
                            "pricing.calculation_duration_ms": calculation_duration_ms,
                            "pricing.limits_applied": explanation.limits_applied,
                            "pricing.best_tier": explanation.best_price_tier,
                            "pricing.total_violations": sum(
                                len(v) for v in limit_violations.values()
                            ),
                        }
                    )

            # Save to database if repository is available and requested
            if save_to_db and self.repository:
                if self.telemetry and span:
                    with self.telemetry.trace_database_operation(
                        "insert", "pricing_explanations"
                    ):
                        await self.repository.save_pricing_explanation(explanation)
                else:
                    await self.repository.save_pricing_explanation(explanation)

                # Log audit event
                if user_id:
                    if self.telemetry and span:
                        with self.telemetry.trace_database_operation(
                            "insert", "pricing_audit_log"
                        ):
                            await self.repository.log_pricing_audit_event(
                                calculation_id=calculation_id,
                                user_id=user_id,
                                action="pricing_calculation",
                                details={
                                    "material": part_spec.material.value,
                                    "process": part_spec.process.value,
                                    "quantity": quantity,
                                    "customer_tier": customer_tier,
                                    "limits_applied": explanation.limits_applied,
                                },
                                ip_address=ip_address,
                            )
                    else:
                        await self.repository.log_pricing_audit_event(
                            calculation_id=calculation_id,
                            user_id=user_id,
                            action="pricing_calculation",
                            details={
                                "material": part_spec.material.value,
                                "process": part_spec.process.value,
                                "quantity": quantity,
                                "customer_tier": customer_tier,
                                "limits_applied": explanation.limits_applied,
                            },
                            ip_address=ip_address,
                        )

            return {
                "calculation_id": str(calculation_id),
                "pricing": tier_pricing,
                "explanation": explanation,
                "metadata": {
                    "calculation_duration_ms": calculation_duration_ms,
                    "limits_applied": explanation.limits_applied,
                    "saved_to_db": save_to_db and self.repository is not None,
                    "timestamp": explanation.timestamp.isoformat(),
                },
            }

        except Exception as e:
            # Log error if repository is available
            if self.repository and user_id:
                await self.repository.log_pricing_audit_event(
                    calculation_id=calculation_id,
                    user_id=user_id,
                    action="pricing_calculation_error",
                    details={
                        "error": str(e),
                        "material": part_spec.material.value,
                        "process": part_spec.process.value,
                        "quantity": quantity,
                    },
                    ip_address=ip_address,
                )
            raise ValueError(f"Pricing calculation failed: {str(e)}") from e

    async def get_pricing_explanation(
        self, calculation_id: str
    ) -> dict[str, Any] | None:
        """
        Retrieve a stored pricing explanation.

        Args:
            calculation_id: Unique calculation identifier

        Returns:
            Pricing explanation or None if not found
        """
        if not self.repository:
            raise ValueError("Repository not configured for explanation retrieval")

        from uuid import UUID

        return await self.repository.get_pricing_explanation(UUID(calculation_id))

    async def search_pricing_history(
        self,
        material: str | None = None,
        process: str | None = None,
        customer_tier: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Search pricing calculation history.

        Args:
            material: Filter by material type
            process: Filter by manufacturing process
            customer_tier: Filter by customer tier
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum number of results

        Returns:
            List of pricing calculations
        """
        if not self.repository:
            raise ValueError("Repository not configured for history search")

        return await self.repository.search_pricing_explanations(
            material=material,
            process=process,
            customer_tier=customer_tier,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    async def get_pricing_analytics(
        self, date_from: datetime, date_to: datetime
    ) -> dict[str, Any]:
        """
        Get pricing analytics for business intelligence.

        Args:
            date_from: Start date
            date_to: End date

        Returns:
            Analytics data
        """
        if not self.repository:
            raise ValueError("Repository not configured for analytics")

        return await self.repository.get_pricing_analytics(date_from, date_to)

    def calculate_cost_only(self, part_spec: PartSpecification) -> Decimal:
        """
        Calculate just the manufacturing cost without pricing.

        Useful for internal cost analysis or when pricing is handled separately.

        Args:
            part_spec: Complete part specification

        Returns:
            Total manufacturing cost
        """
        cost_breakdown = self.cost_service.calculate_manufacturing_cost(part_spec)
        return cost_breakdown.total_cost

    def _get_default_tier_configurations(
        self,
    ) -> dict[PricingTier, PricingConfiguration]:
        """
        Get default pricing configuration for each tier.

        Each tier has different margins, discounts, and surcharges
        to reflect different service levels and customer expectations.

        Returns:
            Dictionary mapping tiers to their pricing configurations
        """
        return {
            PricingTier.EXPEDITED: PricingConfiguration(
                margin_percentage=0.65,  # 65% margin for expedited service
                volume_discount_thresholds={
                    10: 0.02,  # 2% discount for 10+ parts
                    25: 0.04,  # 4% discount for 25+ parts
                    50: 0.06,  # 6% discount for 50+ parts
                    100: 0.08,  # 8% discount for 100+ parts
                },
                complexity_surcharge_threshold=3.5,  # Surcharge for complexity > 3.5
                complexity_surcharge_rate=0.20,  # 20% surcharge for complex parts
            ),
            PricingTier.STANDARD: PricingConfiguration(
                margin_percentage=0.45,  # 45% margin for standard service
                volume_discount_thresholds={
                    10: 0.03,  # 3% discount for 10+ parts
                    25: 0.06,  # 6% discount for 25+ parts
                    50: 0.09,  # 9% discount for 50+ parts
                    100: 0.12,  # 12% discount for 100+ parts
                },
                complexity_surcharge_threshold=4.0,  # More lenient threshold
                complexity_surcharge_rate=0.15,  # 15% surcharge for complex parts
            ),
            PricingTier.ECONOMY: PricingConfiguration(
                margin_percentage=0.30,  # 30% margin for economy service
                volume_discount_thresholds={
                    10: 0.04,  # 4% discount for 10+ parts
                    25: 0.08,  # 8% discount for 25+ parts
                    50: 0.12,  # 12% discount for 50+ parts
                    100: 0.16,  # 16% discount for 100+ parts
                },
                complexity_surcharge_threshold=4.5,  # Even more lenient
                complexity_surcharge_rate=0.10,  # 10% surcharge for complex parts
            ),
            PricingTier.DOMESTIC_ECONOMY: PricingConfiguration(
                margin_percentage=0.25,  # 25% margin for domestic economy
                volume_discount_thresholds={
                    10: 0.05,  # 5% discount for 10+ parts
                    25: 0.10,  # 10% discount for 25+ parts
                    50: 0.15,  # 15% discount for 50+ parts
                    100: 0.20,  # 20% discount for 100+ parts
                },
                complexity_surcharge_threshold=5.0,  # No surcharge unless extremely complex
                complexity_surcharge_rate=0.05,  # 5% surcharge for very complex parts
            ),
        }

    def _get_default_shipping_costs(self) -> dict[PricingTier, ShippingCost]:
        """
        Get default shipping costs for each pricing tier.

        Different tiers have different shipping speeds and costs,
        reflecting the service level and delivery expectations.

        Returns:
            Dictionary mapping tiers to their shipping cost configurations
        """
        return {
            PricingTier.EXPEDITED: ShippingCost(
                base_cost=Decimal("35.00"),  # Higher base cost for expedited
                weight_factor=Decimal("8.50"),  # $8.50 per kg
                volume_factor=Decimal("0.015"),  # $0.015 per cm³ for large items
            ),
            PricingTier.STANDARD: ShippingCost(
                base_cost=Decimal("15.00"),  # Standard base cost
                weight_factor=Decimal("4.25"),  # $4.25 per kg
                volume_factor=Decimal("0.008"),  # $0.008 per cm³ for large items
            ),
            PricingTier.ECONOMY: ShippingCost(
                base_cost=Decimal("8.00"),  # Lower base cost
                weight_factor=Decimal("2.75"),  # $2.75 per kg
                volume_factor=Decimal("0.005"),  # $0.005 per cm³ for large items
            ),
            PricingTier.DOMESTIC_ECONOMY: ShippingCost(
                base_cost=Decimal("5.00"),  # Lowest base cost (domestic only)
                weight_factor=Decimal("1.85"),  # $1.85 per kg
                volume_factor=Decimal("0.003"),  # $0.003 per cm³ for large items
            ),
        }
