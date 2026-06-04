from chordpages.document import (
    ChordLyricLine,
    ChordToken,
    ChordPagesDocument,
    parse_chordpro,
    render_chord_line,
    render_chord_over_lyrics,
    wrap_chord_lyric_line,
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
    document = ChordPagesDocument(text="[D]Gracias [A]Senor")

    assert document.to_chord_over_lyrics_text() == "D       A\nGracias Senor"


def test_render_wraps_chords_with_their_lyrics():
    song = parse_chordpro("[C]Amazing [G]grace [F]how sweet the [C]sound")

    assert render_chord_over_lyrics(song, max_width=13) == (
        "C       G\n"
        "Amazing grace\n"
        "F\n"
        "how sweet the\n"
        "C\n"
        "sound"
    )


def test_wrap_chord_lyric_line_reanchors_chords_to_segments():
    line = parse_chordpro("[C]Amazing [G]grace [F]how sweet").chord_lyric_lines[0]

    wrapped_lines = wrap_chord_lyric_line(line, max_width=13)

    assert [wrapped_line.lyrics for wrapped_line in wrapped_lines] == [
        "Amazing grace",
        "how sweet",
    ]
    assert wrapped_lines[0].chords == (
        ChordToken(symbol="C", lyric_index=0),
        ChordToken(symbol="G", lyric_index=8),
    )
    assert wrapped_lines[1].chords == (ChordToken(symbol="F", lyric_index=0),)


def test_render_wraps_long_words_without_chords_on_continuations():
    song = parse_chordpro("[C]Supercalifragilistic")

    assert render_chord_over_lyrics(song, max_width=5) == (
        "C\n"
        "Super\n"
        "calif\n"
        "ragil\n"
        "istic"
    )


def test_document_render_accepts_max_width():
    document = ChordPagesDocument(text="[D]Gracias [A]Senor por tu amor")

    assert document.to_chord_over_lyrics_text(max_width=13) == (
        "D       A\n"
        "Gracias Senor\n"
        "por tu amor"
    )


def test_render_rejects_invalid_max_width():
    song = parse_chordpro("[C]Sing")

    try:
        render_chord_over_lyrics(song, max_width=0)
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("Expected invalid max_width to raise ValueError.")
