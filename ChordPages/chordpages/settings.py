"""Persistent application settings for ChordPages."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QByteArray, QSettings, QSize
from PyQt6.QtWidgets import QMainWindow


ORGANIZATION_NAME = "ChordPages"
APPLICATION_NAME = "ChordPages"
DEFAULT_MAIN_WINDOW_SIZE = (1100, 850)
DEFAULT_RECENT_FILE_LIMIT = 10
DEFAULT_LANGUAGE = "system"
THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"
DEFAULT_THEME = THEME_SYSTEM
SUPPORTED_THEMES = (THEME_SYSTEM, THEME_LIGHT, THEME_DARK)


@dataclass(frozen=True, slots=True)
class DocumentViewSettings:
    """Per-document visual editor preferences."""

    zoom: float | None = None
    font_family: str | None = None
    font_size: float | None = None
    pages_per_row: int | None = None


class SettingsManager:
    """Small typed wrapper around Qt's persistent settings storage."""

    MAIN_WINDOW_GEOMETRY_KEY = "mainWindow/geometry"
    MAIN_WINDOW_STATE_KEY = "mainWindow/state"
    MAIN_WINDOW_SIZE_KEY = "mainWindow/size"
    LAST_DIRECTORY_KEY = "files/lastDirectory"
    RECENT_FILES_KEY = "files/recent"
    LANGUAGE_KEY = "i18n/language"
    THEME_KEY = "ui/theme"
    EDITOR_FONT_FAMILY_KEY = "editor/fontFamily"
    EDITOR_FONT_SIZE_KEY = "editor/fontSize"
    EDITOR_ZOOM_KEY = "editor/zoom"
    EDITOR_PAGES_PER_ROW_KEY = "editor/pagesPerRow"
    FILE_VIEW_SETTINGS_PREFIX = "files/viewSettings"

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
        """Clear all stored ChordPages settings in this backend."""
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

    def editor_font_family(self, default_family: str) -> str:
        """Return the persisted editor font family."""
        value = self._settings.value(self.EDITOR_FONT_FAMILY_KEY, default_family)
        if value in (None, ""):
            return default_family
        return str(value)

    def set_editor_font_family(self, family: str) -> None:
        """Persist the editor font family."""
        self._settings.setValue(
            self.EDITOR_FONT_FAMILY_KEY,
            family.strip(),
        )

    def editor_font_size(self, default_size: float) -> float:
        """Return the persisted editor font size in points."""
        value = self._settings.value(self.EDITOR_FONT_SIZE_KEY, default_size)
        try:
            font_size = float(value)
        except (TypeError, ValueError):
            return default_size
        return font_size if font_size > 0 else default_size

    def set_editor_font_size(self, point_size: float) -> None:
        """Persist the editor font size in points."""
        self._settings.setValue(self.EDITOR_FONT_SIZE_KEY, float(point_size))

    def editor_zoom(self, default_zoom: float) -> float:
        """Return the persisted default editor zoom factor."""
        return _positive_float(self._settings.value(self.EDITOR_ZOOM_KEY), default_zoom)

    def set_editor_zoom(self, zoom: float) -> None:
        """Persist the default editor zoom factor."""
        self._settings.setValue(self.EDITOR_ZOOM_KEY, float(zoom))

    def editor_pages_per_row(self, default_pages_per_row: int) -> int:
        """Return the persisted default page view column count."""
        return _positive_int(
            self._settings.value(self.EDITOR_PAGES_PER_ROW_KEY),
            default_pages_per_row,
        )

    def set_editor_pages_per_row(self, pages_per_row: int) -> None:
        """Persist the default page view column count."""
        self._settings.setValue(self.EDITOR_PAGES_PER_ROW_KEY, int(pages_per_row))

    def file_view_settings(self, path: str | Path) -> DocumentViewSettings:
        """Return visual preferences saved for one document path."""
        group = self._file_view_settings_group(path)
        font_family = self._settings.value(f"{group}/fontFamily")
        return DocumentViewSettings(
            zoom=_optional_positive_float(self._settings.value(f"{group}/zoom")),
            font_family=(
                str(font_family).strip()
                if font_family not in (None, "")
                else None
            ),
            font_size=_optional_positive_float(self._settings.value(f"{group}/fontSize")),
            pages_per_row=_optional_positive_int(
                self._settings.value(f"{group}/pagesPerRow")
            ),
        )

    def set_file_view_settings(
        self,
        path: str | Path,
        view_settings: DocumentViewSettings,
    ) -> None:
        """Persist visual preferences for one document path."""
        group = self._file_view_settings_group(path)
        self._settings.setValue(f"{group}/path", _normalized_path(path))
        if view_settings.zoom is not None:
            self._settings.setValue(f"{group}/zoom", float(view_settings.zoom))
        if view_settings.font_family is not None:
            self._settings.setValue(
                f"{group}/fontFamily",
                view_settings.font_family.strip(),
            )
        if view_settings.font_size is not None:
            self._settings.setValue(
                f"{group}/fontSize",
                float(view_settings.font_size),
            )
        if view_settings.pages_per_row is not None:
            self._settings.setValue(
                f"{group}/pagesPerRow",
                int(view_settings.pages_per_row),
            )

    def _file_view_settings_group(self, path: str | Path) -> str:
        path_text = _normalized_path(path)
        path_hash = sha1(path_text.encode("utf-8")).hexdigest()
        return f"{self.FILE_VIEW_SETTINGS_PREFIX}/{path_hash}"

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


def _positive_float(value: Any, default: float) -> float:
    parsed_value = _optional_positive_float(value)
    return default if parsed_value is None else parsed_value


def _optional_positive_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed_value = float(value)
    except (TypeError, ValueError):
        return None
    return parsed_value if parsed_value > 0 else None


def _positive_int(value: Any, default: int) -> int:
    parsed_value = _optional_positive_int(value)
    return default if parsed_value is None else parsed_value


def _optional_positive_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return None
    return parsed_value if parsed_value > 0 else None
