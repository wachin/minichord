"""A page-oriented QTextEdit surface for the initial prototype."""

from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from minichord.document.page import DEFAULT_SCREEN_DPI, PageLayout


PAGE_CANVAS_MARGIN_PX = 24
PAGE_SPACING_PX = 24


class PageWidget(QFrame):
    """Visual page frame with a writable text area inside the margins."""

    def __init__(
        self,
        layout: PageLayout | None = None,
        editable: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._layout = layout or PageLayout()
        self._zoom = 1.0
        self.editor = QTextEdit(self)
        self.editor.setObjectName("pageTextEditor")
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText(self.tr("Write your song here..."))
        self.safe_area_frame = QFrame(self)
        self.safe_area_frame.setObjectName("printerSafeAreaFrame")
        self.safe_area_frame.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )

        self.setObjectName("pageWidget")
        self.setStyleSheet(
            """
            QFrame#pageWidget {
                background: white;
                border: 1px solid #c8c8c8;
            }

            QTextEdit#pageTextEditor {
                background: white;
                color: #202124;
                selection-background-color: #b8d7ff;
                selection-color: #111827;
            }

            QFrame#printerSafeAreaFrame {
                background: transparent;
                border: 1px dashed #9aa0a6;
            }
            """
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18.0)
        shadow.setOffset(0.0, 4.0)
        shadow.setColor(QColor(0, 0, 0, 55))
        self.setGraphicsEffect(shadow)
        self.set_editable(editable)
        self._apply_layout()

    def page_layout(self) -> PageLayout:
        return self._layout

    def set_page_layout(self, layout: PageLayout) -> None:
        self._layout = layout
        self._apply_layout()

    def set_zoom(self, zoom: float) -> None:
        self._zoom = max(0.25, min(zoom, 4.0))
        self._apply_layout()

    def zoom(self) -> float:
        return self._zoom

    def set_editable(self, editable: bool) -> None:
        self.editor.setReadOnly(not editable)
        self.editor.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus if editable else Qt.FocusPolicy.NoFocus
        )

    def is_editable(self) -> bool:
        return not self.editor.isReadOnly()

    def text(self) -> str:
        return self.editor.toPlainText()

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def sizeHint(self) -> QSize:
        width, height = self._layout.page_size_px(DEFAULT_SCREEN_DPI, self._zoom)
        return QSize(width, height)

    def resizeEvent(self, event) -> None:  # noqa: ANN001 - Qt override
        super().resizeEvent(event)
        self._place_safe_area_frame()
        self._place_editor()

    def _apply_layout(self) -> None:
        width, height = self._layout.page_size_px(DEFAULT_SCREEN_DPI, self._zoom)
        self.setFixedSize(width, height)
        self.updateGeometry()
        self._place_safe_area_frame()
        self._place_editor()

    def _place_editor(self) -> None:
        left, top, right, bottom = self._layout.margin_px(
            DEFAULT_SCREEN_DPI,
            self._zoom,
        )
        self.editor.setGeometry(
            left,
            top,
            max(1, self.width() - left - right),
            max(1, self.height() - top - bottom),
        )
        self.safe_area_frame.raise_()

    def _place_safe_area_frame(self) -> None:
        if not self._layout.has_printer_safe_area():
            self.safe_area_frame.setVisible(False)
            return

        left, top, right, bottom = self._layout.printer_margin_px(
            DEFAULT_SCREEN_DPI,
            self._zoom,
        )
        self.safe_area_frame.setGeometry(
            left,
            top,
            max(1, self.width() - left - right),
            max(1, self.height() - top - bottom),
        )
        self.safe_area_frame.setVisible(True)


class PageEditor(QWidget):
    """Scrollable editor that presents a real page boundary."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("pageEditor")
        self._pages: list[PageWidget] = []

        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("pageScrollArea")
        self._scroll_area.setWidgetResizable(True)

        self._content = QWidget()
        self._content.setObjectName("pageCanvas")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(
            PAGE_CANVAS_MARGIN_PX,
            PAGE_CANVAS_MARGIN_PX,
            PAGE_CANVAS_MARGIN_PX,
            PAGE_CANVAS_MARGIN_PX,
        )
        self._content_layout.setSpacing(PAGE_SPACING_PX)
        self._content_layout.addStretch(1)
        self._scroll_area.setWidget(self._content)
        self.page = self._append_page(PageLayout(), editable=True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll_area)

    def text(self) -> str:
        return self.page.text()

    def set_text(self, text: str) -> None:
        self.page.set_text(text)

    def text_document(self):
        return self.page.editor.document()

    def page_count(self) -> int:
        return len(self._pages)

    def pages(self) -> tuple[PageWidget, ...]:
        return tuple(self._pages)

    def page_at(self, page_index: int) -> PageWidget:
        if page_index < 0 or page_index >= len(self._pages):
            raise IndexError("Page editor page index out of range.")
        return self._pages[page_index]

    def page_layout(self) -> PageLayout:
        return self.page.page_layout()

    def set_page_layout(self, layout: PageLayout) -> None:
        self.set_page_layouts(tuple(layout for _ in self._pages))

    def page_layouts(self) -> tuple[PageLayout, ...]:
        return tuple(page.page_layout() for page in self._pages)

    def set_page_layouts(self, layouts: Sequence[PageLayout]) -> None:
        page_layouts = tuple(layouts)
        if not page_layouts:
            raise ValueError("Page editor must contain at least one page.")

        while len(self._pages) > len(page_layouts):
            self._remove_last_page()

        while len(self._pages) < len(page_layouts):
            self._append_page(page_layouts[len(self._pages)], editable=False)

        for page_index, (page, layout) in enumerate(
            zip(self._pages, page_layouts)
        ):
            page.set_editable(page_index == 0)
            page.set_page_layout(layout)
            page.set_zoom(self.zoom())

        self.page = self._pages[0]

    def set_page_count(
        self,
        page_count: int,
        layout: PageLayout | None = None,
    ) -> None:
        if page_count < 1:
            raise ValueError("Page editor must contain at least one page.")
        page_layout = layout or self.page_layout()
        self.set_page_layouts(tuple(page_layout for _ in range(page_count)))

    def zoom(self) -> float:
        return self.page.zoom()

    def set_zoom(self, zoom: float) -> None:
        for page in self._pages:
            page.set_zoom(zoom)

    def _append_page(self, layout: PageLayout, editable: bool) -> PageWidget:
        page = PageWidget(layout=layout, editable=editable, parent=self._content)
        self._pages.append(page)
        self._content_layout.insertWidget(
            self._content_layout.count() - 1,
            page,
            0,
            Qt.AlignmentFlag.AlignHCenter,
        )
        return page

    def _remove_last_page(self) -> None:
        page = self._pages.pop()
        self._content_layout.removeWidget(page)
        page.setParent(None)
        page.deleteLater()
