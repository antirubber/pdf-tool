import questionary
from rich.console import Console

from pdf_tool.backends.ocrmypdf_backend import OcrmypdfBackend, OcrOptions
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to OCR")
    if input_path is None:
        return

    advanced = questionary.confirm("Advanced options?", default=False).ask()
    if advanced is None:
        return

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
            return
        force = force_input

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "ocr")),
        hint="e.g. searchable.pdf",
    )
    if output is None:
        return

    OcrmypdfBackend().add_text_layer(
        input_path, output, OcrOptions(language=language, force=force)
    )
    _console.print(f"[green]Wrote {output}[/green]")
