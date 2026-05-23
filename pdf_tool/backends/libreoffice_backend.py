import shutil
from dataclasses import dataclass
from pathlib import Path

from pdf_tool.backends.subprocess_backend import SubprocessBackend


def _resolve_binary() -> str:
    for candidate in ("libreoffice", "soffice"):
        if shutil.which(candidate):
            return candidate
    return "libreoffice"


@dataclass(frozen=True)
class ConvertOptions:
    target_format: str  # "pdf", "docx", "odt", "xlsx", "pptx"


class LibreOfficeBackend(SubprocessBackend):
    binary = _resolve_binary()

    def convert(
        self, input_path: Path, output_path: Path, options: ConvertOptions
    ) -> Path:
        out_dir = output_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        self._check(
            [
                "--headless",
                "--convert-to",
                options.target_format,
                "--outdir",
                str(out_dir),
                str(input_path),
            ],
            timeout=180.0,
        )
        produced = out_dir / f"{input_path.stem}.{options.target_format}"
        if produced != output_path:
            produced.replace(output_path)
        return output_path
