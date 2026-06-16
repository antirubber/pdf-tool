from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.widgets.summary import show_page_count

_console = Console()


def prompt_unlock(
    backend: PikepdfBackend, input_path: Path
) -> tuple[int, str] | None:
    """Resolve a possibly-encrypted input to (page_count, password).

    For an encrypted input, prompt for the password and verify it instead of
    making the user decrypt in a separate run. Returns None on cancel or a
    wrong password; the password is "" for unencrypted inputs.
    """
    info = backend.inspect(input_path)
    if not info.encrypted:
        assert info.n_pages is not None
        show_page_count(info.n_pages)
        return info.n_pages, ""

    password = questionary.password(
        "This PDF is encrypted. Enter its password:"
    ).ask()
    if password is None:
        return None
    info = backend.inspect(input_path, password=password)
    if info.n_pages is None:
        _console.print("[red]Wrong password.[/red]")
        return None
    show_page_count(info.n_pages)
    return info.n_pages, password
