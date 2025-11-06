# Common Anti-Patterns to Avoid

## General Anti-Patterns

### ❌ Business Logic in Controllers

```python
# BAD
@router.post("/calculate")
async def calculate_pricing(request: PricingRequestDTO):
    # Don't do calculations here!
    margin = base_cost * 0.45
    return {"price": margin}

# GOOD
@router.post("/calculate")
async def calculate_pricing(
    request: PricingRequestDTO,
    service: PricingService = Depends(get_pricing_service)
):
    # Delegate to service
    return await service.calculate_pricing(request)
```

### ❌ HTTP Concerns in Services

```python
# BAD
class PricingService:
    async def calculate_pricing(self, request):
        if error:
            raise HTTPException(status_code=400, detail="Error")

# GOOD
class PricingService:
    async def calculate_pricing(self, request):
        if error:
            raise ValidationException("Error")
        # Controller handles HTTP conversion
```

### ❌ Database Queries in Services

```python
# BAD
class PricingService:
    async def calculate_pricing(self, request):
        result = await db.execute("SELECT * FROM costs")

# GOOD
class PricingService:
    async def calculate_pricing(self, request):
        costs = await self.cost_repository.get_material_costs()
```

### ❌ Global Variables for State

```python
# BAD
current_user = None  # Global mutable state

def do_something():
    global current_user
    current_user = get_user()

# GOOD
class SomeService:
    def do_something(self, user: User):
        # Pass as parameter
        return process(user)
```

### ❌ Missing Type Annotations

```python
# BAD
def calculate(cost, config):
    return cost * config.rate

# GOOD
def calculate(cost: Decimal, config: PricingConfiguration) -> Decimal:
    return cost * Decimal(str(config.rate))
```

## Layered Architecture-Specific Anti-Patterns

### ❌ Controllers Calling Repositories Directly

```python
# BAD - Skipping service layer
@router.post("/calculate")
async def calculate_pricing(
    request: PricingRequestDTO,
    repo: CostRepository = Depends(get_cost_repository)  # Wrong!
):
    costs = await repo.get_material_costs()
    # Business logic here...

# GOOD
@router.post("/calculate")
async def calculate_pricing(
    request: PricingRequestDTO,
    service: PricingService = Depends(get_pricing_service)  # Correct!
):
    return await service.calculate_pricing(request)
```

### ❌ Services Knowing About HTTP

```python
# BAD
class PricingService:
    async def calculate_pricing(self, request: Request):  # FastAPI Request!
        headers = request.headers

# GOOD
class PricingService:
    async def calculate_pricing(self, request: PricingRequestDTO):  # DTO!
        # No HTTP knowledge
```

### ❌ Repositories Containing Business Logic

```python
# BAD
class CostRepository:
    async def get_material_costs_with_discount(self):
        costs = await self._fetch()
        # Don't calculate discounts here!
        return {k: v * 0.9 for k, v in costs.items()}

# GOOD
class CostRepository:
    async def get_material_costs(self):
        # Just fetch data
        return await self._fetch()

# Calculate discounts in domain core
result = calculate_discount(costs, discount_rate)
```

### ❌ Domain Depending on Upper Layers

```python
# BAD
# In domain/core/calculations.py
from app.repository.cost_repository import CostRepository  # Wrong!

def calculate_cost(repo: CostRepository):
    costs = await repo.get_material_costs()

# GOOD
# In domain/core/calculations.py
def calculate_cost(
    spec: PartSpecification,
    material_costs: dict[Material, MaterialCost]  # Data passed in
) -> CostBreakdown:
    # Pure function
```

## Functional Core-Specific Anti-Patterns

### ❌ Side Effects in Domain Core

```python
# BAD
def calculate_margin(base_cost: Decimal, config: PricingConfiguration) -> Decimal:
    logger.info("Calculating margin")  # Side effect!
    save_to_cache(base_cost)  # Side effect!
    return base_cost * Decimal(str(config.margin_percentage))

# GOOD
def calculate_margin(base_cost: Decimal, config: PricingConfiguration) -> Decimal:
    """Pure function - no side effects."""
    return base_cost * Decimal(str(config.margin_percentage))
```

### ❌ Database Calls from Domain Core

```python
# BAD
def calculate_price(part_id: int) -> Decimal:
    config = db.query("SELECT * FROM config")  # I/O in pure function!
    return calculate(config)

# GOOD
def calculate_price(config: PricingConfiguration) -> Decimal:
    """Pure function - all data passed as parameters."""
    return calculate(config)
```

### ❌ Using Current Time in Pure Functions

```python
# BAD
def calculate_discount() -> Decimal:
    now = datetime.now()  # Non-deterministic!
    if now.weekday() == 0:
        return Decimal("0.10")

# GOOD
def calculate_discount(current_date: datetime) -> Decimal:
    """Pure function - time passed as parameter."""
    if current_date.weekday() == 0:
        return Decimal("0.10")
```

### ❌ Mocking Pure Functions in Tests

```python
# BAD
def test_service():
    mock_calculate = Mock(return_value=Decimal("100"))
    with patch('app.domain.core.pricing.calculate_margin', mock_calculate):
        # If you need to mock it, it's not pure!

# GOOD
def test_service():
    # Mock repositories, use real domain functions
    mock_repo = Mock(spec=CostRepository)
    service = PricingService(mock_repo)
    # Domain functions execute for real
```

## Testing Anti-Patterns

### ❌ Testing Implementation Details

```python
# BAD
def test_service_calls_repository():
    service.calculate_pricing(request)
    assert service.cost_repository._internal_method.called

# GOOD
def test_service_returns_correct_price():
    result = await service.calculate_pricing(request)
    assert result.final_price == expected_price
```

### ❌ Too Many Mocks

```python
# BAD
def test_with_mocks():
    mock1 = Mock()
    mock2 = Mock()
    mock3 = Mock()
    mock4 = Mock()
    # If you need this many mocks, refactor!

# GOOD - Test smaller units or use real objects
def test_domain_function():
    # Pure function - no mocks needed!
    result = calculate_margin(Decimal("100"), config)
```

## When You See These Patterns

**STOP and refactor immediately!** These patterns lead to:
- Unmaintainable code
- Hard-to-test code
- Tight coupling
- Bugs

**Remember**: Keep it simple, follow SOLID, maintain the functional core!
