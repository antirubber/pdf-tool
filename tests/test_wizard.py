import pytest

from pdf_tool import wizard
from pdf_tool.core.error_translator import BackendError, PikepdfFailure
from pdf_tool.core.probe import BackendName
from pdf_tool.widgets.wizard_menu import MenuEntry, OperationGroup


def _boom_entry() -> MenuEntry:
    def boom() -> None:
        raise BackendError(PikepdfFailure("PdfError", "broken"))

    return MenuEntry(
        "Boom", "rotate", boom, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM
    )


def test_dispatch_reraises_backend_error_under_debug():
    with pytest.raises(BackendError):
        wizard._dispatch(_boom_entry(), debug=True)


def test_dispatch_prints_friendly_message_in_default_mode(capsys):
    wizard._dispatch(_boom_entry(), debug=False)  # must not raise
    out = capsys.readouterr().out
    assert "rotate failed" in out
    assert "--debug" in out
