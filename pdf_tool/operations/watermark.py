import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend, WatermarkOptions
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import All, resolve
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection
from pdf_tool.widgets.unlock import prompt_unlock

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to watermark")
    if input_path is None:
        return

    backend = PikepdfBackend()
    unlocked = prompt_unlock(backend, input_path)
    if unlocked is None:
        return
    n_pages, password = unlocked

    text = questionary.text(
        "Watermark text:",
        default="DRAFT",
        validate=lambda v: bool(v.strip()) or "Text required.",
    ).ask()
    if text is None:
        return

    advanced = questionary.confirm("Advanced options?", default=False).ask()
    if advanced is None:
        return

    if advanced:
        selection = prompt_page_selection(n_pages)
        if selection is None:
            return
    else:
        selection = All()
    pages = resolve(selection, n_pages=n_pages)

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "watermark")),
        hint="e.g. draft.pdf",
    )
    if output is None:
        return

    backend.watermark(
        input_path, output, WatermarkOptions(text=text, pages=pages), password=password
    )
    _console.print(f"[green]Wrote {output}[/green]")
