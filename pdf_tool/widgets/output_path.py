from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.widgets.file_input import normalize_path

_console = Console()


def resolve_custom_output(base_dir: Path, raw: str) -> Path:
    """Resolve a user-typed output path.

    Absolute paths used as-is. Relative paths resolved against base_dir.
    """
    path = normalize_path(raw)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def prompt_output_dir(
    proposed: Path,
    *,
    hint: str = "",
    recap: str = "",
) -> Path | None:
    """Confirm the auto-derived output directory, or let user type a custom one.

    Returns the final Path, or None if cancelled.
    """
    if recap:
        _console.print(f"[dim]{recap}[/dim]")
    if questionary.confirm(f"Will write to {proposed}/. OK?", default=True).ask():
        return proposed

    label = "Output directory:"
    if hint:
        label = f"Output directory ({hint}):"
    raw = questionary.text(label, default=str(proposed)).ask()
    if raw is None or not raw.strip():
        return None
    return resolve_custom_output(proposed.parent, raw)


def prompt_output_path(
    proposed: Path,
    *,
    hint: str = "",
    recap: str = "",
) -> Path | None:
    """Confirm the auto-derived output, or let user type a custom one.

    Returns the final Path, or None if cancelled.
    """
    if recap:
        _console.print(f"[dim]{recap}[/dim]")
    if questionary.confirm(f"Will write to {proposed}. OK?", default=True).ask():
        return proposed

    label = "Output path:"
    if hint:
        label = f"Output path ({hint}):"
    raw = questionary.text(label, default=str(proposed)).ask()
    if raw is None or not raw.strip():
        return None
    return resolve_custom_output(proposed.parent, raw)
