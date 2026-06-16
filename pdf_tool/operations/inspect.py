from rich.console import Console
from rich.table import Table

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.humanize import humanize_bytes
from pdf_tool.widgets.file_input import prompt_input_file

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to inspect")
    if input_path is None:
        return

    info = PikepdfBackend().inspect(input_path)

    table = Table(title=str(input_path), show_header=False, title_justify="left")
    table.add_column()
    table.add_column()
    if info.file_size is not None:
        table.add_row("Size", humanize_bytes(info.file_size))
    table.add_row("Encrypted", "yes" if info.encrypted else "no")
    if info.pdf_version is not None:
        table.add_row("PDF version", info.pdf_version)
    if info.n_pages is not None:
        table.add_row("Pages", str(info.n_pages))
    else:
        table.add_row("Pages", "(unknown — encrypted)")
    if info.page_size is not None and info.page_label is not None:
        width, height = info.page_size
        table.add_row(
            "Page size", f"{width:.0f}×{height:.0f} pt ({info.page_label})"
        )
    if info.has_text is not None:
        table.add_row("Text layer", "yes" if info.has_text else "no (image-only?)")
    for key, value in info.metadata.items():
        table.add_row(key, value)
    _console.print(table)
