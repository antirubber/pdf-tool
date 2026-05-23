import shutil

import pikepdf
import pytest

from pdf_tool.backends.ghostscript_backend import (
    CompressOptions,
    GhostscriptBackend,
)
from pdf_tool.backends.subprocess_backend import (
    CommandResult,
    SubprocessBackend,
)
from pdf_tool.core.error_translator import BackendError, SubprocessFailure


class _Echo(SubprocessBackend):
    binary = "echo"


class _False(SubprocessBackend):
    binary = "false"


class _Missing(SubprocessBackend):
    binary = "no_such_binary_xyz_123"


def test_run_captures_stdout_and_returncode():
    result = _Echo()._run(["hello"])
    assert isinstance(result, CommandResult)
    assert result.returncode == 0
    assert result.stdout.rstrip() == "hello"


def test_check_raises_backend_error_on_nonzero_exit():
    with pytest.raises(BackendError) as exc_info:
        _False()._check([])
    failure = exc_info.value.failure
    assert isinstance(failure, SubprocessFailure)
    assert failure.binary == "false"
    assert failure.exit_code != 0


def test_run_captures_stderr():
    sh = type("Sh", (SubprocessBackend,), {"binary": "sh"})()
    out = sh._run(["-c", "echo oops 1>&2; exit 0"])
    assert "oops" in out.stderr


def test_run_raises_backend_error_on_missing_binary():
    with pytest.raises(BackendError) as exc_info:
        _Missing()._run([])
    failure = exc_info.value.failure
    assert isinstance(failure, SubprocessFailure)
    assert failure.binary == "no_such_binary_xyz_123"
    assert failure.exit_code == -1
    assert "not found" in failure.stderr


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("gs") is None, reason="ghostscript not installed")
def test_ghostscript_compress_produces_valid_pdf(make_pdf, tmp_path):
    src = make_pdf("src.pdf", n_pages=3)
    out = tmp_path / "compressed.pdf"
    result = GhostscriptBackend().compress(src, out, CompressOptions(preset="ebook"))
    assert result == out
    assert out.exists()
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3


@pytest.mark.integration
@pytest.mark.skipif(
    shutil.which("libreoffice") is None and shutil.which("soffice") is None,
    reason="libreoffice not installed",
)
def test_libreoffice_converts_txt_to_pdf(tmp_path):
    from pdf_tool.backends.libreoffice_backend import (
        ConvertOptions,
        LibreOfficeBackend,
    )

    src = tmp_path / "input.txt"
    src.write_text("Hello, PDF!\nLine two.\n")
    out = tmp_path / "input.pdf"
    result = LibreOfficeBackend().convert(src, out, ConvertOptions(target_format="pdf"))
    assert result == out
    assert out.exists()
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) >= 1
