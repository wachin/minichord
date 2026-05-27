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
    row_groups = _keep_together_row_groups(layout.rows)
    group_index = 0
    page_index = 0

    while group_index < len(row_groups) or (ensure_page and not pages):
        columns: list[RenderColumn] = []
        page_break_requested = False
        for column_index in range(column_count):
            column_rows: list[RenderRow] = []
            while group_index < len(row_groups):
                next_group = row_groups[group_index]
                break_kind = _break_kind(next_group)
                if break_kind == "page_break":
                    group_index += 1
                    page_break_requested = True
                    break
                if break_kind == "column_break":
                    group_index += 1
                    break

                if column_rows and len(column_rows) + len(next_group) > rows_per_column:
                    break

                column_rows.extend(next_group)
                group_index += 1

                if len(column_rows) >= rows_per_column:
                    break

            columns.append(
                RenderColumn(
                    page_index=page_index,
                    column_index=column_index,
                    rows=tuple(column_rows),
                )
            )
            if page_break_requested:
                break

        if page_break_requested and not _columns_have_rows(columns):
            continue

        while len(columns) < column_count:
            columns.append(
                RenderColumn(
                    page_index=page_index,
                    column_index=len(columns),
                    rows=(),
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


def _keep_together_row_groups(
    rows: tuple[RenderRow, ...],
) -> tuple[tuple[RenderRow, ...], ...]:
    groups: list[tuple[RenderRow, ...]] = []
    current_group: list[RenderRow] = []
    current_key: tuple[int, int] | None = None

    for row in rows:
        row_key = (row.source_line_index, row.segment_index)
        if current_group and row_key != current_key:
            groups.append(tuple(current_group))
            current_group = []

        current_group.append(row)
        current_key = row_key

    if current_group:
        groups.append(tuple(current_group))

    return tuple(groups)


def _break_kind(row_group: tuple[RenderRow, ...]) -> str | None:
    if len(row_group) != 1:
        return None

    row = row_group[0]
    if row.kind in {"column_break", "page_break"}:
        return row.kind
    return None


def _columns_have_rows(columns: list[RenderColumn]) -> bool:
    return any(column.rows for column in columns)
