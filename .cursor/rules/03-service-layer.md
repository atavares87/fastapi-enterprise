# Service Layer

**Location**: `app/service/`

**Responsibility**: Business logic orchestration

**Analogous to**: Spring `@Service`

## Rules

- Orchestrate business workflows
- Coordinate between repositories
- Call domain core functions for calculations
- Handle business rules and validation
- **NO HTTP concerns**
- **NO database implementation details**

## Example

```python
class PricingService:
    def __init__(
        self,
        cost_repository: CostRepository,
        config_repository: ConfigRepository,
        pricing_repository: PricingRepository,
        metrics_repository: MetricsRepository,
    ):
        self.cost_repository = cost_repository
        # ... other repositories

    async def calculate_pricing(self, request: PricingRequestDTO):
        # 1. Fetch data from repositories
        material_costs = await self.cost_repository.get_material_costs()

        # 2. Call domain core (pure functions)
        tier_pricing = calculate_tier_pricing(...)

        # 3. Persist results
        await self.pricing_repository.save(tier_pricing)

        return response_dto
```

## Service Method Pattern

1. **Validate inputs** (business validation, not HTTP)
2. **Fetch data** from repositories
3. **Execute business logic** via domain core
4. **Persist results** via repositories
5. **Record metrics** via metrics repository
6. **Return result** (DTO or domain model)

## Anti-Patterns to Avoid

- ❌ HTTP status codes or headers in services
- ❌ Direct database queries (use repositories)
- ❌ Request/Response objects from FastAPI
- ❌ Logging business logic (use structured logging for orchestration only)

## Best Practices

- ✅ Constructor injection for all dependencies
- ✅ Use async/await for I/O operations
- ✅ Keep business logic in domain core (pure functions)
- ✅ Transaction boundaries at service level
- ✅ Clear method names describing business operations
