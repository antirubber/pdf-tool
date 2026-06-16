import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PageNumberOptions, PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import All, resolve
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection

_console = Console()

_POSITION_CHOICES = [
    questionary.Choice("Bottom centre (default)", value="bottom-center"),
    questionary.Choice("Bottom left", value="bottom-left"),
    questionary.Choice("Bottom right", value="bottom-right"),
    questionary.Choice("Top centre", value="top-center"),
    questionary.Choice("Top left", value="top-left"),
    questionary.Choice("Top right", value="top-right"),
]

_FORMAT_CHOICES = [
    questionary.Choice("N", value="plain"),
    questionary.Choice("N of M", value="of_total"),
    questionary.Choice("Page N", value="page_n"),
    questionary.Choice("Bates (prefix + zero-padded)", value="bates"),
]


def _positive_int(raw: str) -> bool | str:
    return (raw.isdigit() and int(raw) >= 1) or "Enter a positive integer."


def _collect_options(n_pages: int, advanced: bool) -> PageNumberOptions | None:
    if not advanced:
        return PageNumberOptions(pages=resolve(All(), n_pages=n_pages))

    position = questionary.select("Position?", choices=_POSITION_CHOICES).ask()
    if position is None:
        return None
    style = questionary.select("Number format?", choices=_FORMAT_CHOICES).ask()
    if style is None:
        return None

    bates_prefix = ""
    bates_width = 6
    if style == "bates":
        bates_prefix = questionary.text("Bates prefix (e.g. ABC-):", default="").ask()
        if bates_prefix is None:
            return None
        width_raw = questionary.text(
            "Zero-pad width:", default="6", validate=_positive_int
        ).ask()
        if width_raw is None:
            return None
        bates_width = int(width_raw)

    start_raw = questionary.text(
        "Start number:", default="1", validate=_positive_int
    ).ask()
    if start_raw is None:
        return None

    selection = prompt_page_selection(n_pages)
    if selection is None:
        return None
    pages = resolve(selection, n_pages=n_pages)

    return PageNumberOptions(
        pages=pages,
        start=int(start_raw),
        style=style,
        position=position,
        bates_prefix=bates_prefix,
        bates_width=bates_width,
    )


def run() -> None:
    input_path = prompt_input_file("Input PDF to number")
    if input_path is None:
        return

    backend = PikepdfBackend()
    info = backend.inspect(input_path)
    if info.n_pages is None:
        _console.print(
            "[red]Cannot number an encrypted PDF. Decrypt it first.[/red]"
        )
        return

    advanced = questionary.confirm("Advanced options?", default=False).ask()
    if advanced is None:
        return

    options = _collect_options(info.n_pages, advanced)
    if options is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "page_numbers")),
        hint="e.g. numbered.pdf",
    )
    if output is None:
        return

    backend.add_page_numbers(input_path, output, options)
    _console.print(f"[green]Wrote {output}[/green]")
