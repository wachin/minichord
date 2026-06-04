"""Page geometry primitives for the first ChordPages editor surface."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Literal


MM_PER_INCH = 25.4
DEFAULT_SCREEN_DPI = 96.0
DEFAULT_TEXT_LINE_HEIGHT_MM = 4.2
CHORDPAGES_PAGE_SIZE = "63 x 110 mm"
DEFAULT_PAGE_SIZE = CHORDPAGES_PAGE_SIZE

PAGE_SIZES_MM: dict[str, tuple[float, float]] = {
    CHORDPAGES_PAGE_SIZE: (63.0, 110.0),
    "A4": (210.0, 297.0),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
}
CUSTOM_PAGE_SIZE = "Custom"
MarginPresetName = Literal["normal", "narrow", "moderate", "wide", "mirrored"]


@dataclass(frozen=True, slots=True)
class PageMargins:
    """Page margins in millimeters."""

    left: float = 20.0
    top: float = 20.0
    right: float = 20.0
    bottom: float = 20.0
    gutter: float = 0.0
    header_spacing: float = 0.0
    footer_spacing: float = 0.0
    mirrored: bool = False

    @classmethod
    def from_preset(cls, preset_name: str) -> "PageMargins":
        """Build margins from a named preset."""
        normalized_name = _normalize_margin_preset_name(preset_name)
        try:
            return MARGIN_PRESETS_MM[normalized_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported margin preset: {preset_name}") from exc

    def effective_for_page(self, page_number: int = 1) -> "PageMargins":
        """Return margins after applying mirror and gutter rules."""
        _validate_page_number(page_number)
        left = self.left
        right = self.right
        if self.mirrored and page_number % 2 == 0:
            left, right = right, left

        if self.mirrored and page_number % 2 == 0:
            right += self.gutter
        else:
            left += self.gutter

        return replace(
            self,
            left=left,
            right=right,
            gutter=0.0,
            mirrored=False,
        )

    def validate_for(
        self,
        width_mm: float,
        height_mm: float,
        page_number: int = 1,
    ) -> None:
        effective_margins = self.effective_for_page(page_number)
        if (
            min(
                effective_margins.left,
                effective_margins.top,
                effective_margins.right,
                effective_margins.bottom,
                self.gutter,
                self.header_spacing,
                self.footer_spacing,
            )
            < 0
        ):
            raise ValueError("Page margins cannot be negative.")
        if effective_margins.left + effective_margins.right >= width_mm:
            raise ValueError("Horizontal margins leave no writable page area.")
        if effective_margins.top + effective_margins.bottom >= height_mm:
            raise ValueError("Vertical margins leave no writable page area.")


DEFAULT_PAGE_MARGINS = PageMargins(left=3.0, top=3.0, right=3.0, bottom=3.0)


MARGIN_PRESETS_MM: MappingProxyType[str, PageMargins] = MappingProxyType(
    {
        "normal": PageMargins(left=20.0, top=20.0, right=20.0, bottom=20.0),
        "narrow": PageMargins(left=12.7, top=12.7, right=12.7, bottom=12.7),
        "moderate": PageMargins(left=19.1, top=25.4, right=19.1, bottom=25.4),
        "wide": PageMargins(left=25.4, top=25.4, right=25.4, bottom=25.4),
        "mirrored": PageMargins(
            left=25.0,
            top=20.0,
            right=20.0,
            bottom=20.0,
            mirrored=True,
        ),
    }
)


def margin_preset_names() -> tuple[str, ...]:
    """Return supported margin preset names."""
    return tuple(MARGIN_PRESETS_MM.keys())


def page_size_names() -> tuple[str, ...]:
    """Return supported named page sizes."""
    return tuple(PAGE_SIZES_MM.keys())


@dataclass(frozen=True, slots=True)
class PageLayout:
    """Physical page layout used by the prototype editor."""

    page_size: str = DEFAULT_PAGE_SIZE
    orientation: str = "portrait"
    margins: PageMargins = DEFAULT_PAGE_MARGINS
    custom_size_mm: tuple[float, float] | None = None
    printer_margins: PageMargins = PageMargins(0.0, 0.0, 0.0, 0.0)

    @property
    def size_mm(self) -> tuple[float, float]:
        width, height = self._base_size_mm()

        if self.orientation == "portrait":
            return width, height
        if self.orientation == "landscape":
            return height, width
        raise ValueError(f"Unsupported orientation: {self.orientation}")

    def _base_size_mm(self) -> tuple[float, float]:
        if self.page_size == CUSTOM_PAGE_SIZE:
            if self.custom_size_mm is None:
                raise ValueError("Custom page size requires dimensions.")
            width, height = self.custom_size_mm
            if width <= 0 or height <= 0:
                raise ValueError("Custom page dimensions must be positive.")
            return width, height

        if self.custom_size_mm is not None:
            raise ValueError("Custom dimensions require Custom page size.")

        try:
            return PAGE_SIZES_MM[self.page_size]
        except KeyError as exc:
            raise ValueError(f"Unsupported page size: {self.page_size}") from exc

    def with_margin_preset(self, preset_name: str) -> "PageLayout":
        """Return a copy with margins from a named preset."""
        return replace(self, margins=PageMargins.from_preset(preset_name))

    @property
    def writable_size_mm(self) -> tuple[float, float]:
        return self.writable_size_for_page_mm()

    @property
    def printable_size_mm(self) -> tuple[float, float]:
        return self.printable_size_for_page_mm()

    def effective_margins(self, page_number: int = 1) -> PageMargins:
        """Return margins after applying page-number-dependent rules."""
        width, height = self.size_mm
        self.margins.validate_for(width, height, page_number)
        return self.margins.effective_for_page(page_number)

    def effective_printer_margins(self, page_number: int = 1) -> PageMargins:
        """Return printer margins after applying page-number-dependent rules."""
        width, height = self.size_mm
        self.printer_margins.validate_for(width, height, page_number)
        return self.printer_margins.effective_for_page(page_number)

    def writable_size_for_page_mm(
        self,
        page_number: int = 1,
    ) -> tuple[float, float]:
        width, height = self.size_mm
        margins = self.effective_margins(page_number)
        return (
            width - margins.left - margins.right,
            height - margins.top - margins.bottom,
        )

    def printable_size_for_page_mm(
        self,
        page_number: int = 1,
    ) -> tuple[float, float]:
        width, height = self.size_mm
        printer_margins = self.effective_printer_margins(page_number)
        return (
            width - printer_margins.left - printer_margins.right,
            height - printer_margins.top - printer_margins.bottom,
        )

    def rows_per_column(
        self,
        line_height_mm: float = DEFAULT_TEXT_LINE_HEIGHT_MM,
        page_number: int = 1,
    ) -> int:
        """Return how many text rows fit in the writable page height."""
        if line_height_mm <= 0:
            raise ValueError("Line height must be positive.")
        _, writable_height = self.writable_size_for_page_mm(page_number)
        return max(1, int(writable_height // line_height_mm))

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
        page_number: int = 1,
    ) -> tuple[int, int, int, int]:
        margins = self.effective_margins(page_number)
        return (
            mm_to_px(margins.left, dpi, zoom),
            mm_to_px(margins.top, dpi, zoom),
            mm_to_px(margins.right, dpi, zoom),
            mm_to_px(margins.bottom, dpi, zoom),
        )

    def printer_margin_px(
        self,
        dpi: float = DEFAULT_SCREEN_DPI,
        zoom: float = 1.0,
        page_number: int = 1,
    ) -> tuple[int, int, int, int]:
        printer_margins = self.effective_printer_margins(page_number)
        return (
            mm_to_px(printer_margins.left, dpi, zoom),
            mm_to_px(printer_margins.top, dpi, zoom),
            mm_to_px(printer_margins.right, dpi, zoom),
            mm_to_px(printer_margins.bottom, dpi, zoom),
        )

    def has_printer_safe_area(self, page_number: int = 1) -> bool:
        printer_margins = self.effective_printer_margins(page_number)
        return any(
            margin > 0
            for margin in (
                printer_margins.left,
                printer_margins.top,
                printer_margins.right,
                printer_margins.bottom,
            )
        )


def mm_to_px(mm: float, dpi: float = DEFAULT_SCREEN_DPI, zoom: float = 1.0) -> int:
    """Convert millimeters to device-independent pixels."""
    return round((mm / MM_PER_INCH) * dpi * zoom)


def _normalize_margin_preset_name(preset_name: str) -> str:
    return preset_name.strip().lower()


def _validate_page_number(page_number: int) -> None:
    if page_number < 1:
        raise ValueError("Page number must be at least 1.")
