from pdf_tool import updater


class _Completed:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def test_run_invokes_the_one_liner(monkeypatch):
    captured = {}

    def fake_run(args, **kw):
        captured["args"] = args
        return _Completed(0)

    monkeypatch.setattr(updater.subprocess, "run", fake_run)
    assert updater.run() == 0
    assert captured["args"][:2] == ["sh", "-c"]
    assert updater.INSTALL_URL in captured["args"][2]
    assert "curl -fsSL" in captured["args"][2]


def test_run_returns_installer_exit_code(monkeypatch):
    monkeypatch.setattr(updater.subprocess, "run", lambda *a, **kw: _Completed(3))
    assert updater.run() == 3
