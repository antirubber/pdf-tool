from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from pdf_tool.core.humanize import humanize_bytes

_console = Console()


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
