import pytest

from minichord.document import (
    CUSTOM_PAGE_SIZE,
    PageLayout,
    PageMargins,
    margin_preset_names,
)
from minichord.document.page import mm_to_px


def test_a4_writable_area_uses_margins():
    layout = PageLayout(margins=PageMargins(left=10, top=20, right=10, bottom=20))

    assert layout.size_mm == (210.0, 297.0)
    assert layout.writable_size_mm == (190.0, 257.0)


def test_landscape_swaps_page_dimensions():
    layout = PageLayout(orientation="landscape")

    assert layout.size_mm == (297.0, 210.0)


def test_letter_and_legal_page_sizes_are_supported():
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
