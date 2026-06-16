from dataclasses import dataclass
from pathlib import Path

from pdf_tool.backends.subprocess_backend import SubprocessBackend


@dataclass(frozen=True)
class PdfToImagesOptions:
    image_format: str = "png"
    dpi: int = 150


@dataclass(frozen=True)
class PdfToTextOptions:
    pass


class PdftoppmBackend(SubprocessBackend):
    binary = "pdftoppm"

    def pdf_to_images(
        self, input_path: Path, output_dir: Path, options: PdfToImagesOptions
    ) -> Path:
        fmt_flag = f"-{options.image_format}"
        with self._atomic_dir(output_dir) as staging:
            self._check(
                [
                    fmt_flag,
                    "-r",
                    str(options.dpi),
                    str(input_path),
                    str(staging / "page"),
                ]
            )
        return output_dir


class PdftotextBackend(SubprocessBackend):
    binary = "pdftotext"

    def pdf_to_text(
        self, input_path: Path, output_path: Path, options: PdfToTextOptions
    ) -> Path:
        with self._atomic_path(output_path) as tmp:
            self._check([str(input_path), str(tmp)])
        return output_path
