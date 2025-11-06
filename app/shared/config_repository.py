"""
Configuration Repository - Data access for pricing configurations

Analogous to Spring @Repository - handles all configuration data access.
"""

from decimal import Decimal

from app.pricing.models import PricingConfiguration, ShippingCost
from app.shared.enums import PricingTier


class ConfigRepository:
    """
    Repository for configuration data access.

    In Spring Boot, this would be annotated with @Repository.
    Provides pricing configurations and shipping costs.
    """

    async def get_tier_configurations(
        self,
    ) -> dict[PricingTier, PricingConfiguration]:
        """
        Fetch pricing configurations for all tiers.

        In production, this would:
        - Query database
        - Load from configuration service
        - Read from cache (Redis)
        """
        return self._get_default_tier_configurations()

    async def get_shipping_costs(self) -> dict[PricingTier, ShippingCost]:
        """
        Fetch shipping costs for all tiers.

        In production, this would:
        - Query database
        - Load from configuration service
        - Read from cache
        """
        return self._get_default_shipping_costs()

    def _get_default_tier_configurations(
        self,
    ) -> dict[PricingTier, PricingConfiguration]:
        """Get default pricing configuration for each tier (in-memory)."""
        return {
            PricingTier.EXPEDITED: PricingConfiguration(
                margin_percentage=0.65,
                volume_discount_thresholds={
                    10: 0.02,
                    25: 0.04,
                    50: 0.06,
                    100: 0.08,
                },
                complexity_surcharge_threshold=3.5,
                complexity_surcharge_rate=0.20,
            ),
            PricingTier.STANDARD: PricingConfiguration(
                margin_percentage=0.45,
                volume_discount_thresholds={
                    10: 0.03,
                    25: 0.06,
                    50: 0.09,
                    100: 0.12,
                },
                complexity_surcharge_threshold=4.0,
                complexity_surcharge_rate=0.15,
            ),
            PricingTier.ECONOMY: PricingConfiguration(
                margin_percentage=0.30,
                volume_discount_thresholds={
                    10: 0.04,
                    25: 0.08,
                    50: 0.12,
                    100: 0.16,
                },
                complexity_surcharge_threshold=4.5,
                complexity_surcharge_rate=0.10,
            ),
            PricingTier.DOMESTIC_ECONOMY: PricingConfiguration(
                margin_percentage=0.25,
                volume_discount_thresholds={
                    10: 0.05,
                    25: 0.10,
                    50: 0.15,
                    100: 0.20,
                },
                complexity_surcharge_threshold=5.0,
                complexity_surcharge_rate=0.05,
            ),
        }

    def _get_default_shipping_costs(self) -> dict[PricingTier, ShippingCost]:
        """Get default shipping costs for each tier (in-memory)."""
        return {
            PricingTier.EXPEDITED: ShippingCost(
                base_cost=Decimal("35.00"),
                weight_factor=Decimal("8.50"),
                volume_factor=Decimal("0.015"),
            ),
            PricingTier.STANDARD: ShippingCost(
                base_cost=Decimal("15.00"),
                weight_factor=Decimal("4.25"),
                volume_factor=Decimal("0.008"),
            ),
            PricingTier.ECONOMY: ShippingCost(
                base_cost=Decimal("8.00"),
                weight_factor=Decimal("2.75"),
                volume_factor=Decimal("0.005"),
            ),
            PricingTier.DOMESTIC_ECONOMY: ShippingCost(
                base_cost=Decimal("5.00"),
                weight_factor=Decimal("1.85"),
                volume_factor=Decimal("0.003"),
            ),
        }
