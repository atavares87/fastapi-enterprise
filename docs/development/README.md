# Development Documentation

## Quick Start

```bash
make full-setup    # Complete setup
make start-dev     # Start app
make test          # Run tests
make check-all     # Format & lint
```

## Guides

1. **[Getting Started](getting-started.md)** - Project setup, IDE configuration, first run

2. **[Adding Features](adding-features.md)** - Step-by-step feature development workflow

3. **[Domain Development](domain-development.md)** - Creating business domains with pure functions

## Development Workflow

### 1. Create Domain Logic (Pure Functions)

```python
# app/core/domain/your_feature/calculations.py
def calculate_something(input_data: InputData) -> Result:
    """Pure function - no I/O, deterministic."""
    return Result(...)
```

### 2. Define Ports (Interfaces)

```python
# app/core/port/outbound/your_feature_ports.py
class YourDataPort(Protocol):
    async def get_data(self) -> Data: ...
```

### 3. Create Use Case (Orchestration)

```python
# app/core/application/your_feature/use_cases.py
class YourUseCase:
    def __init__(self, data_port: YourDataPort):
        self._data_port = data_port

    async def execute(self, request: Request) -> Response:
        # 1. Get data (imperative shell)
        data = await self._data_port.get_data()

        # 2. Execute logic (functional core)
        result = calculate_something(data)

        # 3. Return
        return Response(result)
```

### 4. Create Adapter (Implementation)

```python
# app/adapter/outbound/persistence/your_adapter.py
class YourDataAdapter:
    """Implements YourDataPort."""
    async def get_data(self) -> Data:
        # Database I/O here
        ...
```

### 5. Create API Endpoint

```python
# app/adapter/inbound/web/your_feature.py
@router.post("/your-feature")
async def your_endpoint(
    request: RequestSchema,
    use_case: YourUseCase = Depends(get_use_case)
):
    result = await use_case.execute(request)
    return ResponseSchema.from_domain(result)
```

## Testing

### Unit Tests (No Mocks Needed!)

```python
def test_calculation():
    """Test pure function directly."""
    result = calculate_something(input_data)
    assert result.value == expected
```

### Integration Tests (Real Database)

```python
@pytest.mark.asyncio
async def test_adapter():
    """Test adapter with real database."""
    adapter = YourDataAdapter(session)
    data = await adapter.get_data()
    assert data is not None
```

### API Tests

```python
def test_endpoint(client: TestClient):
    """Test HTTP endpoint."""
    response = client.post("/api/v1/your-feature", json={...})
    assert response.status_code == 200
```

## Best Practices

1. **Keep domain pure** - No I/O in `core/domain/`
2. **Test without mocks** - Pure functions don't need mocks
3. **Use type hints** - Full type coverage with mypy
4. **Write docstrings** - Document public functions
5. **Follow naming** - See [folder-structure.md](../architecture/folder-structure.md)

## External Resources

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Type Hints](https://docs.python.org/3/library/typing.html)
