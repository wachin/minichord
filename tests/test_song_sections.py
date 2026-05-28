from minichord.document import SongSection, build_song_sections, parse_chordpro


def test_song_sections_group_explicit_verse_chorus_and_bridge_markers():
    song = parse_chordpro(
        "\n".join(
            [
                "{sov: Verse 1}",
                "[C]Vine",
                "{eov}",
                "{soc}",
                "[G]Coro",
                "{eoc}",
                "{sob}",
                "[Am]Puente",
                "{eob}",
            ]
        )
    )

    sections = song.sections

    assert [section.kind for section in sections] == [
        "verse",
        "chorus",
        "bridge",
    ]
    assert [section.label for section in sections] == [
        "Verse 1",
        "Chorus",
        "Bridge",
    ]
    assert [section.to_source() for section in sections] == [
        "[C]Vine",
        "[G]Coro",
        "[Am]Puente",
    ]


def test_song_sections_keep_unmarked_content_as_unknown_section():
    song = parse_chordpro("[C]Intro\n{soc}\n[G]Coro\n{eoc}\n[D]Final")

    sections = song.sections

    assert [section.kind for section in sections] == [
        "unknown",
        "chorus",
        "unknown",
    ]
    assert [section.start_line_index for section in sections] == [0, 2, 4]
    assert [section.end_line_index for section in sections] == [0, 2, 4]
    assert [section.to_source() for section in sections] == [
        "[C]Intro",
        "[G]Coro",
        "[D]Final",
    ]


def test_song_sections_preserve_chord_lyric_lines():
    song = parse_chordpro("{soc}\nG    D\nAleluya\n{eoc}")

    section = song.sections[0]

    assert isinstance(section, SongSection)
    assert section.kind == "chorus"
    assert section.line_count == 1
    assert section.chord_lyric_lines[0].lyrics == "Aleluya"
    assert section.to_source() == "G    D\nAleluya"


def test_empty_explicit_sections_are_preserved():
    song = parse_chordpro("{soc}\n{eoc}")

    section = song.sections[0]

    assert section.kind == "chorus"
    assert section.line_count == 0
    assert section.start_line_index == 1
    assert section.end_line_index == 1


def test_build_song_sections_accepts_empty_line_tuple():
    assert build_song_sections(()) == ()
