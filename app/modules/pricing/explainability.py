"""
Pricing Explainability Module

Provides detailed explanations of how pricing calculations are performed,
including step-by-step breakdowns, decision rationales, and audit trails.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.modules.cost.domain import CostBreakdown, PartSpecification
from app.modules.pricing.domain import (
    PriceBreakdown,
    PricingRequest,
    PricingTier,
    TierPricing,
)
from app.modules.pricing.limits import LimitViolation


@dataclass(frozen=True)
class CalculationStep:
    """Individual step in a pricing calculation."""

    step_number: int
    step_name: str
    description: str
    input_values: dict[str, Any]
    calculation_formula: str
    output_value: Decimal
    reasoning: str


@dataclass(frozen=True)
class BusinessRuleApplication:
    """Documentation of a business rule application."""

    rule_name: str
    rule_description: str
    condition: str
    condition_met: bool
    applied_value: Decimal | None
    reasoning: str


@dataclass(frozen=True)
class TierExplanation:
    """Detailed explanation for a specific pricing tier."""

    tier_name: str
    tier_description: str
    margin_percentage: float
    margin_reasoning: str
    shipping_calculation: list[CalculationStep]
    discount_applications: list[BusinessRuleApplication]
    surcharge_applications: list[BusinessRuleApplication]
    limit_adjustments: list[LimitViolation]
    final_calculation_steps: list[CalculationStep]
    price_breakdown: PriceBreakdown


@dataclass(frozen=True)
class PricingExplanation:
    """Complete explanation of a pricing calculation."""

    calculation_id: UUID
    timestamp: datetime
    part_specification: PartSpecification
    pricing_request_params: dict[str, Any]

    # Cost calculation explanation
    cost_calculation_steps: list[CalculationStep]
    cost_breakdown: CostBreakdown

    # Tier-specific explanations
    tier_explanations: dict[str, TierExplanation]

    # Overall summary
    best_price_tier: str
    best_price_reasoning: str

    # Metadata
    calculation_duration_ms: int
    service_version: str
    limits_applied: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "calculation_id": str(self.calculation_id),
            "timestamp": self.timestamp.isoformat(),
            "part_specification": {
                "material": self.part_specification.material.value,
                "process": self.part_specification.process.value,
                "dimensions": {
                    "length_mm": float(self.part_specification.dimensions.length_mm),
                    "width_mm": float(self.part_specification.dimensions.width_mm),
                    "height_mm": float(self.part_specification.dimensions.height_mm),
                    "volume_cm3": float(self.part_specification.dimensions.volume_cm3),
                },
                "geometric_complexity_score": self.part_specification.geometric_complexity_score,
                "quantity": self.pricing_request_params.get("quantity", 1),
                "surface_finish": None,  # Not part of PartSpecification
                "tolerance_class": None,  # Not part of PartSpecification
            },
            "pricing_request_params": self.pricing_request_params,
            "cost_calculation_steps": [
                self._step_to_dict(step) for step in self.cost_calculation_steps
            ],
            "cost_breakdown": {
                "material_cost": float(self.cost_breakdown.material_cost),
                "labor_cost": float(self.cost_breakdown.labor_cost),
                "setup_cost": float(self.cost_breakdown.setup_cost),
                "complexity_adjustment": float(
                    self.cost_breakdown.complexity_adjustment
                ),
                "overhead_cost": float(self.cost_breakdown.overhead_cost),
                "total_cost": float(self.cost_breakdown.total_cost),
            },
            "tier_explanations": {
                tier: self._tier_explanation_to_dict(explanation)
                for tier, explanation in self.tier_explanations.items()
            },
            "best_price_tier": self.best_price_tier,
            "best_price_reasoning": self.best_price_reasoning,
            "calculation_duration_ms": self.calculation_duration_ms,
            "service_version": self.service_version,
            "limits_applied": self.limits_applied,
        }

    def _step_to_dict(self, step: CalculationStep) -> dict[str, Any]:
        """Convert calculation step to dictionary."""
        return {
            "step_number": step.step_number,
            "step_name": step.step_name,
            "description": step.description,
            "input_values": step.input_values,
            "calculation_formula": step.calculation_formula,
            "output_value": float(step.output_value),
            "reasoning": step.reasoning,
        }

    def _tier_explanation_to_dict(self, explanation: TierExplanation) -> dict[str, Any]:
        """Convert tier explanation to dictionary."""
        return {
            "tier_name": explanation.tier_name,
            "tier_description": explanation.tier_description,
            "margin_percentage": explanation.margin_percentage,
            "margin_reasoning": explanation.margin_reasoning,
            "shipping_calculation": [
                self._step_to_dict(step) for step in explanation.shipping_calculation
            ],
            "discount_applications": [
                asdict(rule) for rule in explanation.discount_applications
            ],
            "surcharge_applications": [
                asdict(rule) for rule in explanation.surcharge_applications
            ],
            "limit_adjustments": [
                {
                    "violation_type": violation.violation_type.value,
                    "message": violation.message,
                    "original_value": float(violation.original_value),
                    "adjusted_value": float(violation.adjusted_value),
                    "limit_value": float(violation.limit_value),
                }
                for violation in explanation.limit_adjustments
            ],
            "final_calculation_steps": [
                self._step_to_dict(step) for step in explanation.final_calculation_steps
            ],
            "price_breakdown": {
                "base_cost": float(explanation.price_breakdown.base_cost),
                "margin": float(explanation.price_breakdown.margin),
                "shipping_cost": float(explanation.price_breakdown.shipping_cost),
                "volume_discount": float(explanation.price_breakdown.volume_discount),
                "complexity_surcharge": float(
                    explanation.price_breakdown.complexity_surcharge
                ),
                "subtotal": float(explanation.price_breakdown.subtotal),
                "final_discount": float(explanation.price_breakdown.final_discount),
                "final_price": float(explanation.price_breakdown.final_price),
                "price_per_unit": float(explanation.price_breakdown.price_per_unit),
            },
        }


class PricingExplainer:
    """Service for generating detailed pricing explanations."""

    def __init__(self, service_version: str = "1.0.0"):
        self.service_version = service_version

    def explain_cost_calculation(
        self, part_spec: PartSpecification, cost_breakdown: CostBreakdown
    ) -> list[CalculationStep]:
        """Generate explanation for cost calculation steps."""
        steps = []

        # Material cost step
        volume_cm3 = part_spec.dimensions.volume_cm3
        steps.append(
            CalculationStep(
                step_number=1,
                step_name="Material Cost Calculation",
                description="Calculate raw material cost based on volume and material type",
                input_values={
                    "material": part_spec.material.value,
                    "volume_cm3": float(volume_cm3),
                    "quantity": 1,  # Cost calculation is per-unit
                },
                calculation_formula="volume_cm3 * material_cost_per_cm3 * quantity",
                output_value=cost_breakdown.material_cost,
                reasoning=f"Using {part_spec.material.value} at standard market rates for {volume_cm3:.2f}cm³ per unit",
            )
        )

        # Labor cost step
        steps.append(
            CalculationStep(
                step_number=2,
                step_name="Labor Cost Calculation",
                description="Calculate labor cost based on process and complexity",
                input_values={
                    "process": part_spec.process.value,
                    "complexity_score": part_spec.geometric_complexity_score,
                    "quantity": 1,  # Cost calculation is per-unit
                },
                calculation_formula="base_labor_time * complexity_multiplier * hourly_rate * quantity",
                output_value=cost_breakdown.labor_cost,
                reasoning=f"{part_spec.process.value} process with complexity {part_spec.geometric_complexity_score}/5.0",
            )
        )

        # Setup cost step
        steps.append(
            CalculationStep(
                step_number=3,
                step_name="Setup Cost Calculation",
                description="One-time setup costs for the manufacturing process",
                input_values={
                    "process": part_spec.process.value,
                    "quantity": 1,  # Cost calculation is per-unit
                },
                calculation_formula="process_setup_cost / quantity",
                output_value=cost_breakdown.setup_cost,
                reasoning="Setup costs per unit for the manufacturing process",
            )
        )

        # Overhead cost step
        steps.append(
            CalculationStep(
                step_number=4,
                step_name="Overhead Cost Calculation",
                description="Facility overhead and indirect costs",
                input_values={
                    "material_labor_setup_total": float(
                        cost_breakdown.material_cost
                        + cost_breakdown.labor_cost
                        + cost_breakdown.setup_cost
                    ),
                    "overhead_rate": 0.15,  # Typical 15% overhead
                },
                calculation_formula="(material_cost + labor_cost + setup_cost) * overhead_rate",
                output_value=cost_breakdown.overhead_cost,
                reasoning="Standard 15% overhead applied to direct costs",
            )
        )

        # Tooling cost step
        steps.append(
            CalculationStep(
                step_number=5,
                step_name="Tooling Cost Calculation",
                description="Specialized tooling and equipment costs",
                input_values={
                    "process": part_spec.process.value,
                    "complexity_score": part_spec.geometric_complexity_score,
                    "quantity": 1,  # Cost calculation is per-unit
                },
                calculation_formula="setup_cost_per_unit * complexity_factor * quantity",
                output_value=cost_breakdown.setup_cost,
                reasoning=f"Setup requirements for {part_spec.process.value} with complexity adjustments",
            )
        )

        return steps

    def explain_tier_pricing(
        self,
        tier: PricingTier,
        pricing_request: PricingRequest,
        price_breakdown: PriceBreakdown,
        tier_config: Any,
        shipping_cost_calc: Any,
        limit_violations: list[LimitViolation] | None = None,
    ) -> TierExplanation:
        """Generate detailed explanation for a specific pricing tier."""

        # Tier descriptions
        tier_descriptions = {
            PricingTier.EXPEDITED: "Premium service with fastest delivery and highest priority",
            PricingTier.STANDARD: "Standard service with balanced delivery time and cost",
            PricingTier.ECONOMY: "Economy service with longer delivery for cost savings",
            PricingTier.DOMESTIC_ECONOMY: "Domestic-only economy service with lowest cost",
        }

        # Margin reasoning
        margin_reasoning = f"Applied {tier_config.margin_percentage*100:.1f}% margin for {tier.value} service tier"

        # Shipping calculation steps
        shipping_steps = self._explain_shipping_calculation(
            shipping_cost_calc, pricing_request, price_breakdown.shipping_cost
        )

        # Discount applications
        discount_applications = self._explain_discount_applications(
            tier_config, pricing_request, price_breakdown
        )

        # Surcharge applications
        surcharge_applications = self._explain_surcharge_applications(
            tier_config, pricing_request, price_breakdown
        )

        # Final calculation steps
        final_steps = self._explain_final_calculation(
            price_breakdown, pricing_request.quantity
        )

        return TierExplanation(
            tier_name=tier.value,
            tier_description=tier_descriptions.get(tier, "Standard pricing tier"),
            margin_percentage=tier_config.margin_percentage,
            margin_reasoning=margin_reasoning,
            shipping_calculation=shipping_steps,
            discount_applications=discount_applications,
            surcharge_applications=surcharge_applications,
            limit_adjustments=limit_violations or [],
            final_calculation_steps=final_steps,
            price_breakdown=price_breakdown,
        )

    def _explain_shipping_calculation(
        self, shipping_cost_calc: Any, request: PricingRequest, final_cost: Decimal
    ) -> list[CalculationStep]:
        """Explain shipping cost calculation."""
        steps = []

        total_weight = request.part_weight_kg * request.quantity
        total_volume = request.part_volume_cm3 * request.quantity

        steps.append(
            CalculationStep(
                step_number=1,
                step_name="Weight-Based Shipping",
                description="Calculate shipping cost based on total weight",
                input_values={
                    "weight_per_unit_kg": request.part_weight_kg,
                    "quantity": request.quantity,
                    "weight_factor": float(shipping_cost_calc.weight_factor),
                },
                calculation_formula="total_weight_kg * weight_factor",
                output_value=Decimal(str(total_weight))
                * shipping_cost_calc.weight_factor,
                reasoning=f"Weight-based shipping for {total_weight:.2f}kg total",
            )
        )

        steps.append(
            CalculationStep(
                step_number=2,
                step_name="Volume-Based Shipping",
                description="Calculate shipping cost based on total volume",
                input_values={
                    "volume_per_unit_cm3": request.part_volume_cm3,
                    "quantity": request.quantity,
                    "volume_factor": float(shipping_cost_calc.volume_factor),
                },
                calculation_formula="total_volume_cm3 * volume_factor",
                output_value=Decimal(str(total_volume))
                * shipping_cost_calc.volume_factor,
                reasoning=f"Volume-based shipping for {total_volume:.2f}cm³ total",
            )
        )

        steps.append(
            CalculationStep(
                step_number=3,
                step_name="Final Shipping Cost",
                description="Use higher of weight-based or volume-based shipping plus base cost",
                input_values={
                    "base_cost": float(shipping_cost_calc.base_cost),
                    "distance_zone": request.shipping_distance_zone,
                },
                calculation_formula="base_cost + max(weight_cost, volume_cost) * distance_multiplier",
                output_value=final_cost,
                reasoning=f"Applied distance zone {request.shipping_distance_zone} multiplier",
            )
        )

        return steps

    def _explain_discount_applications(
        self, tier_config: Any, request: PricingRequest, breakdown: PriceBreakdown
    ) -> list[BusinessRuleApplication]:
        """Explain discount rule applications."""
        applications = []

        # Volume discount
        volume_discount_rate = Decimal("0")
        for threshold in sorted(
            tier_config.volume_discount_thresholds.keys(), reverse=True
        ):
            if request.quantity >= threshold:
                volume_discount_rate = Decimal(
                    str(tier_config.volume_discount_thresholds[threshold])
                )
                break

        applications.append(
            BusinessRuleApplication(
                rule_name="Volume Discount",
                rule_description="Discount based on order quantity",
                condition=f"quantity >= {list(tier_config.volume_discount_thresholds.keys())[-1] if volume_discount_rate > 0 else 'N/A'}",
                condition_met=volume_discount_rate > 0,
                applied_value=breakdown.volume_discount,
                reasoning=f"Applied {float(volume_discount_rate)*100:.1f}% volume discount for {request.quantity} units",
            )
        )

        # Customer tier discount
        customer_discount_applied = breakdown.final_discount > 0
        applications.append(
            BusinessRuleApplication(
                rule_name="Customer Tier Discount",
                rule_description="Additional discount based on customer tier",
                condition=f"customer_tier == '{request.customer_tier}'",
                condition_met=customer_discount_applied,
                applied_value=breakdown.final_discount,
                reasoning=f"Customer tier '{request.customer_tier}' discount applied",
            )
        )

        return applications

    def _explain_surcharge_applications(
        self, tier_config: Any, request: PricingRequest, breakdown: PriceBreakdown
    ) -> list[BusinessRuleApplication]:
        """Explain surcharge rule applications."""
        applications = []

        # Complexity surcharge
        complexity_applied = (
            request.geometric_complexity_score
            >= tier_config.complexity_surcharge_threshold
            and breakdown.complexity_surcharge > 0
        )

        applications.append(
            BusinessRuleApplication(
                rule_name="Complexity Surcharge",
                rule_description="Additional charge for complex geometries",
                condition=f"complexity_score >= {tier_config.complexity_surcharge_threshold}",
                condition_met=complexity_applied,
                applied_value=(
                    breakdown.complexity_surcharge if complexity_applied else None
                ),
                reasoning=f"Complexity score {request.geometric_complexity_score}/5.0 {'exceeds' if complexity_applied else 'below'} threshold",
            )
        )

        return applications

    def _explain_final_calculation(
        self, breakdown: PriceBreakdown, quantity: int
    ) -> list[CalculationStep]:
        """Explain final price calculation steps."""
        steps = []

        steps.append(
            CalculationStep(
                step_number=1,
                step_name="Subtotal Calculation",
                description="Calculate subtotal before final adjustments",
                input_values={
                    "base_cost": float(breakdown.base_cost),
                    "margin": float(breakdown.margin),
                    "shipping_cost": float(breakdown.shipping_cost),
                    "complexity_surcharge": float(breakdown.complexity_surcharge),
                    "volume_discount": float(breakdown.volume_discount),
                },
                calculation_formula="base_cost + margin + shipping_cost + complexity_surcharge - volume_discount",
                output_value=breakdown.subtotal,
                reasoning="Sum all costs and apply volume discount",
            )
        )

        steps.append(
            CalculationStep(
                step_number=2,
                step_name="Final Price Calculation",
                description="Apply final discounts to get total price",
                input_values={
                    "subtotal": float(breakdown.subtotal),
                    "final_discount": float(breakdown.final_discount),
                },
                calculation_formula="subtotal - final_discount",
                output_value=breakdown.final_price,
                reasoning="Apply customer and promotional discounts",
            )
        )

        steps.append(
            CalculationStep(
                step_number=3,
                step_name="Per-Unit Price Calculation",
                description="Calculate price per individual unit",
                input_values={
                    "final_price": float(breakdown.final_price),
                    "quantity": quantity,
                },
                calculation_formula="final_price / quantity",
                output_value=breakdown.price_per_unit,
                reasoning=f"Divide total price by {quantity} units",
            )
        )

        return steps

    def create_full_explanation(
        self,
        calculation_id: UUID,
        part_spec: PartSpecification,
        pricing_request: PricingRequest,
        cost_breakdown: CostBreakdown,
        tier_pricing: TierPricing,
        tier_configs: dict[PricingTier, Any],
        shipping_configs: dict[PricingTier, Any],
        limit_violations: dict[str, list[LimitViolation]] | None = None,
        calculation_duration_ms: int = 0,
    ) -> PricingExplanation:
        """Create a complete pricing explanation."""

        # Generate cost calculation explanation
        cost_steps = self.explain_cost_calculation(part_spec, cost_breakdown)

        # Generate tier explanations
        tier_explanations = {}

        tiers_and_breakdowns = [
            (PricingTier.EXPEDITED, tier_pricing.expedited),
            (PricingTier.STANDARD, tier_pricing.standard),
            (PricingTier.ECONOMY, tier_pricing.economy),
            (PricingTier.DOMESTIC_ECONOMY, tier_pricing.domestic_economy),
        ]

        for tier, breakdown in tiers_and_breakdowns:
            tier_violations = (
                limit_violations.get(tier.value, []) if limit_violations else []
            )

            explanation = self.explain_tier_pricing(
                tier=tier,
                pricing_request=pricing_request,
                price_breakdown=breakdown,
                tier_config=tier_configs[tier],
                shipping_cost_calc=shipping_configs[tier],
                limit_violations=tier_violations,
            )

            tier_explanations[tier.value] = explanation

        # Determine best price tier
        best_tier = min(tiers_and_breakdowns, key=lambda x: x[1].final_price)[0].value

        best_price_reasoning = f"Tier '{best_tier}' offers the lowest total price of ${tier_explanations[best_tier].price_breakdown.final_price}"

        return PricingExplanation(
            calculation_id=calculation_id,
            timestamp=datetime.utcnow(),
            part_specification=part_spec,
            pricing_request_params={
                "part_weight_kg": pricing_request.part_weight_kg,
                "part_volume_cm3": pricing_request.part_volume_cm3,
                "quantity": pricing_request.quantity,
                "customer_tier": pricing_request.customer_tier,
                "shipping_distance_zone": pricing_request.shipping_distance_zone,
            },
            cost_calculation_steps=cost_steps,
            cost_breakdown=cost_breakdown,
            tier_explanations=tier_explanations,
            best_price_tier=best_tier,
            best_price_reasoning=best_price_reasoning,
            calculation_duration_ms=calculation_duration_ms,
            service_version=self.service_version,
            limits_applied=bool(limit_violations and any(limit_violations.values())),
        )
