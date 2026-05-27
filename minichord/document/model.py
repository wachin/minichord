"""Minimal text-based document model for the first miniChord prototype."""

from __future__ import annotations

from dataclasses import dataclass

from minichord.document.chordpro import (
    ChordProSong,
    parse_chordpro,
    render_chord_over_lyrics,
)
from minichord.document.layout import ChordProLayout, layout_chordpro_song


FRONT_MATTER_DELIMITER = "---"


@dataclass(slots=True)
class MiniChordDocument:
    """A single-song document that can round-trip a simple .mchord file."""

    text: str = ""
    title: str = "Untitled Song"
    version: int = 1

    def to_mchord(self) -> str:
        """Serialize the document to a small Git-friendly .mchord document."""
        title = self.title.replace("\n", " ").strip() or "Untitled Song"
        text = self.text.rstrip("\n")
        return (
            f"{FRONT_MATTER_DELIMITER}\n"
            "format: minichord-song\n"
            f"version: {self.version}\n"
            f"title: {title}\n"
            f"{FRONT_MATTER_DELIMITER}\n\n"
            f"{text}\n"
        )

    def to_chordpro_song(self) -> ChordProSong:
        """Parse the document body as ChordPro source."""
        return parse_chordpro(self.text)

    def to_chordpro_layout(self, max_width: int | None = None) -> ChordProLayout:
        """Build a structured render layout for the document body."""
        return layout_chordpro_song(self.to_chordpro_song(), max_width=max_width)

    def to_chord_over_lyrics_text(self, max_width: int | None = None) -> str:
        """Render the document body as monospaced chord-over-lyrics text."""
        return render_chord_over_lyrics(
            self.to_chordpro_song(),
            max_width=max_width,
        )

    @classmethod
    def from_mchord(cls, content: str) -> "MiniChordDocument":
        """Load the subset of .mchord used by the prototype."""
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        if not normalized.startswith(f"{FRONT_MATTER_DELIMITER}\n"):
            return cls(text=normalized)

        parts = normalized.split(f"\n{FRONT_MATTER_DELIMITER}\n", 1)
        if len(parts) != 2:
            return cls(text=normalized)

        metadata_block = parts[0].removeprefix(f"{FRONT_MATTER_DELIMITER}\n")
        body = parts[1].lstrip("\n")
        metadata = _parse_metadata(metadata_block)
        parsed_song = parse_chordpro(body)
        return cls(
            text=body,
            title=(
                metadata.get("title")
                or parsed_song.title
                or "Untitled Song"
            ),
            version=_parse_version(metadata.get("version")),
        )


def _parse_metadata(metadata_block: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in metadata_block.splitlines():
        key, separator, value = raw_line.partition(":")
        if not separator:
            continue
        metadata[key.strip()] = value.strip()
    return metadata


def _parse_version(value: str | None) -> int:
    if value is None:
        return 1
    try:
        return int(value)
    except ValueError:
        return 1
