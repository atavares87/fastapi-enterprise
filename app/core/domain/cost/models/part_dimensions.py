"""Part Dimensions Model - Single Responsibility: Physical dimensions and geometric calculations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PartDimensions:
    """Physical dimensions of a manufacturing part with automatic calculations."""

    length_mm: float
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        """Validate dimensions are positive."""
        if any(dim <= 0 for dim in [self.length_mm, self.width_mm, self.height_mm]):
            raise ValueError("All dimensions must be positive")

    @property
    def volume_cm3(self) -> float:
        """Calculate part volume in cubic centimeters."""
        return (self.length_mm * self.width_mm * self.height_mm) / 1000

    @property
    def surface_area_cm2(self) -> float:
        """Calculate total surface area in square centimeters."""
        length, width, height = (
            self.length_mm / 10,
            self.width_mm / 10,
            self.height_mm / 10,
        )
        return 2 * (length * width + length * height + width * height)

    @property
    def bounding_box_diagonal_mm(self) -> float:
        """Calculate 3D diagonal of the part's bounding box."""
        return float((self.length_mm**2 + self.width_mm**2 + self.height_mm**2) ** 0.5)
