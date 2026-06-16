import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel

from pdf_tool.core.humanize import humanize_bytes

_console = Console()


def _opener() -> list[str] | None:
    if sys.platform == "darwin":
        return ["open"]
    if shutil.which("xdg-open"):
        return ["xdg-open"]
    return None


def _clipboard_tool(
    which: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    for cmd in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"]):
        if which(cmd[0]):
            return cmd
    return None


def offer_post_run(output: Path) -> None:
    """Opt-in conveniences after a write: open/reveal, copy path. Stateless."""
    if not _console.is_interactive:
        return
    opener = _opener()
    if opener and questionary.confirm("Open the output?", default=False).ask():
        subprocess.run([*opener, str(output)], check=False)
    clip = _clipboard_tool()
    if clip and questionary.confirm(
        "Copy the output path to the clipboard?", default=False
    ).ask():
        subprocess.run(clip, input=str(output.resolve()).encode(), check=False)
        _console.print("[dim]Path copied to the clipboard.[/dim]")


def _pages(n: int) -> str:
    return f"{n} {'page' if n == 1 else 'pages'}"


def show_page_count(n_pages: int) -> None:
    """Echo the page count right after the input file is chosen."""
    _console.print(f"[dim]Document has {_pages(n_pages)}.[/dim]")


def closing_panel(output: Path, *, n_pages: int | None = None) -> None:
    """Compact closing summary for a successful single-file run."""
    lines = [f"[green]Wrote[/green] {output}"]
    try:
        lines.append(f"Size: {humanize_bytes(output.stat().st_size)}")
    except OSError:
        pass
    if n_pages is not None:
        lines.append(f"Pages: {_pages(n_pages)}")
    _console.print(Panel("\n".join(lines), expand=False, border_style="green"))
    offer_post_run(output)
