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


class _ShWriter(SubprocessBackend):
    binary = "sh"

    def write_file(self, out, *, fail: bool):
        with self._atomic_path(out) as tmp:
            script = f"printf %s hello > '{tmp}'"
            if fail:
                script += "; exit 3"
            self._check(["-c", script])
        return out

    def write_dir(self, out_dir, *, fail: bool):
        with self._atomic_dir(out_dir) as staging:
            script = f"printf %s x > '{staging}/page-1.txt'"
            if fail:
                script += "; exit 3"
            self._check(["-c", script])
        return out_dir


def test_atomic_path_success_writes_full_output(tmp_path):
    out = tmp_path / "result.pdf"
    _ShWriter().write_file(out, fail=False)
    assert out.read_text() == "hello"
    assert [p.name for p in tmp_path.iterdir()] == ["result.pdf"]


def test_atomic_path_failure_leaves_no_partial_output(tmp_path):
    out = tmp_path / "result.pdf"
    with pytest.raises(BackendError):
        _ShWriter().write_file(out, fail=True)
    assert not out.exists()
    assert list(tmp_path.iterdir()) == []


def test_atomic_dir_success_moves_into_place(tmp_path):
    out_dir = tmp_path / "pages"
    _ShWriter().write_dir(out_dir, fail=False)
    assert (out_dir / "page-1.txt").read_text() == "x"
    assert [p.name for p in tmp_path.iterdir()] == ["pages"]


def test_atomic_dir_failure_leaves_no_partial_directory(tmp_path):
    out_dir = tmp_path / "pages"
    with pytest.raises(BackendError):
        _ShWriter().write_dir(out_dir, fail=True)
    assert not out_dir.exists()
    assert list(tmp_path.iterdir()) == []


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
