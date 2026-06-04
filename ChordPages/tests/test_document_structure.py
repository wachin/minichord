import pytest

from chordpages.document import (
    DocumentModel,
    DocumentPage,
    ChordPagesDocument,
    PageLayout,
    PageMargins,
)


def test_document_model_adapts_storage_document_and_round_trips():
    document = ChordPagesDocument(
        title="Vine a adorarte",
        text="[G]Vine a adorarte\n",
        version=3,
    )

    model = DocumentModel.from_document(document)

    assert model.title == "Vine a adorarte"
    assert model.body_text == "[G]Vine a adorarte\n"
    assert model.version == 3
    assert model.page_count == 1
    assert model.page(0).page_id == "page-1"
    assert model.to_document() == document


def test_document_model_uses_supplied_initial_page_layout():
    layout = PageLayout(
        page_size="Letter",
        orientation="landscape",
        margins=PageMargins(left=15, top=12, right=15, bottom=12),
    )

    model = DocumentModel.from_document(ChordPagesDocument(), layout=layout)

    assert model.page(0).layout == layout
    assert model.page(0).size_mm == (279.4, 215.9)
    assert model.page(0).writable_size_mm == pytest.approx((249.4, 191.9))


def test_document_model_requires_at_least_one_page():
    with pytest.raises(ValueError, match="at least one page"):
        DocumentModel(pages=())


def test_document_model_rejects_duplicate_page_ids():
    with pytest.raises(ValueError, match="Duplicate document page id"):
        DocumentModel(pages=(DocumentPage(page_id="page-1"), DocumentPage()))


def test_document_model_rejects_invalid_page_indexes():
    model = DocumentModel()

    with pytest.raises(IndexError, match="out of range"):
        model.page(-1)

    with pytest.raises(IndexError, match="out of range"):
        model.page(1)


def test_document_page_validates_layout_geometry():
    invalid_layout = PageLayout(margins=PageMargins(left=120, right=120))

    with pytest.raises(ValueError, match="Horizontal margins"):
        DocumentPage(layout=invalid_layout)


def test_document_page_normalizes_ids_and_rejects_blank_ids():
    assert DocumentPage(page_id=" page-2 ").page_id == "page-2"

    with pytest.raises(ValueError, match="page id"):
        DocumentPage(page_id=" ")


def test_document_model_updates_body_and_title_immutably():
    model = DocumentModel()

    updated = model.with_title("Updated").with_body_text("[C]Updated")

    assert model.title == "Untitled Song"
    assert model.body_text == ""
    assert updated.title == "Updated"
    assert updated.body_text == "[C]Updated"


def test_document_model_drives_existing_render_pipeline():
    model = DocumentModel(body_text="[C]One\n[D]Two")

    layout = model.to_chordpro_layout()
    pagination = model.to_paginated_layout(rows_per_column=2)

    assert layout.to_text() == "C\nOne\nD\nTwo"
    assert model.to_chord_over_lyrics_text() == "C\nOne\nD\nTwo"
    assert [page.to_text() for page in pagination.pages] == [
        "C\nOne",
        "D\nTwo",
    ]


def test_document_model_can_paginate_from_page_geometry():
    model = DocumentModel(body_text="[C]One\n[D]Two")
    model = model.with_page_layout(0, PageLayout(page_size="A4"))

    pagination = model.to_page_paginated_layout(line_height_mm=100.0)

    assert pagination.rows_per_column == 2
    assert [page.to_text() for page in pagination.pages] == [
        "C\nOne",
        "D\nTwo",
    ]


def test_document_model_page_pagination_reacts_to_orientation():
    model = DocumentModel(body_text="[C]One")
    margins = PageMargins(top=20.0, bottom=20.0)
    model = model.with_page_layout(
        0,
        PageLayout(page_size="A4", margins=margins),
    )
    landscape = model.with_page_layout(
        0,
        PageLayout(page_size="A4", orientation="landscape", margins=margins),
    )

    assert model.to_page_paginated_layout(line_height_mm=10.0).rows_per_column == 25
    assert landscape.to_page_paginated_layout(line_height_mm=10.0).rows_per_column == 17


def test_document_model_replaces_page_layout_immutably():
    model = DocumentModel()
    landscape = PageLayout(orientation="landscape")

    updated = model.with_page_layout(0, landscape)

    assert model.page(0).layout.orientation == "portrait"
    assert updated.page(0).layout == landscape
    assert updated.page(0).page_id == "page-1"


def test_document_model_appends_pages_with_stable_ids():
    model = DocumentModel().append_page().append_page(page_id="ending")

    assert model.page_count == 3
    assert [page.page_id for page in model.pages] == [
        "page-1",
        "page-2",
        "ending",
    ]
    assert model.page_number("ending") == 3


def test_document_model_validates_appended_page_id():
    with pytest.raises(ValueError, match="page id"):
        DocumentModel().append_page(page_id="")


def test_document_model_append_page_inherits_previous_layout_by_default():
    model = DocumentModel().with_page_layout(0, PageLayout(page_size="Legal"))

    updated = model.append_page()

    assert updated.page(1).layout == PageLayout(page_size="Legal")
