"""Qt translation loading for ChordPages."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator
from PyQt6.QtWidgets import QApplication


SYSTEM_LANGUAGE = "system"
TRANSLATION_BASENAME = "chordpages"
QT_TRANSLATION_BASENAME = "qtbase"
SOURCE_TRANSLATIONS_PATH = Path(__file__).resolve().parent.parent / "translations"
INSTALLED_TRANSLATIONS_PATH = Path(sys.prefix) / "share" / "chordpages" / "translations"


@dataclass(frozen=True, slots=True)
class TranslationState:
    """Current translation loading result."""

    requested_language: str
    candidates: tuple[str, ...]
    application_loaded: bool
    qt_loaded: bool
    application_file: Path | None = None
    qt_file: Path | None = None


class TranslationManager:
    """Install and keep Qt translators alive for the application lifetime."""

    def __init__(
        self,
        app: QApplication,
        translations_paths: tuple[Path, ...] | None = None,
    ):
        self._app = app
        self._translations_paths = translations_paths or translation_search_paths()
        self._application_translator: QTranslator | None = None
        self._qt_translator: QTranslator | None = None
        self.state = TranslationState(
            requested_language=SYSTEM_LANGUAGE,
            candidates=language_candidates(SYSTEM_LANGUAGE),
            application_loaded=False,
            qt_loaded=False,
        )

    def load(self, language: str | None = None) -> TranslationState:
        """Load ChordPages and Qt translators for a requested language."""
        requested_language = _normalized_language(language or SYSTEM_LANGUAGE)
        candidates = language_candidates(requested_language)
        self._remove_installed_translators()

        application_translator, application_file = self._load_first_available(
            TRANSLATION_BASENAME,
            candidates,
            self._translations_paths,
        )
        qt_translator, qt_file = self._load_first_available(
            QT_TRANSLATION_BASENAME,
            candidates,
            (Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)),),
        )

        if qt_translator is not None:
            self._app.installTranslator(qt_translator)
            self._qt_translator = qt_translator

        if application_translator is not None:
            self._app.installTranslator(application_translator)
            self._application_translator = application_translator

        self.state = TranslationState(
            requested_language=requested_language,
            candidates=candidates,
            application_loaded=application_translator is not None,
            qt_loaded=qt_translator is not None,
            application_file=application_file,
            qt_file=qt_file,
        )
        return self.state

    def _remove_installed_translators(self) -> None:
        if self._application_translator is not None:
            self._app.removeTranslator(self._application_translator)
            self._application_translator = None

        if self._qt_translator is not None:
            self._app.removeTranslator(self._qt_translator)
            self._qt_translator = None

    @staticmethod
    def _load_first_available(
        basename: str,
        candidates: tuple[str, ...],
        paths: tuple[Path, ...],
    ) -> tuple[QTranslator | None, Path | None]:
        for directory in paths:
            for candidate in candidates:
                translation_file = directory / f"{basename}_{candidate}.qm"
                if not translation_file.is_file():
                    continue

                translator = QTranslator()
                if translator.load(str(translation_file)):
                    return translator, translation_file

        return None, None


def install_translations(
    app: QApplication,
    language: str | None = None,
) -> TranslationManager:
    """Install translations on ``app`` and store the manager on the instance."""
    manager = getattr(app, "_chordpages_translation_manager", None)
    if not isinstance(manager, TranslationManager):
        manager = TranslationManager(app)
        setattr(app, "_chordpages_translation_manager", manager)

    manager.load(language)
    return manager


def translation_manager(app: QApplication) -> TranslationManager | None:
    """Return the currently installed ChordPages translation manager."""
    manager = getattr(app, "_chordpages_translation_manager", None)
    if isinstance(manager, TranslationManager):
        return manager
    return None


def translation_search_paths() -> tuple[Path, ...]:
    """Return translation directories in source-run then installed order."""
    candidates = (SOURCE_TRANSLATIONS_PATH, INSTALLED_TRANSLATIONS_PATH)
    paths: list[Path] = []
    for path in candidates:
        if path in paths:
            continue
        paths.append(path)
    return tuple(paths)


def language_candidates(
    language: str | None = None,
    *,
    system_locale_name: str | None = None,
) -> tuple[str, ...]:
    """Return locale candidates from most specific to broadest."""
    requested = _normalized_language(language or SYSTEM_LANGUAGE)
    if requested == SYSTEM_LANGUAGE:
        requested = _normalized_language(system_locale_name or QLocale.system().name())

    candidates = [requested]
    base_language = requested.split("_", 1)[0]
    if base_language and base_language not in candidates:
        candidates.append(base_language)

    return tuple(candidate for candidate in candidates if candidate)


def _normalized_language(language: str) -> str:
    normalized = language.strip().replace("-", "_")
    return normalized or SYSTEM_LANGUAGE
