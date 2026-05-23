from typing import Annotated, Optional

import typer

from pdf_tool import __version__, wizard

app = typer.Typer(add_completion=False)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"pdf-tool {__version__}")
        raise typer.Exit()


@app.command()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", callback=_version_callback, is_eager=True, help="Show version and exit."
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            envvar="PDF_TOOL_DEBUG",
            help="Show raw Backend output and full tracebacks.",
        ),
    ] = False,
) -> None:
    """Interactive wizard for everyday PDF tasks."""
    wizard.run(debug=debug)
