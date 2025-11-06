# Controller Layer

**Location**: `app/controller/`

**Responsibility**: Handle HTTP requests and responses

**Analogous to**: Spring `@RestController`

## Rules

- Route HTTP requests to service methods
- Validate requests (Pydantic does this automatically)
- Convert DTOs to/from HTTP
- Handle HTTP-specific concerns (status codes, headers)
- **NO business logic**

## Example

```python
@router.post("/calculate", response_model=PricingResponseDTO)
async def calculate_pricing(
    request: PricingRequestDTO,
    pricing_service: PricingService = Depends(get_pricing_service)
) -> PricingResponseDTO:
    """Delegate to service layer for business logic."""
    return await pricing_service.calculate_pricing(request)
```

## Anti-Patterns to Avoid

- ❌ Business logic in controllers
- ❌ Direct repository calls (must go through service)
- ❌ Database queries in controllers
- ❌ Complex data transformations (use DTOs)

## Best Practices

- ✅ Keep controllers thin (< 50 lines per endpoint)
- ✅ Use dependency injection for services
- ✅ Handle exceptions appropriately (convert to HTTP errors)
- ✅ Return proper HTTP status codes
- ✅ Document endpoints with OpenAPI descriptions
