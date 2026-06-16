import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import resolve
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection
from pdf_tool.widgets.unlock import prompt_unlock

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to rotate")
    if input_path is None:
        return

    backend = PikepdfBackend()
    unlocked = prompt_unlock(backend, input_path)
    if unlocked is None:
        return
    n_pages, password = unlocked

    selection = prompt_page_selection(n_pages)
    if selection is None:
        return
    pages = resolve(selection, n_pages=n_pages)

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

    backend.rotate(
        input_path, output, pages=pages, degrees=int(angle_choice), password=password
    )
    _console.print(f"[green]Wrote {output}[/green]")
