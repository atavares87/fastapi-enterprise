# AI Assistant Development Workflow

**CRITICAL**: These rules apply whenever you (AI assistant) are helping with code changes.

## ⚠️ MANDATORY: Change Validation Workflow

### Rule 1: Always Validate Changes

**After making ANY code changes**, you MUST:

1. **Run all tests**:
   ```bash
   make test
   ```

2. **Run all code checks**:
   ```bash
   make check-all
   ```

3. **Fix any failures/errors/warnings**

4. **Re-run tests and checks** until ALL pass

5. **Only then** consider the task complete

### Rule 2: Never Leave Broken Code

- ❌ **NEVER** finish a task with failing tests
- ❌ **NEVER** ignore linter errors or warnings
- ❌ **NEVER** skip validation steps
- ❌ **NEVER** assume code works without verification

### Rule 3: Iterative Fix Process

If tests or checks fail:

1. **Read the error message carefully**
2. **Identify the root cause**
3. **Fix the issue** (don't just suppress the error)
4. **Run validation again**
5. **Repeat until clean**

## Complete Validation Workflow

### Step-by-Step Process

```bash
# 1. After making code changes
make check-all

# Expected: No errors or warnings
# If failures: Fix and re-run

# 2. Run all tests
make test

# Expected: All tests pass
# If failures: Fix and re-run

# 3. Optional: Run specific test categories
make test-unit        # Fast unit tests
make test-integration # Integration tests

# 4. Verify specific files if needed
pytest tests/unit/test_specific.py -v

# 5. Final confirmation
echo "✅ All validation passed - changes are ready"
```

## What Each Command Does

### `make check-all`

Runs:
- **Black** - Code formatting
- **Ruff** - Linting
- **MyPy** - Type checking

Output should be:
```
✅ All code checks passed!
```

### `make test`

Runs:
- All unit tests (domain core, services, repositories)
- All integration tests (API endpoints)
- Contract tests

Output should end with:
```
====== X passed in Y.YYs ======
```

## Common Failure Scenarios

### Scenario 1: Import Errors

**Error**:
```python
ImportError: cannot import name 'OldClass' from 'app.old.path'
```

**Fix**:
1. Update import to new path
2. Check all files for same import
3. Run `make test` again

### Scenario 2: Type Errors

**Error**:
```
error: Argument 1 to "calculate" has incompatible type "str"; expected "Decimal"
```

**Fix**:
1. Convert type: `Decimal(str_value)`
2. Update type hints if needed
3. Run `make check-all` again

### Scenario 3: Test Failures

**Error**:
```
AssertionError: assert Decimal('100.00') == Decimal('99.99')
```

**Fix**:
1. Understand why values differ
2. Update test or fix code logic
3. Run `make test` again

### Scenario 4: Linter Warnings

**Warning**:
```
app/service/pricing_service.py:45:1: F401 'Decimal' imported but unused
```

**Fix**:
1. Remove unused import
2. Or use `# noqa: F401` if intentional (rarely)
3. Run `make check-all` again

## Test-Driven Development Flow

When adding new features:

### 1. Write Test First (TDD)

```python
# tests/unit/domains/test_new_feature.py
def test_calculate_new_thing():
    """Test the pure function we're about to write."""
    result = calculate_new_thing(input_data)
    assert result == expected_value
```

### 2. Run Test (Should Fail)

```bash
pytest tests/unit/domains/test_new_feature.py -v
# Expected: FAILED (function doesn't exist yet)
```

### 3. Implement Feature

```python
# app/domain/core/new_feature/calculations.py
def calculate_new_thing(input_data):
    """Pure function implementation."""
    return result
```

### 4. Run Test Again (Should Pass)

```bash
pytest tests/unit/domains/test_new_feature.py -v
# Expected: PASSED
```

### 5. Run Full Test Suite

```bash
make test
# Expected: All tests pass
```

### 6. Run Code Checks

```bash
make check-all
# Expected: No errors
```

## Validation Checklist

Before considering a task complete, verify:

- [ ] `make check-all` passes (no errors, no warnings)
- [ ] `make test` passes (all tests green)
- [ ] No files with linter errors
- [ ] No type checking errors
- [ ] All imports are correct
- [ ] No unused imports or variables
- [ ] Code is formatted (Black)
- [ ] Type hints are present
- [ ] Docstrings are added for public functions
- [ ] Tests are added for new functionality

## Handling Long-Running Tasks

For tasks that create many files:

### Progressive Validation

1. **After each major component**:
   ```bash
   make check-all  # Quick syntax check
   ```

2. **After completing a layer**:
   ```bash
   make test-unit  # Fast tests
   ```

3. **At the end**:
   ```bash
   make test       # Full test suite
   make check-all  # Complete validation
   ```

## Error Recovery Process

If you encounter persistent failures:

### Step 1: Isolate the Problem

```bash
# Run specific test
pytest tests/unit/test_failing.py -v

# Check specific file
ruff check app/service/failing_service.py
mypy app/service/failing_service.py
```

### Step 2: Understand the Error

- Read the full error message
- Identify the file and line number
- Understand what the code is trying to do
- Understand what the error is saying

### Step 3: Fix Systematically

- Fix one error at a time
- Don't make multiple changes at once
- Verify each fix before moving to next

### Step 4: Re-validate

```bash
# After each fix
make check-all
make test
```

## Special Cases

### Case 1: Intentional Breaking Changes

If you're refactoring and tests need to be updated:

1. **Update code first**
2. **Run tests** (will fail - expected)
3. **Update tests** to match new behavior
4. **Run tests again** (should pass)
5. **Run check-all** (should pass)

### Case 2: Migration/Refactoring

When moving code:

1. **Move files**
2. **Update imports everywhere**
3. **Run check-all** (catches import errors)
4. **Fix import errors**
5. **Run tests** (ensures behavior unchanged)
6. **Fix any test failures**

### Case 3: New Dependencies

When adding new dependencies:

1. **Add to pyproject.toml**
2. **Run**: `uv pip install -e .`
3. **Use in code**
4. **Run check-all** (verifies dependency works)
5. **Run tests** (verifies integration)

## Real-World Example

### Scenario: Adding a new service method

```python
# 1. Write the test first
# tests/unit/test_pricing_service.py
async def test_calculate_bulk_discount():
    mock_repo = Mock(spec=CostRepository)
    service = PricingService(mock_repo)

    result = await service.calculate_bulk_discount(quantity=100)

    assert result.discount_rate == Decimal("0.15")

# 2. Run test (will fail)
$ pytest tests/unit/test_pricing_service.py::test_calculate_bulk_discount -v
# FAILED - AttributeError: 'PricingService' object has no attribute 'calculate_bulk_discount'

# 3. Implement the method
# app/service/pricing_service.py
async def calculate_bulk_discount(self, quantity: int) -> DiscountResult:
    """Calculate bulk discount based on quantity."""
    discount_rate = calculate_discount_rate(quantity)
    return DiscountResult(discount_rate=discount_rate)

# 4. Implement the pure function
# app/domain/core/pricing/discount_calculations.py
def calculate_discount_rate(quantity: int) -> Decimal:
    """Pure function: Calculate discount rate based on quantity."""
    if quantity >= 100:
        return Decimal("0.15")
    elif quantity >= 50:
        return Decimal("0.10")
    else:
        return Decimal("0")

# 5. Run test again
$ pytest tests/unit/test_pricing_service.py::test_calculate_bulk_discount -v
# PASSED ✅

# 6. Run all tests
$ make test
# All tests pass ✅

# 7. Run code checks
$ make check-all
# ✅ All code checks passed!

# 8. Task complete!
```

## Summary: The Golden Rule

### 🏆 Always Complete This Sequence

```bash
# 1. Make changes
[edit files]

# 2. Validate code quality
make check-all
# ↳ Fix any errors
# ↳ Re-run until clean

# 3. Validate functionality
make test
# ↳ Fix any failures
# ↳ Re-run until all pass

# 4. Confirm completion
echo "✅ Changes validated and ready"
```

## Never Skip These Steps

- ✅ **ALWAYS** run `make check-all` after code changes
- ✅ **ALWAYS** run `make test` after code changes
- ✅ **ALWAYS** fix errors before moving on
- ✅ **ALWAYS** verify all tests pass
- ✅ **NEVER** leave broken code
- ✅ **NEVER** skip validation
- ✅ **NEVER** assume code works

## Reporting to User

When finishing a task, always report:

```
✅ Task Complete!

Changes made:
- [List of files changed]
- [List of features added]

Validation results:
✅ make check-all: PASSED (no errors, no warnings)
✅ make test: PASSED (X tests, Y.YY seconds)

All changes are validated and ready for commit.
```

If validation fails and you can't fix it:

```
⚠️ Task Incomplete - Validation Issues

Changes made:
- [List of changes]

Validation issues:
❌ make check-all: 3 linter errors
❌ make test: 2 tests failing

Errors encountered:
1. [Describe error 1]
2. [Describe error 2]

Attempted fixes:
- [What you tried]

Need assistance with:
- [What's blocking completion]
```

## Remember

**Quality over speed**. It's better to take extra time to ensure all tests pass than to deliver broken code quickly.

**Every change must be validated.** No exceptions.

**The user trusts you to deliver working code.** Don't betray that trust by skipping validation steps.
