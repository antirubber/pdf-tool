from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.reorder import reorder_items

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to reorder")
    if input_path is None:
        return

    backend = PikepdfBackend()
    info = backend.inspect(input_path)
    if info.n_pages is None:
        _console.print(
            "[red]Cannot reorder an encrypted PDF. Decrypt it first.[/red]"
        )
        return

    order = reorder_items(
        list(range(1, info.n_pages + 1)),
        label=lambda p: f"Page {p}",
        done_label="Looks good — write",
    )
    if order is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "reorder")),
        hint="e.g. reordered.pdf",
    )
    if output is None:
        return

    backend.reorder_pages(input_path, output, order=order)
    _console.print(f"[green]Wrote {output}[/green]")
