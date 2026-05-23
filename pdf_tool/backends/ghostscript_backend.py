from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pdf_tool.backends.subprocess_backend import SubprocessBackend

CompressPreset = Literal["screen", "ebook", "printer", "prepress"]


@dataclass(frozen=True)
class CompressOptions:
    preset: CompressPreset = "ebook"


class GhostscriptBackend(SubprocessBackend):
    binary = "gs"

    def compress(
        self, input_path: Path, output_path: Path, options: CompressOptions
    ) -> Path:
        self._check(
            [
                "-dBATCH",
                "-dNOPAUSE",
                "-q",
                "-sDEVICE=pdfwrite",
                f"-dPDFSETTINGS=/{options.preset}",
                "-o",
                str(output_path),
                str(input_path),
            ]
        )
        return output_path
