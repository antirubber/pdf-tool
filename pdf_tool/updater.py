import subprocess

from rich.console import Console

from pdf_tool import __version__

_console = Console()

INSTALL_URL = "https://raw.githubusercontent.com/antirubber/pdf-tool/master/install.sh"


def run() -> int:
    """Re-run the one-liner installer, which lands the latest release."""
    _console.print(f"Updating pdf-tool (current v{__version__})…")
    result = subprocess.run(["sh", "-c", f"curl -fsSL {INSTALL_URL} | sh"])
    if result.returncode != 0:
        _console.print(f"[red]Update failed (exit {result.returncode}).[/red]")
    return result.returncode
