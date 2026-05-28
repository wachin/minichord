"""Page-based document model abstractions for miniChord."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable

from minichord.document.chordpro import ChordProSong
from minichord.document.dom import DocumentDom
from minichord.document.layout import ChordProLayout
from minichord.document.model import MiniChordDocument
from minichord.document.pagination import PaginatedLayout
from minichord.document.page import DEFAULT_TEXT_LINE_HEIGHT_MM, PageLayout


DEFAULT_PAGE_ID = "page-1"


@dataclass(frozen=True, slots=True)
class DocumentPage:
    """A logical document page with physical layout metadata."""

    page_id: str = DEFAULT_PAGE_ID
    layout: PageLayout = field(default_factory=PageLayout)

    def __post_init__(self) -> None:
        normalized_page_id = self.page_id.strip()
        if not normalized_page_id:
            raise ValueError("Document page id cannot be empty.")

        object.__setattr__(self, "page_id", normalized_page_id)
        self.layout.writable_size_mm

    @property
    def size_mm(self) -> tuple[float, float]:
        """Physical page size in millimeters."""
        return self.layout.size_mm

    @property
    def writable_size_mm(self) -> tuple[float, float]:
        """Writable page area after margins in millimeters."""
        return self.layout.writable_size_mm


@dataclass(frozen=True, slots=True)
class DocumentModel:
    """Page-based editing model that can adapt the current .mchord document."""

    body_text: str = ""
    title: str = "Untitled Song"
    pages: tuple[DocumentPage, ...] = field(
        default_factory=lambda: (DocumentPage(),)
    )
    version: int = 1

    def __post_init__(self) -> None:
        pages = tuple(self.pages)
        if not pages:
            raise ValueError("A document model must contain at least one page.")
        _validate_unique_page_ids(pages)
        object.__setattr__(self, "pages", pages)

    @property
    def page_count(self) -> int:
        """Number of logical pages in the document."""
        return len(self.pages)

    def page(self, page_index: int) -> DocumentPage:
        """Return the page at a zero-based index."""
        if page_index < 0 or page_index >= len(self.pages):
            raise IndexError("Document page index out of range.")
        return self.pages[page_index]

    def page_number(self, page_id: str) -> int:
        """Return the one-based page number for a page id."""
        for page_index, page in enumerate(self.pages):
            if page.page_id == page_id:
                return page_index + 1
        raise ValueError(f"Unknown document page id: {page_id}")

    def to_document(self) -> MiniChordDocument:
        """Convert the editing model back to the current storage document."""
        return MiniChordDocument(
            text=self.body_text,
            title=self.title,
            version=self.version,
        )

    def to_chordpro_song(self) -> ChordProSong:
        """Parse the document body as ChordPro source."""
        return self.to_document().to_chordpro_song()

    def to_chordpro_layout(self, max_width: int | None = None) -> ChordProLayout:
        """Build a structured render layout for the document body."""
        return self.to_document().to_chordpro_layout(max_width=max_width)

    def to_paginated_layout(
        self,
        rows_per_column: int,
        column_count: int = 1,
        max_width: int | None = None,
    ) -> PaginatedLayout:
        """Build a row-based paginated layout for the document body."""
        return self.to_document().to_paginated_layout(
            rows_per_column=rows_per_column,
            column_count=column_count,
            max_width=max_width,
        )

    def to_page_paginated_layout(
        self,
        page_index: int = 0,
        line_height_mm: float = DEFAULT_TEXT_LINE_HEIGHT_MM,
        column_count: int = 1,
        max_width: int | None = None,
    ) -> PaginatedLayout:
        """Paginate using row capacity derived from a document page layout."""
        page = self.page(page_index)
        rows_per_column = page.layout.rows_per_column(
            line_height_mm=line_height_mm,
            page_number=page_index + 1,
        )
        return self.to_paginated_layout(
            rows_per_column=rows_per_column,
            column_count=column_count,
            max_width=max_width,
        )

    def to_chord_over_lyrics_text(self, max_width: int | None = None) -> str:
        """Render the document body as monospaced chord-over-lyrics text."""
        return self.to_document().to_chord_over_lyrics_text(max_width=max_width)

    def to_dom(self) -> DocumentDom:
        """Build the internal semantic DOM for the document body."""
        return DocumentDom.from_chordpro_text(self.body_text)

    def with_body_text(self, body_text: str) -> "DocumentModel":
        """Return a copy with updated document body text."""
        return replace(self, body_text=body_text)

    def with_title(self, title: str) -> "DocumentModel":
        """Return a copy with an updated title."""
        return replace(self, title=title)

    def with_page_layout(
        self,
        page_index: int,
        layout: PageLayout,
    ) -> "DocumentModel":
        """Return a copy with one page's layout replaced."""
        page = self.page(page_index)
        pages = (
            self.pages[:page_index]
            + (replace(page, layout=layout),)
            + self.pages[page_index + 1 :]
        )
        return replace(self, pages=pages)

    def append_page(
        self,
        layout: PageLayout | None = None,
        page_id: str | None = None,
    ) -> "DocumentModel":
        """Return a copy with a new page appended."""
        next_page = DocumentPage(
            page_id=(
                page_id if page_id is not None else _next_page_id(self.pages)
            ),
            layout=layout if layout is not None else self.pages[-1].layout,
        )
        return replace(self, pages=self.pages + (next_page,))

    @classmethod
    def from_document(
        cls,
        document: MiniChordDocument,
        layout: PageLayout | None = None,
    ) -> "DocumentModel":
        """Build a page-based model around the current storage document."""
        return cls(
            body_text=document.text,
            title=document.title,
            pages=(
                DocumentPage(
                    layout=layout if layout is not None else PageLayout()
                ),
            ),
            version=document.version,
        )


def _validate_unique_page_ids(pages: Iterable[DocumentPage]) -> None:
    seen: set[str] = set()
    for page in pages:
        if page.page_id in seen:
            raise ValueError(f"Duplicate document page id: {page.page_id}")
        seen.add(page.page_id)


def _next_page_id(pages: tuple[DocumentPage, ...]) -> str:
    existing_page_ids = {page.page_id for page in pages}
    number = len(pages) + 1
    while True:
        page_id = f"page-{number}"
        if page_id not in existing_page_ids:
            return page_id
        number += 1
