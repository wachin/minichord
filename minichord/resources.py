"""Shared application resources."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon


APP_ICON_PATH = Path(__file__).with_name("assets") / "minichord.svg"


def app_icon() -> QIcon:
    """Return the miniChord application icon."""
    return QIcon(str(APP_ICON_PATH))
