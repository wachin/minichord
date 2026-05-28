from PyQt6.QtWidgets import QComboBox

from minichord.settings import DEFAULT_LANGUAGE
from minichord.ui.preferences_dialog import PreferencesDialog


def test_preferences_dialog_selects_saved_language(qtbot):
    dialog = PreferencesDialog(language="es")
    qtbot.addWidget(dialog)

    combo = dialog.findChild(QComboBox, "languageComboBox")

    assert combo is not None
    assert combo.currentData() == "es"
    assert dialog.selected_language() == "es"


def test_preferences_dialog_falls_back_to_system_language(qtbot):
    dialog = PreferencesDialog(language="unknown")
    qtbot.addWidget(dialog)

    assert dialog.selected_language() == DEFAULT_LANGUAGE
