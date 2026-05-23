from rich.console import Console
from rich.table import Table

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
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
    table.add_row("Encrypted", "yes" if info.encrypted else "no")
    if info.n_pages is not None:
        table.add_row("Pages", str(info.n_pages))
    else:
        table.add_row("Pages", "(unknown — encrypted)")
    for key, value in info.metadata.items():
        table.add_row(key, value)
    _console.print(table)
