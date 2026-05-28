"""A page-oriented QTextEdit surface for the initial prototype."""

from __future__ import annotations

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


class PageWidget(QFrame):
    """Visual page frame with a writable text area inside the margins."""

    def __init__(
        self,
        layout: PageLayout | None = None,
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
            """
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18.0)
        shadow.setOffset(0.0, 4.0)
        shadow.setColor(QColor(0, 0, 0, 55))
        self.setGraphicsEffect(shadow)
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

    def text(self) -> str:
        return self.editor.toPlainText()

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def sizeHint(self) -> QSize:
        width, height = self._layout.page_size_px(DEFAULT_SCREEN_DPI, self._zoom)
        return QSize(width, height)

    def resizeEvent(self, event) -> None:  # noqa: ANN001 - Qt override
        super().resizeEvent(event)
        self._place_editor()

    def _apply_layout(self) -> None:
        width, height = self._layout.page_size_px(DEFAULT_SCREEN_DPI, self._zoom)
        self.setFixedSize(width, height)
        self.updateGeometry()
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


class PageEditor(QWidget):
    """Scrollable editor that presents a real page boundary."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("pageEditor")
        self.page = PageWidget()

        self._scroll_area = QScrollArea()
        self._scroll_area.setObjectName("pageScrollArea")
        self._scroll_area.setWidgetResizable(True)

        content = QWidget()
        content.setObjectName("pageCanvas")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.addWidget(self.page, 0, Qt.AlignmentFlag.AlignHCenter)
        content_layout.addStretch(1)
        self._scroll_area.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._scroll_area)

    def text(self) -> str:
        return self.page.text()

    def set_text(self, text: str) -> None:
        self.page.set_text(text)

    def text_document(self):
        return self.page.editor.document()

    def page_layout(self) -> PageLayout:
        return self.page.page_layout()

    def set_page_layout(self, layout: PageLayout) -> None:
        self.page.set_page_layout(layout)

    def zoom(self) -> float:
        return self.page.zoom()

    def set_zoom(self, zoom: float) -> None:
        self.page.set_zoom(zoom)
