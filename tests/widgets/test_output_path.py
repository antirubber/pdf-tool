from pathlib import Path

from pdf_tool.widgets import output_path
from pdf_tool.widgets.output_path import resolve_custom_output


class _Sel:
    def __init__(self, value):
        self._value = value

    def ask(self):
        return self._value


def test_resolve_collision_returns_path_when_free(tmp_path):
    out = tmp_path / "free.pdf"
    assert output_path._resolve_collision(out, as_directory=False) == out


def test_resolve_collision_overwrite_keeps_path(monkeypatch, tmp_path):
    out = tmp_path / "exists.pdf"
    out.write_bytes(b"x")
    monkeypatch.setattr(
        output_path.questionary, "select", lambda *a, **k: _Sel("overwrite")
    )
    assert output_path._resolve_collision(out, as_directory=False) == out


def test_resolve_collision_rename_returns_unique(monkeypatch, tmp_path):
    out = tmp_path / "exists.pdf"
    out.write_bytes(b"x")
    monkeypatch.setattr(
        output_path.questionary, "select", lambda *a, **k: _Sel("rename")
    )
    result = output_path._resolve_collision(out, as_directory=False)
    assert result == tmp_path / "exists-2.pdf"


def test_resolve_collision_cancel_returns_none(monkeypatch, tmp_path):
    out = tmp_path / "exists.pdf"
    out.write_bytes(b"x")
    monkeypatch.setattr(
        output_path.questionary, "select", lambda *a, **k: _Sel("cancel")
    )
    assert output_path._resolve_collision(out, as_directory=False) is None


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
