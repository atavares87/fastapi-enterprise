"""
Dependency Injection Configuration

Analogous to Spring @Configuration and @Bean methods.
Provides dependency injection for services and repositories.
"""

from functools import lru_cache

from app.cost.repository import CostRepository
from app.pricing.repository import PricingRepository
from app.pricing.service import PricingService
from app.shared.config_repository import ConfigRepository
from app.shared.metrics_repository import MetricsRepository


# Repository singletons (analogous to Spring @Bean with singleton scope)
@lru_cache
def get_cost_repository() -> CostRepository:
    """Get cost repository instance (singleton)."""
    return CostRepository()


@lru_cache
def get_config_repository() -> ConfigRepository:
    """Get configuration repository instance (singleton)."""
    return ConfigRepository()


@lru_cache
def get_pricing_repository() -> PricingRepository:
    """Get pricing repository instance (singleton)."""
    return PricingRepository()


@lru_cache
def get_metrics_repository() -> MetricsRepository:
    """Get metrics repository instance (singleton)."""
    return MetricsRepository()


# Service singletons (analogous to Spring @Bean with singleton scope)
@lru_cache
def get_pricing_service() -> PricingService:
    """
    Get pricing service instance (singleton).

    In Spring Boot, this would be:
    @Bean
    public PricingService pricingService(
        CostRepository costRepository,
        ConfigRepository configRepository,
        PricingRepository pricingRepository,
        MetricsRepository metricsRepository
    ) {
        return new PricingService(
            costRepository,
            configRepository,
            pricingRepository,
            metricsRepository
        );
    }
    """
    return PricingService(
        cost_repository=get_cost_repository(),
        config_repository=get_config_repository(),
        pricing_repository=get_pricing_repository(),
        metrics_repository=get_metrics_repository(),
    )
