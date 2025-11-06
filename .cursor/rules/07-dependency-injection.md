# Dependency Injection

**Location**: `app/config/dependencies.py`

Using `functools.lru_cache` for singleton pattern (analogous to Spring `@Bean`).

## Repository Singletons

```python
from functools import lru_cache

@lru_cache()
def get_cost_repository() -> CostRepository:
    """Get cost repository instance (singleton)."""
    return CostRepository()

@lru_cache()
def get_config_repository() -> ConfigRepository:
    """Get configuration repository instance (singleton)."""
    return ConfigRepository()
```

## Service Singletons

```python
@lru_cache()
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
```

## Using in Controllers

```python
from fastapi import Depends
from app.config.dependencies import get_pricing_service

@router.post("/calculate")
async def calculate_pricing(
    request: PricingRequestDTO,
    pricing_service: PricingService = Depends(get_pricing_service)
):
    return await pricing_service.calculate_pricing(request)
```

## Dependency Graph

```
Controller
    ↓ (depends on)
Service
    ↓ (depends on)
Repositories
    ↓ (depends on)
Domain Models
```

## Rules

- ✅ Use constructor injection for all dependencies
- ✅ All dependencies must be interfaces/abstract classes
- ✅ Singleton scope for repositories and services (via `lru_cache`)
- ✅ Request scope for request-specific data
- ❌ No service locator pattern
- ❌ No global variables
- ❌ No circular dependencies

## Testing with Dependency Injection

```python
# Easy to inject mocks for testing
def test_controller():
    mock_service = Mock(spec=PricingService)
    mock_service.calculate_pricing.return_value = expected_result

    # Inject mock
    result = await calculate_pricing(request, mock_service)

    assert result == expected_result
```
