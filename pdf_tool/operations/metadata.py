import questionary
from rich.console import Console
from rich.table import Table

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path

_console = Console()

_EDITABLE_FIELDS = ("Title", "Author", "Subject", "Keywords")


def _view(backend: PikepdfBackend, input_path) -> None:
    info = backend.inspect(input_path)
    table = Table(title=str(input_path), show_header=False)
    table.add_column()
    table.add_column()
    for key, value in info.metadata.items():
        table.add_row(key, value)
    if not info.metadata:
        table.add_row("(no metadata fields set)", "")
    _console.print(table)


def _edit(backend: PikepdfBackend, input_path) -> None:
    info = backend.inspect(input_path)
    fields: dict[str, str] = {}
    for name in _EDITABLE_FIELDS:
        current = info.metadata.get(name, "")
        new_value = questionary.text(
            f"{name}:",
            default=current,
        ).ask()
        if new_value is None:
            return
        if new_value:
            fields[name] = new_value

    output = prompt_output_path(
        ensure_unique(input_path.with_stem(f"{input_path.stem}-tagged")),
        hint="e.g. tagged.pdf",
    )
    if output is None:
        return

    backend.set_metadata(input_path, output, fields=fields)
    _console.print(f"[green]Wrote {output}[/green]")


def _strip(backend: PikepdfBackend, input_path) -> None:
    output = prompt_output_path(
        ensure_unique(input_path.with_stem(f"{input_path.stem}-sanitised")),
        hint="e.g. clean.pdf",
    )
    if output is None:
        return

    backend.strip_metadata(input_path, output)
    _console.print(f"[green]Wrote {output}[/green]")


def run() -> None:
    input_path = prompt_input_file("Input PDF")
    if input_path is None:
        return

    backend = PikepdfBackend()
    action = questionary.select(
        "Action?",
        choices=[
            questionary.Choice("View metadata", value="view"),
            questionary.Choice("Edit metadata", value="edit"),
            questionary.Choice("Strip all metadata", value="strip"),
        ],
    ).ask()
    if action is None:
        return

    if action == "view":
        _view(backend, input_path)
    elif action == "edit":
        _edit(backend, input_path)
    else:
        _strip(backend, input_path)
