import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import DecryptOptions, PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to decrypt")
    if input_path is None:
        return

    password = questionary.password("Password").ask()
    if password is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "decrypt")),
        hint="e.g. unlocked.pdf",
    )
    if output is None:
        return

    PikepdfBackend().decrypt(input_path, output, DecryptOptions(password=password))
    _console.print(f"[green]Wrote {output}[/green]")
