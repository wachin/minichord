"""ChordPro parsing primitives for the ChordPages document engine."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal


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
    "cb": "column_break",
    "colb": "column_break",
    "eob": "end_of_bridge",
    "eoc": "end_of_chorus",
    "eov": "end_of_verse",
    "new_page": "page_break",
    "np": "page_break",
    "pagebreak": "page_break",
    "sob": "start_of_bridge",
    "soc": "start_of_chorus",
    "sov": "start_of_verse",
    "st": "subtitle",
    "t": "title",
}

CHORD_SYMBOL_RE = re.compile(
    r"""
    (?:
        N\.C\.
        |
        [A-G](?:\#|b)?
        (?:
            maj|min|dim|aug|sus|add|m
        )?
        [0-9]*
        (?:[#b][0-9]+)*
        (?:/[A-G](?:\#|b)?)?
    )
    """,
    re.VERBOSE,
)

CHORD_SEPARATORS = frozenset({"|", "||", "-", "/", ":", "::"})
TOKEN_EDGE_PUNCTUATION = "()[]{}|,;"


@dataclass(frozen=True, slots=True)
class ChordToken:
    """A chord symbol anchored before a lyric character index."""

    symbol: str
    lyric_index: int
    source_column: int | None = None


@dataclass(frozen=True, slots=True)
class LyricSyllable:
    """A singable lyric unit with source offsets and attached chords."""

    text: str
    start_index: int
    end_index: int
    chords: tuple[ChordToken, ...] = ()

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("Lyric syllable text cannot be empty.")
        if self.start_index < 0 or self.end_index <= self.start_index:
            raise ValueError("Lyric syllable indexes must describe a range.")
        if len(self.text) != self.end_index - self.start_index:
            raise ValueError("Lyric syllable text must match its index range.")
        object.__setattr__(self, "chords", tuple(self.chords))

    @property
    def length(self) -> int:
        return self.end_index - self.start_index


@dataclass(frozen=True, slots=True)
class ChordLyricLine:
    """A ChordPro lyric line with zero or more inline chord tokens."""

    lyrics: str
    chords: tuple[ChordToken, ...]
    source: str
    chord_source: str | None = None

    @property
    def has_chords(self) -> bool:
        return bool(self.chords)

    @property
    def syllables(self) -> tuple[LyricSyllable, ...]:
        return build_lyric_syllables(self.lyrics, self.chords)


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
SongSectionKind = Literal["bridge", "chorus", "unknown", "verse"]
SECTION_START_DIRECTIVES: Mapping[str, SongSectionKind] = MappingProxyType(
    {
        "start_of_bridge": "bridge",
        "start_of_chorus": "chorus",
        "start_of_verse": "verse",
    }
)
SECTION_END_DIRECTIVES: Mapping[str, SongSectionKind] = MappingProxyType(
    {
        "end_of_bridge": "bridge",
        "end_of_chorus": "chorus",
        "end_of_verse": "verse",
    }
)


@dataclass(frozen=True, slots=True)
class SongSection:
    """A semantic group of song lines such as a verse, chorus, or bridge."""

    kind: SongSectionKind
    label: str
    lines: tuple[SongLine, ...]
    start_line_index: int
    end_line_index: int

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def chord_lyric_lines(self) -> tuple[ChordLyricLine, ...]:
        return tuple(
            line for line in self.lines if isinstance(line, ChordLyricLine)
        )

    def to_source(self) -> str:
        source_lines: list[str] = []
        for line in self.lines:
            source_lines.extend(source_lines_for_song_line(line))
        return "\n".join(source_lines)


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
        return tuple(
            line for line in self.lines if isinstance(line, ChordLyricLine)
        )

    @property
    def sections(self) -> tuple[SongSection, ...]:
        return build_song_sections(self.lines)


def build_song_sections(lines: tuple[SongLine, ...]) -> tuple[SongSection, ...]:
    """Build semantic song sections from explicit ChordPro section markers."""
    sections: list[SongSection] = []
    current_kind: SongSectionKind = "unknown"
    current_label = ""
    current_lines: list[SongLine] = []
    current_start_line_index = 0

    for line_index, line in enumerate(lines):
        section_start = _section_start_kind(line)
        if section_start is not None:
            _append_song_section(
                sections,
                current_kind,
                current_label,
                current_lines,
                current_start_line_index,
                line_index - 1,
            )
            current_kind = section_start
            current_label = _section_label(line, section_start)
            current_lines = []
            current_start_line_index = line_index + 1
            continue

        section_end = _section_end_kind(line)
        if section_end is not None:
            _append_song_section(
                sections,
                current_kind,
                current_label,
                current_lines,
                current_start_line_index,
                line_index - 1,
                include_empty=current_kind == section_end,
            )
            current_kind = "unknown"
            current_label = ""
            current_lines = []
            current_start_line_index = line_index + 1
            continue

        current_lines.append(line)

    _append_song_section(
        sections,
        current_kind,
        current_label,
        current_lines,
        current_start_line_index,
        len(lines) - 1,
    )
    return tuple(sections)


def build_lyric_syllables(
    lyrics: str,
    chords: tuple[ChordToken, ...] = (),
) -> tuple[LyricSyllable, ...]:
    """Split a lyric line into syllable ranges and attach anchored chords."""
    syllable_ranges = _lyric_syllable_ranges(lyrics)
    attached_chords: list[list[ChordToken]] = [
        [] for _ in syllable_ranges
    ]

    for chord in chords:
        syllable_index = _syllable_index_for_chord(
            chord,
            syllable_ranges,
            len(lyrics),
        )
        if syllable_index is not None:
            attached_chords[syllable_index].append(chord)

    return tuple(
        LyricSyllable(
            text=lyrics[start_index:end_index],
            start_index=start_index,
            end_index=end_index,
            chords=tuple(attached_chords[syllable_index]),
        )
        for syllable_index, (start_index, end_index) in enumerate(
            syllable_ranges
        )
    )


def render_chord_over_lyrics(
    song: ChordProSong,
    max_width: int | None = None,
) -> str:
    """Render parsed ChordPro as monospaced chord-over-lyrics text."""
    if max_width is not None and max_width < 1:
        raise ValueError("Maximum render width must be at least 1.")

    rendered_lines: list[str] = []

    for line in song.lines:
        if isinstance(line, BlankLine):
            rendered_lines.append("")
            continue

        if isinstance(line, ChordProDirective):
            directive_text = _render_directive_text(line)
            if directive_text is not None:
                rendered_lines.append(directive_text)
            continue

        for wrapped_line in wrap_chord_lyric_line(line, max_width):
            chord_text = render_chord_line(wrapped_line)
            if chord_text:
                rendered_lines.append(chord_text)
            rendered_lines.append(wrapped_line.lyrics)

    return "\n".join(rendered_lines)


def render_chord_line(line: ChordLyricLine) -> str:
    """Render only the chord row for a parsed chord/lyric line."""
    rendered: list[str] = []
    occupied_until = 0

    for chord in line.chords:
        preferred_column = _chord_render_column(chord)
        column = max(preferred_column, occupied_until)
        if column > len(rendered):
            rendered.extend(" " for _ in range(column - len(rendered)))

        rendered.extend(chord.symbol)
        occupied_until = column + len(chord.symbol) + 1

    return "".join(rendered).rstrip()


def wrap_chord_lyric_line(
    line: ChordLyricLine,
    max_width: int | None,
) -> tuple[ChordLyricLine, ...]:
    """Wrap a chord/lyric line while keeping chords with their lyric segment."""
    if max_width is None or line.lyrics == "":
        return (line,)
    if max_width < 1:
        raise ValueError("Maximum wrap width must be at least 1.")

    wrapped_lines: list[ChordLyricLine] = []
    for start_index, end_index, next_index in _lyric_wrap_ranges(
        line.lyrics,
        max_width,
    ):
        segment_lyrics = line.lyrics[start_index:end_index]
        segment_chords = _chords_for_wrapped_range(
            line.chords,
            start_index,
            next_index,
            len(segment_lyrics),
        )
        wrapped_lines.append(
            ChordLyricLine(
                lyrics=segment_lyrics,
                chords=segment_chords,
                source=line.source,
                chord_source=line.chord_source,
            )
        )

    return tuple(wrapped_lines)


def parse_chordpro(source: str) -> ChordProSong:
    """Parse a small but useful subset of ChordPro into semantic line objects."""
    normalized = source.replace("\r\n", "\n").replace("\r", "\n")
    parsed_lines: list[SongLine] = []
    metadata: dict[str, str] = {}
    raw_lines = normalized.splitlines()
    line_index = 0

    while line_index < len(raw_lines):
        raw_line = raw_lines[line_index]
        if raw_line.strip() == "":
            parsed_lines.append(BlankLine(source=raw_line))
            line_index += 1
            continue

        directive = _parse_directive(raw_line)
        if directive is not None:
            parsed_lines.append(directive)
            if directive.is_metadata and directive.value is not None:
                metadata[directive.canonical_name] = directive.value
            line_index += 1
            continue

        chord_line_tokens = _traditional_chord_line_tokens(raw_line)
        if chord_line_tokens:
            next_line_index = line_index + 1
            if next_line_index < len(raw_lines):
                next_raw_line = raw_lines[next_line_index]
                if _is_lyric_pair_candidate(next_raw_line):
                    parsed_lines.append(
                        _parse_traditional_chord_pair(
                            chord_line=raw_line,
                            lyric_line=next_raw_line,
                            chord_tokens=chord_line_tokens,
                        )
                    )
                    line_index += 2
                    continue

            parsed_lines.append(
                _parse_standalone_chord_line(raw_line, chord_line_tokens)
            )
            line_index += 1
            continue

        parsed_lines.append(_parse_chord_lyric_line(raw_line))
        line_index += 1

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


def _parse_traditional_chord_pair(
    chord_line: str,
    lyric_line: str,
    chord_tokens: tuple[ChordToken, ...],
) -> ChordLyricLine:
    return ChordLyricLine(
        lyrics=lyric_line,
        chords=_anchor_chord_tokens_to_lyrics(chord_tokens, lyric_line),
        source=lyric_line,
        chord_source=chord_line,
    )


def _parse_standalone_chord_line(
    chord_line: str,
    chord_tokens: tuple[ChordToken, ...],
) -> ChordLyricLine:
    return ChordLyricLine(
        lyrics="",
        chords=_anchor_chord_tokens_to_lyrics(chord_tokens, ""),
        source=chord_line,
        chord_source=chord_line,
    )


def _anchor_chord_tokens_to_lyrics(
    chord_tokens: tuple[ChordToken, ...],
    lyrics: str,
) -> tuple[ChordToken, ...]:
    anchored_tokens = []
    for token in chord_tokens:
        source_column = token.source_column if token.source_column is not None else 0
        anchored_tokens.append(
            ChordToken(
                symbol=token.symbol,
                lyric_index=min(source_column, len(lyrics)),
                source_column=source_column,
            )
        )
    return tuple(anchored_tokens)


def _traditional_chord_line_tokens(raw_line: str) -> tuple[ChordToken, ...]:
    if raw_line.strip() == "":
        return ()

    chord_tokens: list[ChordToken] = []
    for match in re.finditer(r"\S+", raw_line):
        raw_token = match.group()
        candidate, offset = _clean_chord_candidate(raw_token)
        if _is_chord_separator(raw_token) or _is_chord_separator(candidate):
            continue
        if _is_chord_symbol(candidate):
            source_column = match.start() + offset
            chord_tokens.append(
                ChordToken(
                    symbol=candidate,
                    lyric_index=source_column,
                    source_column=source_column,
                )
            )
            continue
        return ()

    return tuple(chord_tokens)


def _clean_chord_candidate(raw_token: str) -> tuple[str, int]:
    left_index = 0
    right_index = len(raw_token)

    while (
        left_index < right_index
        and raw_token[left_index] in TOKEN_EDGE_PUNCTUATION
    ):
        left_index += 1

    while (
        right_index > left_index
        and raw_token[right_index - 1] in TOKEN_EDGE_PUNCTUATION
    ):
        right_index -= 1

    return raw_token[left_index:right_index], left_index


def _is_chord_symbol(candidate: str) -> bool:
    return bool(CHORD_SYMBOL_RE.fullmatch(candidate))


def _is_chord_separator(candidate: str) -> bool:
    return candidate in CHORD_SEPARATORS


def _is_lyric_pair_candidate(raw_line: str) -> bool:
    return (
        raw_line.strip() != ""
        and _parse_directive(raw_line) is None
        and not _traditional_chord_line_tokens(raw_line)
        and not _parse_chord_lyric_line(raw_line).has_chords
    )


def _lyric_wrap_ranges(
    lyrics: str,
    max_width: int,
) -> tuple[tuple[int, int, int], ...]:
    ranges: list[tuple[int, int, int]] = []
    start_index = 0
    lyric_length = len(lyrics)

    while start_index < lyric_length:
        remaining_width = lyric_length - start_index
        if remaining_width <= max_width:
            ranges.append((start_index, lyric_length, lyric_length))
            break

        limit = start_index + max_width
        space_index = lyrics.rfind(" ", start_index + 1, limit + 1)
        if space_index > start_index:
            next_index = space_index
            while next_index < lyric_length and lyrics[next_index].isspace():
                next_index += 1
            ranges.append((start_index, space_index, next_index))
            start_index = next_index
            continue

        next_index = min(limit, lyric_length)
        ranges.append((start_index, next_index, next_index))
        start_index = next_index

    return tuple(ranges)


def _lyric_syllable_ranges(lyrics: str) -> tuple[tuple[int, int], ...]:
    ranges: list[tuple[int, int]] = []
    index = 0

    while index < len(lyrics):
        if lyrics[index].isspace():
            index += 1
            continue

        start_index = index
        while index < len(lyrics) and not lyrics[index].isspace():
            index += 1
            if (
                lyrics[index - 1] == "-"
                and index < len(lyrics)
                and not lyrics[index].isspace()
            ):
                break

        ranges.append((start_index, index))

    return tuple(ranges)


def _syllable_index_for_chord(
    chord: ChordToken,
    syllable_ranges: tuple[tuple[int, int], ...],
    lyric_length: int,
) -> int | None:
    if not syllable_ranges:
        return None

    lyric_index = min(max(chord.lyric_index, 0), lyric_length)
    for syllable_index, (start_index, end_index) in enumerate(syllable_ranges):
        if start_index <= lyric_index < end_index:
            return syllable_index
        if lyric_index < start_index:
            return syllable_index

    return len(syllable_ranges) - 1


def _chords_for_wrapped_range(
    chords: tuple[ChordToken, ...],
    start_index: int,
    next_index: int,
    segment_length: int,
) -> tuple[ChordToken, ...]:
    segment_chords: list[ChordToken] = []
    for chord in chords:
        if start_index <= chord.lyric_index < next_index:
            segment_chords.append(
                ChordToken(
                    symbol=chord.symbol,
                    lyric_index=min(chord.lyric_index - start_index, segment_length),
                )
            )
    return tuple(segment_chords)


def _render_directive_text(directive: ChordProDirective) -> str | None:
    if directive.canonical_name == "comment":
        return directive.value or ""
    return None


def source_lines_for_song_line(song_line: SongLine) -> tuple[str, ...]:
    """Return source lines for a parsed ChordPro song line."""
    if isinstance(song_line, ChordLyricLine) and song_line.chord_source is not None:
        if song_line.chord_source != song_line.source:
            return song_line.chord_source, song_line.source
    return (song_line.source,)


def _append_song_section(
    sections: list[SongSection],
    kind: SongSectionKind,
    label: str,
    lines: list[SongLine],
    start_line_index: int,
    end_line_index: int,
    include_empty: bool = False,
) -> None:
    if not lines and not include_empty:
        return
    sections.append(
        SongSection(
            kind=kind,
            label=label,
            lines=tuple(lines),
            start_line_index=start_line_index,
            end_line_index=max(start_line_index, end_line_index),
        )
    )


def _section_start_kind(song_line: SongLine) -> SongSectionKind | None:
    if not isinstance(song_line, ChordProDirective):
        return None
    return SECTION_START_DIRECTIVES.get(song_line.canonical_name)


def _section_end_kind(song_line: SongLine) -> SongSectionKind | None:
    if not isinstance(song_line, ChordProDirective):
        return None
    return SECTION_END_DIRECTIVES.get(song_line.canonical_name)


def _section_label(
    song_line: SongLine,
    kind: SongSectionKind,
) -> str:
    if isinstance(song_line, ChordProDirective) and song_line.value:
        return song_line.value
    return kind.title()


def _chord_render_column(chord: ChordToken) -> int:
    if chord.source_column is not None:
        return max(0, chord.source_column)
    return max(0, chord.lyric_index)


def _is_chord_marker(symbol: str) -> bool:
    return bool(symbol) and "[" not in symbol and "]" not in symbol
