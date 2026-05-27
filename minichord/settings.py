"""Persistent application settings for miniChord."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray, QSettings, QSize
from PyQt6.QtWidgets import QMainWindow


ORGANIZATION_NAME = "miniChord"
APPLICATION_NAME = "miniChord"
DEFAULT_MAIN_WINDOW_SIZE = (1100, 850)
DEFAULT_RECENT_FILE_LIMIT = 10
DEFAULT_LANGUAGE = "system"
THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"
DEFAULT_THEME = THEME_SYSTEM
SUPPORTED_THEMES = (THEME_SYSTEM, THEME_LIGHT, THEME_DARK)


class SettingsManager:
    """Small typed wrapper around Qt's persistent settings storage."""

    MAIN_WINDOW_GEOMETRY_KEY = "mainWindow/geometry"
    MAIN_WINDOW_STATE_KEY = "mainWindow/state"
    MAIN_WINDOW_SIZE_KEY = "mainWindow/size"
    LAST_DIRECTORY_KEY = "files/lastDirectory"
    RECENT_FILES_KEY = "files/recent"
    LANGUAGE_KEY = "i18n/language"
    THEME_KEY = "ui/theme"

    def __init__(self, qsettings: QSettings | None = None):
        self._settings = qsettings or QSettings(ORGANIZATION_NAME, APPLICATION_NAME)

    @classmethod
    def from_file(cls, path: str | Path) -> "SettingsManager":
        """Create a settings manager backed by an INI file."""
        return cls(QSettings(str(path), QSettings.Format.IniFormat))

    def value(self, key: str, default: Any = None) -> Any:
        """Return a raw setting value."""
        return self._settings.value(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """Store a raw setting value."""
        self._settings.setValue(key, value)

    def remove(self, key: str) -> None:
        """Remove a setting key and any child keys."""
        self._settings.remove(key)

    def clear(self) -> None:
        """Clear all stored miniChord settings in this backend."""
        self._settings.clear()

    def sync(self) -> None:
        """Flush pending settings to persistent storage."""
        self._settings.sync()

    def save_main_window(self, window: QMainWindow) -> None:
        """Persist the main window geometry, dock/toolbar state, and size."""
        self._settings.setValue(self.MAIN_WINDOW_GEOMETRY_KEY, window.saveGeometry())
        self._settings.setValue(self.MAIN_WINDOW_STATE_KEY, window.saveState())
        self._settings.setValue(self.MAIN_WINDOW_SIZE_KEY, window.size())
        self.sync()

    def restore_main_window(
        self,
        window: QMainWindow,
        default_size: tuple[int, int] = DEFAULT_MAIN_WINDOW_SIZE,
    ) -> None:
        """Restore the main window geometry and toolbar state when available."""
        restored_geometry = False
        geometry = self._settings.value(self.MAIN_WINDOW_GEOMETRY_KEY)
        if isinstance(geometry, QByteArray) and not geometry.isEmpty():
            restored_geometry = window.restoreGeometry(geometry)

        if not restored_geometry:
            window.resize(self._stored_window_size(default_size))

        state = self._settings.value(self.MAIN_WINDOW_STATE_KEY)
        if isinstance(state, QByteArray) and not state.isEmpty():
            window.restoreState(state)

    def last_directory(self) -> Path | None:
        """Return the last directory used by a file dialog."""
        value = self._settings.value(self.LAST_DIRECTORY_KEY, "")
        if value in (None, ""):
            return None
        return Path(str(value))

    def set_last_directory(self, directory: str | Path) -> None:
        """Store the last directory used by a file dialog."""
        self._settings.setValue(self.LAST_DIRECTORY_KEY, _normalized_path(directory))

    def recent_files(self) -> list[Path]:
        """Return recently used document paths from newest to oldest."""
        value = self._settings.value(self.RECENT_FILES_KEY, [])
        if value in (None, ""):
            return []

        raw_paths: Iterable[Any]
        if isinstance(value, str):
            raw_paths = [value]
        else:
            raw_paths = value

        paths: list[Path] = []
        seen: set[str] = set()
        for raw_path in raw_paths:
            text = str(raw_path)
            if not text or text in seen:
                continue
            paths.append(Path(text))
            seen.add(text)
        return paths

    def set_recent_files(
        self,
        paths: Iterable[str | Path],
        limit: int = DEFAULT_RECENT_FILE_LIMIT,
    ) -> None:
        """Replace the recent document list, preserving order and removing duplicates."""
        normalized_paths: list[str] = []
        seen: set[str] = set()
        for path in paths:
            text = _normalized_path(path)
            if text in seen:
                continue
            normalized_paths.append(text)
            seen.add(text)
            if len(normalized_paths) >= limit:
                break

        self._settings.setValue(self.RECENT_FILES_KEY, normalized_paths)

    def remember_file(
        self,
        path: str | Path,
        limit: int = DEFAULT_RECENT_FILE_LIMIT,
    ) -> None:
        """Record a successfully opened or saved document path."""
        path_text = _normalized_path(path)
        older_paths = [
            recent_path
            for recent_path in self.recent_files()
            if _normalized_path(recent_path) != path_text
        ]
        self.set_recent_files([path_text, *older_paths], limit=limit)
        self.set_last_directory(Path(path_text).parent)

    def language(self) -> str:
        """Return the requested UI language code or ``system``."""
        value = self._settings.value(self.LANGUAGE_KEY, DEFAULT_LANGUAGE)
        if value in (None, ""):
            return DEFAULT_LANGUAGE
        return str(value)

    def set_language(self, language: str) -> None:
        """Persist the requested UI language code."""
        self._settings.setValue(self.LANGUAGE_KEY, language.strip() or DEFAULT_LANGUAGE)

    def theme(self) -> str:
        """Return the requested UI theme."""
        value = self._settings.value(self.THEME_KEY, DEFAULT_THEME)
        return normalized_theme(str(value) if value not in (None, "") else DEFAULT_THEME)

    def set_theme(self, theme: str) -> None:
        """Persist the requested UI theme."""
        self._settings.setValue(self.THEME_KEY, normalized_theme(theme))

    def _stored_window_size(self, default_size: tuple[int, int]) -> QSize:
        stored_size = self._settings.value(self.MAIN_WINDOW_SIZE_KEY)
        if isinstance(stored_size, QSize) and _is_usable_size(stored_size):
            return stored_size

        return QSize(default_size[0], default_size[1])


def normalized_theme(theme: str) -> str:
    """Return a supported theme name, falling back to the system theme."""
    normalized = theme.strip().lower()
    if normalized in SUPPORTED_THEMES:
        return normalized
    return DEFAULT_THEME


def _normalized_path(path: str | Path) -> str:
    candidate = Path(path).expanduser()
    try:
        return str(candidate.resolve(strict=False))
    except OSError:
        return str(candidate.absolute())


def _is_usable_size(size: QSize) -> bool:
    return size.isValid() and size.width() > 0 and size.height() > 0
