"""Internal semantic document tree primitives for ChordPages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from chordpages.document.chordpro import (
    ChordProSong,
    parse_chordpro,
    source_lines_for_song_line,
)


@dataclass(frozen=True, slots=True)
class ParagraphBlock:
    """A plain text paragraph made of one or more non-blank source lines."""

    lines: tuple[str, ...]

    def __post_init__(self) -> None:
        lines = tuple(self.lines)
        if not lines:
            raise ValueError("Paragraph block must contain at least one line.")
        if any("\n" in line or "\r" in line for line in lines):
            raise ValueError("Paragraph block lines cannot contain newlines.")
        if any(line.strip() == "" for line in lines):
            raise ValueError("Paragraph block lines cannot be blank.")
        object.__setattr__(self, "lines", lines)

    @property
    def kind(self) -> Literal["paragraph"]:
        return "paragraph"

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)

    @classmethod
    def from_text(cls, text: str) -> "ParagraphBlock":
        normalized = _normalize_text(text)
        return cls(lines=tuple(normalized.split("\n")))


@dataclass(frozen=True, slots=True)
class SongBlock:
    """A ChordPro song block inside the internal document tree."""

    song: ChordProSong

    @property
    def kind(self) -> Literal["song"]:
        return "song"

    @property
    def title(self) -> str:
        return self.song.title

    @property
    def line_count(self) -> int:
        return len(self.song.lines)

    def to_source(self) -> str:
        """Render the block back to ChordPro-like source text."""
        source_lines: list[str] = []
        for line in self.song.lines:
            source_lines.extend(source_lines_for_song_line(line))
        return "\n".join(source_lines)

    @classmethod
    def from_source(cls, source: str) -> "SongBlock":
        return cls(song=parse_chordpro(source))


DocumentBlock = ParagraphBlock | SongBlock


@dataclass(frozen=True, slots=True)
class DocumentDom:
    """A semantic document tree independent from visual page layout."""

    blocks: tuple[DocumentBlock, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocks", tuple(self.blocks))

    @property
    def block_count(self) -> int:
        return len(self.blocks)

    @property
    def paragraphs(self) -> tuple[ParagraphBlock, ...]:
        return tuple(
            block for block in self.blocks if isinstance(block, ParagraphBlock)
        )

    @property
    def songs(self) -> tuple[SongBlock, ...]:
        return tuple(
            block for block in self.blocks if isinstance(block, SongBlock)
        )

    def block(self, block_index: int) -> DocumentBlock:
        if block_index < 0 or block_index >= len(self.blocks):
            raise IndexError("Document DOM block index out of range.")
        return self.blocks[block_index]

    def to_text(self) -> str:
        return "\n\n".join(_block_to_text(block) for block in self.blocks)

    @classmethod
    def from_chordpro_text(cls, source: str) -> "DocumentDom":
        return cls(blocks=(SongBlock.from_source(source),))

    @classmethod
    def from_plain_text(cls, source: str) -> "DocumentDom":
        normalized = _normalize_text(source)
        paragraphs: list[ParagraphBlock] = []
        current_lines: list[str] = []

        for line in normalized.split("\n"):
            if line.strip() == "":
                if current_lines:
                    paragraphs.append(ParagraphBlock(lines=tuple(current_lines)))
                    current_lines = []
                continue
            current_lines.append(line)

        if current_lines:
            paragraphs.append(ParagraphBlock(lines=tuple(current_lines)))

        return cls(blocks=tuple(paragraphs))


def _block_to_text(block: DocumentBlock) -> str:
    if isinstance(block, SongBlock):
        return block.to_source()
    return block.text


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")
