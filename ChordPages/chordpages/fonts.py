"""Font helpers for the ChordPages text editing surface."""

from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtGui import QFont, QFontDatabase


DEFAULT_EDITOR_FONT_SIZE_PT = 6.5
PREFERRED_MONOSPACE_FAMILIES = (
    "DejaVu Sans Mono",
    "Liberation Mono",
    "Noto Sans Mono",
    "Monospace",
    "Courier 10 Pitch",
    "Courier New",
)


def default_editor_font() -> QFont:
    """Return the default monospaced font for song/chord editing."""
    return make_editor_font(
        resolve_default_monospace_family(),
        DEFAULT_EDITOR_FONT_SIZE_PT,
    )


def make_editor_font(family: str, point_size: float) -> QFont:
    """Build a normalized editor font from a family and point size."""
    font = QFont(resolve_font_family(family))
    font.setPointSizeF(normalized_font_size(point_size))
    font.setStyleHint(QFont.StyleHint.TypeWriter)
    font.setFixedPitch(True)
    return font


def normalized_font_size(point_size: float) -> float:
    """Return a usable editor font size in points."""
    try:
        size = float(point_size)
    except (TypeError, ValueError):
        return DEFAULT_EDITOR_FONT_SIZE_PT
    if size <= 0:
        return DEFAULT_EDITOR_FONT_SIZE_PT
    return size


def resolve_default_monospace_family(
    preferred_families: Iterable[str] = PREFERRED_MONOSPACE_FAMILIES,
) -> str:
    """Return a monospaced family available on the current system."""
    families = QFontDatabase.families()
    families_by_name = {family.casefold(): family for family in families}

    for preferred_family in preferred_families:
        family = families_by_name.get(preferred_family.casefold())
        if family is not None:
            return family

    for family in families:
        if QFontDatabase.isFixedPitch(family):
            return family

    fallback = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
    return fallback or "monospace"


def resolve_font_family(family: str) -> str:
    """Return the requested font family when available, otherwise the default."""
    requested_family = family.strip()
    if not requested_family:
        return resolve_default_monospace_family()

    families_by_name = {
        available_family.casefold(): available_family
        for available_family in QFontDatabase.families()
    }
    return families_by_name.get(
        requested_family.casefold(),
        resolve_default_monospace_family(),
    )
