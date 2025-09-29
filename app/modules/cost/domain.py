"""
Cost Domain Models - Manufacturing Cost Calculation Business Logic

This module contains the core business domain models and logic for manufacturing
cost calculations. Following hexagonal architecture principles, these models are
pure business logic with no external dependencies (database, API, etc.).

Key Components:
- 🏭 Manufacturing processes and materials enumeration
- 📐 Part dimensions with automatic volume/area calculations
- 💰 Cost breakdown structures with validation
- 🧮 Cost calculation engine with complexity-aware pricing

Business Rules:
- All dimensions must be positive values in millimeters
- Complexity scores range from 1.0 (simple) to 5.0 (very complex)
- Material costs include waste factors (typically 10-20% overhead)
- Labor costs scale with part complexity and manufacturing process
- High complexity parts (4.0+) incur 25% surcharge, medium (3.0+) get 10%

Example Usage:
    # Define a part specification
    dimensions = PartDimensions(length_mm=100, width_mm=50, height_mm=25)
    spec = PartSpecification(
        dimensions=dimensions,
        geometric_complexity_score=3.5,
        material=Material.ALUMINUM,
        process=ManufacturingProcess.CNC
    )

    # Calculate costs
    engine = CostCalculationEngine(material_costs, process_costs)
    breakdown = engine.calculate_cost(spec)
    print(f"Total cost: ${breakdown.total_cost}")
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ManufacturingProcess(str, Enum):
    """
    Manufacturing processes supported by the cost calculation system.

    Each process has different cost characteristics:
    - CNC: High precision, surface area dependent
    - 3D Printing: Volume and height dependent, longer lead times
    - Sheet/Laser Cutting: Perimeter/area dependent, fast for thin parts
    - Tube Bending: Specialized for cylindrical parts
    - Injection Molding: High setup cost, low per-unit cost for volume
    - Waterjet: Precision cutting for thick materials
    """

    CNC = "cnc"
    THREE_D_PRINTING = "3d_printing"
    SHEET_CUTTING = "sheet_cutting"
    TUBE_BENDING = "tube_bending"
    INJECTION_MOLDING = "injection_molding"
    LASER_CUTTING = "laser_cutting"
    WATERJET_CUTTING = "waterjet_cutting"


class Material(str, Enum):
    """
    Materials supported for manufacturing cost calculations.

    Each material has different properties affecting cost:
    - Metals (Aluminum, Steel, Stainless, Titanium): Higher material costs, good machinability
    - Plastics (ABS, PLA, PETG): Lower costs, suitable for 3D printing
    - Specialty (Brass, Copper, Carbon Fiber): Premium materials with specific applications

    Material costs include:
    - Base cost per cubic centimeter
    - Waste factor (material loss during processing)
    - Setup costs (tooling, preparation)
    """

    ALUMINUM = "aluminum"
    STEEL = "steel"
    STAINLESS_STEEL = "stainless_steel"
    PLASTIC_ABS = "plastic_abs"
    PLASTIC_PLA = "plastic_pla"
    PLASTIC_PETG = "plastic_petg"
    TITANIUM = "titanium"
    BRASS = "brass"
    COPPER = "copper"
    CARBON_FIBER = "carbon_fiber"


@dataclass(frozen=True)
class PartDimensions:
    """
    Physical dimensions of a manufacturing part with automatic calculations.

    This immutable dataclass stores part dimensions in millimeters and provides
    computed properties for volume, surface area, and bounding box diagonal.
    These derived measurements are used throughout the cost calculation process.

    Attributes:
        length_mm: Part length in millimeters (must be positive)
        width_mm: Part width in millimeters (must be positive)
        height_mm: Part height in millimeters (must be positive)

    Computed Properties:
        volume_cm3: Volume in cubic centimeters (for material cost calculation)
        surface_area_cm2: Surface area in square centimeters (for machining time estimation)
        bounding_box_diagonal_mm: 3D diagonal for complexity assessment

    Example:
        dimensions = PartDimensions(length_mm=100, width_mm=50, height_mm=25)
        print(f"Volume: {dimensions.volume_cm3} cm³")  # 125.0 cm³
        print(f"Surface: {dimensions.surface_area_cm2} cm²")  # 175.0 cm²
    """

    length_mm: float
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        """Validate dimensions are positive."""
        if any(dim <= 0 for dim in [self.length_mm, self.width_mm, self.height_mm]):
            raise ValueError("All dimensions must be positive")

    @property
    def volume_cm3(self) -> float:
        """
        Calculate part volume in cubic centimeters.

        Used for material cost calculations - multiply by material density
        and cost per cm³ to get base material cost.

        Returns:
            Volume in cubic centimeters (length × width × height / 1000)
        """
        return (self.length_mm * self.width_mm * self.height_mm) / 1000

    @property
    def surface_area_cm2(self) -> float:
        """
        Calculate total surface area in square centimeters.

        Used for machining time estimation - processes like CNC milling
        and surface finishing scale with surface area rather than volume.

        Returns:
            Total surface area in cm² using box formula: 2(lw + lh + wh)
        """
        length, width, height = (
            self.length_mm / 10,
            self.width_mm / 10,
            self.height_mm / 10,
        )
        return 2 * (length * width + length * height + width * height)

    @property
    def bounding_box_diagonal_mm(self) -> float:
        """
        Calculate 3D diagonal of the part's bounding box.

        Used for complexity assessment and machine capability checks.
        Larger diagonals may require bigger machines or special fixtures.

        Returns:
            3D diagonal in millimeters: √(length² + width² + height²)
        """
        return float((self.length_mm**2 + self.width_mm**2 + self.height_mm**2) ** 0.5)


@dataclass(frozen=True)
class PartSpecification:
    """
    Complete specification defining a part for manufacturing cost calculation.

    This is the main input to the cost calculation system, combining physical
    dimensions with material choice, manufacturing process, and complexity rating.

    Attributes:
        dimensions: Physical dimensions with computed volume/area properties
        geometric_complexity_score: Complexity rating from 1.0 (simple box) to 5.0 (complex geometry)
        material: Material type affecting cost, weight, and machinability
        process: Manufacturing process determining labor costs and capabilities

    Complexity Score Guidelines:
        1.0-2.0: Simple geometry (boxes, cylinders, basic shapes)
        2.0-3.0: Moderate complexity (holes, slots, basic features)
        3.0-4.0: Complex geometry (multiple features, tight tolerances)
        4.0-5.0: Very complex (intricate details, difficult machining angles)

    Example:
        spec = PartSpecification(
            dimensions=PartDimensions(100, 50, 25),
            geometric_complexity_score=3.2,  # Moderately complex
            material=Material.ALUMINUM,
            process=ManufacturingProcess.CNC
        )
    """

    dimensions: PartDimensions  # Physical dimensions and computed properties
    geometric_complexity_score: (
        float  # 1.0 = simple geometry, 5.0 = very complex geometry
    )
    material: Material  # Material type affecting cost and processing
    process: ManufacturingProcess  # Manufacturing method determining labor costs

    def __post_init__(self) -> None:
        """Validate part specification."""
        if not (1.0 <= self.geometric_complexity_score <= 5.0):
            raise ValueError("Geometric complexity score must be between 1.0 and 5.0")


@dataclass(frozen=True)
class MaterialCost:
    """Cost information for a specific material."""

    cost_per_cm3: Decimal
    waste_factor: float  # Multiplier for material waste (1.1 = 10% waste)
    setup_cost: Decimal  # Fixed setup cost for this material

    def __post_init__(self) -> None:
        """Validate material cost parameters."""
        if self.cost_per_cm3 < 0:
            raise ValueError("Cost per cm3 must be non-negative")
        if self.waste_factor < 1.0:
            raise ValueError("Waste factor must be >= 1.0")
        if self.setup_cost < 0:
            raise ValueError("Setup cost must be non-negative")


@dataclass(frozen=True)
class ProcessCost:
    """Cost information for a specific manufacturing process."""

    hourly_rate: Decimal
    setup_time_hours: float
    complexity_multiplier: dict[float, float]  # Complexity score -> time multiplier

    def __post_init__(self) -> None:
        """Validate process cost parameters."""
        if self.hourly_rate < 0:
            raise ValueError("Hourly rate must be non-negative")
        if self.setup_time_hours < 0:
            raise ValueError("Setup time must be non-negative")


@dataclass(frozen=True)
class CostBreakdown:
    """
    Complete breakdown of manufacturing costs with itemized components.

    This immutable structure provides transparency into cost calculation,
    showing exactly how the total cost is derived from individual components.
    Essential for customer quotes and internal cost analysis.

    Components:
        material_cost: Raw material cost including waste factor
        labor_cost: Processing time × hourly rate with complexity multipliers
        setup_cost: One-time setup costs for tooling and machine preparation
        complexity_adjustment: Additional charges for complex geometries
        overhead_cost: Facility overhead (typically 15% of base costs)
        total_cost: Sum of all cost components

    Example:
        breakdown = CostBreakdown.create(
            material_cost=Decimal('25.50'),
            labor_cost=Decimal('45.00'),
            setup_cost=Decimal('15.00'),
            complexity_adjustment=Decimal('4.50')
        )
        print(f"Total with overhead: ${breakdown.total_cost}")
    """

    material_cost: Decimal  # Raw material cost including waste factor
    labor_cost: Decimal  # Processing time costs with complexity multipliers
    setup_cost: Decimal  # Machine setup and tooling preparation costs
    complexity_adjustment: Decimal  # Additional charges for complex parts (10-25%)
    overhead_cost: Decimal  # Facility overhead calculated as percentage of base costs
    total_cost: Decimal  # Final total cost including all components

    @classmethod
    def create(
        cls,
        material_cost: Decimal,
        labor_cost: Decimal,
        setup_cost: Decimal,
        complexity_adjustment: Decimal,
        overhead_rate: float = 0.15,  # 15% overhead
    ) -> "CostBreakdown":
        """Create cost breakdown with calculated totals."""
        base_cost = material_cost + labor_cost + setup_cost + complexity_adjustment
        overhead_cost = base_cost * Decimal(str(overhead_rate))
        total_cost = base_cost + overhead_cost

        return cls(
            material_cost=material_cost,
            labor_cost=labor_cost,
            setup_cost=setup_cost,
            complexity_adjustment=complexity_adjustment,
            overhead_cost=overhead_cost,
            total_cost=total_cost,
        )


class CostCalculationEngine:
    """
    Core business logic engine for manufacturing cost calculations.

    This is the heart of the cost calculation domain, implementing all business
    rules for converting part specifications into detailed cost breakdowns.
    The engine is configurable with different material and process cost data,
    making it adaptable to different manufacturing environments.

    Key Features:
    - 🎯 Configurable material and process cost databases
    - 📊 Complexity-aware time estimation algorithms
    - 💡 Intelligent interpolation for complexity multipliers
    - 🔄 Transparent cost breakdown with audit trail
    - ⚡ Fast calculation suitable for real-time quoting

    Business Logic:
    - Material costs scale with volume and include waste factors
    - Labor costs depend on estimated processing time and complexity
    - Setup costs are process-specific and amortized across quantity
    - Complexity surcharges apply graduated penalties for difficult parts
    - Overhead is calculated as percentage of base manufacturing costs

    Example:
        # Initialize with cost databases
        engine = CostCalculationEngine(
            material_costs={Material.ALUMINUM: MaterialCost(...)},
            process_costs={ManufacturingProcess.CNC: ProcessCost(...)}
        )

        # Calculate costs for a part
        breakdown = engine.calculate_cost(part_specification)
        print(f"Material: ${breakdown.material_cost}")
        print(f"Labor: ${breakdown.labor_cost}")
        print(f"Total: ${breakdown.total_cost}")
    """

    def __init__(
        self,
        material_costs: dict[Material, MaterialCost],
        process_costs: dict[ManufacturingProcess, ProcessCost],
    ):
        """Initialize with cost data."""
        self.material_costs = material_costs
        self.process_costs = process_costs

    def calculate_cost(self, spec: PartSpecification) -> CostBreakdown:
        """
        Calculate the total manufacturing cost for a part.

        Args:
            spec: Complete part specification

        Returns:
            Detailed cost breakdown

        Raises:
            ValueError: If material or process not supported
        """
        if spec.material not in self.material_costs:
            raise ValueError(f"Unsupported material: {spec.material}")
        if spec.process not in self.process_costs:
            raise ValueError(f"Unsupported process: {spec.process}")

        material_cost_info = self.material_costs[spec.material]
        process_cost_info = self.process_costs[spec.process]

        # Calculate material cost
        material_cost = self._calculate_material_cost(spec, material_cost_info)

        # Calculate labor cost
        labor_cost = self._calculate_labor_cost(spec, process_cost_info)

        # Calculate setup costs
        setup_cost = material_cost_info.setup_cost + (
            process_cost_info.hourly_rate
            * Decimal(str(process_cost_info.setup_time_hours))
        )

        # Calculate complexity adjustment
        complexity_adjustment = self._calculate_complexity_adjustment(spec, labor_cost)

        return CostBreakdown.create(
            material_cost=material_cost,
            labor_cost=labor_cost,
            setup_cost=setup_cost,
            complexity_adjustment=complexity_adjustment,
        )

    def _calculate_material_cost(
        self, spec: PartSpecification, material_cost_info: MaterialCost
    ) -> Decimal:
        """Calculate cost of materials including waste."""
        volume = Decimal(str(spec.dimensions.volume_cm3))
        base_cost = volume * material_cost_info.cost_per_cm3
        return base_cost * Decimal(str(material_cost_info.waste_factor))

    def _calculate_labor_cost(
        self, spec: PartSpecification, process_cost_info: ProcessCost
    ) -> Decimal:
        """Calculate labor cost based on estimated time."""
        # Base time calculation (simplified heuristic)
        base_time_hours = self._estimate_processing_time(spec)

        # Apply complexity multiplier
        complexity_multiplier = self._get_complexity_multiplier(
            spec.geometric_complexity_score, process_cost_info.complexity_multiplier
        )

        total_time = base_time_hours * complexity_multiplier
        return process_cost_info.hourly_rate * Decimal(str(total_time))

    def _estimate_processing_time(self, spec: PartSpecification) -> float:
        """
        Estimate manufacturing processing time using heuristic algorithms.

        This function implements simplified time estimation based on part geometry
        and manufacturing process. In production systems, this would typically be
        replaced with more sophisticated models including:
        - CAD geometry analysis
        - Historical manufacturing data
        - Machine learning time prediction models
        - Process simulation results

        Current Heuristics:
        - CNC: Time scales with surface area (more cutting) + some volume factor
        - 3D Printing: Time scales with volume (material deposition) + height (layers)
        - Cutting: Time scales with perimeter/area being cut
        - Default: Conservative volume-based estimation

        Args:
            spec: Part specification with dimensions and process

        Returns:
            Estimated processing time in hours
        """
        # Base time calculation depends on process type and part size
        volume_factor = spec.dimensions.volume_cm3 / 100  # Normalize volume
        surface_area_factor = spec.dimensions.surface_area_cm2 / 1000  # Normalize area

        if spec.process == ManufacturingProcess.CNC:
            # CNC time depends more on surface area and complexity
            return 0.5 + (surface_area_factor * 0.8) + (volume_factor * 0.2)
        elif spec.process == ManufacturingProcess.THREE_D_PRINTING:
            # 3D printing time depends mainly on volume and height
            height_factor = spec.dimensions.height_mm / 100
            return 1.0 + (volume_factor * 0.1) + (height_factor * 0.5)
        elif spec.process in [
            ManufacturingProcess.SHEET_CUTTING,
            ManufacturingProcess.LASER_CUTTING,
        ]:
            # Cutting processes depend on perimeter/area
            return 0.2 + (surface_area_factor * 0.3)
        else:
            # Default estimation
            return 1.0 + (volume_factor * 0.5)

    def _get_complexity_multiplier(
        self, complexity_score: float, complexity_map: dict[float, float]
    ) -> float:
        """Get complexity multiplier for the given score."""
        # Find the closest complexity score in the map
        if complexity_score in complexity_map:
            return complexity_map[complexity_score]

        # Linear interpolation between closest values
        scores = sorted(complexity_map.keys())
        if complexity_score <= scores[0]:
            return complexity_map[scores[0]]
        if complexity_score >= scores[-1]:
            return complexity_map[scores[-1]]

        # Find surrounding scores
        lower = max(s for s in scores if s <= complexity_score)
        upper = min(s for s in scores if s >= complexity_score)

        if lower == upper:
            return complexity_map[lower]

        # Linear interpolation
        ratio = (complexity_score - lower) / (upper - lower)
        return complexity_map[lower] + ratio * (
            complexity_map[upper] - complexity_map[lower]
        )

    def _calculate_complexity_adjustment(
        self, spec: PartSpecification, base_labor_cost: Decimal
    ) -> Decimal:
        """Calculate additional cost adjustments for complexity."""
        # High complexity parts may require additional tooling, setup, or QC
        if spec.geometric_complexity_score >= 4.0:
            return base_labor_cost * Decimal("0.25")  # 25% surcharge
        elif spec.geometric_complexity_score >= 3.0:
            return base_labor_cost * Decimal("0.10")  # 10% surcharge
        else:
            return Decimal("0")
