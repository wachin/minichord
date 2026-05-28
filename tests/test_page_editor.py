from PyQt6.QtCore import QRect, QSize
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from minichord.document import CUSTOM_PAGE_SIZE, PageLayout, PageMargins
from minichord.document.page import DEFAULT_SCREEN_DPI, mm_to_px
from minichord.ui.page_editor import PageEditor, PageWidget


def expected_editor_rect(layout: PageLayout, zoom: float = 1.0) -> QRect:
    page_width, page_height = layout.page_size_px(DEFAULT_SCREEN_DPI, zoom)
    left, top, right, bottom = layout.margin_px(DEFAULT_SCREEN_DPI, zoom)
    return QRect(
        left,
        top,
        page_width - left - right,
        page_height - top - bottom,
    )


def test_page_widget_sizes_itself_from_page_layout(qtbot):
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(100.0, 150.0),
        margins=PageMargins(left=10.0, top=15.0, right=20.0, bottom=25.0),
    )
    page = PageWidget(layout=layout)
    qtbot.addWidget(page)

    assert page.size() == QSize(
        mm_to_px(100.0, DEFAULT_SCREEN_DPI),
        mm_to_px(150.0, DEFAULT_SCREEN_DPI),
    )
    assert page.editor.geometry() == expected_editor_rect(layout)


def test_page_widget_renders_page_background_and_shadow(qtbot):
    page = PageWidget()
    qtbot.addWidget(page)

    stylesheet = page.styleSheet()
    shadow = page.graphicsEffect()

    assert "QFrame#pageWidget" in stylesheet
    assert "background: white" in stylesheet
    assert "border: 1px solid #c8c8c8" in stylesheet
    assert isinstance(shadow, QGraphicsDropShadowEffect)
    assert shadow.blurRadius() == 18.0
    assert shadow.xOffset() == 0.0
    assert shadow.yOffset() == 4.0
    assert shadow.color().alpha() == 55


def test_page_widget_resizes_dynamically_after_layout_change(qtbot):
    page = PageWidget(
        layout=PageLayout(
            page_size=CUSTOM_PAGE_SIZE,
            custom_size_mm=(100.0, 150.0),
            margins=PageMargins(left=10.0, top=10.0, right=10.0, bottom=10.0),
        )
    )
    qtbot.addWidget(page)
    page.set_text("[C]Text survives")

    updated_layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        orientation="landscape",
        custom_size_mm=(100.0, 150.0),
        margins=PageMargins(left=5.0, top=8.0, right=15.0, bottom=12.0),
    )
    page.set_page_layout(updated_layout)

    assert page.text() == "[C]Text survives"
    assert page.size() == QSize(
        mm_to_px(150.0, DEFAULT_SCREEN_DPI),
        mm_to_px(100.0, DEFAULT_SCREEN_DPI),
    )
    assert page.editor.geometry() == expected_editor_rect(updated_layout)


def test_page_widget_zoom_resizes_page_and_writable_frame(qtbot):
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(100.0, 150.0),
        margins=PageMargins(left=10.0, top=10.0, right=10.0, bottom=10.0),
    )
    page = PageWidget(layout=layout)
    qtbot.addWidget(page)

    page.set_zoom(2.0)

    assert page.zoom() == 2.0
    assert page.size() == QSize(
        mm_to_px(100.0, DEFAULT_SCREEN_DPI, zoom=2.0),
        mm_to_px(150.0, DEFAULT_SCREEN_DPI, zoom=2.0),
    )
    assert page.editor.geometry() == expected_editor_rect(layout, zoom=2.0)


def test_page_widget_clamps_zoom(qtbot):
    page = PageWidget()
    qtbot.addWidget(page)

    page.set_zoom(0.01)
    assert page.zoom() == 0.25

    page.set_zoom(10.0)
    assert page.zoom() == 4.0


def test_page_editor_exposes_page_layout_and_zoom_controls(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)

    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(90.0, 120.0),
        margins=PageMargins(left=9.0, top=9.0, right=9.0, bottom=9.0),
    )
    editor.set_text("draft")
    editor.set_page_layout(layout)
    editor.set_zoom(1.5)

    assert editor.text() == "draft"
    assert editor.page_layout() == layout
    assert editor.zoom() == 1.5
    assert editor.page.size() == QSize(
        mm_to_px(90.0, DEFAULT_SCREEN_DPI, zoom=1.5),
        mm_to_px(120.0, DEFAULT_SCREEN_DPI, zoom=1.5),
    )
