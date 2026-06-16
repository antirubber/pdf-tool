from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend, WatermarkOptions
from pdf_tool.core.error_translator import BackendError, PikepdfFailure
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import All, PageSelection, resolve
from pdf_tool.widgets.batch import run_one_or_many
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection
from pdf_tool.widgets.summary import closing_panel
from pdf_tool.widgets.unlock import prompt_unlock

_console = Console()

_BATCH_PAGE_REF = 1_000_000


def _prompt_text() -> str | None:
    return questionary.text(
        "Watermark text:",
        default="DRAFT",
        validate=lambda v: bool(v.strip()) or "Text required.",
    ).ask()


def _run_one() -> None:
    input_path = prompt_input_file("Input PDF to watermark")
    if input_path is None:
        return

    backend = PikepdfBackend()
    unlocked = prompt_unlock(backend, input_path)
    if unlocked is None:
        return
    n_pages, password = unlocked

    text = _prompt_text()
    if text is None:
        return

    advanced = questionary.confirm("Advanced options?", default=False).ask()
    if advanced is None:
        return
    if advanced:
        selection = prompt_page_selection(n_pages)
        if selection is None:
            return
    else:
        selection = All()
    pages = resolve(selection, n_pages=n_pages)

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "watermark")),
        hint="e.g. draft.pdf",
        recap=f'Watermark {input_path.name} with "{text}" ({len(pages)} page(s))',
    )
    if output is None:
        return

    backend.watermark(
        input_path, output, WatermarkOptions(text=text, pages=pages), password=password
    )
    closing_panel(output, n_pages=n_pages)


def _collect_batch_params() -> tuple[str, PageSelection] | None:
    text = _prompt_text()
    if text is None:
        return None
    advanced = questionary.confirm(
        "Choose specific pages? (default: all)", default=False
    ).ask()
    if advanced is None:
        return None
    if advanced:
        selection = prompt_page_selection(_BATCH_PAGE_REF)
        if selection is None:
            return None
    else:
        selection = All()
    return text, selection


def _make_process(params: tuple[str, PageSelection]):
    text, selection = params
    backend = PikepdfBackend()

    def process(path: Path) -> Path:
        info = backend.inspect(path)
        if info.n_pages is None:
            raise BackendError(PikepdfFailure("PasswordError"))
        pages = resolve(selection, n_pages=info.n_pages)
        return backend.watermark(
            path,
            ensure_unique(derive_output(path, "watermark")),
            WatermarkOptions(text=text, pages=pages),
        )

    return process


def run() -> None:
    run_one_or_many(
        operation="watermark",
        first_prompt="First PDF to watermark",
        run_single=_run_one,
        collect_params=_collect_batch_params,
        make_process=_make_process,
        confirm_message=lambda n, p: f'Will watermark {n} files with "{p[0]}". OK?',
    )
