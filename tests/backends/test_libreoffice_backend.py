from pathlib import Path

from pdf_tool.backends.libreoffice_backend import (
    ConvertOptions,
    LibreOfficeBackend,
    _soffice_args,
    _write_macro_hardening,
)
from pdf_tool.backends.subprocess_backend import CommandResult


class _FakeSoffice(LibreOfficeBackend):
    """Mimics LibreOffice writing <input_stem>.<format> into its --outdir."""

    def _check(self, args, *, timeout: float = 180.0) -> CommandResult:
        outdir = Path(args[args.index("--outdir") + 1])
        fmt = args[args.index("--convert-to") + 1]
        input_path = Path(args[-1])
        (outdir / f"{input_path.stem}.{fmt}").write_bytes(b"CONVERTED")
        return CommandResult(returncode=0, stdout="", stderr="")


def test_soffice_args_carry_isolation_flags(tmp_path):
    profile = tmp_path / "prof"
    args = _soffice_args(Path("/in/report.docx"), "pdf", tmp_path / "out", profile)
    assert "--headless" in args
    assert "--norestore" in args
    assert any(
        a.startswith("-env:UserInstallation=file://") and str(profile) in a
        for a in args
    )
    assert "--convert-to" in args
    assert "pdf" in args


def test_macro_hardening_writes_highest_security_level(tmp_path):
    _write_macro_hardening(tmp_path)
    xcu = (tmp_path / "user" / "registrymodifications.xcu").read_text()
    assert "MacroSecurityLevel" in xcu
    assert "<value>3</value>" in xcu


def test_convert_does_not_clobber_a_preexisting_same_stem_file(tmp_path):
    src = tmp_path / "report.pdf"
    src.write_bytes(b"%PDF-1.4\n%%EOF\n")
    # An unrelated user file that LibreOffice's fixed <stem>.<format> output
    # name would otherwise overwrite before the rename.
    victim = tmp_path / "report.docx"
    victim.write_bytes(b"PRECIOUS USER DATA")
    out = tmp_path / "report-converted.docx"

    _FakeSoffice().convert(src, out, ConvertOptions(target_format="docx"))

    assert victim.read_bytes() == b"PRECIOUS USER DATA"
    assert out.read_bytes() == b"CONVERTED"
