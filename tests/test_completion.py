from typer.testing import CliRunner

from pdf_tool import cli, completion

runner = CliRunner()


def test_script_for_known_shells():
    for shell in ("bash", "zsh", "fish"):
        assert completion.script_for(shell) is not None
    assert completion.script_for("powershell") is None


def test_completion_command_emits_a_script():
    result = runner.invoke(cli.app, ["completion", "bash"])
    assert result.exit_code == 0, result.output
    assert "complete" in result.output
    assert "pdf-tool" in result.output


def test_completion_command_rejects_unknown_shell():
    result = runner.invoke(cli.app, ["completion", "powershell"])
    assert result.exit_code == 1
