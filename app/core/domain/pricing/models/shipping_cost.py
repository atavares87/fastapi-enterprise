"""Shipping Cost Model - Single Responsibility: Shipping cost calculations."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ShippingCost:
    """Shipping cost calculation based on part characteristics."""

    base_cost: Decimal
    weight_factor: Decimal
    volume_factor: Decimal
    distance_multiplier: float = 1.0

    def calculate_shipping_cost(
        self,
        weight_kg: float,
        volume_cm3: float,
        distance_zone: int = 1,
    ) -> Decimal:
        """
        Pure function: Calculate shipping cost based on weight, volume, and distance.

        Args:
            weight_kg: Weight of the part in kilograms
            volume_cm3: Volume of the part in cubic centimeters
            distance_zone: Shipping distance zone (1-4)

        Returns:
            Total shipping cost
        """
        weight_cost = Decimal(str(weight_kg)) * self.weight_factor
        volume_cost = Decimal(str(volume_cm3)) * self.volume_factor

        shipping_cost = self.base_cost + max(weight_cost, volume_cost)

        distance_multipliers = {1: 1.0, 2: 1.3, 3: 1.8, 4: 2.5}
        multiplier = distance_multipliers.get(distance_zone, 1.0)

        return shipping_cost * Decimal(str(multiplier))
