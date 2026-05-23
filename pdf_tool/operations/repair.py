import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to repair")
    if input_path is None:
        return

    output = ensure_unique(derive_output(input_path, "repair"))
    if not questionary.confirm(f"Will write to {output}. OK?", default=True).ask():
        return

    try:
        PikepdfBackend().try_repair(input_path, output)
    except BackendError as e:
        friendly = translate("repair", e.failure)
        _console.print(f"[red]{friendly.message}[/red]")
        return

    _console.print(f"[green]Wrote {output}[/green]")
