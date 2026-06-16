import contextlib
import os
from collections.abc import Iterator

from rich.console import Console

_console = Console()


def _suppressed() -> bool:
    # No spinner when output is not a live terminal, or under --debug, where it
    # would corrupt piped output / interleave with raw Backend tracebacks.
    return not _console.is_interactive or bool(os.environ.get("PDF_TOOL_DEBUG"))


@contextlib.contextmanager
def spinner(label: str) -> Iterator[None]:
    """Show an animated status with ``label`` while a slow Operation runs."""
    if _suppressed():
        yield
        return
    with _console.status(f"[cyan]{label}…[/cyan]", spinner="dots"):
        yield
