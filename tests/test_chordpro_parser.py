from minichord.document import (
    BlankLine,
    ChordLyricLine,
    ChordProDirective,
    ChordToken,
    MiniChordDocument,
    parse_chordpro,
)


def test_parse_chordpro_metadata_and_required_directives():
    song = parse_chordpro(
        "\n".join(
            [
                "{title: Vine a adorarte}",
                "{artist: Marcela Gandara}",
                "{key: G}",
                "{tempo: 72}",
                "{album: En vivo}",
                "{capo: 2}",
                "{subtitle: Worship}",
            ]
        )
    )

    assert song.metadata == {
        "album": "En vivo",
        "artist": "Marcela Gandara",
        "capo": "2",
        "key": "G",
        "subtitle": "Worship",
        "tempo": "72",
        "title": "Vine a adorarte",
    }
    assert song.title == "Vine a adorarte"
    assert all(isinstance(line, ChordProDirective) for line in song.lines)


def test_parse_inline_chords_as_tokens_anchored_to_lyrics():
    song = parse_chordpro("[G]Vine [D]a [Em]adorarte")

    line = song.chord_lyric_lines[0]

    assert line == ChordLyricLine(
        lyrics="Vine a adorarte",
        chords=(
            ChordToken(symbol="G", lyric_index=0),
            ChordToken(symbol="D", lyric_index=5),
            ChordToken(symbol="Em", lyric_index=7),
        ),
        source="[G]Vine [D]a [Em]adorarte",
    )
    assert line.has_chords


def test_parse_comments_section_markers_and_blank_lines():
    song = parse_chordpro("{comment: Intro}\n\n{soc}\nAleluya\n{eoc}")

    assert isinstance(song.lines[0], ChordProDirective)
    assert song.lines[0].name == "comment"
    assert song.lines[0].value == "Intro"
    assert isinstance(song.lines[1], BlankLine)
    assert song.lines[2].canonical_name == "start_of_chorus"
    assert song.lines[4].canonical_name == "end_of_chorus"


def test_parse_unclosed_or_empty_chord_marker_as_literal_text():
    song = parse_chordpro("Sing [ with [] us")

    line = song.chord_lyric_lines[0]

    assert line.lyrics == "Sing [ with [] us"
    assert line.chords == ()


def test_document_can_expose_parsed_chordpro_song():
    document = MiniChordDocument(text="{title: Gracias}\n[D]Gracias")

    song = document.to_chordpro_song()

    assert song.title == "Gracias"
    assert song.chord_lyric_lines[0].chords[0].symbol == "D"
