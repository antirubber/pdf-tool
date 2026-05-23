from pathlib import Path

from pdf_tool.widgets.file_input import normalize_path


def test_normalize_strips_surrounding_double_quotes():
    assert normalize_path('"/tmp/foo.pdf"') == Path("/tmp/foo.pdf")


def test_normalize_strips_surrounding_single_quotes():
    assert normalize_path("'/tmp/foo.pdf'") == Path("/tmp/foo.pdf")


def test_normalize_strips_surrounding_whitespace():
    assert normalize_path("  /tmp/foo.pdf  ") == Path("/tmp/foo.pdf")


def test_normalize_expands_tilde():
    result = normalize_path("~/foo.pdf")
    assert not str(result).startswith("~")
    assert str(result).endswith("/foo.pdf")


def test_normalize_leaves_internal_quotes_alone():
    assert normalize_path("/tmp/has'quote.pdf") == Path("/tmp/has'quote.pdf")
