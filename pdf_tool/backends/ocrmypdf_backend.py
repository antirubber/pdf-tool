from dataclasses import dataclass
from pathlib import Path

from pdf_tool.backends.subprocess_backend import SubprocessBackend


@dataclass(frozen=True)
class OcrOptions:
    language: str = "eng"
    force: bool = False


class OcrmypdfBackend(SubprocessBackend):
    binary = "ocrmypdf"

    def add_text_layer(
        self, input_path: Path, output_path: Path, options: OcrOptions
    ) -> Path:
        args: list[str] = ["-l", options.language]
        if options.force:
            args.append("--force-ocr")
        with self._atomic_path(output_path) as tmp:
            self._check([*args, str(input_path), str(tmp)], timeout=600.0)
        return output_path
