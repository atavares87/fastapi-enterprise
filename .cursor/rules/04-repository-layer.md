# Repository Layer

**Location**: `app/repository/`

**Responsibility**: Data access and persistence

**Analogous to**: Spring `@Repository`

## Rules

- Abstract database access
- Execute database queries
- Map database results to domain models
- Handle database transactions
- Cache management
- **NO business logic**

## Example

```python
class CostRepository:
    async def get_material_costs(self) -> dict[Material, MaterialCost]:
        """Fetch material costs from database."""
        # Database access here
        return await self._fetch_from_database()
```

## Repository Method Patterns

### Query Methods
- `get_*()` - Fetch single entity, raise if not found
- `find_*()` - Fetch single entity, return None if not found
- `list_*()` - Fetch multiple entities
- `search_*()` - Search with filters

### Mutation Methods
- `save()` - Insert or update
- `create()` - Insert only
- `update()` - Update only
- `delete()` - Remove entity

## Anti-Patterns to Avoid

- ❌ Business logic in repositories
- ❌ Business validation in repositories
- ❌ Complex calculations in repositories
- ❌ Calling other services from repositories

## Best Practices

- ✅ Return domain models, not database entities
- ✅ Use async/await for database operations
- ✅ Handle connection pooling at infrastructure level
- ✅ Use transactions for related operations
- ✅ Cache frequently accessed data
- ✅ Log database errors appropriately
