import questionary
from rich.console import Console
from rich.table import Table

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path

_console = Console()


def _show_order(paths):
    table = Table(title="Current order", show_header=False)
    table.add_column("#")
    table.add_column("Path")
    for i, p in enumerate(paths, start=1):
        table.add_row(str(i), str(p))
    _console.print(table)


def _reorder(paths):
    while True:
        _show_order(paths)
        action = questionary.select(
            "Reorder?",
            choices=[
                questionary.Choice("Looks good — merge", value="done"),
                questionary.Choice("Move an item", value="move"),
                questionary.Choice("Cancel", value="cancel"),
            ],
        ).ask()
        if action is None or action == "cancel":
            return None
        if action == "done":
            return paths
        from_idx = questionary.text(
            f"Move which item (1..{len(paths)})?",
            validate=lambda v: (
                v.isdigit() and 1 <= int(v) <= len(paths)
            )
            or f"Enter 1..{len(paths)}.",
        ).ask()
        if from_idx is None:
            continue
        to_idx = questionary.text(
            f"Move to which position (1..{len(paths)})?",
            validate=lambda v: (
                v.isdigit() and 1 <= int(v) <= len(paths)
            )
            or f"Enter 1..{len(paths)}.",
        ).ask()
        if to_idx is None:
            continue
        item = paths.pop(int(from_idx) - 1)
        paths.insert(int(to_idx) - 1, item)


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

    final_order = _reorder(paths)
    if final_order is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(final_order[0], "merge")),
        hint="e.g. combined.pdf",
    )
    if output is None:
        return

    try:
        PikepdfBackend().merge(final_order, output)
    except BackendError as e:
        friendly = translate("merge", e.failure)
        _console.print(f"[red]{friendly.message}[/red]")
        return

    _console.print(f"[green]Wrote {output}[/green]")
