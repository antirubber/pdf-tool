from pathlib import Path

from pdf_tool.widgets.output_path import resolve_custom_output


class TestResolveCustomOutput:
    def test_absolute_path_used_as_is(self, tmp_path: Path):
        result = resolve_custom_output(tmp_path, "/tmp/out.pdf")
        assert result == Path("/tmp/out.pdf")

    def test_relative_path_resolved_against_base(self, tmp_path: Path):
        result = resolve_custom_output(tmp_path, "report.pdf")
        assert result == tmp_path / "report.pdf"

    def test_tilde_expanded(self, tmp_path: Path):
        result = resolve_custom_output(tmp_path, "~/report.pdf")
        assert not str(result).startswith("~")

    def test_subdirectory_relative_path(self, tmp_path: Path):
        result = resolve_custom_output(tmp_path, "sub/report.pdf")
        assert result == tmp_path / "sub" / "report.pdf"

    def test_quoted_path_stripped(self, tmp_path: Path):
        result = resolve_custom_output(tmp_path, '"/tmp/out.pdf"')
        assert result == Path("/tmp/out.pdf")
