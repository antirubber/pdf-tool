from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.core.output_namer import ensure_unique
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


def _resolve_collision(path: Path, *, as_directory: bool) -> Path | None:
    """Confirm before clobbering an existing destination.

    Offers overwrite / write-a-unique-copy / cancel instead of silently
    auto-renaming or overwriting. Returns the chosen path, or None on cancel.
    """
    if not path.exists():
        return path
    kind = "directory" if as_directory else "file"
    choice = questionary.select(
        f"{path} already exists ({kind}).",
        choices=[
            questionary.Choice("Write a uniquely-named copy", value="rename"),
            questionary.Choice("Overwrite it", value="overwrite"),
            questionary.Choice("Cancel", value="cancel"),
        ],
    ).ask()
    if choice == "overwrite":
        return path
    if choice == "rename":
        return ensure_unique(path, as_directory=as_directory)
    _console.print("[yellow]Nothing changed.[/yellow]")
    return None


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
        return _resolve_collision(proposed, as_directory=True)

    label = "Output directory:"
    if hint:
        label = f"Output directory ({hint}):"
    raw = questionary.text(label, default=str(proposed)).ask()
    if raw is None or not raw.strip():
        _console.print("[yellow]Nothing changed.[/yellow]")
        return None
    return _resolve_collision(
        resolve_custom_output(proposed.parent, raw), as_directory=True
    )


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
        return _resolve_collision(proposed, as_directory=False)

    label = "Output path:"
    if hint:
        label = f"Output path ({hint}):"
    raw = questionary.text(label, default=str(proposed)).ask()
    if raw is None or not raw.strip():
        _console.print("[yellow]Nothing changed.[/yellow]")
        return None
    return _resolve_collision(
        resolve_custom_output(proposed.parent, raw), as_directory=False
    )
