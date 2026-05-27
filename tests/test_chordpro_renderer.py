from minichord.document import (
    ChordLyricLine,
    ChordToken,
    MiniChordDocument,
    parse_chordpro,
    render_chord_line,
    render_chord_over_lyrics,
)


def test_render_inline_chords_above_lyrics():
    song = parse_chordpro("[C]Amazing [G]grace")

    assert render_chord_over_lyrics(song) == "C       G\nAmazing grace"


def test_render_chord_line_moves_colliding_chords_apart():
    line = ChordLyricLine(
        lyrics="Grace",
        chords=(
            ChordToken(symbol="Cmaj7", lyric_index=0),
            ChordToken(symbol="G", lyric_index=0),
        ),
        source="[Cmaj7][G]Grace",
    )

    assert render_chord_line(line) == "Cmaj7 G"


def test_render_traditional_chord_pair_uses_source_columns():
    song = parse_chordpro("G    D/F#  Em\nAmazing grace")

    assert render_chord_over_lyrics(song) == "G    D/F#  Em\nAmazing grace"


def test_render_comments_and_blank_lines_without_metadata_directives():
    song = parse_chordpro("{title: Song}\n{comment: Verse 1}\n\n[G]Sing")

    assert render_chord_over_lyrics(song) == "Verse 1\n\nG\nSing"


def test_document_can_render_chord_over_lyrics_text():
    document = MiniChordDocument(text="[D]Gracias [A]Senor")

    assert document.to_chord_over_lyrics_text() == "D       A\nGracias Senor"
