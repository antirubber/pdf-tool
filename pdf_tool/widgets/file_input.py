from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

import questionary


def normalize_path(raw: str) -> Path:
    """Normalise a drag-and-drop path: quotes, ~, file:// URIs, escaped spaces."""
    stripped = raw.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ("'", '"'):
        stripped = stripped[1:-1]
    if stripped.startswith("file://"):
        # file:///home/u/a%20b.pdf  ->  /home/u/a b.pdf
        stripped = url2pathname(urlparse(stripped).path)
    else:
        # Shell-style escaped spaces from a dragged path: a\ b.pdf -> a b.pdf
        stripped = stripped.replace("\\ ", " ")
    return Path(stripped).expanduser()


def _validate_existing_file(raw: str) -> bool | str:
    if not raw or not raw.strip():
        return "Path is required."
    path = normalize_path(raw)
    if not path.exists():
        return f"File not found: {path}"
    if not path.is_file():
        return f"Not a file: {path}"
    return True


def _validate_existing_directory(raw: str) -> bool | str:
    if not raw or not raw.strip():
        return "Path is required."
    path = normalize_path(raw)
    if not path.exists():
        return f"Directory not found: {path}"
    if not path.is_dir():
        return f"Not a directory: {path}"
    return True


def prompt_input_directory(message: str = "Input directory") -> Path | None:
    raw = questionary.path(
        message, validate=_validate_existing_directory, only_directories=True
    ).ask()
    if raw is None:
        return None
    return normalize_path(raw).resolve()


def prompt_input_file(message: str = "Input PDF") -> Path | None:
    raw = questionary.path(message, validate=_validate_existing_file).ask()
    if raw is None:
        return None
    return normalize_path(raw).resolve()
