from PyQt6.QtCore import QCoreApplication

from chordpages.app import build_application
from chordpages.i18n import (
    SOURCE_TRANSLATIONS_PATH,
    install_translations,
    language_candidates,
    translation_manager,
)
from chordpages.settings import SettingsManager


def temporary_settings(tmp_path) -> SettingsManager:
    return SettingsManager.from_file(tmp_path / "chordpages-settings.ini")


def test_translation_assets_exist():
    expected_files = [
        "chordpages_es.ts",
        "chordpages_es.qm",
        "chordpages_en.ts",
        "chordpages_en.qm",
    ]

    for filename in expected_files:
        assert (SOURCE_TRANSLATIONS_PATH / filename).is_file()


def test_language_candidates_include_base_language_fallback():
    assert language_candidates("es_EC") == ("es_EC", "es")
    assert language_candidates("system", system_locale_name="es_EC") == ("es_EC", "es")
    assert language_candidates("en") == ("en",)


def test_settings_manager_persists_language(tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_language("es")
    settings.sync()

    reloaded = temporary_settings(tmp_path)

    assert reloaded.language() == "es"


def test_build_application_loads_saved_spanish_translation(tmp_path):
    settings = temporary_settings(tmp_path)
    settings.set_language("es_EC")
    settings.sync()

    app = build_application([], settings=settings)

    try:
        manager = translation_manager(app)
        assert manager is not None
        assert manager.state.requested_language == "es_EC"
        assert manager.state.candidates == ("es_EC", "es")
        assert manager.state.application_loaded
        assert manager.state.application_file == SOURCE_TRANSLATIONS_PATH / "chordpages_es.qm"
        assert QCoreApplication.translate("MainWindow", "File") == "Archivo"
    finally:
        install_translations(app, "en")
