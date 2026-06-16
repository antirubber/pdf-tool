from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.ocrmypdf_backend import OcrmypdfBackend, OcrOptions
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.batch import run_one_or_many
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.progress import spinner

_console = Console()


def _collect_options() -> OcrOptions | None:
    advanced = questionary.confirm("Advanced options?", default=False).ask()
    if advanced is None:
        return None

    language = "eng"
    force = False
    if advanced:
        language = (
            questionary.text(
                "OCR language (tesseract code, e.g. eng, deu, fra):",
                default="eng",
                validate=lambda v: bool(v.strip()) or "Required.",
            ).ask()
            or "eng"
        )
        force_input = questionary.confirm(
            "Force re-OCR even if PDF already has text?", default=False
        ).ask()
        if force_input is None:
            return None
        force = force_input

    return OcrOptions(language=language, force=force)


def _run_one() -> None:
    input_path = prompt_input_file("Input PDF to OCR")
    if input_path is None:
        return

    options = _collect_options()
    if options is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "ocr")),
        hint="e.g. searchable.pdf",
    )
    if output is None:
        return

    with spinner("Running OCR"):
        OcrmypdfBackend().add_text_layer(input_path, output, options)
    _console.print(f"[green]Wrote {output}[/green]")


def _make_process(options: OcrOptions):
    backend = OcrmypdfBackend()

    def process(path: Path) -> Path:
        return backend.add_text_layer(
            path, ensure_unique(derive_output(path, "ocr")), options
        )

    return process


def run() -> None:
    run_one_or_many(
        operation="ocr",
        first_prompt="First PDF to OCR",
        run_single=_run_one,
        collect_params=_collect_options,
        make_process=_make_process,
        confirm_message=lambda n, p: f"Will OCR {n} files ({p.language}). OK?",
    )
