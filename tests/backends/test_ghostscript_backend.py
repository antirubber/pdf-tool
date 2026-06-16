from pathlib import Path

from pdf_tool.backends.ghostscript_backend import (
    CompressOptions,
    GhostscriptBackend,
    ghostscript_version,
    ghostscript_warning,
)
from pdf_tool.backends.subprocess_backend import CommandResult


class _CaptureGs(GhostscriptBackend):
    def __init__(self) -> None:
        self.captured: list[str] = []

    def _check(self, args, *, timeout: float = 300.0) -> CommandResult:
        self.captured = list(args)
        out = Path(args[args.index("-o") + 1])
        out.write_bytes(b"%PDF-1.4\n%%EOF\n")
        return CommandResult(returncode=0, stdout="", stderr="")


def test_compress_invocation_includes_dSAFER(tmp_path):
    (tmp_path / "in.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    backend = _CaptureGs()
    backend.compress(tmp_path / "in.pdf", tmp_path / "out.pdf", CompressOptions())
    assert "-dSAFER" in backend.captured


def test_ghostscript_version_parses_major_minor():
    assert ghostscript_version(run=lambda: "10.02.1\n") == (10, 2)
    assert ghostscript_version(run=lambda: "9.55.0\n") == (9, 55)


def test_ghostscript_version_none_when_unavailable_or_unparseable():
    assert ghostscript_version(run=lambda: None) is None
    assert ghostscript_version(run=lambda: "not-a-version") is None


def test_ghostscript_warning_only_below_minimum():
    assert ghostscript_warning((9, 26)) is not None
    assert ghostscript_warning((9, 50)) is None
    assert ghostscript_warning((10, 2)) is None
    assert ghostscript_warning(None) is None
