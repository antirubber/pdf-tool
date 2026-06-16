from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import EncryptOptions, PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.batch import (
    collect_directory_files_interactive,
    collect_input_files,
    print_summary,
    prompt_one_or_many,
    run_per_file,
)
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path

_console = Console()


def _validate_non_empty_password(raw: str) -> bool | str:
    return bool(raw.strip()) or "Password cannot be empty."


def _prompt_one_password(label: str) -> str | None:
    password = questionary.password(
        label, validate=_validate_non_empty_password
    ).ask()
    if password is None:
        return None
    confirm = questionary.password(f"Confirm {label.lower()}").ask()
    if confirm is None:
        return None
    if password != confirm:
        _console.print("[red]Passwords do not match.[/red]")
        return None
    return password


def _prompt_strength() -> int | None:
    return questionary.select(
        "Encryption strength?",
        choices=[
            questionary.Choice("256-bit AES (default)", value=256),
            questionary.Choice("128-bit AES", value=128),
            questionary.Choice("40-bit RC4 (weak, legacy)", value=40),
        ],
    ).ask()


def _prompt_permissions() -> list[str] | None:
    return questionary.checkbox(
        "Allow which actions? (uncheck to forbid)",
        choices=[
            questionary.Choice("Print", value="print", checked=True),
            questionary.Choice("Copy text/graphics", value="copy", checked=True),
            questionary.Choice("Modify", value="modify", checked=True),
            questionary.Choice("Annotate", value="annotate", checked=True),
        ],
    ).ask()


def collect_advanced_options(
    base: EncryptOptions,
    *,
    ask_advanced: Callable[[], bool | None],
    ask_strength: Callable[[], int | None],
    ask_permissions: Callable[[], list[str] | None],
) -> EncryptOptions | None:
    """Layer the optional Advanced gate (strength + permissions) onto ``base``.

    Declining the gate returns ``base`` unchanged (AES-256, all allowed). The
    prompts are injected so the branching is exercised without driving them.
    """
    advanced = ask_advanced()
    if advanced is None:
        return None
    if not advanced:
        return base
    strength = ask_strength()
    if strength is None:
        return None
    allowed = ask_permissions()
    if allowed is None:
        return None
    return replace(
        base,
        strength=strength,
        allow_print="print" in allowed,
        allow_copy="copy" in allowed,
        allow_modify="modify" in allowed,
        allow_annotate="annotate" in allowed,
    )


def _prompt_encrypt_options() -> EncryptOptions | None:
    base = collect_encrypt_options(
        ask_same=questionary.confirm(
            "Use the same password for opening and for owner permissions?",
            default=True,
        ).ask,
        ask_password=_prompt_one_password,
    )
    if base is None:
        return None
    return collect_advanced_options(
        base,
        ask_advanced=questionary.confirm("Advanced options?", default=False).ask,
        ask_strength=_prompt_strength,
        ask_permissions=_prompt_permissions,
    )


def collect_encrypt_options(
    *,
    ask_same: Callable[[], bool | None],
    ask_password: Callable[[str], str | None],
) -> EncryptOptions | None:
    """Branch the password prompts on whether owner and user share a password.

    ``ask_same`` and ``ask_password`` are injected so the branching logic can be
    exercised without driving the interactive prompts. Any ``None`` answer means
    the user cancelled and aborts the whole flow.
    """
    same = ask_same()
    if same is None:
        return None
    if same:
        password = ask_password("Password")
        if password is None:
            return None
        if not _is_usable(password):
            return None
        return EncryptOptions(password=password)
    user_pw = ask_password("User password (required to open the document)")
    if user_pw is None:
        return None
    if not _is_usable(user_pw):
        return None
    owner_pw = ask_password("Owner password (full permissions)")
    if owner_pw is None:
        return None
    return EncryptOptions(password=user_pw, owner_password=owner_pw)


def _is_usable(password: str) -> bool:
    # Defence in depth for the headline feature: never emit a file whose
    # "encryption" opens with no prompt because the password was blank.
    if password.strip():
        return True
    _console.print("[red]Password cannot be empty.[/red]")
    return False


def _run_one() -> None:
    input_path = prompt_input_file("Input PDF to encrypt")
    if input_path is None:
        return
    options = _prompt_encrypt_options()
    if options is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "encrypt")),
        hint="e.g. secrets/contract-locked.pdf",
    )
    if output is None:
        return

    PikepdfBackend().encrypt(input_path, output, options)
    _console.print(f"[green]Wrote {output}[/green]")


def _run_batch() -> None:
    inputs = collect_input_files("First PDF to encrypt")
    if not inputs:
        return
    options = _prompt_encrypt_options()
    if options is None:
        return
    if not questionary.confirm(
        f"Will encrypt {len(inputs)} files (each → <name>-encrypted.pdf). OK?",
        default=True,
    ).ask():
        return

    backend = PikepdfBackend()

    def process(path: Path) -> Path:
        output = ensure_unique(derive_output(path, "encrypt"))
        return backend.encrypt(path, output, options)

    outcomes = run_per_file("encrypt", inputs, process)
    print_summary(outcomes)


def _run_directory() -> None:
    files = collect_directory_files_interactive({".pdf"})
    if not files:
        return
    options = _prompt_encrypt_options()
    if options is None:
        return
    if not questionary.confirm(
        f"Will encrypt {len(files)} files (each → <name>-encrypted.pdf). OK?",
        default=True,
    ).ask():
        return

    backend = PikepdfBackend()

    def process(path: Path) -> Path:
        output = ensure_unique(derive_output(path, "encrypt"))
        return backend.encrypt(path, output, options)

    outcomes = run_per_file("encrypt", files, process)
    print_summary(outcomes)


def run() -> None:
    mode = prompt_one_or_many()
    if mode == "one":
        _run_one()
    elif mode == "many":
        _run_batch()
    elif mode == "directory":
        _run_directory()
