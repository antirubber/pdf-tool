from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.ghostscript_backend import CompressOptions, GhostscriptBackend
from pdf_tool.core.error_translator import BackendError, translate
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


def _human(n_bytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


def _prompt_preset() -> str | None:
    advanced = questionary.confirm("Advanced options?", default=False).ask()
    if advanced is None:
        return None
    if not advanced:
        return "ebook"
    return questionary.select(
        "Preset?",
        choices=[
            questionary.Choice("/ebook (default — good for email)", value="ebook"),
            questionary.Choice("/screen (smallest, lowest quality)", value="screen"),
            questionary.Choice("/printer (high quality)", value="printer"),
            questionary.Choice("/prepress (highest quality)", value="prepress"),
        ],
    ).ask()


def _run_one() -> None:
    input_path = prompt_input_file("Input PDF to compress")
    if input_path is None:
        return
    preset = _prompt_preset()
    if preset is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "compress")),
        hint="e.g. small.pdf",
    )
    if output is None:
        return

    try:
        GhostscriptBackend().compress(input_path, output, CompressOptions(preset=preset))
    except BackendError as e:
        _console.print(f"[red]{translate('compress', e.failure).message}[/red]")
        return

    before = input_path.stat().st_size
    after = output.stat().st_size
    pct = (after / before * 100) if before else 100
    _console.print(
        f"[green]Wrote {output}[/green]  "
        f"({_human(before)} → {_human(after)}, {pct:.0f}%)"
    )


def _run_batch() -> None:
    inputs = collect_input_files("First PDF to compress")
    if not inputs:
        return
    preset = _prompt_preset()
    if preset is None:
        return
    if not questionary.confirm(
        f"Will compress {len(inputs)} files using /{preset}. OK?", default=True
    ).ask():
        return

    backend = GhostscriptBackend()

    def process(path: Path) -> Path:
        output = ensure_unique(derive_output(path, "compress"))
        return backend.compress(path, output, CompressOptions(preset=preset))

    outcomes = run_per_file("compress", inputs, process)
    print_summary(outcomes)


def _run_directory() -> None:
    files = collect_directory_files_interactive({".pdf"})
    if not files:
        return
    preset = _prompt_preset()
    if preset is None:
        return
    if not questionary.confirm(
        f"Will compress {len(files)} files using /{preset}. OK?", default=True
    ).ask():
        return

    backend = GhostscriptBackend()

    def process(path: Path) -> Path:
        output = ensure_unique(derive_output(path, "compress"))
        return backend.compress(path, output, CompressOptions(preset=preset))

    outcomes = run_per_file("compress", files, process)
    print_summary(outcomes)


def run() -> None:
    mode = prompt_one_or_many()
    if mode == "one":
        _run_one()
    elif mode == "many":
        _run_batch()
    elif mode == "directory":
        _run_directory()
