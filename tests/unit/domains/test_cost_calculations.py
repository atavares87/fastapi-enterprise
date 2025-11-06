"""
Tests for Cost Calculation Functions - FUNCTIONAL CORE

Testing pure functions is simple:
- No mocks needed!
- No setup/teardown
- Fast execution
- Deterministic results
"""

from decimal import Decimal

import pytest

from app.cost.core.calculations import calculate_manufacturing_cost, estimate_cost_range
from app.cost.models import MaterialCost, PartDimensions, PartSpecification, ProcessCost
from app.shared.enums import ManufacturingProcess, Material


def test_calculate_manufacturing_cost_with_aluminum_cnc():
    """Test pure function - no mocks needed!"""
    # Arrange: Just create input data
    spec = PartSpecification(
        dimensions=PartDimensions(length_mm=100, width_mm=50, height_mm=25),
        geometric_complexity_score=2.5,
        material=Material.ALUMINUM,
        process=ManufacturingProcess.CNC,
    )

    material_costs = {
        Material.ALUMINUM: MaterialCost(
            cost_per_cm3=Decimal("0.15"),
            waste_factor=1.15,
            setup_cost=Decimal("25.00"),
        )
    }

    process_costs = {
        ManufacturingProcess.CNC: ProcessCost(
            hourly_rate=Decimal("85.00"),
            setup_time_hours=1.5,
            complexity_multiplier={
                1.0: 1.0,
                2.0: 1.3,
                3.0: 1.7,
                4.0: 2.2,
                5.0: 3.0,
            },
        )
    }

    # Act: Call pure function directly
    result = calculate_manufacturing_cost(
        spec=spec, material_costs=material_costs, process_costs=process_costs
    )

    # Assert: Check result
    assert result.total_cost > 0
    assert result.material_cost > 0
    assert result.labor_cost > 0
    assert result.setup_cost > 0
    # No mocks, no database, no setup!


def test_calculate_manufacturing_cost_with_different_complexity():
    """Test that higher complexity increases cost."""
    # Shared setup
    dimensions = PartDimensions(length_mm=100, width_mm=50, height_mm=25)
    material_costs = {
        Material.ALUMINUM: MaterialCost(
            cost_per_cm3=Decimal("0.15"),
            waste_factor=1.15,
            setup_cost=Decimal("25.00"),
        )
    }
    process_costs = {
        ManufacturingProcess.CNC: ProcessCost(
            hourly_rate=Decimal("85.00"),
            setup_time_hours=1.5,
            complexity_multiplier={1.0: 1.0, 2.0: 1.3, 3.0: 1.7, 4.0: 2.2, 5.0: 3.0},
        )
    }

    # Calculate cost for low complexity
    spec_low = PartSpecification(
        dimensions=dimensions,
        geometric_complexity_score=1.0,
        material=Material.ALUMINUM,
        process=ManufacturingProcess.CNC,
    )
    result_low = calculate_manufacturing_cost(spec_low, material_costs, process_costs)

    # Calculate cost for high complexity
    spec_high = PartSpecification(
        dimensions=dimensions,
        geometric_complexity_score=5.0,
        material=Material.ALUMINUM,
        process=ManufacturingProcess.CNC,
    )
    result_high = calculate_manufacturing_cost(spec_high, material_costs, process_costs)

    # Assert: High complexity should cost more
    assert result_high.total_cost > result_low.total_cost
    assert result_high.labor_cost > result_low.labor_cost
    assert result_high.complexity_adjustment > result_low.complexity_adjustment


def test_estimate_cost_range():
    """Test cost range estimation with min/max complexity."""
    spec = PartSpecification(
        dimensions=PartDimensions(100, 50, 25),
        geometric_complexity_score=3.0,  # Will be overridden
        material=Material.ALUMINUM,
        process=ManufacturingProcess.CNC,
    )

    material_costs = {
        Material.ALUMINUM: MaterialCost(
            cost_per_cm3=Decimal("0.15"),
            waste_factor=1.15,
            setup_cost=Decimal("25.00"),
        )
    }

    process_costs = {
        ManufacturingProcess.CNC: ProcessCost(
            hourly_rate=Decimal("85.00"),
            setup_time_hours=1.5,
            complexity_multiplier={1.0: 1.0, 5.0: 3.0},
        )
    }

    min_cost, max_cost = estimate_cost_range(spec, material_costs, process_costs)

    assert min_cost < max_cost
    assert min_cost > 0
    assert max_cost > 0


def test_calculate_manufacturing_cost_raises_error_for_unsupported_material():
    """Test that function raises error for unsupported material."""
    spec = PartSpecification(
        dimensions=PartDimensions(100, 50, 25),
        geometric_complexity_score=2.5,
        material=Material.ALUMINUM,
        process=ManufacturingProcess.CNC,
    )

    # Empty cost dictionaries
    material_costs = {}
    process_costs = {
        ManufacturingProcess.CNC: ProcessCost(
            hourly_rate=Decimal("85.00"),
            setup_time_hours=1.5,
            complexity_multiplier={1.0: 1.0},
        )
    }

    with pytest.raises(ValueError, match="Unsupported material"):
        calculate_manufacturing_cost(spec, material_costs, process_costs)
