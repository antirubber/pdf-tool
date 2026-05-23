from pathlib import Path

import questionary
from rich.console import Console

from pdf_tool.backends.img2pdf_backend import Img2pdfBackend
from pdf_tool.backends.libreoffice_backend import ConvertOptions, LibreOfficeBackend
from pdf_tool.backends.poppler_backend import (
    PdfToImagesOptions,
    PdfToTextOptions,
    PdftoppmBackend,
    PdftotextBackend,
)
from pdf_tool.core.error_translator import BackendError, translate
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.batch import (
    collect_directory_files_interactive,
    collect_input_files,
    print_summary,
    prompt_one_or_many,
    run_per_file,
)
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_dir, prompt_output_path

_console = Console()

_OFFICE_EXTS = {
    ".docx",
    ".xlsx",
    ".pptx",
    ".odt",
    ".rtf",
    ".doc",
    ".xls",
    ".ppt",
    ".ods",
    ".odp",
}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".gif"}
_CONVERTIBLE_EXTS = _OFFICE_EXTS | _IMAGE_EXTS | {".pdf"}


def _convert_office_to_pdf_one(input_path: Path) -> None:
    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "convert", target_format="pdf")),
        hint="e.g. report.pdf",
    )
    if output is None:
        return
    try:
        LibreOfficeBackend().convert(
            input_path, output, ConvertOptions(target_format="pdf")
        )
    except BackendError as e:
        _console.print(f"[red]{translate('convert', e.failure).message}[/red]")
        return
    _console.print(f"[green]Wrote {output}[/green]")


def _convert_office_to_pdf_batch(inputs: list[Path]) -> None:
    if not questionary.confirm(
        f"Will convert {len(inputs)} file(s) to PDF. OK?", default=True
    ).ask():
        return
    backend = LibreOfficeBackend()

    def process(path: Path) -> Path:
        output = ensure_unique(derive_output(path, "convert", target_format="pdf"))
        return backend.convert(
            path, output, ConvertOptions(target_format="pdf")
        )

    outcomes = run_per_file("convert", inputs, process)
    print_summary(outcomes)


def _convert_pdf(input_path: Path) -> None:
    target = questionary.select(
        "Convert PDF to?",
        choices=[
            questionary.Choice("Word (.docx)", value="docx"),
            questionary.Choice("OpenDocument Text (.odt)", value="odt"),
            questionary.Choice("Excel (.xlsx)", value="xlsx"),
            questionary.Choice("PowerPoint (.pptx)", value="pptx"),
            questionary.Choice("Images (PNG, one per page)", value="png"),
            questionary.Choice("Images (JPEG, one per page)", value="jpeg"),
            questionary.Choice("Plain text", value="txt"),
        ],
    ).ask()
    if target is None:
        return

    try:
        if target in ("docx", "odt", "xlsx", "pptx"):
            output = prompt_output_path(
                ensure_unique(
                    derive_output(input_path, "convert", target_format=target)
                ),
                hint=f"e.g. output.{target}",
            )
            if output is None:
                return
            LibreOfficeBackend().convert(
                input_path, output, ConvertOptions(target_format=target)
            )
            _console.print(f"[green]Wrote {output}[/green]")
        elif target in ("png", "jpeg"):
            output_dir = prompt_output_dir(
                ensure_unique(
                    derive_output(input_path, "convert", target_format=target)
                ),
                hint="e.g. pages/",
            )
            if output_dir is None:
                return
            PdftoppmBackend().pdf_to_images(
                input_path, output_dir, PdfToImagesOptions(image_format=target)
            )
            _console.print(f"[green]Wrote images to {output_dir}[/green]")
        else:  # txt
            output = prompt_output_path(
                ensure_unique(input_path.with_suffix(".txt")),
                hint="e.g. content.txt",
            )
            if output is None:
                return
            PdftotextBackend().pdf_to_text(input_path, output, PdfToTextOptions())
            _console.print(f"[green]Wrote {output}[/green]")
    except BackendError as e:
        _console.print(f"[red]{translate('convert', e.failure).message}[/red]")


def _convert_images_to_pdf_one(first_image: Path) -> None:
    paths = [first_image]
    while True:
        more = questionary.confirm("Add another image?", default=True).ask()
        if not more:
            break
        nxt = prompt_input_file(f"Image #{len(paths) + 1}")
        if nxt is None:
            break
        paths.append(nxt)

    output = prompt_output_path(
        ensure_unique(first_image.with_suffix(".pdf")),
        hint="e.g. scan.pdf",
    )
    if output is None:
        return

    try:
        Img2pdfBackend().images_to_pdf(paths, output)
    except BackendError as e:
        _console.print(f"[red]{translate('convert', e.failure).message}[/red]")
        return
    _console.print(f"[green]Wrote {output}[/green]")


def _convert_images_to_pdf_batch(inputs: list[Path]) -> None:
    if not questionary.confirm(
        f"Will combine {len(inputs)} image(s) into one PDF. OK?", default=True
    ).ask():
        return
    output = prompt_output_path(
        ensure_unique(inputs[0].with_suffix(".pdf")),
        hint="e.g. combined.pdf",
    )
    if output is None:
        return
    try:
        Img2pdfBackend().images_to_pdf(inputs, output)
    except BackendError as e:
        _console.print(f"[red]{translate('convert', e.failure).message}[/red]")
        return
    _console.print(f"[green]Wrote {output}[/green]")


def _run_directory() -> None:
    files = collect_directory_files_interactive(_CONVERTIBLE_EXTS)
    if not files:
        return
    office = [f for f in files if f.suffix.lower() in _OFFICE_EXTS]
    pdfs = [f for f in files if f.suffix.lower() == ".pdf"]
    images = [f for f in files if f.suffix.lower() in _IMAGE_EXTS]
    if office:
        _convert_office_to_pdf_batch(office)
    if pdfs:
        _console.print(
            f"[yellow]Skipping {len(pdfs)} PDF(s) — "
            f"PDF→other requires choosing a target format per run.[/yellow]"
        )
    if images:
        _convert_images_to_pdf_batch(images)


def _run_many() -> None:
    inputs = collect_input_files("First file to convert")
    if not inputs:
        return
    exts = {p.suffix.lower() for p in inputs}
    if len(exts) > 1:
        _console.print(
            "[yellow]Batch mode works best with one file type. "
            "Consider using directory mode for mixed types.[/yellow]"
        )
    representative = inputs[0].suffix.lower()
    if representative in _OFFICE_EXTS:
        _convert_office_to_pdf_batch(inputs)
    elif representative in _IMAGE_EXTS:
        _convert_images_to_pdf_batch(inputs)
    elif representative == ".pdf":
        _console.print(
            "[yellow]PDF batch conversion requires choosing a target format. "
            "Use single-file mode for PDF→other conversions.[/yellow]"
        )
    else:
        _console.print(
            f"[red]This is pdf-tool, not a general format converter. "
            f"{representative} files are not supported.[/red]"
        )


def run() -> None:
    mode = prompt_one_or_many()
    if mode is None:
        return
    if mode == "directory":
        _run_directory()
        return
    if mode == "many":
        _run_many()
        return

    input_path = prompt_input_file("File to convert")
    if input_path is None:
        return

    ext = input_path.suffix.lower()
    if ext in _OFFICE_EXTS:
        _convert_office_to_pdf_one(input_path)
    elif ext == ".pdf":
        _convert_pdf(input_path)
    elif ext in _IMAGE_EXTS:
        _convert_images_to_pdf_one(input_path)
    else:
        _console.print(
            f"[red]This is pdf-tool, not a general format converter. "
            f"{ext} files are not supported.[/red]"
        )
