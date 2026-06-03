from chordpages.document import CHORDPAGES_PAGE_SIZE, ChordPagesSongbook


def test_mchordbook_round_trip_preserves_songbook_settings():
    songbook = ChordPagesSongbook(
        title="Sunday Morning",
        songs=["songs/amazing-grace.mchord", "songs/how-great.mchord"],
        page_size="A4",
        orientation="landscape",
        margins="narrow",
        column_count=2,
        index_enabled=True,
        index_position="beginning",
    )

    loaded = ChordPagesSongbook.from_mchordbook(songbook.to_mchordbook())

    assert loaded.title == "Sunday Morning"
    assert loaded.songs == ["songs/amazing-grace.mchord", "songs/how-great.mchord"]
    assert loaded.page_size == "A4"
    assert loaded.orientation == "landscape"
    assert loaded.margins == "narrow"
    assert loaded.column_count == 2
    assert loaded.index_enabled is True
    assert loaded.index_position == "beginning"


def test_mchordbook_loads_unknown_content_as_empty_songbook():
    loaded = ChordPagesSongbook.from_mchordbook("not a songbook")

    assert loaded.title == "Untitled Songbook"
    assert loaded.songs == []
    assert loaded.page_size == CHORDPAGES_PAGE_SIZE


def test_mchordbook_quotes_paths_that_need_yaml_escaping():
    songbook = ChordPagesSongbook(
        title="2026",
        songs=["songs/song:with-colon.mchord"],
    )

    loaded = ChordPagesSongbook.from_mchordbook(songbook.to_mchordbook())

    assert loaded.title == "2026"
    assert loaded.songs == ["songs/song:with-colon.mchord"]
