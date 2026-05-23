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
from pdf_tool.widgets.file_input import prompt_input_file

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


def _convert_office_to_pdf(input_path):
    output = ensure_unique(derive_output(input_path, "convert", target_format="pdf"))
    if not questionary.confirm(f"Will write to {output}. OK?", default=True).ask():
        return
    try:
        LibreOfficeBackend().convert(
            input_path, output, ConvertOptions(target_format="pdf")
        )
    except BackendError as e:
        _console.print(f"[red]{translate('convert', e.failure).message}[/red]")
        return
    _console.print(f"[green]Wrote {output}[/green]")


def _convert_pdf(input_path):
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
            output = ensure_unique(
                derive_output(input_path, "convert", target_format=target)
            )
            if not questionary.confirm(f"Will write to {output}. OK?", default=True).ask():
                return
            LibreOfficeBackend().convert(
                input_path, output, ConvertOptions(target_format=target)
            )
            _console.print(f"[green]Wrote {output}[/green]")
        elif target in ("png", "jpeg"):
            output_dir = ensure_unique(
                derive_output(input_path, "convert", target_format=target)
            )
            if not questionary.confirm(
                f"Will write to {output_dir}/. OK?", default=True
            ).ask():
                return
            PdftoppmBackend().pdf_to_images(
                input_path, output_dir, PdfToImagesOptions(image_format=target)
            )
            _console.print(f"[green]Wrote images to {output_dir}[/green]")
        else:  # txt
            output = ensure_unique(input_path.with_suffix(".txt"))
            if not questionary.confirm(f"Will write to {output}. OK?", default=True).ask():
                return
            PdftotextBackend().pdf_to_text(input_path, output, PdfToTextOptions())
            _console.print(f"[green]Wrote {output}[/green]")
    except BackendError as e:
        _console.print(f"[red]{translate('convert', e.failure).message}[/red]")


def _convert_images_to_pdf(first_image):
    paths = [first_image]
    while True:
        more = questionary.confirm("Add another image?", default=True).ask()
        if not more:
            break
        nxt = prompt_input_file(f"Image #{len(paths) + 1}")
        if nxt is None:
            break
        paths.append(nxt)

    output = ensure_unique(first_image.with_suffix(".pdf"))
    if not questionary.confirm(f"Will write to {output}. OK?", default=True).ask():
        return

    try:
        Img2pdfBackend().images_to_pdf(paths, output)
    except BackendError as e:
        _console.print(f"[red]{translate('convert', e.failure).message}[/red]")
        return
    _console.print(f"[green]Wrote {output}[/green]")


def run() -> None:
    input_path = prompt_input_file("File to convert")
    if input_path is None:
        return

    ext = input_path.suffix.lower()
    if ext in _OFFICE_EXTS:
        _convert_office_to_pdf(input_path)
    elif ext == ".pdf":
        _convert_pdf(input_path)
    elif ext in _IMAGE_EXTS:
        _convert_images_to_pdf(input_path)
    else:
        _console.print(
            f"[red]This is pdf-tool, not a general format converter. "
            f"{ext} files are not supported.[/red]"
        )
