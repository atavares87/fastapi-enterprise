# API Contract Testing

This directory contains contract tests for the FastAPI Enterprise application using JSON Schema validation - a reliable, industry-standard approach for API contract testing.

## Overview

Contract testing ensures that APIs maintain compatibility and behave consistently across different versions and deployments. Our approach uses JSON Schema validation to verify that API responses conform to expected structures and business rules.

## Approach

### JSON Schema Contract Testing

We use **JSON Schema** instead of Pact for the following reasons:

1. **Reliability**: No dependency on external mock servers or complex setup
2. **Standard**: JSON Schema is a widely adopted W3C standard
3. **Comprehensive**: Can validate structure, types, constraints, and business rules
4. **Fast**: Runs as part of regular test suite without additional infrastructure
5. **Maintainable**: Schemas are self-documenting and version-controlled

### Test Structure

```
tests/contract/
├── README.md                 # This documentation
├── __init__.py              # Package initialization
├── schemas.py               # JSON Schema definitions
└── test_api_contracts.py    # Contract test implementations
```

## Running Contract Tests

### Via Make Commands

```bash
# Run all contract tests
make test-contract

# Run consumer contract tests only
make test-contract-consumer

# Run all tests including contract tests
make test-all
```

### Via pytest

```bash
# Run all contract tests
uv run pytest tests/contract -v -m contract

# Run specific test file
uv run pytest tests/contract/test_api_contracts.py -v

# Run specific test
uv run pytest tests/contract/test_api_contracts.py::TestAPIContracts::test_pricing_calculation_contract -v
```

## Contract Definitions

### Health API Contracts

- **Basic Health Check**: `/health`
  - Returns system status, timestamp, app info
  - Validates response structure and required fields

- **Detailed Health Check**: `/health/detailed`
  - Returns comprehensive health status including database connectivity
  - Validates service status consistency

- **Root Endpoint**: `/`
  - Returns API metadata and navigation links
  - Validates API documentation URLs

### Pricing API Contracts

- **Pricing Calculation**: `POST /api/v1/pricing`
  - Validates request and response schemas
  - Ensures all pricing tiers are present and valid
  - Validates cost breakdowns and calculations

- **Metadata Endpoints**:
  - `GET /api/v1/pricing/materials` - Available materials list
  - `GET /api/v1/pricing/processes` - Available manufacturing processes
  - `GET /api/v1/pricing/tiers` - Available pricing tiers

- **Error Handling**:
  - Validates error response format for validation errors (422)
  - Ensures consistent error message structure

## Schema Validation

### Request Validation

The schemas validate:
- Required fields are present
- Field types are correct
- Value ranges and constraints
- Business rule compliance

### Response Validation

The schemas validate:
- Response structure matches API specification
- All required fields are present
- Data types are consistent
- Business logic constraints are met

### Example Schema Structure

```python
PRICING_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "part_specification": { ... },
        "cost_breakdown": { ... },
        "pricing_tiers": { ... },
        "estimated_weight_kg": {"type": "number"},
        "quantity": {"type": "integer"}
    },
    "required": ["part_specification", "cost_breakdown", "pricing_tiers", "estimated_weight_kg", "quantity"]
}
```

## Contract Test Coverage

### Current Coverage (13 tests)

✅ **Health Endpoints (3 tests)**
- Basic health check contract
- Detailed health check contract
- Root endpoint contract

✅ **Pricing API (7 tests)**
- Pricing calculation contract
- Materials endpoint contract
- Processes endpoint contract
- Tiers endpoint contract
- Validation error contract
- Edge cases contract
- Backward compatibility contract

✅ **Cross-cutting Concerns (3 tests)**
- Response headers contract
- Error response consistency
- Async endpoint contracts

### Test Characteristics

- **Fast**: All tests run in under 1 second
- **Reliable**: No external dependencies or mock servers
- **Comprehensive**: Covers happy path, edge cases, and error scenarios
- **Maintainable**: Clear schema definitions and test structure

## Best Practices

### Schema Design

1. **Be Specific**: Define exact field types and constraints
2. **Version Schemas**: Maintain schema versions for backward compatibility
3. **Document Business Rules**: Include validation for business logic
4. **Use Standard Types**: Leverage JSON Schema standard types and formats

### Test Design

1. **Test Both Directions**: Validate requests and responses
2. **Cover Edge Cases**: Test minimum/maximum values and boundary conditions
3. **Validate Headers**: Ensure proper content types and custom headers
4. **Test Error Scenarios**: Validate error response formats

### Maintenance

1. **Update Schemas First**: Update schemas before implementing API changes
2. **Run Contracts in CI**: Include contract tests in continuous integration
3. **Version Control**: Keep schema changes in version control
4. **Document Changes**: Update documentation when contracts change

## Integration with CI/CD

Contract tests are integrated into the CI pipeline:

```bash
# Standard CI pipeline
make ci                  # Includes contract tests

# Full CI pipeline
make ci-full            # Includes provider verification
```

## Future Enhancements

1. **Schema Registry**: Consider using a schema registry for larger teams
2. **Contract Publishing**: Publish contracts for consumer teams
3. **Versioning Strategy**: Implement semantic versioning for API contracts
4. **Provider Verification**: Add tests that verify provider against published contracts

## Troubleshooting

### Common Issues

1. **Schema Validation Errors**: Check field types and required properties
2. **Missing Fields**: Ensure all required fields are present in response
3. **Type Mismatches**: Verify that field types match schema definitions

### Debugging

```bash
# Run with verbose output
uv run pytest tests/contract -v -s

# Run specific failing test
uv run pytest tests/contract/test_api_contracts.py::TestAPIContracts::test_name -v -s

# Enable JSON Schema validation debugging
export JSONSCHEMA_DEBUG=1
```

## Resources

- [JSON Schema Documentation](https://json-schema.org/)
- [Contract Testing Best Practices](https://martinfowler.com/articles/contract-testing.html)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest Documentation](https://docs.pytest.org/)
