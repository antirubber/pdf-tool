import questionary
from rich.console import Console

from pdf_tool import __version__
from pdf_tool.backends.ghostscript_backend import (
    ghostscript_version,
    ghostscript_warning,
)
from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.probe import Available, BackendName, probe
from pdf_tool.operations import compress as compress_op
from pdf_tool.operations import convert as convert_op
from pdf_tool.operations import decrypt as decrypt_op
from pdf_tool.operations import encrypt as encrypt_op
from pdf_tool.operations import inspect as inspect_op
from pdf_tool.operations import merge as merge_op
from pdf_tool.operations import metadata as metadata_op
from pdf_tool.operations import ocr as ocr_op
from pdf_tool.operations import remove as remove_op
from pdf_tool.operations import reorder as reorder_op
from pdf_tool.operations import repair as repair_op
from pdf_tool.operations import rotate as rotate_op
from pdf_tool.operations import split as split_op
from pdf_tool.operations import watermark as watermark_op
from pdf_tool.widgets.wizard_menu import (
    WIZARD_STYLE,
    MenuEntry,
    OperationGroup,
    build_header,
    build_menu,
)


_console = Console()


_OPERATIONS: tuple[MenuEntry, ...] = (
    MenuEntry("Encrypt", "encrypt", encrypt_op.run, (BackendName.PIKEPDF,), OperationGroup.PROTECT),
    MenuEntry("Decrypt", "decrypt", decrypt_op.run, (BackendName.PIKEPDF,), OperationGroup.PROTECT),
    MenuEntry("Inspect", "inspect", inspect_op.run, (BackendName.PIKEPDF,), OperationGroup.INSPECT),
    MenuEntry("Metadata", "metadata", metadata_op.run, (BackendName.PIKEPDF,), OperationGroup.INSPECT),
    MenuEntry("Rotate", "rotate", rotate_op.run, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM),
    MenuEntry("Split", "split", split_op.run, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM),
    MenuEntry("Remove pages", "remove", remove_op.run, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM),
    MenuEntry("Reorder pages", "reorder", reorder_op.run, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM),
    MenuEntry("Merge", "merge", merge_op.run, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM),
    MenuEntry("Compress", "compress", compress_op.run, (BackendName.GHOSTSCRIPT,), OperationGroup.TRANSFORM),
    MenuEntry("Watermark", "watermark", watermark_op.run, (BackendName.PIKEPDF,), OperationGroup.TRANSFORM),
    MenuEntry(
        "Convert",
        "convert",
        convert_op.run,
        (BackendName.LIBREOFFICE, BackendName.PDFTOPPM, BackendName.PDFTOTEXT, BackendName.IMG2PDF),
        OperationGroup.GENERATE,
    ),
    MenuEntry("OCR", "ocr", ocr_op.run, (BackendName.OCRMYPDF,), OperationGroup.GENERATE),
    MenuEntry("Repair", "repair", repair_op.run, (BackendName.PIKEPDF,), OperationGroup.GENERATE),
)


def _dispatch(entry: MenuEntry, *, debug: bool) -> None:
    """Run an Operation, translating any BackendError to the Friendly path.

    This is the single place that decides Friendly vs Debug for a one-shot run:
    under --debug the BackendError (with its chained cause) propagates so the
    real traceback is shown; otherwise a plain-English message is printed.
    """
    try:
        entry.handler()
    except BackendError as e:
        if debug:
            raise
        friendly = translate(entry.value, e.failure)
        _console.print(f"[red]{friendly.message}[/red]")
        if friendly.suggested_action:
            _console.print(f"[yellow]{friendly.suggested_action}[/yellow]")


def run(*, debug: bool = False) -> None:
    availability = probe()
    _console.print(build_header(__version__))
    if isinstance(availability.get(BackendName.GHOSTSCRIPT), Available):
        warning = ghostscript_warning(ghostscript_version())
        if warning:
            _console.print(f"[yellow]{warning}[/yellow]")
    choices = build_menu(_OPERATIONS, availability)
    choice = questionary.select(
        "Pick an Operation:", choices=choices, style=WIZARD_STYLE
    ).ask()
    if choice is None:
        return
    entry = next(e for e in _OPERATIONS if e.value == choice)
    _dispatch(entry, debug=debug)
