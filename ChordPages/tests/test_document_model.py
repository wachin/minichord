from chordpages.document import ChordPagesDocument


def test_mchord_round_trip_preserves_text_and_title():
    document = ChordPagesDocument(title="Vine a adorarte", text="[G]Vine a adorarte\n")

    loaded = ChordPagesDocument.from_mchord(document.to_mchord())

    assert loaded.title == "Vine a adorarte"
    assert loaded.text == "[G]Vine a adorarte\n"


def test_plain_text_loads_as_document_body():
    loaded = ChordPagesDocument.from_mchord("plain song text")

    assert loaded.text == "plain song text"
    assert loaded.title == "Untitled Song"
