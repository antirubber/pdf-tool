import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import resolve
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to rotate")
    if input_path is None:
        return

    backend = PikepdfBackend()
    info = backend.inspect(input_path)
    if info.n_pages is None:
        _console.print("[red]Cannot rotate an encrypted PDF. Decrypt it first.[/red]")
        return

    selection = prompt_page_selection(info.n_pages)
    if selection is None:
        return
    pages = resolve(selection, n_pages=info.n_pages)

    angle_choice = questionary.select(
        "Rotation?",
        choices=[
            questionary.Choice("90° clockwise (default)", value=90),
            questionary.Choice("90° counter-clockwise", value=-90),
            questionary.Choice("180°", value=180),
        ],
    ).ask()
    if angle_choice is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "rotate")),
        hint="e.g. rotated.pdf",
    )
    if output is None:
        return

    backend.rotate(input_path, output, pages=pages, degrees=int(angle_choice))
    _console.print(f"[green]Wrote {output}[/green]")
