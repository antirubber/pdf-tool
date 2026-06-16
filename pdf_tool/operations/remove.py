from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.core.page_selection import resolve
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.page_selection import prompt_page_selection
from pdf_tool.widgets.summary import closing_panel
from pdf_tool.widgets.unlock import prompt_unlock

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to trim")
    if input_path is None:
        return

    backend = PikepdfBackend()
    unlocked = prompt_unlock(backend, input_path)
    if unlocked is None:
        return
    n_pages, password = unlocked

    _console.print("Choose the pages to remove; the rest are kept.")
    selection = prompt_page_selection(n_pages)
    if selection is None:
        return
    pages = resolve(selection, n_pages=n_pages)
    if len(set(pages)) >= n_pages:
        _console.print(
            "[red]That would remove every page — nothing to write.[/red]"
        )
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "remove")),
        hint="e.g. trimmed.pdf",
        recap=f"Remove {len(pages)} page(s) from {input_path.name}",
    )
    if output is None:
        return

    backend.remove_pages(input_path, output, pages=pages, password=password)
    closing_panel(output, n_pages=n_pages - len(set(pages)))
