from rich.console import Console

from pdf_tool.backends.pikepdf_backend import PikepdfBackend
from pdf_tool.core.output_namer import derive_output, ensure_unique
from pdf_tool.widgets.file_input import prompt_input_file
from pdf_tool.widgets.output_path import prompt_output_path
from pdf_tool.widgets.summary import closing_panel

_console = Console()


def run() -> None:
    input_path = prompt_input_file("Input PDF to repair")
    if input_path is None:
        return

    output = prompt_output_path(
        ensure_unique(derive_output(input_path, "repair")),
        hint="e.g. fixed.pdf",
        recap=f"Repair {input_path.name}",
    )
    if output is None:
        return

    PikepdfBackend().try_repair(input_path, output)
    closing_panel(output)
