import pytest

from chordpages.document import (
    DocumentDom,
    DocumentModel,
    ParagraphBlock,
    SongBlock,
)


def test_document_dom_wraps_chordpro_source_as_song_block():
    source = "{title: Gracias}\n{comment: Verse 1}\n[D]Gracias"

    dom = DocumentDom.from_chordpro_text(source)

    assert dom.block_count == 1
    assert isinstance(dom.block(0), SongBlock)
    assert dom.songs[0].kind == "song"
    assert dom.songs[0].title == "Gracias"
    assert dom.songs[0].line_count == 3
    assert dom.to_text() == source


def test_song_block_reconstructs_traditional_chord_pairs():
    source = "G    D/F#  Em\nAmazing grace"

    block = SongBlock.from_source(source)

    assert block.to_source() == source


def test_document_dom_groups_plain_text_into_paragraph_blocks():
    source = "First line\nstill first\n\nSecond paragraph\n\n\nThird paragraph"

    dom = DocumentDom.from_plain_text(source)

    assert dom.block_count == 3
    assert all(paragraph.kind == "paragraph" for paragraph in dom.paragraphs)
    assert [paragraph.line_count for paragraph in dom.paragraphs] == [2, 1, 1]
    assert [paragraph.text for paragraph in dom.paragraphs] == [
        "First line\nstill first",
        "Second paragraph",
        "Third paragraph",
    ]
    assert dom.to_text() == (
        "First line\nstill first\n\nSecond paragraph\n\nThird paragraph"
    )


def test_document_dom_accepts_empty_plain_text():
    dom = DocumentDom.from_plain_text("")

    assert dom.block_count == 0
    assert dom.to_text() == ""


def test_paragraph_block_rejects_blank_lines():
    with pytest.raises(ValueError, match="cannot be blank"):
        ParagraphBlock(lines=("First", "", "Second"))


def test_document_dom_rejects_invalid_block_indexes():
    dom = DocumentDom.from_plain_text("First")

    with pytest.raises(IndexError, match="out of range"):
        dom.block(-1)

    with pytest.raises(IndexError, match="out of range"):
        dom.block(1)


def test_document_model_exposes_internal_dom():
    model = DocumentModel(body_text="{title: Santo}\n[C]Santo")

    dom = model.to_dom()

    assert dom.songs[0].title == "Santo"
    assert dom.to_text() == "{title: Santo}\n[C]Santo"
