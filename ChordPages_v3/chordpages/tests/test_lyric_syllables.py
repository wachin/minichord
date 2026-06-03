import pytest

from chordpages.document import (
    ChordLyricLine,
    ChordToken,
    LyricSyllable,
    build_lyric_syllables,
    parse_chordpro,
    wrap_chord_lyric_line,
)


def test_inline_chords_attach_to_hyphenated_lyric_syllables():
    song = parse_chordpro("[G]A-le-[D]lu-ya [C]amen")

    syllables = song.chord_lyric_lines[0].syllables

    assert [syllable.text for syllable in syllables] == [
        "A-",
        "le-",
        "lu-",
        "ya",
        "amen",
    ]
    assert [(syllable.start_index, syllable.end_index) for syllable in syllables] == [
        (0, 2),
        (2, 5),
        (5, 8),
        (8, 10),
        (11, 15),
    ]
    assert [[chord.symbol for chord in syllable.chords] for syllable in syllables] == [
        ["G"],
        [],
        ["D"],
        [],
        ["C"],
    ]


def test_traditional_chord_columns_attach_to_covered_syllables():
    song = parse_chordpro("G    D/F#  Em\nAmazing grace")

    syllables = song.chord_lyric_lines[0].syllables

    assert [syllable.text for syllable in syllables] == ["Amazing", "grace"]
    assert [[chord.symbol for chord in syllable.chords] for syllable in syllables] == [
        ["G", "D/F#"],
        ["Em"],
    ]


def test_chords_anchored_on_space_attach_to_following_syllable():
    syllables = build_lyric_syllables(
        "Sing again",
        chords=(ChordToken(symbol="C", lyric_index=4),),
    )

    assert [syllable.text for syllable in syllables] == ["Sing", "again"]
    assert [chord.symbol for chord in syllables[1].chords] == ["C"]


def test_chords_after_lyric_end_attach_to_last_syllable():
    syllables = build_lyric_syllables(
        "Amen",
        chords=(ChordToken(symbol="G", lyric_index=20),),
    )

    assert [syllable.text for syllable in syllables] == ["Amen"]
    assert [chord.symbol for chord in syllables[0].chords] == ["G"]


def test_empty_lyrics_have_no_syllables():
    line = ChordLyricLine(
        lyrics="",
        chords=(ChordToken(symbol="C", lyric_index=0),),
        source="[C]",
    )

    assert line.syllables == ()


def test_wrapped_lines_recompute_syllable_chord_indexes():
    line = parse_chordpro("[C]Amazing [G]grace").chord_lyric_lines[0]

    wrapped_lines = wrap_chord_lyric_line(line, max_width=7)

    assert [wrapped_line.lyrics for wrapped_line in wrapped_lines] == [
        "Amazing",
        "grace",
    ]
    assert [wrapped_lines[0].syllables[0].chords[0].symbol] == ["C"]
    assert [wrapped_lines[1].syllables[0].chords[0].symbol] == ["G"]


def test_lyric_syllable_validates_text_and_range():
    with pytest.raises(ValueError, match="text"):
        LyricSyllable(text="", start_index=0, end_index=0)

    with pytest.raises(ValueError, match="range"):
        LyricSyllable(text="A", start_index=1, end_index=1)

    with pytest.raises(ValueError, match="match"):
        LyricSyllable(text="Amen", start_index=0, end_index=3)
