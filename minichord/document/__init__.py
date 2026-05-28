"""Document data structures used by miniChord."""

from minichord.document.chordpro import (
    BlankLine,
    ChordLyricLine,
    ChordProDirective,
    ChordProSong,
    ChordToken,
    LyricSyllable,
    SongSection,
    SongSectionKind,
    build_lyric_syllables,
    build_song_sections,
    parse_chordpro,
    render_chord_line,
    render_chord_over_lyrics,
    wrap_chord_lyric_line,
)
from minichord.document.dom import (
    DocumentBlock,
    DocumentDom,
    ParagraphBlock,
    SongBlock,
)
from minichord.document.layout import ChordProLayout, RenderRow, layout_chordpro_song
from minichord.document.model import MiniChordDocument
from minichord.document.pagination import (
    PaginatedLayout,
    RenderColumn,
    RenderPage,
    paginate_layout,
)
from minichord.document.page import (
    CUSTOM_PAGE_SIZE,
    MARGIN_PRESETS_MM,
    MarginPresetName,
    PageLayout,
    PageMargins,
    margin_preset_names,
)
from minichord.document.songbook import MiniChordSongbook
from minichord.document.structure import DocumentModel, DocumentPage

__all__ = [
    "BlankLine",
    "ChordLyricLine",
    "ChordProDirective",
    "ChordProLayout",
    "ChordProSong",
    "ChordToken",
    "CUSTOM_PAGE_SIZE",
    "DocumentBlock",
    "DocumentDom",
    "DocumentModel",
    "DocumentPage",
    "MiniChordDocument",
    "MiniChordSongbook",
    "MARGIN_PRESETS_MM",
    "MarginPresetName",
    "ParagraphBlock",
    "PaginatedLayout",
    "PageLayout",
    "PageMargins",
    "RenderColumn",
    "RenderPage",
    "RenderRow",
    "LyricSyllable",
    "SongBlock",
    "SongSection",
    "SongSectionKind",
    "build_lyric_syllables",
    "build_song_sections",
    "layout_chordpro_song",
    "margin_preset_names",
    "paginate_layout",
    "parse_chordpro",
    "render_chord_line",
    "render_chord_over_lyrics",
    "wrap_chord_lyric_line",
]
