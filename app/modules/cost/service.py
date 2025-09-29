"""
Cost Service Layer - Manufacturing Cost Calculation Application Services

This service layer provides the application interface for cost calculations,
orchestrating domain objects and implementing business use cases. Following
hexagonal architecture, it acts as the boundary between external systems
(web APIs, databases) and the core domain logic.

Key Responsibilities:
- 🎯 Orchestrate cost calculation workflows and business use cases
- 📄 Manage default cost data and pricing configurations
- 🔄 Provide clean API for external systems (controllers, other services)
- ⚡ Handle error translation from domain to application layer
- 📊 Offer additional business operations (cost ranges, material lists)

Service Operations:
- calculate_manufacturing_cost(): Main cost calculation use case
- estimate_cost_range(): Provide min/max cost estimates for uncertainty
- get_supported_materials/processes(): Discover available options

Example Usage:
    service = CostCalculationService()

    # Calculate exact cost
    breakdown = service.calculate_manufacturing_cost(part_spec)
    print(f"Total cost: ${breakdown.total_cost}")

    # Get cost range for uncertain complexity
    min_cost, max_cost = service.estimate_cost_range(part_spec)
    print(f"Cost range: ${min_cost} - ${max_cost}")

    # Discover available options
    materials = service.get_supported_materials()
    processes = service.get_supported_processes()
"""

from decimal import Decimal

from app.modules.cost.domain import (
    CostBreakdown,
    CostCalculationEngine,
    ManufacturingProcess,
    Material,
    MaterialCost,
    PartSpecification,
    ProcessCost,
)


class CostCalculationService:
    """
    Application service for manufacturing cost calculations and pricing operations.

    This service encapsulates all cost-related business use cases and provides
    a clean, stable API for external systems. It manages the cost calculation
    engine with realistic material and process cost data, handles error translation,
    and offers additional business operations like cost range estimation.

    The service is initialized with default cost databases that reflect current
    market pricing for materials and realistic labor rates for manufacturing processes.
    In production, these would typically be loaded from external pricing services
    or configuration databases.

    Key Features:
    - 💰 Comprehensive cost calculation with detailed breakdowns
    - 📊 Cost range estimation for uncertain specifications
    - 🗺️ Discovery of supported materials and processes
    - ⚡ Fast calculation suitable for real-time quoting systems
    - 🔒 Robust error handling with meaningful error messages

    Thread Safety: This service is stateless and thread-safe after initialization.
    Multiple instances can be created or a single instance can be shared safely.
    """

    def __init__(self) -> None:
        """
        Initialize the cost calculation service with default pricing data.

        The service is configured with realistic cost databases containing:
        - Material costs with current market pricing per cm³
        - Process costs with typical manufacturing labor rates
        - Complexity multipliers based on manufacturing difficulty
        - Setup costs reflecting real-world tooling and preparation times

        Cost data is loaded from internal defaults but could be extended
        to load from external pricing services, databases, or configuration files.
        """
        self.engine = CostCalculationEngine(
            material_costs=self._get_default_material_costs(),
            process_costs=self._get_default_process_costs(),
        )

    def calculate_manufacturing_cost(self, spec: PartSpecification) -> CostBreakdown:
        """
        Calculate the manufacturing cost for a given part specification.

        This is the main use case for cost calculation. It takes a complete
        part specification and returns a detailed cost breakdown.

        Args:
            spec: Complete part specification including dimensions, material,
                 process, and complexity score

        Returns:
            Detailed cost breakdown with material, labor, setup, and total costs

        Raises:
            ValueError: If the specification contains unsupported materials or processes
        """
        try:
            return self.engine.calculate_cost(spec)
        except ValueError as e:
            # Re-raise domain errors as service errors
            raise ValueError(f"Cost calculation failed: {str(e)}") from e

    def get_supported_materials(self) -> list[Material]:
        """
        Get list of supported materials.

        Returns:
            List of all materials that can be used for cost calculation
        """
        return list(self.engine.material_costs.keys())

    def get_supported_processes(self) -> list[ManufacturingProcess]:
        """
        Get list of supported manufacturing processes.

        Returns:
            List of all processes that can be used for cost calculation
        """
        return list(self.engine.process_costs.keys())

    def estimate_cost_range(self, spec: PartSpecification) -> tuple[Decimal, Decimal]:
        """
        Estimate cost range by varying geometric complexity from simple to very complex.

        This method is valuable for early-stage cost estimation when the exact
        geometric complexity isn't known. It calculates costs using the minimum
        (1.0 - simple geometry) and maximum (5.0 - very complex geometry)
        complexity scores while keeping all other parameters constant.

        Use Cases:
        - Early project cost estimation and budgeting
        - Feasibility analysis for design alternatives
        - Risk assessment for manufacturing cost overruns
        - Customer quote ranges before final design completion

        Args:
            spec: Part specification with tentative complexity score
                 (the complexity score will be overridden during calculation)

        Returns:
            Tuple of (minimum_cost, maximum_cost) representing the cost range
            based on complexity variation from 1.0 to 5.0

        Example:
            min_cost, max_cost = service.estimate_cost_range(rough_spec)
            print(f"Estimated cost range: ${min_cost} - ${max_cost}")
            print(f"Cost uncertainty: {(max_cost - min_cost) / min_cost * 100:.1f}%")
        """
        # Calculate with minimum complexity (1.0)
        min_spec = PartSpecification(
            dimensions=spec.dimensions,
            geometric_complexity_score=1.0,
            material=spec.material,
            process=spec.process,
        )
        min_cost = self.calculate_manufacturing_cost(min_spec).total_cost

        # Calculate with maximum complexity (5.0)
        max_spec = PartSpecification(
            dimensions=spec.dimensions,
            geometric_complexity_score=5.0,
            material=spec.material,
            process=spec.process,
        )
        max_cost = self.calculate_manufacturing_cost(max_spec).total_cost

        return min_cost, max_cost

    def _get_default_material_costs(self) -> dict[Material, MaterialCost]:
        """
        Configure default material cost database with realistic market pricing.

        This method provides current material cost estimates based on 2024 market
        pricing for manufacturing materials. In production systems, this data would
        typically be:
        - Loaded from external material pricing APIs
        - Updated from supplier cost databases
        - Managed through configuration management systems
        - Refreshed periodically to reflect market changes

        Cost Structure:
        - cost_per_cm³: Base material cost per cubic centimeter
        - waste_factor: Manufacturing waste multiplier (1.15 = 15% waste)
        - setup_cost: One-time setup and preparation costs

        Pricing Categories:
        - Plastics ($0.04-$0.06/cm³): Low cost, suitable for prototyping and consumer goods
        - Common Metals ($0.08-$0.25/cm³): Aluminum, steel, stainless steel for general use
        - Specialty Metals ($0.35-$2.50/cm³): Brass, copper, titanium for specialized applications
        - Advanced Materials ($1.80/cm³): Carbon fiber for high-performance applications

        Returns:
            Dictionary mapping Material enum values to MaterialCost configurations
            with current market-based pricing and realistic waste factors
        """
        return {
            Material.ALUMINUM: MaterialCost(
                cost_per_cm3=Decimal("0.15"),  # $0.15 per cm³
                waste_factor=1.15,  # 15% waste
                setup_cost=Decimal("25.00"),  # $25 setup
            ),
            Material.STEEL: MaterialCost(
                cost_per_cm3=Decimal("0.08"),  # $0.08 per cm³
                waste_factor=1.20,  # 20% waste
                setup_cost=Decimal("30.00"),  # $30 setup
            ),
            Material.STAINLESS_STEEL: MaterialCost(
                cost_per_cm3=Decimal("0.25"),  # $0.25 per cm³
                waste_factor=1.15,  # 15% waste
                setup_cost=Decimal("35.00"),  # $35 setup
            ),
            Material.PLASTIC_ABS: MaterialCost(
                cost_per_cm3=Decimal("0.05"),  # $0.05 per cm³
                waste_factor=1.10,  # 10% waste
                setup_cost=Decimal("10.00"),  # $10 setup
            ),
            Material.PLASTIC_PLA: MaterialCost(
                cost_per_cm3=Decimal("0.04"),  # $0.04 per cm³
                waste_factor=1.05,  # 5% waste
                setup_cost=Decimal("5.00"),  # $5 setup
            ),
            Material.PLASTIC_PETG: MaterialCost(
                cost_per_cm3=Decimal("0.06"),  # $0.06 per cm³
                waste_factor=1.08,  # 8% waste
                setup_cost=Decimal("8.00"),  # $8 setup
            ),
            Material.TITANIUM: MaterialCost(
                cost_per_cm3=Decimal("2.50"),  # $2.50 per cm³
                waste_factor=1.25,  # 25% waste
                setup_cost=Decimal("100.00"),  # $100 setup
            ),
            Material.BRASS: MaterialCost(
                cost_per_cm3=Decimal("0.35"),  # $0.35 per cm³
                waste_factor=1.18,  # 18% waste
                setup_cost=Decimal("40.00"),  # $40 setup
            ),
            Material.COPPER: MaterialCost(
                cost_per_cm3=Decimal("0.45"),  # $0.45 per cm³
                waste_factor=1.20,  # 20% waste
                setup_cost=Decimal("45.00"),  # $45 setup
            ),
            Material.CARBON_FIBER: MaterialCost(
                cost_per_cm3=Decimal("1.80"),  # $1.80 per cm³
                waste_factor=1.30,  # 30% waste
                setup_cost=Decimal("80.00"),  # $80 setup
            ),
        }

    def _get_default_process_costs(self) -> dict[ManufacturingProcess, ProcessCost]:
        """
        Configure default manufacturing process cost database with realistic labor rates.

        This method provides typical manufacturing process costs based on industry
        standards and current labor markets. The configuration includes hourly rates,
        setup times, and complexity multipliers that reflect real-world manufacturing.

        Process Categories & Characteristics:

        🔩 Subtractive Manufacturing (CNC, Cutting):
        - Higher hourly rates ($65-$90/hour) due to skilled operation
        - Moderate complexity sensitivity
        - Setup times vary by process complexity

        🖨️ Additive Manufacturing (3D Printing):
        - Lower hourly rates ($25/hour) due to automation
        - Better complexity handling (lower multipliers)
        - Minimal setup time requirements

        🏭 High-Volume Processes (Injection Molding):
        - Higher rates ($120/hour) including tooling amortization
        - Very high setup times (8+ hours) for tooling
        - Extreme complexity sensitivity for mold design

        Complexity Multiplier Strategy:
        - 1.0: Simple geometry (basic shapes, minimal features)
        - 1.3-1.7: Moderate complexity (holes, slots, standard features)
        - 2.2-3.0: High complexity (tight tolerances, intricate features)
        - 3.5-5.0: Extreme complexity (injection molding with complex molds)

        Returns:
            Dictionary mapping ManufacturingProcess enum values to ProcessCost
            configurations with realistic hourly rates and complexity handling
        """
        # Standard complexity multipliers for traditional manufacturing processes
        # These reflect typical time increases due to geometric complexity
        standard_complexity = {
            1.0: 1.0,  # Simple geometry - basic shapes, minimal setup
            2.0: 1.3,  # Moderate complexity - standard features, holes, slots
            3.0: 1.7,  # Complex geometry - multiple features, tighter tolerances
            4.0: 2.2,  # Very complex - intricate details, difficult access angles
            5.0: 3.0,  # Extremely complex - maximum manufacturing difficulty
        }

        return {
            ManufacturingProcess.CNC: ProcessCost(
                hourly_rate=Decimal("85.00"),  # $85/hour
                setup_time_hours=1.5,  # 1.5 hours setup
                complexity_multiplier=standard_complexity,
            ),
            ManufacturingProcess.THREE_D_PRINTING: ProcessCost(
                hourly_rate=Decimal("25.00"),  # $25/hour (mostly automated)
                setup_time_hours=0.5,  # 0.5 hours setup
                complexity_multiplier={
                    1.0: 1.0,  # 3D printing handles complexity well
                    2.0: 1.1,
                    3.0: 1.3,
                    4.0: 1.6,
                    5.0: 2.0,
                },
            ),
            ManufacturingProcess.SHEET_CUTTING: ProcessCost(
                hourly_rate=Decimal("65.00"),  # $65/hour
                setup_time_hours=0.8,  # 0.8 hours setup
                complexity_multiplier={
                    1.0: 1.0,  # Sheet cutting is less affected by 3D complexity
                    2.0: 1.2,
                    3.0: 1.4,
                    4.0: 1.7,
                    5.0: 2.1,
                },
            ),
            ManufacturingProcess.TUBE_BENDING: ProcessCost(
                hourly_rate=Decimal("70.00"),  # $70/hour
                setup_time_hours=1.2,  # 1.2 hours setup
                complexity_multiplier=standard_complexity,
            ),
            ManufacturingProcess.INJECTION_MOLDING: ProcessCost(
                hourly_rate=Decimal(
                    "120.00"
                ),  # $120/hour (including tooling amortization)
                setup_time_hours=8.0,  # 8 hours setup (tooling)
                complexity_multiplier={
                    1.0: 1.0,  # Injection molding has high setup but scales well
                    2.0: 1.5,
                    3.0: 2.2,
                    4.0: 3.5,
                    5.0: 5.0,  # Very complex molds are expensive
                },
            ),
            ManufacturingProcess.LASER_CUTTING: ProcessCost(
                hourly_rate=Decimal("75.00"),  # $75/hour
                setup_time_hours=0.3,  # 0.3 hours setup
                complexity_multiplier={
                    1.0: 1.0,  # Laser cutting handles complexity efficiently
                    2.0: 1.1,
                    3.0: 1.3,
                    4.0: 1.6,
                    5.0: 2.0,
                },
            ),
            ManufacturingProcess.WATERJET_CUTTING: ProcessCost(
                hourly_rate=Decimal("90.00"),  # $90/hour
                setup_time_hours=0.5,  # 0.5 hours setup
                complexity_multiplier={
                    1.0: 1.0,  # Waterjet similar to laser but slower
                    2.0: 1.2,
                    3.0: 1.4,
                    4.0: 1.7,
                    5.0: 2.2,
                },
            ),
        }
