"""Minimal text-based songbook model for `.mchordbook` files."""

from __future__ import annotations

from dataclasses import dataclass, field

from chordpages.document.page import DEFAULT_PAGE_SIZE


SONGBOOK_FORMAT = "ChordPagesBook"


@dataclass(slots=True)
class ChordPagesSongbook:
    """A multi-song project that references `.mchord` files."""

    title: str = "Untitled Songbook"
    songs: list[str] = field(default_factory=list)
    version: int = 1
    page_size: str = DEFAULT_PAGE_SIZE
    orientation: str = "portrait"
    margins: str = "normal"
    column_count: int = 1
    index_enabled: bool = False
    index_position: str = "beginning"

    def to_mchordbook(self) -> str:
        """Serialize the songbook as a small Git-friendly `.mchordbook` file."""
        lines = [
            f"format: {SONGBOOK_FORMAT}",
            f"version: {self.version}",
            f"title: {_scalar(self.title or 'Untitled Songbook')}",
            "",
            "page:",
            f"  size: {_scalar(self.page_size)}",
            f"  orientation: {_scalar(self.orientation)}",
            f"  margins: {_scalar(self.margins)}",
            "",
            "columns:",
            f"  count: {max(1, self.column_count)}",
            "",
            "songs:",
        ]
        lines.extend(f"  - {_scalar(song)}" for song in self.songs)
        if not self.songs:
            lines.append("  []")

        lines.extend(
            [
                "",
                "index:",
                f"  enabled: {_bool_text(self.index_enabled)}",
                f"  position: {_scalar(self.index_position)}",
                "",
            ]
        )
        return "\n".join(lines)

    @classmethod
    def from_mchordbook(cls, content: str) -> "ChordPagesSongbook":
        """Load the subset of `.mchordbook` written by the prototype."""
        data = _parse_simple_yaml(content)
        if data.get("format") != SONGBOOK_FORMAT:
            return cls()

        page = data.get("page")
        columns = data.get("columns")
        index = data.get("index")
        return cls(
            title=_text(data.get("title"), "Untitled Songbook"),
            songs=[str(song) for song in data.get("songs", []) if str(song)],
            version=_int(data.get("version"), 1),
            page_size=_nested_text(page, "size", DEFAULT_PAGE_SIZE),
            orientation=_nested_text(page, "orientation", "portrait"),
            margins=_nested_text(page, "margins", "normal"),
            column_count=max(1, _nested_int(columns, "count", 1)),
            index_enabled=_nested_bool(index, "enabled", False),
            index_position=_nested_text(index, "position", "beginning"),
        )


def _parse_simple_yaml(content: str) -> dict[str, object]:
    root: dict[str, object] = {}
    current_section: str | None = None
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")

    for raw_line in normalized.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue

        if not line.startswith(" "):
            key, separator, value = line.partition(":")
            if not separator:
                continue
            key = key.strip()
            value = value.strip()
            if value:
                root[key] = _parse_scalar(value)
                current_section = None
            else:
                root[key] = []
                current_section = key
            continue

        if current_section is None:
            continue

        stripped = line.strip()
        section = root[current_section]
        if stripped.startswith("- "):
            if not isinstance(section, list):
                section = []
                root[current_section] = section
            section.append(_parse_scalar(stripped[2:].strip()))
            continue

        if stripped == "[]":
            root[current_section] = []
            continue

        key, separator, value = stripped.partition(":")
        if not separator:
            continue
        if not isinstance(section, dict):
            section = {}
            root[current_section] = section
        section[key.strip()] = _parse_scalar(value.strip())

    return root


def _parse_scalar(value: str) -> object:
    if value == "[]":
        return []
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    if value.isdecimal():
        return int(value)
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1].replace('\\"', '"')
    return value


def _scalar(value: object) -> str:
    text = " ".join(str(value).splitlines()).strip()
    if not text:
        return '""'
    if (
        any(character in text for character in (":", "#"))
        or text.startswith(("-", "[", "{"))
        or text.lower() in {"true", "false"}
        or text.isdecimal()
    ):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def _text(value: object, default: str) -> str:
    if value in (None, ""):
        return default
    return str(value)


def _int(value: object, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _nested_text(value: object, key: str, default: str) -> str:
    if not isinstance(value, dict):
        return default
    return _text(value.get(key), default)


def _nested_int(value: object, key: str, default: int) -> int:
    if not isinstance(value, dict):
        return default
    return _int(value.get(key), default)


def _nested_bool(value: object, key: str, default: bool) -> bool:
    if not isinstance(value, dict):
        return default
    candidate = value.get(key)
    if isinstance(candidate, bool):
        return candidate
    if isinstance(candidate, str) and candidate.lower() in {"true", "false"}:
        return candidate.lower() == "true"
    return default


def _bool_text(value: bool) -> str:
    return "true" if value else "false"
