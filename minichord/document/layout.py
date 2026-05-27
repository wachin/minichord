"""Structured render layout primitives for miniChord documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from minichord.document.chordpro import (
    BlankLine,
    ChordLyricLine,
    ChordProDirective,
    ChordProSong,
    render_chord_line,
    wrap_chord_lyric_line,
)


RenderRowKind = Literal[
    "blank",
    "chord",
    "column_break",
    "comment",
    "lyric",
    "page_break",
]


@dataclass(frozen=True, slots=True)
class RenderRow:
    """A single row ready for monospaced ChordPro rendering."""

    kind: RenderRowKind
    text: str
    source_line_index: int
    segment_index: int = 0

    @property
    def is_control(self) -> bool:
        return self.kind in {"column_break", "page_break"}

    @property
    def is_visible(self) -> bool:
        return not self.is_control


@dataclass(frozen=True, slots=True)
class ChordProLayout:
    """A simple render tree for parsed ChordPro content."""

    rows: tuple[RenderRow, ...]

    @property
    def line_count(self) -> int:
        return sum(1 for row in self.rows if row.is_visible)

    @property
    def max_row_width(self) -> int:
        if not self.rows:
            return 0
        return max((len(row.text) for row in self.rows if row.is_visible), default=0)

    def to_text(self) -> str:
        return "\n".join(row.text for row in self.rows if row.is_visible)


def layout_chordpro_song(
    song: ChordProSong,
    max_width: int | None = None,
) -> ChordProLayout:
    """Build a structured monospaced render layout from a parsed ChordPro song."""
    if max_width is not None and max_width < 1:
        raise ValueError("Maximum layout width must be at least 1.")

    rows: list[RenderRow] = []
    for source_line_index, source_line in enumerate(song.lines):
        if isinstance(source_line, BlankLine):
            rows.append(
                RenderRow(
                    kind="blank",
                    text="",
                    source_line_index=source_line_index,
                )
            )
            continue

        if isinstance(source_line, ChordProDirective):
            _append_directive_rows(rows, source_line, source_line_index)
            continue

        _append_chord_lyric_rows(rows, source_line, source_line_index, max_width)

    return ChordProLayout(rows=tuple(rows))


def _append_directive_rows(
    rows: list[RenderRow],
    directive: ChordProDirective,
    source_line_index: int,
) -> None:
    break_kind = _directive_break_kind(directive)
    if break_kind is not None:
        rows.append(
            RenderRow(
                kind=break_kind,
                text="",
                source_line_index=source_line_index,
            )
        )
        return

    if directive.canonical_name != "comment":
        return

    rows.append(
        RenderRow(
            kind="comment",
            text=directive.value or "",
            source_line_index=source_line_index,
        )
    )


def _directive_break_kind(
    directive: ChordProDirective,
) -> Literal["column_break", "page_break"] | None:
    if directive.canonical_name in {"column_break", "page_break"}:
        return directive.canonical_name
    return None


def _append_chord_lyric_rows(
    rows: list[RenderRow],
    line: ChordLyricLine,
    source_line_index: int,
    max_width: int | None,
) -> None:
    for segment_index, wrapped_line in enumerate(
        wrap_chord_lyric_line(line, max_width)
    ):
        chord_text = render_chord_line(wrapped_line)
        if chord_text:
            rows.append(
                RenderRow(
                    kind="chord",
                    text=chord_text,
                    source_line_index=source_line_index,
                    segment_index=segment_index,
                )
            )

        rows.append(
            RenderRow(
                kind="lyric",
                text=wrapped_line.lyrics,
                source_line_index=source_line_index,
                segment_index=segment_index,
            )
        )
