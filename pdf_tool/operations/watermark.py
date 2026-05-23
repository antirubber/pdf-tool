import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend, WatermarkOptions
from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import All, resolve
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.page_selection import prompt_page_selection

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to watermark")
    if input_path is None:
        return

    backend = PikepdfBackend()
    info = backend.inspect(input_path)
    if info.n_pages is None:
        _console.print(
            "[red]Cannot watermark an encrypted PDF. Decrypt it first.[/red]"
        )
        return
    n_pages = info.n_pages

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

    output = ensure_unique(derive_output(input_path, "watermark"))
    if not questionary.confirm(f"Will write to {output}. OK?", default=True).ask():
        return

    try:
        backend.watermark(
            input_path, output, WatermarkOptions(text=text, pages=pages)
        )
    except BackendError as e:
        friendly = translate("watermark", e.failure)
        _console.print(f"[red]{friendly.message}[/red]")
        return

    _console.print(f"[green]Wrote {output}[/green]")
