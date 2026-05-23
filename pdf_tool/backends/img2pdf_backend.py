from pathlib import Path

from pdf_tool.backends.subprocess_backend import SubprocessBackend


class Img2pdfBackend(SubprocessBackend):
    binary = "img2pdf"

    def images_to_pdf(self, input_paths: list[Path], output_path: Path) -> Path:
        self._check(
            [*[str(p) for p in input_paths], "-o", str(output_path)]
        )
        return output_path
