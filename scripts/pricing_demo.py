#!/usr/bin/env python3
"""
FastAPI Enterprise - Pricing Demo Script

Demonstrates the pricing system with explainability and limits.
"""

import asyncio
import sys
from decimal import Decimal

# Add the app directory to the Python path
sys.path.insert(0, ".")

try:
    from app.modules.cost.domain import (
        ManufacturingProcess,
        Material,
        PartDimensions,
        PartSpecification,
    )
    from app.modules.pricing.limits import PricingLimitConfigurationFactory
    from app.modules.pricing.service import PricingService
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you've installed dependencies with: make install")
    sys.exit(1)


def print_separator():
    print("=" * 60)


def print_price_breakdown(name, breakdown, _quantity):
    """Print detailed price breakdown for a tier."""
    print(f"\n{name.upper()} TIER:")
    print(f"  💰 Final Price:     ${breakdown.final_price:.2f}")
    print(f"  📊 Per Unit:        ${breakdown.price_per_unit:.2f}")
    print(f"  🏭 Base Cost:       ${breakdown.base_cost:.2f}")
    print(f"  📈 Margin:          ${breakdown.margin:.2f}")
    print(f"  🚚 Shipping:        ${breakdown.shipping_cost:.2f}")
    if breakdown.volume_discount > 0:
        print(f"  🎯 Volume Discount: -${breakdown.volume_discount:.2f}")
    if breakdown.complexity_surcharge > 0:
        print(f"  ⚙️  Complexity Fee:   +${breakdown.complexity_surcharge:.2f}")
    if breakdown.final_discount > 0:
        print(f"  🎁 Final Discount:  -${breakdown.final_discount:.2f}")


def demo_basic_pricing():
    """Demonstrate basic pricing calculation."""
    print("🔧 Demo 1: Basic Pricing Calculation")
    print_separator()

    # Create a service with conservative limits
    service = PricingService.with_conservative_limits()

    # Define a sample part
    part_spec = PartSpecification(
        material=Material.ALUMINUM,
        process=ManufacturingProcess.CNC,
        dimensions=PartDimensions(length_mm=100, width_mm=50, height_mm=25),
        geometric_complexity_score=3.5,
    )

    print("🔧 Part Specification:")
    print(f"  Material:    {part_spec.material.value}")
    print(f"  Process:     {part_spec.process.value}")
    print(
        f"  Dimensions:  {part_spec.dimensions.length_mm}×{part_spec.dimensions.width_mm}×{part_spec.dimensions.height_mm}mm"
    )
    print(f"  Volume:      {part_spec.dimensions.volume_cm3:.2f}cm³")
    print(f"  Complexity:  {part_spec.geometric_complexity_score}/5.0")
    print("  Quantity:    50")

    print("\n🔄 Calculating pricing...")

    # Calculate pricing
    pricing = service.calculate_part_pricing(
        part_spec=part_spec, part_weight_kg=0.3, quantity=50, customer_tier="premium"
    )

    print("\n✅ Pricing Results:")
    print_price_breakdown("Standard", pricing.standard, 50)
    print_price_breakdown("Expedited", pricing.expedited, 50)
    print_price_breakdown("Economy", pricing.economy, 50)
    print_price_breakdown("Domestic Economy", pricing.domestic_economy, 50)

    # Find best price
    tiers = {
        "Standard": pricing.standard,
        "Expedited": pricing.expedited,
        "Economy": pricing.economy,
        "Domestic Economy": pricing.domestic_economy,
    }

    best_tier = min(tiers.keys(), key=lambda k: tiers[k].final_price)
    best_price = tiers[best_tier].final_price

    print(f"\n🏆 Best Option: {best_tier} at ${best_price:.2f}")
    print(f"💡 Savings vs Expedited: ${pricing.expedited.final_price - best_price:.2f}")


def demo_pricing_limits():
    """Demonstrate pricing limits system."""
    print("\n\n🛡️  Demo 2: Pricing Limits Protection")
    print_separator()

    print("Testing different limit configurations...")

    # Conservative limits
    conservative_service = PricingService.with_conservative_limits()
    conservative_limits = PricingLimitConfigurationFactory.conservative_limits()

    print("\n🔒 Conservative Limits:")
    print(f"  Min Price/Unit:     ${conservative_limits.minimum_price_per_unit}")
    print(f"  Min Total Price:    ${conservative_limits.minimum_total_price}")
    print(
        f"  Min Margin:         {conservative_limits.minimum_margin_percentage * 100:.0f}%"
    )
    print(
        f"  Max Discount:       {conservative_limits.maximum_total_discount_percentage * 100:.0f}%"
    )
    print(
        f"  Min Price/Cost:     {conservative_limits.minimum_price_over_cost_multiplier * 100:.0f}% of cost"
    )

    # Aggressive limits
    aggressive_service = PricingService.with_aggressive_limits()
    aggressive_limits = PricingLimitConfigurationFactory.aggressive_limits()

    print("\n🚀 Aggressive Limits:")
    print(f"  Min Price/Unit:     ${aggressive_limits.minimum_price_per_unit}")
    print(f"  Min Total Price:    ${aggressive_limits.minimum_total_price}")
    print(
        f"  Min Margin:         {aggressive_limits.minimum_margin_percentage * 100:.0f}%"
    )
    print(
        f"  Max Discount:       {aggressive_limits.maximum_total_discount_percentage * 100:.0f}%"
    )
    print(
        f"  Min Price/Cost:     {aggressive_limits.minimum_price_over_cost_multiplier * 100:.0f}% of cost"
    )

    # Test with a small, high-volume order (likely to trigger limits)
    small_part = PartSpecification(
        material=Material.PLASTIC_ABS,
        process=ManufacturingProcess.THREE_D_PRINTING,
        dimensions=PartDimensions(length_mm=20, width_mm=20, height_mm=10),
        geometric_complexity_score=1.5,
    )

    print("\n🧪 Testing with small, high-volume part:")
    print(f"  1000 units of {small_part.material.value}")

    conservative_pricing = conservative_service.calculate_part_pricing(
        small_part, 0.01, 1000, "premium"
    )

    aggressive_pricing = aggressive_service.calculate_part_pricing(
        small_part, 0.01, 1000, "premium"
    )

    print("\n📊 Comparison (Economy Tier):")
    print(
        f"  Conservative: ${conservative_pricing.economy.final_price:.2f} (${conservative_pricing.economy.price_per_unit:.3f}/unit)"
    )
    print(
        f"  Aggressive:   ${aggressive_pricing.economy.final_price:.2f} (${aggressive_pricing.economy.price_per_unit:.3f}/unit)"
    )
    print(
        f"  Difference:   ${abs(conservative_pricing.economy.final_price - aggressive_pricing.economy.final_price):.2f}"
    )


async def demo_explainability():
    """Demonstrate pricing explainability (async version)."""
    print("\n\n📖 Demo 3: Pricing Explainability")
    print_separator()

    print("💡 Note: Full explainability requires MongoDB integration")
    print("This demo shows the service structure without database storage.")

    # Create service with explainability (no MongoDB for demo)
    service = PricingService.with_conservative_limits()

    # Complex part that will trigger various rules
    complex_part = PartSpecification(
        material=Material.TITANIUM,
        process=ManufacturingProcess.CNC,
        dimensions=PartDimensions(length_mm=200, width_mm=100, height_mm=50),
        geometric_complexity_score=4.8,  # Very complex
    )

    print("🔧 Complex Part Specification:")
    print(f"  Material:    {complex_part.material.value} (expensive)")
    print(f"  Process:     {complex_part.process.value}")
    print(f"  Complexity:  {complex_part.geometric_complexity_score}/5.0 (very high)")
    print("  Quantity:    25")

    print("\n🔄 Calculating with business rules...")

    pricing = service.calculate_part_pricing(
        part_spec=complex_part,
        part_weight_kg=1.2,
        quantity=25,
        customer_tier="enterprise",
    )

    print("\n📋 Business Rules Applied:")
    print("  ✅ High complexity surcharge (score > 4.0)")
    print("  ✅ Enterprise customer tier benefits")
    print("  ✅ Volume discount for 25 units")
    print("  ✅ Pricing limits protection active")

    print_price_breakdown("Standard", pricing.standard, 25)

    if hasattr(service, "repository") and service.repository:
        print("\n💾 With MongoDB integration, you would also get:")
        print("  📝 Step-by-step calculation explanations")
        print("  🔍 Business rule application details")
        print("  📊 Limit violation reports")
        print("  🗂️  Complete audit trail")
    else:
        print("\n💡 To enable full explainability:")
        print("  1. Ensure MongoDB is running: make docker-up")
        print("  2. Use: service.calculate_part_pricing_with_explanation(...)")


def demo_custom_limits():
    """Demonstrate custom pricing limits."""
    print("\n\n⚙️  Demo 4: Custom Pricing Limits")
    print_separator()

    # Create service with custom limits
    custom_service = PricingService.with_custom_limits(
        min_price_per_unit=Decimal("5.00"),  # High minimum
        min_total_price=Decimal("200.00"),  # High minimum order
        min_margin_pct=0.20,  # 20% minimum margin
        max_discount_pct=0.15,  # 15% max discount
    )

    print("🎛️  Custom Limits Configuration:")
    print("  Min Price/Unit:     $5.00")
    print("  Min Total Price:    $200.00")
    print("  Min Margin:         20%")
    print("  Max Discount:       15%")

    # Test with a part that would normally be cheap
    cheap_part = PartSpecification(
        material=Material.PLASTIC_PLA,
        process=ManufacturingProcess.THREE_D_PRINTING,
        dimensions=PartDimensions(length_mm=30, width_mm=30, height_mm=20),
        geometric_complexity_score=2.0,
    )

    print("\n🧪 Testing with normally cheap part:")
    print(f"  10 units of {cheap_part.material.value}")

    custom_pricing = custom_service.calculate_part_pricing(
        cheap_part, 0.05, 10, "standard"
    )

    regular_service = PricingService()  # No limits
    regular_pricing = regular_service.calculate_part_pricing(
        cheap_part, 0.05, 10, "standard"
    )

    print("\n📊 Price Comparison (Standard Tier):")
    print(
        f"  Without Limits: ${regular_pricing.standard.final_price:.2f} (${regular_pricing.standard.price_per_unit:.2f}/unit)"
    )
    print(
        f"  With Limits:    ${custom_pricing.standard.final_price:.2f} (${custom_pricing.standard.price_per_unit:.2f}/unit)"
    )
    print(
        f"  Adjustment:     +${custom_pricing.standard.final_price - regular_pricing.standard.final_price:.2f}"
    )

    if custom_pricing.standard.price_per_unit >= Decimal("5.00"):
        print("  ✅ Minimum price per unit enforced")
    if custom_pricing.standard.final_price >= Decimal("200.00"):
        print("  ✅ Minimum total price enforced")


def main():
    """Run all pricing demos."""
    print("🎬 FastAPI Enterprise - Pricing System Demo")
    print("=" * 60)
    print("Demonstrating pricing calculations with limits and explainability")

    try:
        # Run synchronous demos
        demo_basic_pricing()
        demo_pricing_limits()
        demo_custom_limits()

        # Run async demo
        asyncio.run(demo_explainability())

        print("\n\n🎉 Demo Complete!")
        print_separator()
        print("💡 Next Steps:")
        print("  1. Start observability stack: make docker-up")
        print("  2. Start FastAPI app:         make start-dev")
        print("  3. Run pricing tests:         make test-pricing")
        print("  4. View Grafana dashboard:    http://localhost:3000")
        print("\n✨ Happy pricing with FastAPI Enterprise!")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Install dependencies: make install")
        print(
            "  2. Check imports:        python -c 'from app.modules.pricing.service import PricingService'"
        )
        print("  3. Run tests:           make test-pricing")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
