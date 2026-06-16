import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pdf_tool.backends.subprocess_backend import SubprocessBackend

CompressPreset = Literal["screen", "ebook", "printer", "prepress"]

# Ghostscript defaults -dSAFER on from 9.50; below this the sandbox is weaker
# even with -dSAFER passed explicitly, so we recommend upgrading.
MIN_GHOSTSCRIPT_VERSION = (9, 50)


@dataclass(frozen=True)
class CompressOptions:
    preset: CompressPreset = "ebook"


class GhostscriptBackend(SubprocessBackend):
    binary = "gs"

    def compress(
        self, input_path: Path, output_path: Path, options: CompressOptions
    ) -> Path:
        with self._atomic_path(output_path) as tmp:
            self._check(
                [
                    "-dSAFER",
                    "-dBATCH",
                    "-dNOPAUSE",
                    "-q",
                    "-sDEVICE=pdfwrite",
                    f"-dPDFSETTINGS=/{options.preset}",
                    "-o",
                    str(tmp),
                    str(input_path),
                ]
            )
        return output_path


def _run_gs_version() -> str | None:
    try:
        result = subprocess.run(
            ["gs", "--version"], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout


def ghostscript_version(
    run: Callable[[], str | None] = _run_gs_version,
) -> tuple[int, int] | None:
    """Parse (major, minor) from `gs --version`, or None if absent/unparseable."""
    raw = run()
    if not raw:
        return None
    match = re.match(r"\s*(\d+)\.(\d+)", raw)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def ghostscript_warning(version: tuple[int, int] | None) -> str | None:
    """A user-facing warning when the detected gs is below the minimum."""
    if version is None or version >= MIN_GHOSTSCRIPT_VERSION:
        return None
    have = f"{version[0]}.{version[1]}"
    want = f"{MIN_GHOSTSCRIPT_VERSION[0]}.{MIN_GHOSTSCRIPT_VERSION[1]}"
    return (
        f"Ghostscript {have} is older than the recommended {want}; "
        "its sandboxing is weaker — consider upgrading."
    )
