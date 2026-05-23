from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import questionary
from rich.console import Console
from rich.table import Table

from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.widgets.file_input import prompt_input_directory, prompt_input_file


def collect_directory_files(
    directory: Path,
    extensions: set[str],
    *,
    recursive: bool = False,
) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(
        p
        for p in directory.glob(pattern)
        if p.is_file() and p.suffix.lower() in extensions
    )

_console = Console()


@dataclass(frozen=True)
class BatchOutcome:
    path: Path
    succeeded: bool
    message: str


def prompt_one_or_many() -> str | None:
    """Returns 'one', 'many', 'directory', or None on cancel."""
    return questionary.select(
        "One file or many?",
        choices=[
            questionary.Choice("Just one", value="one"),
            questionary.Choice("Multiple (Batch mode)", value="many"),
            questionary.Choice("All files in a directory", value="directory"),
        ],
    ).ask()


def collect_directory_files_interactive(
    extensions: set[str],
) -> list[Path]:
    directory = prompt_input_directory("Directory containing files")
    if directory is None:
        return []
    recursive = questionary.confirm(
        "Include subdirectories?", default=False
    ).ask()
    if recursive is None:
        return []
    files = collect_directory_files(directory, extensions, recursive=recursive)
    if not files:
        _console.print(f"[yellow]No matching files found in {directory}[/yellow]")
        return []
    preview = ", ".join(f.name for f in files[:5])
    suffix = f" and {len(files) - 5} more" if len(files) > 5 else ""
    if not questionary.confirm(
        f"Found {len(files)} file(s): {preview}{suffix}. Proceed?",
        default=True,
    ).ask():
        return []
    return files


def collect_input_files(first_prompt: str = "Input PDF") -> list[Path]:
    paths: list[Path] = []
    first = prompt_input_file(first_prompt)
    if first is None:
        return paths
    paths.append(first)
    while True:
        more = questionary.confirm(
            f"Add another file? ({len(paths)} so far)", default=True
        ).ask()
        if not more:
            return paths
        nxt = prompt_input_file(f"PDF #{len(paths) + 1}")
        if nxt is None:
            return paths
        paths.append(nxt)


def run_per_file(
    operation: str,
    inputs: list[Path],
    process: Callable[[Path], Path],
) -> list[BatchOutcome]:
    """Run `process(path)` for each input. Returns per-file outcomes.

    `process` returns the output Path on success; raises BackendError on failure.
    """
    outcomes: list[BatchOutcome] = []
    for i, path in enumerate(inputs, start=1):
        _console.print(f"[bold]({i}/{len(inputs)}) {path.name}[/bold]")
        try:
            out = process(path)
            outcomes.append(
                BatchOutcome(path=path, succeeded=True, message=f"→ {out}")
            )
        except BackendError as e:
            friendly = translate(operation, e.failure)
            outcomes.append(
                BatchOutcome(path=path, succeeded=False, message=friendly.message)
            )
    return outcomes


def print_summary(outcomes: list[BatchOutcome]) -> None:
    n_ok = sum(1 for o in outcomes if o.succeeded)
    n_fail = len(outcomes) - n_ok
    table = Table(title=f"Batch summary: {n_ok} succeeded, {n_fail} failed")
    table.add_column("Status")
    table.add_column("File")
    table.add_column("Detail")
    for o in outcomes:
        status = "[green]OK[/green]" if o.succeeded else "[red]FAIL[/red]"
        table.add_row(status, o.path.name, o.message)
    _console.print(table)
