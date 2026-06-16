import questionary
from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import resolve
from pdf_tool.core.range_parser import RangeParseError, parse_range
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_dir, prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection
from pdf_tool.widgets.unlock import prompt_unlock

_console = Console()


def _validate_positive_int(raw: str) -> bool | str:
    return (raw.isdigit() and int(raw) >= 1) or "Enter a positive integer."


def _validate_boundaries(n_pages: int):
    def _validate(raw: str) -> bool | str:
        try:
            pages = parse_range(raw, n_pages=n_pages)
        except RangeParseError as e:
            return str(e)
        if any(p == 1 for p in pages):
            return "Boundary 1 is meaningless (it's the start of the document)."
        return True

    return _validate


def run() -> None:
    input_path = prompt_input_file("Input PDF to split")
    if input_path is None:
        return

    backend = PikepdfBackend()
    unlocked = prompt_unlock(backend, input_path)
    if unlocked is None:
        return
    n_pages, password = unlocked

    mode = questionary.select(
        "Split Mode?",
        choices=[
            questionary.Choice("One file per page", value="every_page"),
            questionary.Choice("Every N pages", value="every_n"),
            questionary.Choice("At specific page boundaries", value="boundaries"),
            questionary.Choice("Extract pages into one new PDF", value="extract"),
        ],
    ).ask()
    if mode is None:
        return

    if mode == "every_page":
        out_dir = prompt_output_dir(
            ensure_unique(derive_output(input_path, "split"), as_directory=True),
            hint="e.g. pages/",
        )
        if out_dir is None:
            return
        outputs = backend.split_every_page(input_path, out_dir, password=password)
        _console.print(f"[green]Wrote {len(outputs)} files to {out_dir}[/green]")
    elif mode == "every_n":
        raw = questionary.text(
            "Split every how many pages?", validate=_validate_positive_int
        ).ask()
        if raw is None:
            return
        out_dir = prompt_output_dir(
            ensure_unique(derive_output(input_path, "split"), as_directory=True),
            hint="e.g. chunks/",
        )
        if out_dir is None:
            return
        outputs = backend.split_every_n(
            input_path, out_dir, n=int(raw), password=password
        )
        _console.print(f"[green]Wrote {len(outputs)} files to {out_dir}[/green]")
    elif mode == "boundaries":
        raw = questionary.text(
            f"Page boundaries (1..{n_pages}, e.g. 5,12,20):",
            validate=_validate_boundaries(n_pages),
        ).ask()
        if raw is None:
            return
        boundaries = parse_range(raw, n_pages=n_pages)
        out_dir = prompt_output_dir(
            ensure_unique(derive_output(input_path, "split"), as_directory=True),
            hint="e.g. sections/",
        )
        if out_dir is None:
            return
        outputs = backend.split_at_boundaries(
            input_path, out_dir, boundaries=boundaries, password=password
        )
        _console.print(f"[green]Wrote {len(outputs)} files to {out_dir}[/green]")
    else:  # extract
        selection = prompt_page_selection(n_pages)
        if selection is None:
            return
        pages = resolve(selection, n_pages=n_pages)
        output = prompt_output_path(
            ensure_unique(input_path.with_stem(f"{input_path.stem}-extracted")),
            hint="e.g. extracted.pdf",
        )
        if output is None:
            return
        backend.extract_pages(input_path, output, pages=pages, password=password)
        _console.print(f"[green]Wrote {output}[/green]")
