from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.error_translator import BackendError, PikepdfFailure
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import PageSelection, resolve
from pdf_tool.widgets.batch import run_one_or_many
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection
from pdf_tool.widgets.summary import closing_panel
from pdf_tool.widgets.unlock import prompt_unlock

_console = Console()

_ANGLE_CHOICES = [
    questionary.Choice("90° clockwise (default)", value=90),
    questionary.Choice("90° counter-clockwise", value=-90),
    questionary.Choice("180°", value=180),
]
# Reference page count for the Batch page-selection prompt; the selection is
# re-resolved against each file's real page count when it runs.
_BATCH_PAGE_REF = 1_000_000


def _prompt_angle() -> int | None:
    return questionary.select("Rotation?", choices=_ANGLE_CHOICES).ask()


def _run_one() -> None:
    input_path = prompt_input_file("Input PDF to rotate")
    if input_path is None:
        return

    backend = PikepdfBackend()
    unlocked = prompt_unlock(backend, input_path)
    if unlocked is None:
        return
    n_pages, password = unlocked

    selection = prompt_page_selection(n_pages)
    if selection is None:
        return
    pages = resolve(selection, n_pages=n_pages)

    angle = _prompt_angle()
    if angle is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "rotate")),
        hint="e.g. rotated.pdf",
        recap=f"Rotate {input_path.name} by {int(angle)}° ({len(pages)} page(s))",
    )
    if output is None:
        return

    backend.rotate(
        input_path, output, pages=pages, degrees=int(angle), password=password
    )
    closing_panel(output, n_pages=n_pages)


def _collect_batch_params() -> tuple[PageSelection, int] | None:
    selection = prompt_page_selection(_BATCH_PAGE_REF)
    if selection is None:
        return None
    angle = _prompt_angle()
    if angle is None:
        return None
    return selection, int(angle)


def _make_process(params: tuple[PageSelection, int]):
    selection, degrees = params
    backend = PikepdfBackend()

    def process(path: Path) -> Path:
        info = backend.inspect(path)
        if info.n_pages is None:
            raise BackendError(PikepdfFailure("PasswordError"))
        pages = resolve(selection, n_pages=info.n_pages)
        return backend.rotate(
            path, ensure_unique(derive_output(path, "rotate")),
            pages=pages, degrees=degrees,
        )

    return process


def run() -> None:
    run_one_or_many(
        operation="rotate",
        first_prompt="First PDF to rotate",
        run_single=_run_one,
        collect_params=_collect_batch_params,
        make_process=_make_process,
        confirm_message=lambda n, p: f"Will rotate {n} files by {p[1]}°. OK?",
    )
