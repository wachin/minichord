"""Application preferences dialog."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
    QWidget,
)

from minichord.settings import DEFAULT_LANGUAGE


LANGUAGE_CODES = (DEFAULT_LANGUAGE, "en", "es")


class PreferencesDialog(QDialog):
    """Edit application-level preferences."""

    def __init__(self, language: str = DEFAULT_LANGUAGE, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Preferences"))
        self.setMinimumWidth(360)

        self._language_combo = QComboBox()
        self._language_combo.setObjectName("languageComboBox")
        language_labels = {
            DEFAULT_LANGUAGE: self.tr("System default"),
            "en": self.tr("English"),
            "es": self.tr("Spanish"),
        }
        for language_code in LANGUAGE_CODES:
            self._language_combo.addItem(language_labels[language_code], language_code)

        selected_index = self._language_combo.findData(language or DEFAULT_LANGUAGE)
        if selected_index < 0:
            selected_index = self._language_combo.findData(DEFAULT_LANGUAGE)
        self._language_combo.setCurrentIndex(max(0, selected_index))

        form_layout = QFormLayout()
        form_layout.addRow(self.tr("Language"), self._language_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form_layout)
        layout.addWidget(buttons)

    def selected_language(self) -> str:
        """Return the selected language code."""
        value = self._language_combo.currentData()
        return str(value) if value else DEFAULT_LANGUAGE
