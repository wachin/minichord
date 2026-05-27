"""ChordPro parsing primitives for the miniChord document engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


METADATA_DIRECTIVES = frozenset(
    {
        "album",
        "artist",
        "capo",
        "key",
        "subtitle",
        "tempo",
        "title",
    }
)

DIRECTIVE_ALIASES = {
    "eoc": "end_of_chorus",
    "soc": "start_of_chorus",
    "st": "subtitle",
    "t": "title",
}


@dataclass(frozen=True, slots=True)
class ChordToken:
    """A chord symbol anchored before a lyric character index."""

    symbol: str
    lyric_index: int


@dataclass(frozen=True, slots=True)
class ChordLyricLine:
    """A ChordPro lyric line with zero or more inline chord tokens."""

    lyrics: str
    chords: tuple[ChordToken, ...]
    source: str

    @property
    def has_chords(self) -> bool:
        return bool(self.chords)


@dataclass(frozen=True, slots=True)
class ChordProDirective:
    """A single ChordPro directive line such as ``{title: My Song}``."""

    name: str
    value: str | None
    source: str

    @property
    def canonical_name(self) -> str:
        return DIRECTIVE_ALIASES.get(self.name, self.name)

    @property
    def is_metadata(self) -> bool:
        return self.canonical_name in METADATA_DIRECTIVES


@dataclass(frozen=True, slots=True)
class BlankLine:
    """A source blank line preserved in the parsed song structure."""

    source: str = ""


SongLine = ChordProDirective | ChordLyricLine | BlankLine


@dataclass(frozen=True, slots=True)
class ChordProSong:
    """Parsed ChordPro song structure used by later layout and rendering code."""

    lines: tuple[SongLine, ...]
    metadata: Mapping[str, str]

    @property
    def title(self) -> str:
        return self.metadata.get("title", "")

    @property
    def directives(self) -> tuple[ChordProDirective, ...]:
        return tuple(
            line for line in self.lines if isinstance(line, ChordProDirective)
        )

    @property
    def chord_lyric_lines(self) -> tuple[ChordLyricLine, ...]:
        return tuple(line for line in self.lines if isinstance(line, ChordLyricLine))


def parse_chordpro(source: str) -> ChordProSong:
    """Parse a small but useful subset of ChordPro into semantic line objects."""
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    parsed_lines: list[SongLine] = []
    metadata: dict[str, str] = {}

    for raw_line in normalized.splitlines():
        if raw_line.strip() == "":
            parsed_lines.append(BlankLine(source=raw_line))
            continue

        directive = _parse_directive(raw_line)
        if directive is not None:
            parsed_lines.append(directive)
            if directive.is_metadata and directive.value is not None:
                metadata[directive.canonical_name] = directive.value
            continue

        parsed_lines.append(_parse_chord_lyric_line(raw_line))

    return ChordProSong(
        lines=tuple(parsed_lines),
        metadata=MappingProxyType(metadata),
    )


def _parse_directive(raw_line: str) -> ChordProDirective | None:
    stripped = raw_line.strip()
    if not stripped.startswith("{") or not stripped.endswith("}"):
        return None

    inner = stripped[1:-1].strip()
    if not inner:
        return None

    raw_name, separator, raw_value = inner.partition(":")
    name = raw_name.strip().lower()
    if not name:
        return None

    value = raw_value.strip() if separator else None
    return ChordProDirective(name=name, value=value, source=raw_line)


def _parse_chord_lyric_line(raw_line: str) -> ChordLyricLine:
    lyrics: list[str] = []
    chords: list[ChordToken] = []
    index = 0

    while index < len(raw_line):
        character = raw_line[index]
        if character == "[":
            closing_index = raw_line.find("]", index + 1)
            if closing_index != -1:
                symbol = raw_line[index + 1 : closing_index].strip()
                if _is_chord_marker(symbol):
                    chords.append(
                        ChordToken(symbol=symbol, lyric_index=len(lyrics))
                    )
                    index = closing_index + 1
                    continue

        lyrics.append(character)
        index += 1

    return ChordLyricLine(
        lyrics="".join(lyrics),
        chords=tuple(chords),
        source=raw_line,
    )


def _is_chord_marker(symbol: str) -> bool:
    return bool(symbol) and "[" not in symbol and "]" not in symbol
