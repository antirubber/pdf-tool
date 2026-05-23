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
        output_dir.mkdir(parents=True, exist_ok=True)
        prefix = str(output_dir / "page")
        fmt_flag = f"-{options.image_format}"
        self._check(
            [
                fmt_flag,
                "-r",
                str(options.dpi),
                str(input_path),
                prefix,
            ]
        )
        return output_dir


class PdftotextBackend(SubprocessBackend):
    binary = "pdftotext"

    def pdf_to_text(
        self, input_path: Path, output_path: Path, options: PdfToTextOptions
    ) -> Path:
        self._check([str(input_path), str(output_path)])
        return output_path
