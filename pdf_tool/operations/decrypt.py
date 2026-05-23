import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import DecryptOptions, PikepdfBackend
from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to decrypt")
    if input_path is None:
        return

    password = questionary.password("Password").ask()
    if password is None:
        return

    output = ensure_unique(derive_output(input_path, "decrypt"))

    proceed = questionary.confirm(f"Will write to {output}. OK?", default=True).ask()
    if not proceed:
        return

    try:
        PikepdfBackend().decrypt(input_path, output, DecryptOptions(password=password))
    except BackendError as e:
        friendly = translate("decrypt", e.failure)
        _console.print(f"[red]{friendly.message}[/red]")
        return

    _console.print(f"[green]Wrote {output}[/green]")
