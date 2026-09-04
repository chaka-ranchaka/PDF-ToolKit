import pytest

from pdf_toolkit.pdf_operations import parse_page_ranges


def test_parse_page_ranges():
    assert parse_page_ranges("2,5,8-10") == [1, 4, 7, 8, 9]
    assert parse_page_ranges("10-8") == [7, 8, 9]
    assert parse_page_ranges("all") is None


@pytest.mark.parametrize("value", ["0", "a", "2-"])
def test_parse_page_ranges_rejects_invalid_input(value):
    with pytest.raises(ValueError):
        parse_page_ranges(value)