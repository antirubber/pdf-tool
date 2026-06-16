import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.reorder import reorder_items

_console = Console()


def run() -> None:
    paths = []
    first = prompt_input_file("First PDF")
    if first is None:
        return
    paths.append(first)

    while True:
        add_more = questionary.confirm("Add another PDF?", default=True).ask()
        if not add_more:
            break
        nxt = prompt_input_file(f"PDF #{len(paths) + 1}")
        if nxt is None:
            break
        paths.append(nxt)

    if len(paths) < 2:
        _console.print("[yellow]Need at least 2 PDFs to merge.[/yellow]")
        return

    final_order = reorder_items(paths, label=str, done_label="Looks good — merge")
    if final_order is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(final_order[0], "merge")),
        hint="e.g. combined.pdf",
    )
    if output is None:
        return

    PikepdfBackend().merge(final_order, output)
    _console.print(f"[green]Wrote {output}[/green]")
