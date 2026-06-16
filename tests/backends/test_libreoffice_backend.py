from pathlib import Path

from pdf_tool.backends.libreoffice_backend import (
    _soffice_args,
    _write_macro_hardening,
)


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
