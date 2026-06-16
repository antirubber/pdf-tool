from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import DecryptOptions, PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.batch import run_one_or_many
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.summary import closing_panel

_console = Console()


def _run_one() -> None:
    input_path = prompt_input_file("Input PDF to decrypt")
    if input_path is None:
        return

    backend = PikepdfBackend()
    if not backend.inspect(input_path).encrypted:
        _console.print(
            "[yellow]This PDF is not encrypted — nothing to decrypt.[/yellow]"
        )
        return

    password = questionary.password("Password").ask()
    if password is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "decrypt")),
        hint="e.g. unlocked.pdf",
        recap=f"Decrypt {input_path.name}",
    )
    if output is None:
        return

    backend.decrypt(input_path, output, DecryptOptions(password=password))
    closing_panel(output)


def _collect_password() -> str | None:
    return questionary.password("Password for all files:").ask()


def _make_process(password: str):
    backend = PikepdfBackend()

    def process(path: Path) -> Path:
        return backend.decrypt(
            path,
            ensure_unique(derive_output(path, "decrypt")),
            DecryptOptions(password=password),
        )

    return process


def run() -> None:
    run_one_or_many(
        operation="decrypt",
        first_prompt="First PDF to decrypt",
        run_single=_run_one,
        collect_params=_collect_password,
        make_process=_make_process,
        confirm_message=lambda n, p: f"Will decrypt {n} files. OK?",
    )
