from pathlib import Path

import pytest
from PyQt6.QtCore import QByteArray, QSize
from PyQt6.QtWidgets import QApplication

from minichord import __version__
from minichord.app import build_application
from minichord.autosave import AutosaveManager
from minichord.backup import BackupManager
from minichord.document import (
    CUSTOM_PAGE_SIZE,
    MiniChordDocument,
    PageLayout,
    PageMargins,
)
from minichord.i18n import install_translations
import minichord.main_window as main_window_module
from minichord.main_window import MainWindow
from minichord.recovery import RecoveryManager
from minichord.resources import APP_ICON_PATH
from minichord.settings import (
    APPLICATION_NAME,
    ORGANIZATION_NAME,
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
    SettingsManager,
)
from minichord.theme import CURRENT_THEME_PROPERTY, EFFECTIVE_THEME_PROPERTY


def temporary_settings(tmp_path) -> SettingsManager:
    return SettingsManager.from_file(tmp_path / "minichord-settings.ini")


def test_application_icon_asset_exists():
    assert APP_ICON_PATH.is_file()
    assert APP_ICON_PATH.suffix == ".svg"
    assert "<svg" in APP_ICON_PATH.read_text(encoding="utf-8")


def test_build_application_sets_application_icon(qtbot, tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_language("en")

    app = build_application([], settings=settings)

    assert app.applicationName() == "miniChord"
    assert app.organizationName() == ORGANIZATION_NAME
    assert app.applicationName() == APPLICATION_NAME
    assert app.applicationVersion() == __version__
    assert not app.windowIcon().isNull()


def test_settings_manager_persists_raw_values(tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_value("ui/theme", "dark")
    settings.sync()

    reloaded = temporary_settings(tmp_path)

    assert reloaded.value("ui/theme") == "dark"


def test_settings_manager_persists_theme(tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_theme(THEME_DARK)
    settings.sync()

    reloaded = temporary_settings(tmp_path)

    assert reloaded.theme() == THEME_DARK


def test_settings_manager_rejects_unknown_theme(tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_theme("unknown")
    settings.sync()

    reloaded = temporary_settings(tmp_path)

    assert reloaded.theme() == THEME_SYSTEM


def test_build_application_applies_saved_theme(qtbot, tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_theme(THEME_DARK)
    settings.sync()

    app = build_application([], settings=settings)

    assert app.property(CURRENT_THEME_PROPERTY) == THEME_DARK
    assert app.property(EFFECTIVE_THEME_PROPERTY) == THEME_DARK
    assert "QScrollArea#pageScrollArea" in app.styleSheet()


def test_settings_manager_tracks_recent_files(tmp_path):
    settings = temporary_settings(tmp_path)
    first_path = tmp_path / "first.mchord"
    second_path = tmp_path / "second.mchord"

    settings.remember_file(first_path)
    settings.remember_file(second_path)
    settings.remember_file(first_path)

    assert settings.recent_files() == [
        first_path.resolve(strict=False),
        second_path.resolve(strict=False),
    ]
    assert settings.last_directory() == tmp_path.resolve(strict=False)


def test_settings_manager_saves_main_window_state(qtbot, tmp_path):
    settings = temporary_settings(tmp_path)
    window = MainWindow(settings=settings)
    qtbot.addWidget(window)
    window.resize(900, 700)

    settings.save_main_window(window)

    assert isinstance(settings.value(SettingsManager.MAIN_WINDOW_GEOMETRY_KEY), QByteArray)
    assert isinstance(settings.value(SettingsManager.MAIN_WINDOW_STATE_KEY), QByteArray)
    assert settings.value(SettingsManager.MAIN_WINDOW_SIZE_KEY) == QSize(900, 700)


def test_main_window_starts_with_page_editor(qtbot, tmp_path):
    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)

    assert window.windowTitle() == "miniChord - Untitled"
    assert not window.windowIcon().isNull()
    assert window.editor.text() == ""


def test_main_window_has_about_dialog_action(qtbot, tmp_path):
    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)

    menu_titles = [action.text() for action in window.menuBar().actions()]
    assert "Help" in menu_titles
    assert window.about_action.text() == "About miniChord"

    help_action = next(action for action in window.menuBar().actions() if action.text() == "Help")
    help_menu = help_action.menu()

    assert help_menu is not None
    assert window.about_action in help_menu.actions()


def test_main_window_exposes_theme_menu(qtbot, tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_theme(THEME_LIGHT)
    window = MainWindow(settings=settings)
    qtbot.addWidget(window)

    menu_titles = [action.text() for action in window.menuBar().actions()]
    assert "View" in menu_titles
    assert window.light_theme_action.isChecked()

    window.dark_theme_action.trigger()

    app = QApplication.instance()
    assert settings.theme() == THEME_DARK
    assert window.dark_theme_action.isChecked()
    assert app is not None
    assert app.property(CURRENT_THEME_PROPERTY) == THEME_DARK


def test_main_window_exposes_zoom_actions(qtbot, tmp_path):
    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)

    assert window.page_view_menu.title() == "Page View"
    assert window.single_page_view_action.text() == "Single Page"
    assert window.multiple_page_view_action.text() == "Multiple Pages"
    assert window.single_page_view_action.isChecked()
    assert not window.multiple_page_view_action.isChecked()
    assert window.zoom_menu.title() == "Zoom"
    assert window.zoom_in_action.text() == "Zoom In"
    assert window.zoom_out_action.text() == "Zoom Out"
    assert window.reset_zoom_action.text() == "Actual Size"
    assert window.fit_width_action.text() == "Fit Width"
    assert window.fit_page_action.text() == "Fit Page"
    assert not window.reset_zoom_action.isEnabled()

    window.zoom_in_action.trigger()

    assert window.editor.zoom() == pytest.approx(1.1)
    assert window.reset_zoom_action.isEnabled()
    assert window.statusBar().currentMessage() == "Zoom: 110%"

    window.zoom_out_action.trigger()

    assert window.editor.zoom() == pytest.approx(1.0)
    assert not window.reset_zoom_action.isEnabled()


def test_main_window_switches_page_view_modes(qtbot, tmp_path):
    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)

    window.multiple_page_view_action.trigger()

    assert window.editor.pages_per_row() == 2
    assert window.multiple_page_view_action.isChecked()
    assert not window.single_page_view_action.isChecked()
    assert window.statusBar().currentMessage() == "Page view: Multiple Pages"

    window.single_page_view_action.trigger()

    assert window.editor.pages_per_row() == 1
    assert window.single_page_view_action.isChecked()
    assert window.statusBar().currentMessage() == "Page view: Single Page"


def test_main_window_zoom_actions_sync_at_supported_limits(qtbot, tmp_path):
    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)

    window.set_zoom(0.01)

    assert window.editor.zoom() == 0.25
    assert not window.zoom_out_action.isEnabled()
    assert window.zoom_in_action.isEnabled()

    window.set_zoom(10.0)

    assert window.editor.zoom() == 4.0
    assert window.zoom_out_action.isEnabled()
    assert not window.zoom_in_action.isEnabled()


def test_main_window_fit_actions_report_zoom(qtbot, monkeypatch, tmp_path):
    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)

    def fake_fit_width():
        window.editor.set_zoom(1.5)
        return window.editor.zoom()

    def fake_fit_page():
        window.editor.set_zoom(0.75)
        return window.editor.zoom()

    monkeypatch.setattr(window.editor, "fit_width", fake_fit_width)
    monkeypatch.setattr(window.editor, "fit_page", fake_fit_page)

    window.fit_width_action.trigger()
    assert window.statusBar().currentMessage() == "Zoom: 150%"

    window.fit_page_action.trigger()
    assert window.statusBar().currentMessage() == "Zoom: 75%"


def test_main_window_exposes_preferences_action(qtbot, tmp_path):
    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)

    menu_titles = [action.text() for action in window.menuBar().actions()]

    assert "Edit" in menu_titles
    assert window.preferences_action.text() == "Preferences..."


def test_about_dialog_shows_version_and_toolkit_details(qtbot, monkeypatch, tmp_path):
    captured = {}

    class FakeMessageBox:
        @staticmethod
        def about(parent, title, text):
            captured["parent"] = parent
            captured["title"] = title
            captured["text"] = text

    monkeypatch.setattr(main_window_module, "QMessageBox", FakeMessageBox)

    window = MainWindow(settings=temporary_settings(tmp_path))
    qtbot.addWidget(window)
    window.show_about_dialog()

    assert captured["parent"] is window
    assert captured["title"] == "About miniChord"
    assert f"miniChord {__version__}" in captured["text"]
    assert "Qt:" in captured["text"]
    assert "PyQt:" in captured["text"]


def test_preferences_dialog_persists_selected_language(qtbot, monkeypatch, tmp_path):
    settings = temporary_settings(tmp_path)

    class FakePreferencesDialog:
        class DialogCode:
            Accepted = 1

        def __init__(self, language, parent):
            self.language = language
            self.parent = parent

        def exec(self):
            return self.DialogCode.Accepted

        def selected_language(self):
            return "es"

    monkeypatch.setattr(main_window_module, "PreferencesDialog", FakePreferencesDialog)
    window = MainWindow(settings=settings)
    qtbot.addWidget(window)

    app = QApplication.instance()
    try:
        window.show_preferences_dialog()
        reloaded = temporary_settings(tmp_path)

        assert reloaded.language() == "es"
        assert window.preferences_action.text() == "Preferencias..."
        assert window.zoom_in_action.text() == "Acercar"
        assert window.fit_width_action.text() == "Ajustar al ancho"
        assert window.page_view_menu.title() == "Vista de página"
        assert window.multiple_page_view_action.text() == "Varias páginas"
        assert window.statusBar().currentMessage() == "Idioma cambiado: Español"
    finally:
        if app is not None:
            install_translations(app, "en")


def test_main_window_saves_mchord_file(qtbot, tmp_path):
    settings = temporary_settings(tmp_path)
    window = MainWindow(settings=settings)
    qtbot.addWidget(window)
    path = Path(tmp_path) / "song.mchord"

    window.editor.set_text("[C]Amazing grace")
    window.save_path(path)

    content = path.read_text(encoding="utf-8")
    assert "format: minichord-song" in content
    assert "[C]Amazing grace" in content
    assert settings.recent_files() == [path.resolve(strict=False)]
    assert settings.last_directory() == tmp_path.resolve(strict=False)


def test_main_window_saves_full_paginated_document(qtbot, tmp_path):
    settings = temporary_settings(tmp_path)
    window = MainWindow(settings=settings)
    qtbot.addWidget(window)
    path = Path(tmp_path) / "long-song.mchord"
    source = "".join(f"[C]Verse line {line_number}\n" for line_number in range(1, 40))
    window.editor.set_page_layout(
        PageLayout(
            page_size=CUSTOM_PAGE_SIZE,
            custom_size_mm=(80.0, 40.0),
            margins=PageMargins(left=5.0, top=5.0, right=5.0, bottom=5.0),
        )
    )

    window.editor.set_text(source)
    window.save_path(path)

    content = path.read_text(encoding="utf-8")
    assert window.editor.page_count() > 1
    assert "[C]Verse line 1" in content
    assert "[C]Verse line 39" in content


def test_main_window_autosaves_modified_document(qtbot, tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    window = MainWindow(
        settings=temporary_settings(tmp_path),
        autosave_manager=autosave_manager,
    )
    qtbot.addWidget(window)

    window.editor.set_text("[G]Blessed assurance")
    draft_path = window.perform_autosave(force=True)

    assert draft_path is not None
    assert draft_path.is_file()
    assert "[G]Blessed assurance" in draft_path.read_text(encoding="utf-8")


def test_main_window_save_clears_existing_autosave(qtbot, tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    window = MainWindow(
        settings=temporary_settings(tmp_path),
        autosave_manager=autosave_manager,
    )
    qtbot.addWidget(window)

    window.editor.set_text("[D]How great")
    draft_path = window.perform_autosave(force=True)
    assert draft_path is not None
    assert draft_path.exists()

    window.save_path(tmp_path / "song.mchord")

    assert not draft_path.exists()


def test_main_window_creates_backup_before_overwriting_file(qtbot, tmp_path):
    backup_manager = BackupManager(tmp_path / "backups")
    window = MainWindow(
        settings=temporary_settings(tmp_path),
        backup_manager=backup_manager,
    )
    qtbot.addWidget(window)
    path = tmp_path / "song.mchord"
    path.write_text("old version\n", encoding="utf-8")

    window.editor.set_text("[A]New version")
    window.save_path(path)

    snapshots = backup_manager.snapshots_for(path)
    assert len(snapshots) == 1
    assert snapshots[0].read_text(encoding="utf-8") == "old version\n"
    assert "[A]New version" in path.read_text(encoding="utf-8")


def test_main_window_recovers_selected_autosave_draft(qtbot, monkeypatch, tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    source_path = tmp_path / "song.mchord"
    autosave_manager.write(
        MiniChordDocument(text="[E]Recovered", title="Recovered"),
        source_path=source_path,
        draft_id="draft-1",
    )
    recovery_manager = RecoveryManager(autosave_manager)
    selected_draft = recovery_manager.autosave_drafts()[0]

    class FakeRecoveryDialog:
        DISCARD_ACTION = "discard"
        RECOVER_ACTION = "recover"

        class DialogCode:
            Accepted = 1

        def __init__(self, drafts, parent):
            self.drafts = drafts
            self.parent = parent

        def exec(self):
            return self.DialogCode.Accepted

        def selected_draft(self):
            return selected_draft

        def selected_action(self):
            return self.RECOVER_ACTION

    monkeypatch.setattr(main_window_module, "RecoveryDialog", FakeRecoveryDialog)
    window = MainWindow(
        settings=temporary_settings(tmp_path),
        autosave_manager=autosave_manager,
        recovery_manager=recovery_manager,
    )
    qtbot.addWidget(window)

    assert window.show_crash_recovery_dialog()
    assert window.editor.text() == "[E]Recovered\n"
    assert window.current_path == source_path.resolve(strict=False)
    assert not selected_draft.path.exists()


def test_main_window_discards_selected_autosave_draft(qtbot, monkeypatch, tmp_path):
    autosave_manager = AutosaveManager(tmp_path / "autosave")
    autosave_manager.write(
        MiniChordDocument(text="[E]Discard me", title="Discard"),
        source_path=None,
        draft_id="draft-1",
    )
    recovery_manager = RecoveryManager(autosave_manager)
    selected_draft = recovery_manager.autosave_drafts()[0]

    class FakeRecoveryDialog:
        DISCARD_ACTION = "discard"

        class DialogCode:
            Accepted = 1

        def __init__(self, drafts, parent):
            self.drafts = drafts
            self.parent = parent

        def exec(self):
            return self.DialogCode.Accepted

        def selected_draft(self):
            return selected_draft

        def selected_action(self):
            return self.DISCARD_ACTION

    monkeypatch.setattr(main_window_module, "RecoveryDialog", FakeRecoveryDialog)
    window = MainWindow(
        settings=temporary_settings(tmp_path),
        autosave_manager=autosave_manager,
        recovery_manager=recovery_manager,
    )
    qtbot.addWidget(window)

    assert window.show_crash_recovery_dialog()
    assert window.editor.text() == ""
    assert not selected_draft.path.exists()
