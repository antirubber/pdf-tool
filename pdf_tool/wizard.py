from dataclasses import dataclass
from typing import Callable

import questionary
from rich.console import Console

from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.probe import Available, BackendName, Missing, probe
from pdf_tool.operations import compress as compress_op
from pdf_tool.operations import convert as convert_op
from pdf_tool.operations import decrypt as decrypt_op
from pdf_tool.operations import encrypt as encrypt_op
from pdf_tool.operations import inspect as inspect_op
from pdf_tool.operations import merge as merge_op
from pdf_tool.operations import metadata as metadata_op
from pdf_tool.operations import ocr as ocr_op
from pdf_tool.operations import repair as repair_op
from pdf_tool.operations import rotate as rotate_op
from pdf_tool.operations import split as split_op
from pdf_tool.operations import watermark as watermark_op


@dataclass(frozen=True)
class _MenuEntry:
    label: str
    value: str
    handler: Callable[[], None]
    backends: tuple[BackendName, ...]
    """Backends this Operation needs. Enabled if ANY are available."""


_console = Console()


_OPERATIONS: tuple[_MenuEntry, ...] = (
    _MenuEntry("Encrypt", "encrypt", encrypt_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Decrypt", "decrypt", decrypt_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Inspect", "inspect", inspect_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Rotate", "rotate", rotate_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Split", "split", split_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Merge", "merge", merge_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Metadata", "metadata", metadata_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Watermark", "watermark", watermark_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Repair", "repair", repair_op.run, (BackendName.PIKEPDF,)),
    _MenuEntry("Compress", "compress", compress_op.run, (BackendName.GHOSTSCRIPT,)),
    _MenuEntry(
        "Convert",
        "convert",
        convert_op.run,
        (BackendName.LIBREOFFICE, BackendName.PDFTOPPM, BackendName.PDFTOTEXT, BackendName.IMG2PDF),
    ),
    _MenuEntry("OCR", "ocr", ocr_op.run, (BackendName.OCRMYPDF,)),
)


def _build_choice(entry: _MenuEntry, availability) -> questionary.Choice:
    missing = [b for b in entry.backends if not isinstance(availability[b], Available)]
    if len(missing) < len(entry.backends):
        # At least one backend is available.
        return questionary.Choice(entry.label, value=entry.value)
    # All backends missing — disable and show install hints.
    hints = []
    for b in missing:
        status = availability[b]
        if isinstance(status, Missing):
            hints.append(status.install_hint)
    hint = " or ".join(hints) if hints else "missing backend"
    return questionary.Choice(
        entry.label, value=entry.value, disabled=f"install: {hint}"
    )


def run(*, debug: bool = False) -> None:
    availability = probe()
    choices = [_build_choice(e, availability) for e in _OPERATIONS]
    choice = questionary.select("Pick an Operation:", choices=choices).ask()
    if choice is None:
        return
    handler = next(e.handler for e in _OPERATIONS if e.value == choice)
    try:
        handler()
    except BackendError as e:
        if debug:
            raise
        friendly = translate("operation", e.failure)
        _console.print(f"[red]{friendly.message}[/red]")
