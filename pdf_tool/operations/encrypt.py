from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import EncryptOptions, PikepdfBackend
from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.batch import (
    collect_input_files,
    print_summary,
    prompt_one_or_many,
    run_per_file,
)
from pdf_tool.widgets.file_input import prompt_input_file

_console = Console()


def _prompt_password() -> str | None:
    password = questionary.password("Password").ask()
    if password is None:
        return None
    confirm = questionary.password("Confirm password").ask()
    if confirm is None:
        return None
    if password != confirm:
        _console.print("[red]Passwords do not match.[/red]")
        return None
    return password


def _run_one() -> None:
    input_path = prompt_input_file("Input PDF to encrypt")
    if input_path is None:
        return
    password = _prompt_password()
    if password is None:
        return

    output = ensure_unique(derive_output(input_path, "encrypt"))
    if not questionary.confirm(f"Will write to {output}. OK?", default=True).ask():
        return

    try:
        PikepdfBackend().encrypt(input_path, output, EncryptOptions(password=password))
    except BackendError as e:
        _console.print(f"[red]{translate('encrypt', e.failure).message}[/red]")
        return
    _console.print(f"[green]Wrote {output}[/green]")


def _run_batch() -> None:
    inputs = collect_input_files("First PDF to encrypt")
    if not inputs:
        return
    password = _prompt_password()
    if password is None:
        return
    if not questionary.confirm(
        f"Will encrypt {len(inputs)} files (each → <name>-encrypted.pdf). OK?",
        default=True,
    ).ask():
        return

    backend = PikepdfBackend()

    def process(path: Path) -> Path:
        output = ensure_unique(derive_output(path, "encrypt"))
        return backend.encrypt(path, output, EncryptOptions(password=password))

    outcomes = run_per_file("encrypt", inputs, process)
    print_summary(outcomes)


def run() -> None:
    mode = prompt_one_or_many()
    if mode == "one":
        _run_one()
    elif mode == "many":
        _run_batch()
