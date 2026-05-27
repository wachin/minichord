import pytest

from minichord.document import (
    MiniChordDocument,
    RenderColumn,
    RenderPage,
    layout_chordpro_song,
    paginate_layout,
    parse_chordpro,
)


def test_paginate_single_column_creates_pages_from_row_capacity():
    song = parse_chordpro("[C]One\n[D]Two\n[Em]Three")
    layout = layout_chordpro_song(song)

    pagination = paginate_layout(layout, rows_per_column=4)

    assert pagination.page_count == 2
    assert pagination.row_count == 6
    assert [page.line_count for page in pagination.pages] == [4, 2]
    assert pagination.pages[0].to_text() == "C\nOne\nD\nTwo"
    assert pagination.pages[1].to_text() == "Em\nThree"


def test_paginate_keeps_chord_and_lyric_rows_together():
    song = parse_chordpro("[C]One\n[D]Two")
    layout = layout_chordpro_song(song)

    pagination = paginate_layout(layout, rows_per_column=3)

    assert pagination.page_count == 2
    assert [page.to_text() for page in pagination.pages] == [
        "C\nOne",
        "D\nTwo",
    ]


def test_paginate_keeps_oversized_group_together_in_empty_column():
    song = parse_chordpro("[C]One")
    layout = layout_chordpro_song(song)

    pagination = paginate_layout(layout, rows_per_column=1)

    assert pagination.page_count == 1
    assert pagination.pages[0].columns[0].line_count == 2
    assert pagination.pages[0].to_text() == "C\nOne"


def test_paginate_flows_rows_across_columns_before_next_page():
    song = parse_chordpro("[C]One\n[D]Two\n[Em]Three")
    layout = layout_chordpro_song(song)

    pagination = paginate_layout(layout, rows_per_column=2, column_count=2)

    assert pagination.page_count == 2
    assert pagination.pages[0] == RenderPage(
        page_index=0,
        columns=(
            RenderColumn(page_index=0, column_index=0, rows=layout.rows[0:2]),
            RenderColumn(page_index=0, column_index=1, rows=layout.rows[2:4]),
        ),
    )
    assert [row.text for row in pagination.pages[1].columns[0].rows] == [
        "Em",
        "Three",
    ]
    assert pagination.pages[1].columns[1].is_empty


def test_paginate_empty_layout_can_still_create_blank_page():
    layout = layout_chordpro_song(parse_chordpro(""))

    pagination = paginate_layout(layout, rows_per_column=4, column_count=2)

    assert pagination.page_count == 1
    assert pagination.row_count == 0
    assert len(pagination.pages[0].columns) == 2
    assert all(column.is_empty for column in pagination.pages[0].columns)


def test_paginate_empty_layout_can_return_no_pages():
    layout = layout_chordpro_song(parse_chordpro(""))

    pagination = paginate_layout(layout, rows_per_column=4, ensure_page=False)

    assert pagination.page_count == 0
    assert pagination.row_count == 0


def test_document_can_build_paginated_layout():
    document = MiniChordDocument(text="[G]Sing\n[D]Praise")

    pagination = document.to_paginated_layout(rows_per_column=2)

    assert pagination.page_count == 2
    assert [page.to_text() for page in pagination.pages] == [
        "G\nSing",
        "D\nPraise",
    ]


def test_paginate_rejects_invalid_dimensions():
    layout = layout_chordpro_song(parse_chordpro("[C]Sing"))

    with pytest.raises(ValueError, match="Rows per column"):
        paginate_layout(layout, rows_per_column=0)

    with pytest.raises(ValueError, match="Column count"):
        paginate_layout(layout, rows_per_column=1, column_count=0)
