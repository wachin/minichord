import pytest

from minichord.document import PageLayout, PageMargins
from minichord.document.page import mm_to_px


def test_a4_writable_area_uses_margins():
    layout = PageLayout(margins=PageMargins(left=10, top=20, right=10, bottom=20))

    assert layout.size_mm == (210.0, 297.0)
    assert layout.writable_size_mm == (190.0, 257.0)


def test_landscape_swaps_page_dimensions():
    layout = PageLayout(orientation="landscape")

    assert layout.size_mm == (297.0, 210.0)


def test_invalid_margins_raise_value_error():
    layout = PageLayout(margins=PageMargins(left=120, right=120))

    with pytest.raises(ValueError):
        layout.writable_size_mm


def test_mm_to_px_uses_dpi_and_zoom():
    assert mm_to_px(25.4, dpi=96, zoom=2.0) == 192
