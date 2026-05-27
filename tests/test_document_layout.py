import pytest

from minichord.document import (
    MiniChordDocument,
    RenderRow,
    layout_chordpro_song,
    parse_chordpro,
    render_chord_over_lyrics,
)


def test_layout_rows_keep_render_kind_and_source_line():
    song = parse_chordpro("{title: Song}\n{comment: Verse 1}\n\n[C]Amazing")

    layout = layout_chordpro_song(song)

    assert layout.rows == (
        RenderRow(kind="comment", text="Verse 1", source_line_index=1),
        RenderRow(kind="blank", text="", source_line_index=2),
        RenderRow(kind="chord", text="C", source_line_index=3, segment_index=0),
        RenderRow(
            kind="lyric",
            text="Amazing",
            source_line_index=3,
            segment_index=0,
        ),
    )


def test_layout_to_text_matches_renderer_output():
    song = parse_chordpro("[C]Amazing [G]grace [F]how sweet the [C]sound")

    layout = layout_chordpro_song(song, max_width=13)

    assert layout.to_text() == render_chord_over_lyrics(song, max_width=13)
    assert layout.line_count == 6
    assert layout.max_row_width == 13


def test_layout_exposes_wrapped_segment_indexes():
    song = parse_chordpro("[D]Gracias [A]Senor por tu amor")

    layout = layout_chordpro_song(song, max_width=13)

    assert [row.segment_index for row in layout.rows] == [0, 0, 1]
    assert [row.kind for row in layout.rows] == ["chord", "lyric", "lyric"]
    assert [row.text for row in layout.rows] == [
        "D       A",
        "Gracias Senor",
        "por tu amor",
    ]


def test_document_can_build_chordpro_layout():
    document = MiniChordDocument(text="[G]Sing to the [D]Lord")

    layout = document.to_chordpro_layout(max_width=12)

    assert layout.to_text() == "G\nSing to the\nD\nLord"


def test_layout_rejects_invalid_width():
    song = parse_chordpro("[C]Sing")

    with pytest.raises(ValueError, match="at least 1"):
        layout_chordpro_song(song, max_width=0)
