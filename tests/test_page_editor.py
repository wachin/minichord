from PyQt6.QtCore import QRect, QSize
import pytest
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QScrollArea

from minichord.document import CUSTOM_PAGE_SIZE, PageLayout, PageMargins
from minichord.document.page import DEFAULT_SCREEN_DPI, mm_to_px
from minichord.ui.page_editor import (
    MAX_ZOOM,
    MIN_ZOOM,
    PAGE_CANVAS_MARGIN_PX,
    PageEditor,
    PageWidget,
)


def expected_editor_rect(layout: PageLayout, zoom: float = 1.0) -> QRect:
    page_width, page_height = layout.page_size_px(DEFAULT_SCREEN_DPI, zoom)
    left, top, right, bottom = layout.margin_px(DEFAULT_SCREEN_DPI, zoom)
    return QRect(
        left,
        top,
        page_width - left - right,
        page_height - top - bottom,
    )


def expected_safe_area_rect(layout: PageLayout, zoom: float = 1.0) -> QRect:
    page_width, page_height = layout.page_size_px(DEFAULT_SCREEN_DPI, zoom)
    left, top, right, bottom = layout.printer_margin_px(DEFAULT_SCREEN_DPI, zoom)
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


def test_page_widget_hides_safe_area_frame_without_printer_margins(qtbot):
    page = PageWidget()
    qtbot.addWidget(page)

    assert page.safe_area_frame.isHidden()


def test_page_widget_visualizes_non_printable_margins(qtbot):
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(100.0, 140.0),
        printer_margins=PageMargins(left=4.0, top=5.0, right=6.0, bottom=7.0),
    )

    page = PageWidget(layout=layout)
    qtbot.addWidget(page)

    assert not page.safe_area_frame.isHidden()
    assert "QFrame#printerSafeAreaFrame" in page.styleSheet()
    assert "border: 1px dashed #9aa0a6" in page.styleSheet()
    assert page.safe_area_frame.geometry() == expected_safe_area_rect(layout)


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


def test_page_editor_stacks_multiple_pages_in_continuous_scroll_view(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)
    first_layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(90.0, 120.0),
    )
    second_layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        orientation="landscape",
        custom_size_mm=(90.0, 120.0),
    )

    editor.set_text("[C]First page text")
    editor.set_page_layouts((first_layout, second_layout))

    scroll_area = editor.findChild(QScrollArea, "pageScrollArea")

    assert scroll_area is not None
    assert scroll_area.widgetResizable()
    assert editor.page_count() == 2
    assert editor.pages() == (editor.page_at(0), editor.page_at(1))
    assert editor.page_at(0).is_editable()
    assert not editor.page_at(1).is_editable()
    assert editor.text() == "[C]First page text"
    assert editor.page_layouts() == (first_layout, second_layout)
    assert editor.page_at(0).size() == QSize(
        mm_to_px(90.0, DEFAULT_SCREEN_DPI),
        mm_to_px(120.0, DEFAULT_SCREEN_DPI),
    )
    assert editor.page_at(1).size() == QSize(
        mm_to_px(120.0, DEFAULT_SCREEN_DPI),
        mm_to_px(90.0, DEFAULT_SCREEN_DPI),
    )


def test_page_editor_set_page_layout_updates_all_visible_pages(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)
    editor.set_page_count(3)

    layout = PageLayout(page_size="Letter", orientation="landscape")
    editor.set_page_layout(layout)

    assert editor.page_count() == 3
    assert editor.page_layouts() == (layout, layout, layout)


def test_page_editor_applies_zoom_to_every_page(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(100.0, 140.0),
    )
    editor.set_page_count(2, layout=layout)

    editor.set_zoom(1.75)

    assert editor.zoom() == 1.75
    assert [page.zoom() for page in editor.pages()] == [1.75, 1.75]
    assert [page.size() for page in editor.pages()] == [
        QSize(
            mm_to_px(100.0, DEFAULT_SCREEN_DPI, zoom=1.75),
            mm_to_px(140.0, DEFAULT_SCREEN_DPI, zoom=1.75),
        ),
        QSize(
            mm_to_px(100.0, DEFAULT_SCREEN_DPI, zoom=1.75),
            mm_to_px(140.0, DEFAULT_SCREEN_DPI, zoom=1.75),
        ),
    ]


def test_page_editor_calculates_fit_zoom_values_from_viewport(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(100.0, 160.0),
    )
    editor.set_page_layout(layout)
    page_width, page_height = layout.page_size_px(DEFAULT_SCREEN_DPI)
    viewport = QSize(
        (page_width * 2) + (PAGE_CANVAS_MARGIN_PX * 2),
        (page_height // 2) + (PAGE_CANVAS_MARGIN_PX * 2),
    )

    assert editor.fit_width_zoom(viewport) == 2.0
    assert editor.fit_page_zoom(viewport) == pytest.approx(
        (page_height // 2) / page_height
    )


def test_page_editor_fit_zoom_values_are_clamped(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(100.0, 160.0),
    )
    editor.set_page_layout(layout)

    assert editor.fit_width_zoom(QSize(1, 1)) == MIN_ZOOM
    assert editor.fit_width_zoom(QSize(10000, 10000)) == MAX_ZOOM


def test_page_editor_can_shrink_page_stack_without_losing_text(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)
    editor.set_text("draft")
    editor.set_page_count(4)

    editor.set_page_count(1)

    assert editor.page_count() == 1
    assert editor.text() == "draft"
    assert editor.page_at(0) is editor.page


def test_page_editor_rejects_empty_page_stack(qtbot):
    editor = PageEditor()
    qtbot.addWidget(editor)

    with pytest.raises(ValueError, match="at least one page"):
        editor.set_page_layouts(())

    with pytest.raises(ValueError, match="at least one page"):
        editor.set_page_count(0)

    with pytest.raises(IndexError, match="out of range"):
        editor.page_at(1)
