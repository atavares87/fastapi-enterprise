"""
Pure Cost Calculation Functions - FUNCTIONAL CORE

These functions contain pure business logic with NO side effects:
- No database calls
- No logging
- No metrics
- No current time access
- All dependencies passed as parameters
- Same input always produces same output
"""

from decimal import Decimal

from app.domain.model import (
    CostBreakdown,
    ManufacturingProcess,
    Material,
    MaterialCost,
    PartSpecification,
    ProcessCost,
)


def calculate_manufacturing_cost(
    spec: PartSpecification,
    material_costs: dict[Material, MaterialCost],
    process_costs: dict[ManufacturingProcess, ProcessCost],
) -> CostBreakdown:
    """
    Pure function: Calculate manufacturing cost for a part.

    All required data is passed in as parameters.
    No side effects - same input always produces same output.

    Args:
        spec: Complete part specification
        material_costs: Material cost database
        process_costs: Process cost database

    Returns:
        Detailed cost breakdown

    Raises:
        ValueError: If material or process not found in cost databases
    """
    if spec.material not in material_costs:
        raise ValueError(f"Unsupported material: {spec.material}")
    if spec.process not in process_costs:
        raise ValueError(f"Unsupported process: {spec.process}")

    material_cost_info = material_costs[spec.material]
    process_cost_info = process_costs[spec.process]

    # Pure calculations
    material_cost = _calculate_material_cost(spec, material_cost_info)
    labor_cost = _calculate_labor_cost(spec, process_cost_info)
    setup_cost = _calculate_setup_cost(material_cost_info, process_cost_info)
    complexity_adjustment = _calculate_complexity_adjustment(spec, labor_cost)

    return CostBreakdown.create(
        material_cost=material_cost,
        labor_cost=labor_cost,
        setup_cost=setup_cost,
        complexity_adjustment=complexity_adjustment,
    )


def estimate_cost_range(
    spec: PartSpecification,
    material_costs: dict[Material, MaterialCost],
    process_costs: dict[ManufacturingProcess, ProcessCost],
) -> tuple[Decimal, Decimal]:
    """
    Pure function: Estimate cost range by varying complexity.

    Calculates minimum (complexity=1.0) and maximum (complexity=5.0) costs.
    """
    min_spec = PartSpecification(
        dimensions=spec.dimensions,
        geometric_complexity_score=1.0,
        material=spec.material,
        process=spec.process,
    )
    min_cost = calculate_manufacturing_cost(
        min_spec, material_costs, process_costs
    ).total_cost

    max_spec = PartSpecification(
        dimensions=spec.dimensions,
        geometric_complexity_score=5.0,
        material=spec.material,
        process=spec.process,
    )
    max_cost = calculate_manufacturing_cost(
        max_spec, material_costs, process_costs
    ).total_cost

    return min_cost, max_cost


def _calculate_material_cost(
    spec: PartSpecification, material_cost_info: MaterialCost
) -> Decimal:
    """Pure function: Calculate material cost including waste."""
    volume = Decimal(str(spec.dimensions.volume_cm3))
    base_cost = volume * material_cost_info.cost_per_cm3
    return base_cost * Decimal(str(material_cost_info.waste_factor))


def _calculate_labor_cost(
    spec: PartSpecification, process_cost_info: ProcessCost
) -> Decimal:
    """Pure function: Calculate labor cost based on estimated time."""
    base_time_hours = _estimate_processing_time(spec)
    complexity_multiplier = _get_complexity_multiplier(
        spec.geometric_complexity_score, process_cost_info.complexity_multiplier
    )
    total_time = base_time_hours * complexity_multiplier
    return process_cost_info.hourly_rate * Decimal(str(total_time))


def _calculate_setup_cost(
    material_cost_info: MaterialCost, process_cost_info: ProcessCost
) -> Decimal:
    """Pure function: Calculate setup costs."""
    return material_cost_info.setup_cost + (
        process_cost_info.hourly_rate * Decimal(str(process_cost_info.setup_time_hours))
    )


def _estimate_processing_time(spec: PartSpecification) -> float:
    """Pure function: Estimate processing time using heuristics."""
    volume_factor = spec.dimensions.volume_cm3 / 100
    surface_area_factor = spec.dimensions.surface_area_cm2 / 1000

    if spec.process == ManufacturingProcess.CNC:
        return 0.5 + (surface_area_factor * 0.8) + (volume_factor * 0.2)
    elif spec.process == ManufacturingProcess.THREE_D_PRINTING:
        height_factor = spec.dimensions.height_mm / 100
        return 1.0 + (volume_factor * 0.1) + (height_factor * 0.5)
    elif spec.process in [
        ManufacturingProcess.SHEET_CUTTING,
        ManufacturingProcess.LASER_CUTTING,
    ]:
        return 0.2 + (surface_area_factor * 0.3)
    else:
        return 1.0 + (volume_factor * 0.5)


def _get_complexity_multiplier(
    complexity_score: float, complexity_map: dict[float, float]
) -> float:
    """Pure function: Get complexity multiplier with interpolation."""
    if complexity_score in complexity_map:
        return complexity_map[complexity_score]

    scores = sorted(complexity_map.keys())
    if complexity_score <= scores[0]:
        return complexity_map[scores[0]]
    if complexity_score >= scores[-1]:
        return complexity_map[scores[-1]]

    # Linear interpolation
    lower = max(s for s in scores if s <= complexity_score)
    upper = min(s for s in scores if s >= complexity_score)

    if lower == upper:
        return complexity_map[lower]

    ratio = (complexity_score - lower) / (upper - lower)
    return complexity_map[lower] + ratio * (
        complexity_map[upper] - complexity_map[lower]
    )


def _calculate_complexity_adjustment(
    spec: PartSpecification, base_labor_cost: Decimal
) -> Decimal:
    """Pure function: Calculate complexity surcharge."""
    if spec.geometric_complexity_score >= 4.0:
        return base_labor_cost * Decimal("0.25")
    elif spec.geometric_complexity_score >= 3.0:
        return base_labor_cost * Decimal("0.10")
    else:
        return Decimal("0")
