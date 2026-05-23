import pytest

from pdf_tool.core.range_parser import RangeParseError, parse_range


def test_single_page():
    assert parse_range("5", n_pages=10) == [5]


def test_simple_range():
    assert parse_range("1-3", n_pages=10) == [1, 2, 3]


def test_multi_segment_sorted_and_deduped():
    assert parse_range("5,1-3,2", n_pages=10) == [1, 2, 3, 5]


def test_whitespace_tolerance():
    assert parse_range(" 1 - 3 , 5 ", n_pages=10) == [1, 2, 3, 5]


def test_empty_spec_rejected():
    with pytest.raises(RangeParseError):
        parse_range("", n_pages=10)


def test_whitespace_only_spec_rejected():
    with pytest.raises(RangeParseError):
        parse_range("   ", n_pages=10)


def test_empty_token_rejected():
    with pytest.raises(RangeParseError):
        parse_range("1,,3", n_pages=10)


def test_trailing_comma_rejected():
    with pytest.raises(RangeParseError):
        parse_range("1,3,", n_pages=10)


def test_non_integer_rejected():
    with pytest.raises(RangeParseError):
        parse_range("abc", n_pages=10)


def test_non_integer_in_range_rejected():
    with pytest.raises(RangeParseError):
        parse_range("1-x", n_pages=10)


def test_descending_range_rejected():
    with pytest.raises(RangeParseError):
        parse_range("5-3", n_pages=10)


def test_zero_page_rejected():
    with pytest.raises(RangeParseError):
        parse_range("0", n_pages=10)


def test_negative_page_rejected():
    with pytest.raises(RangeParseError):
        parse_range("-1", n_pages=10)


def test_out_of_bounds_single_page_rejected():
    with pytest.raises(RangeParseError):
        parse_range("11", n_pages=10)


def test_out_of_bounds_range_rejected():
    with pytest.raises(RangeParseError):
        parse_range("1-15", n_pages=10)


def test_range_at_exact_upper_bound_accepted():
    assert parse_range("1-10", n_pages=10) == list(range(1, 11))
