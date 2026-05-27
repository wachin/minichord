"""Page geometry primitives for the first miniChord editor surface."""

from __future__ import annotations

from dataclasses import dataclass


MM_PER_INCH = 25.4
DEFAULT_SCREEN_DPI = 96.0

PAGE_SIZES_MM: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
}


@dataclass(frozen=True, slots=True)
class PageMargins:
    """Page margins in millimeters."""

    left: float = 20.0
    top: float = 20.0
    right: float = 20.0
    bottom: float = 20.0

    def validate_for(self, width_mm: float, height_mm: float) -> None:
        if min(self.left, self.top, self.right, self.bottom) < 0:
            raise ValueError("Page margins cannot be negative.")
        if self.left + self.right >= width_mm:
            raise ValueError("Horizontal margins leave no writable page area.")
        if self.top + self.bottom >= height_mm:
            raise ValueError("Vertical margins leave no writable page area.")


@dataclass(frozen=True, slots=True)
class PageLayout:
    """Physical page layout used by the prototype editor."""

    page_size: str = "A4"
    orientation: str = "portrait"
    margins: PageMargins = PageMargins()

    @property
    def size_mm(self) -> tuple[float, float]:
        try:
            width, height = PAGE_SIZES_MM[self.page_size]
        except KeyError as exc:
            raise ValueError(f"Unsupported page size: {self.page_size}") from exc

        if self.orientation == "portrait":
            return width, height
        if self.orientation == "landscape":
            return height, width
        raise ValueError(f"Unsupported orientation: {self.orientation}")

    @property
    def writable_size_mm(self) -> tuple[float, float]:
        width, height = self.size_mm
        self.margins.validate_for(width, height)
        return (
            width - self.margins.left - self.margins.right,
            height - self.margins.top - self.margins.bottom,
        )

    def page_size_px(
        self,
        dpi: float = DEFAULT_SCREEN_DPI,
        zoom: float = 1.0,
    ) -> tuple[int, int]:
        width, height = self.size_mm
        return mm_to_px(width, dpi, zoom), mm_to_px(height, dpi, zoom)

    def margin_px(
        self,
        dpi: float = DEFAULT_SCREEN_DPI,
        zoom: float = 1.0,
    ) -> tuple[int, int, int, int]:
        self.writable_size_mm
        return (
            mm_to_px(self.margins.left, dpi, zoom),
            mm_to_px(self.margins.top, dpi, zoom),
            mm_to_px(self.margins.right, dpi, zoom),
            mm_to_px(self.margins.bottom, dpi, zoom),
        )


def mm_to_px(mm: float, dpi: float = DEFAULT_SCREEN_DPI, zoom: float = 1.0) -> int:
    """Convert millimeters to device-independent pixels."""
    return round((mm / MM_PER_INCH) * dpi * zoom)
