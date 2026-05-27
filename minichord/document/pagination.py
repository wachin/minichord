"""Row-based pagination primitives for miniChord document layouts."""

from __future__ import annotations

from dataclasses import dataclass

from minichord.document.layout import ChordProLayout, RenderRow


@dataclass(frozen=True, slots=True)
class RenderColumn:
    """A fixed-height column of render rows on a page."""

    page_index: int
    column_index: int
    rows: tuple[RenderRow, ...]

    @property
    def line_count(self) -> int:
        return len(self.rows)

    @property
    def is_empty(self) -> bool:
        return not self.rows

    def to_text(self) -> str:
        return "\n".join(row.text for row in self.rows)


@dataclass(frozen=True, slots=True)
class RenderPage:
    """A page containing one or more render columns."""

    page_index: int
    columns: tuple[RenderColumn, ...]

    @property
    def page_number(self) -> int:
        return self.page_index + 1

    @property
    def rows(self) -> tuple[RenderRow, ...]:
        return tuple(row for column in self.columns for row in column.rows)

    @property
    def line_count(self) -> int:
        return sum(column.line_count for column in self.columns)

    def to_text(self, column_separator: str = "\n") -> str:
        return column_separator.join(
            column.to_text() for column in self.columns if not column.is_empty
        )


@dataclass(frozen=True, slots=True)
class PaginatedLayout:
    """A row layout distributed into pages and columns."""

    pages: tuple[RenderPage, ...]
    rows_per_column: int
    column_count: int

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def row_count(self) -> int:
        return sum(page.line_count for page in self.pages)


def paginate_layout(
    layout: ChordProLayout,
    rows_per_column: int,
    column_count: int = 1,
    ensure_page: bool = True,
) -> PaginatedLayout:
    """Flow render rows into fixed-height columns and pages."""
    if rows_per_column < 1:
        raise ValueError("Rows per column must be at least 1.")
    if column_count < 1:
        raise ValueError("Column count must be at least 1.")

    pages: list[RenderPage] = []
    row_index = 0
    page_index = 0

    while row_index < len(layout.rows) or (ensure_page and not pages):
        columns: list[RenderColumn] = []
        for column_index in range(column_count):
            column_rows = layout.rows[row_index : row_index + rows_per_column]
            row_index += len(column_rows)
            columns.append(
                RenderColumn(
                    page_index=page_index,
                    column_index=column_index,
                    rows=column_rows,
                )
            )

        pages.append(
            RenderPage(
                page_index=page_index,
                columns=tuple(columns),
            )
        )
        page_index += 1

    return PaginatedLayout(
        pages=tuple(pages),
        rows_per_column=rows_per_column,
        column_count=column_count,
    )
