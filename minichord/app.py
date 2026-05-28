"""Application bootstrap for miniChord."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from minichord import __version__
from minichord.i18n import install_translations
from minichord.main_window import MainWindow
from minichord.resources import app_icon
from minichord.settings import APPLICATION_NAME, ORGANIZATION_NAME, SettingsManager
from minichord.theme import apply_theme


def build_application(
    argv: Sequence[str] | None = None,
    settings: SettingsManager | None = None,
) -> QApplication:
    """Create or reuse the QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else sys.argv)

    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationVersion(__version__)
    app.setWindowIcon(app_icon())
    settings_manager = settings or SettingsManager()
    install_translations(app, settings_manager.language())
    apply_theme(app, settings_manager.theme())
    return app


def main(argv: Sequence[str] | None = None) -> int:
    """Start the miniChord GUI application."""
    app = build_application(argv)
    window = MainWindow(settings=SettingsManager())
    window.show()
    QTimer.singleShot(0, window.show_crash_recovery_dialog)
    return app.exec()
