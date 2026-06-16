from pathlib import Path

from pdf_tool.widgets.file_input import _validate_existing_directory, normalize_path


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


def test_normalize_decodes_file_uri_with_encoded_space():
    assert normalize_path("file:///home/u/a%20b.pdf") == Path("/home/u/a b.pdf")


def test_normalize_unescapes_backslash_spaces():
    assert normalize_path("/home/u/a\\ b.pdf") == Path("/home/u/a b.pdf")


class TestValidateExistingDirectory:
    def test_rejects_empty(self):
        result = _validate_existing_directory("")
        assert result is not True

    def test_rejects_whitespace(self):
        result = _validate_existing_directory("   ")
        assert result is not True

    def test_rejects_nonexistent(self):
        result = _validate_existing_directory("/no/such/directory")
        assert result is not True

    def test_rejects_file_not_directory(self, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.write_text("hi")
        result = _validate_existing_directory(str(f))
        assert result is not True

    def test_accepts_real_directory(self, tmp_path: Path):
        assert _validate_existing_directory(str(tmp_path)) is True
