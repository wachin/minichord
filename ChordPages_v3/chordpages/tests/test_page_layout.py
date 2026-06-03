import pytest

from chordpages.document import (
    CHORDPAGES_PAGE_SIZE,
    CUSTOM_PAGE_SIZE,
    DEFAULT_PAGE_MARGINS,
    DEFAULT_PAGE_SIZE,
    PageLayout,
    PageMargins,
    margin_preset_names,
    page_size_names,
)
from chordpages.document.page import mm_to_px


def test_default_page_layout_uses_chordpages_size_and_3mm_margins():
    layout = PageLayout()

    assert DEFAULT_PAGE_SIZE == CHORDPAGES_PAGE_SIZE
    assert layout.page_size == CHORDPAGES_PAGE_SIZE
    assert layout.size_mm == (63.0, 110.0)
    assert DEFAULT_PAGE_MARGINS == PageMargins(
        left=3.0,
        top=3.0,
        right=3.0,
        bottom=3.0,
    )
    assert layout.margins == DEFAULT_PAGE_MARGINS
    assert layout.writable_size_mm == (57.0, 104.0)


def test_a4_writable_area_uses_margins():
    layout = PageLayout(
        page_size="A4",
        margins=PageMargins(left=10, top=20, right=10, bottom=20),
    )

    assert layout.size_mm == (210.0, 297.0)
    assert layout.writable_size_mm == (190.0, 257.0)


def test_landscape_swaps_page_dimensions():
    layout = PageLayout(orientation="landscape")

    assert layout.size_mm == (110.0, 63.0)


def test_named_page_sizes_are_supported():
    assert page_size_names() == (CHORDPAGES_PAGE_SIZE, "A4", "Letter", "Legal")
    assert PageLayout(page_size=CHORDPAGES_PAGE_SIZE).size_mm == (63.0, 110.0)
    assert PageLayout(page_size="A4").size_mm == (210.0, 297.0)
    assert PageLayout(page_size="Letter").size_mm == (215.9, 279.4)
    assert PageLayout(page_size="Legal").size_mm == (215.9, 355.6)


def test_custom_page_size_uses_supplied_dimensions():
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(148.0, 210.0),
        margins=PageMargins(left=12, top=10, right=12, bottom=10),
    )

    assert layout.size_mm == (148.0, 210.0)
    assert layout.writable_size_mm == (124.0, 190.0)


def test_custom_page_size_supports_landscape_orientation():
    layout = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        orientation="landscape",
        custom_size_mm=(148.0, 210.0),
    )

    assert layout.size_mm == (210.0, 148.0)


def test_custom_page_size_requires_positive_dimensions():
    missing_size = PageLayout(page_size=CUSTOM_PAGE_SIZE)
    invalid_size = PageLayout(
        page_size=CUSTOM_PAGE_SIZE,
        custom_size_mm=(0.0, 210.0),
    )

    with pytest.raises(ValueError, match="requires dimensions"):
        missing_size.size_mm

    with pytest.raises(ValueError, match="positive"):
        invalid_size.size_mm


def test_named_page_size_rejects_custom_dimensions():
    layout = PageLayout(page_size="A4", custom_size_mm=(100.0, 100.0))

    with pytest.raises(ValueError, match="Custom dimensions"):
        layout.size_mm


def test_invalid_margins_raise_value_error():
    layout = PageLayout(margins=PageMargins(left=120, right=120))

    with pytest.raises(ValueError):
        layout.writable_size_mm


def test_gutter_margin_extends_inner_margin():
    margins = PageMargins(left=20.0, right=15.0, gutter=5.0)

    effective = margins.effective_for_page()

    assert effective.left == 25.0
    assert effective.right == 15.0
    assert effective.gutter == 0.0
    assert not effective.mirrored


def test_mirrored_margins_swap_on_even_pages_and_apply_gutter_inside():
    margins = PageMargins(left=25.0, right=15.0, gutter=4.0, mirrored=True)

    odd_page = margins.effective_for_page(1)
    even_page = margins.effective_for_page(2)

    assert (odd_page.left, odd_page.right) == (29.0, 15.0)
    assert (even_page.left, even_page.right) == (15.0, 29.0)


def test_layout_writable_size_can_use_page_number_dependent_margins():
    layout = PageLayout(
        page_size="A4",
        margins=PageMargins(left=25.0, right=15.0, gutter=4.0, mirrored=True)
    )

    assert layout.writable_size_for_page_mm(1) == (166.0, 257.0)
    assert layout.writable_size_for_page_mm(2) == (166.0, 257.0)
    assert layout.margin_px(page_number=2) == (
        mm_to_px(15.0),
        mm_to_px(20.0),
        mm_to_px(29.0),
        mm_to_px(20.0),
    )


def test_layout_printable_size_uses_printer_safe_area():
    layout = PageLayout(
        page_size="A4",
        printer_margins=PageMargins(left=4.0, top=5.0, right=6.0, bottom=7.0)
    )

    assert layout.printable_size_mm == (200.0, 285.0)
    assert layout.has_printer_safe_area()
    assert layout.printer_margin_px() == (
        mm_to_px(4.0),
        mm_to_px(5.0),
        mm_to_px(6.0),
        mm_to_px(7.0),
    )


def test_rows_per_column_uses_writable_height():
    layout = PageLayout(
        page_size="A4",
        margins=PageMargins(top=10.0, bottom=20.0),
    )

    assert layout.rows_per_column(line_height_mm=10.0) == 26


def test_rows_per_column_changes_after_orientation_switch():
    portrait = PageLayout(
        page_size="A4",
        margins=PageMargins(top=20.0, bottom=20.0),
    )
    landscape = PageLayout(
        page_size="A4",
        orientation="landscape",
        margins=PageMargins(top=20.0, bottom=20.0),
    )

    assert portrait.rows_per_column(line_height_mm=10.0) == 25
    assert landscape.rows_per_column(line_height_mm=10.0) == 17


def test_rows_per_column_has_minimum_and_validates_line_height():
    layout = PageLayout()

    assert layout.rows_per_column(line_height_mm=1000.0) == 1
    with pytest.raises(ValueError, match="Line height"):
        layout.rows_per_column(line_height_mm=0.0)


def test_layout_without_printer_margins_has_no_safe_area():
    layout = PageLayout()

    assert layout.printable_size_mm == layout.size_mm
    assert not layout.has_printer_safe_area()


def test_printer_safe_area_validates_page_geometry():
    layout = PageLayout(printer_margins=PageMargins(left=120.0, right=120.0))

    with pytest.raises(ValueError, match="Horizontal"):
        layout.printable_size_mm


def test_margin_spacing_fields_are_validated():
    layout = PageLayout(margins=PageMargins(header_spacing=-1.0))

    with pytest.raises(ValueError, match="negative"):
        layout.writable_size_mm


def test_margin_page_numbers_must_be_positive():
    with pytest.raises(ValueError, match="at least 1"):
        PageMargins().effective_for_page(0)


def test_margin_presets_expose_standard_profiles():
    assert margin_preset_names() == (
        "normal",
        "narrow",
        "moderate",
        "wide",
        "mirrored",
    )
    assert PageMargins.from_preset("Normal") == PageMargins()
    assert PageMargins.from_preset(" narrow ") == PageMargins(
        left=12.7,
        top=12.7,
        right=12.7,
        bottom=12.7,
    )
    assert PageMargins.from_preset("mirrored").mirrored


def test_margin_preset_rejects_unknown_names():
    with pytest.raises(ValueError, match="Unsupported margin preset"):
        PageMargins.from_preset("compact")


def test_page_layout_can_apply_margin_preset_immutably():
    layout = PageLayout(margins=PageMargins(left=8, top=8, right=8, bottom=8))

    updated = layout.with_margin_preset("wide")

    assert layout.margins == PageMargins(left=8, top=8, right=8, bottom=8)
    assert updated.margins == PageMargins(
        left=25.4,
        top=25.4,
        right=25.4,
        bottom=25.4,
    )


def test_mm_to_px_uses_dpi_and_zoom():
    assert mm_to_px(25.4, dpi=96, zoom=2.0) == 192
