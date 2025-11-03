"""Price Breakdown Model - Single Responsibility: Price breakdown calculation and structure."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PriceBreakdown:
    """Detailed breakdown of final pricing including all components."""

    base_cost: Decimal
    margin: Decimal
    shipping_cost: Decimal
    volume_discount: Decimal
    complexity_surcharge: Decimal
    subtotal: Decimal
    final_discount: Decimal
    final_price: Decimal
    price_per_unit: Decimal

    @classmethod
    def create(
        cls,
        base_cost: Decimal,
        margin: Decimal,
        shipping_cost: Decimal,
        volume_discount: Decimal = Decimal("0"),
        complexity_surcharge: Decimal = Decimal("0"),
        final_discount: Decimal = Decimal("0"),
    ) -> "PriceBreakdown":
        """Create price breakdown with calculated totals."""
        subtotal = (
            base_cost + margin + shipping_cost + complexity_surcharge - volume_discount
        )
        final_price = subtotal - final_discount

        return cls(
            base_cost=base_cost,
            margin=margin,
            shipping_cost=shipping_cost,
            volume_discount=volume_discount,
            complexity_surcharge=complexity_surcharge,
            subtotal=subtotal,
            final_discount=final_discount,
            final_price=final_price,
            price_per_unit=final_price,
        )
