from pathlib import Path

from PyQt6.QtCore import QByteArray, QSize

from minichord import __version__
from minichord.app import build_application
import minichord.main_window as main_window_module
from minichord.main_window import MainWindow
from minichord.resources import APP_ICON_PATH
from minichord.settings import (
    APPLICATION_NAME,
    ORGANIZATION_NAME,
    SettingsManager,
)


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
