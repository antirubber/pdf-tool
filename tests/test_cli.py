from typer.testing import CliRunner

from pdf_tool import __version__, cli

runner = CliRunner()


def test_bare_invocation_launches_wizard(monkeypatch):
    called = {}
    monkeypatch.setattr(cli.wizard, "run", lambda **kw: called.update(kw))
    result = runner.invoke(cli.app, [])
    assert result.exit_code == 0, result.output
    assert called == {"debug": False}


def test_debug_flag_forwarded_to_wizard(monkeypatch):
    called = {}
    monkeypatch.setattr(cli.wizard, "run", lambda **kw: called.update(kw))
    runner.invoke(cli.app, ["--debug"])
    assert called == {"debug": True}


def test_version_prints_and_exits(monkeypatch):
    monkeypatch.setattr(
        cli.wizard, "run", lambda **kw: (_ for _ in ()).throw(AssertionError("wizard ran"))
    )
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == f"pdf-tool {__version__}"


def test_update_runs_installer_not_wizard(monkeypatch):
    monkeypatch.setattr(
        cli.wizard, "run", lambda **kw: (_ for _ in ()).throw(AssertionError("wizard ran"))
    )
    invoked = {}

    def fake_update():
        invoked["ran"] = True
        return 0

    monkeypatch.setattr(cli.updater, "run", fake_update)
    result = runner.invoke(cli.app, ["update"])
    assert result.exit_code == 0, result.output
    assert invoked == {"ran": True}


def test_update_propagates_installer_failure(monkeypatch):
    monkeypatch.setattr(cli.updater, "run", lambda: 7)
    result = runner.invoke(cli.app, ["update"])
    assert result.exit_code == 7, result.output
