"""Application bootstrap for miniChord."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PyQt6.QtWidgets import QApplication

from minichord.main_window import MainWindow


def build_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create or reuse the QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else sys.argv)

    app.setApplicationName("miniChord")
    app.setOrganizationName("miniChord")
    return app


def main(argv: Sequence[str] | None = None) -> int:
    """Start the miniChord GUI application."""
    app = build_application(argv)
    window = MainWindow()
    window.show()
    return app.exec()
