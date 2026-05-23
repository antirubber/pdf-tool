import pytest

from pdf_tool.core.page_selection import (
    All,
    CustomRange,
    Even,
    FirstN,
    LastN,
    Odd,
    resolve,
)


def test_all_over_three_pages():
    assert resolve(All(), n_pages=3) == [1, 2, 3]


def test_odd_over_five_pages():
    assert resolve(Odd(), n_pages=5) == [1, 3, 5]


def test_even_over_five_pages():
    assert resolve(Even(), n_pages=5) == [2, 4]


def test_first_n_within_range():
    assert resolve(FirstN(3), n_pages=10) == [1, 2, 3]


def test_last_n_within_range():
    assert resolve(LastN(2), n_pages=5) == [4, 5]


def test_custom_range_delegates_to_parser():
    assert resolve(CustomRange("1-3,5"), n_pages=10) == [1, 2, 3, 5]


def test_first_n_clamps_to_document_length():
    assert resolve(FirstN(99), n_pages=5) == [1, 2, 3, 4, 5]


def test_last_n_clamps_to_document_length():
    assert resolve(LastN(99), n_pages=5) == [1, 2, 3, 4, 5]


def test_first_n_zero_rejected():
    with pytest.raises(ValueError):
        resolve(FirstN(0), n_pages=5)


def test_last_n_zero_rejected():
    with pytest.raises(ValueError):
        resolve(LastN(0), n_pages=5)


def test_first_n_negative_rejected():
    with pytest.raises(ValueError):
        resolve(FirstN(-1), n_pages=5)


@pytest.mark.parametrize(
    "selection", [All(), Odd(), Even(), FirstN(3), LastN(3)]
)
def test_empty_document_returns_empty_list(selection):
    assert resolve(selection, n_pages=0) == []
