# Testing Strategy

## Test Pyramid

```
       /\
      /  \      Integration Tests (API tests)
     /____\
    /      \    Service Tests (mock repositories)
   /________\
  /          \  Domain Core Tests (pure functions, no mocks!)
 /__________/
```

## Domain Core Tests

**Location**: `tests/unit/domains/`

**NO mocks needed!** Pure functions are easy to test.

```python
def test_calculate_complexity_surcharge():
    result = calculate_complexity_surcharge(
        Decimal("100"), 4.0, PricingConfiguration(...)
    )
    assert result == Decimal("20.00")
```

### Benefits
- ✅ Fast (no I/O)
- ✅ Simple (no setup)
- ✅ Reliable (deterministic)
- ✅ Easy to debug

## Service Tests

**Location**: `tests/unit/`

Mock repositories, use real domain logic.

```python
async def test_pricing_service():
    # Arrange
    mock_repo = Mock(spec=CostRepository)
    mock_repo.get_material_costs.return_value = {...}

    service = PricingService(mock_repo, ...)
    request_dto = PricingRequestDTO(...)

    # Act
    result = await service.calculate_pricing(request_dto)

    # Assert
    assert result.pricing_tiers.standard.final_price > 0
    mock_repo.get_material_costs.assert_called_once()
```

### What to Mock
- ✅ Repositories (data access)
- ✅ External services
- ✅ Time/date functions

### What NOT to Mock
- ❌ Domain core functions (use real ones!)
- ❌ Domain models
- ❌ DTOs

## Controller Tests

**Location**: `tests/integration/`

Mock services, test HTTP concerns.

```python
async def test_pricing_endpoint(client):
    response = client.post(
        "/api/v1/pricing/calculate",
        json=request_data
    )
    assert response.status_code == 200
    assert "pricing_tiers" in response.json()
```

## Integration Tests

**Location**: `tests/integration/`

Test complete workflows with real dependencies.

```python
async def test_pricing_calculation_integration(client):
    # Test with real database, cache, etc.
    response = await client.post("/api/v1/pricing/calculate", json={...})
    assert response.status_code == 200
```

## Test Organization

```
tests/
├── unit/
│   ├── domains/         # Domain core tests (pure functions)
│   ├── test_services.py # Service tests (mock repos)
│   └── test_repos.py    # Repository tests (mock DB)
│
├── integration/         # API/controller tests
│   ├── test_pricing_api.py
│   └── test_error_handling.py
│
└── conftest.py         # Shared fixtures
```

## Best Practices

### General
- ✅ One test file per module
- ✅ Clear test names describing behavior
- ✅ Arrange-Act-Assert pattern
- ✅ Test edge cases and error paths
- ✅ Use fixtures for common setup

### Domain Core
- ✅ Test business rules exhaustively
- ✅ No mocks (defeats the purpose!)
- ✅ Fast tests (< 1ms each)

### Services
- ✅ Mock all repositories
- ✅ Test orchestration logic
- ✅ Verify repository calls

### Controllers
- ✅ Mock services
- ✅ Test HTTP status codes
- ✅ Test error handling
- ✅ Test request/response schemas

## Running Tests

```bash
make test           # All tests
make test-unit      # Fast tests (domain core)
make test-integration  # Integration tests
```

## Before Committing

```bash
make check-all      # Format, lint, type-check
make test           # All tests must pass
```
