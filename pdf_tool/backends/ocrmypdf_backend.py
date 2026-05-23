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
        args.extend([str(input_path), str(output_path)])
        self._check(args, timeout=600.0)
        return output_path
