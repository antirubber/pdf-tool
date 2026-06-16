import os
import shutil
import tempfile
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


# Macro security level 3 ("Very High"): only macros from trusted, explicitly
# configured locations run — a crafted document cannot execute macros.
_MACRO_HARDENING_XCU = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<oor:items xmlns:oor="http://openoffice.org/2001/registry" '
    'xmlns:xs="http://www.w3.org/2001/XMLSchema" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
    ' <item oor:path="/org.openoffice.Office.Common/Security/Scripting">'
    '<prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop>'
    "</item>\n"
    "</oor:items>\n"
)


def _write_macro_hardening(profile_dir: Path) -> None:
    user_dir = profile_dir / "user"
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "registrymodifications.xcu").write_text(_MACRO_HARDENING_XCU)


def _soffice_args(
    input_path: Path, target_format: str, out_dir: Path, profile_dir: Path
) -> list[str]:
    return [
        # Per-invocation private profile: never touches the user's real config
        # and cannot collide with an already-open GUI LibreOffice instance.
        f"-env:UserInstallation=file://{profile_dir}",
        "--headless",
        "--norestore",
        "--convert-to",
        target_format,
        "--outdir",
        str(out_dir),
        str(input_path),
    ]


class LibreOfficeBackend(SubprocessBackend):
    binary = _resolve_binary()

    def convert(
        self, input_path: Path, output_path: Path, options: ConvertOptions
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # LibreOffice always writes <stem>.<format> into its --outdir and would
        # overwrite a real user file of that name before we could rename it.
        # Convert into an isolated work dir (same filesystem as the output, so
        # the move is atomic) and move only the single product into place.
        with (
            tempfile.TemporaryDirectory(prefix=".soffice-profile-") as profile,
            tempfile.TemporaryDirectory(
                prefix=".soffice-out-", dir=output_path.parent
            ) as work,
        ):
            profile_dir = Path(profile)
            work_dir = Path(work)
            _write_macro_hardening(profile_dir)
            self._check(
                _soffice_args(
                    input_path, options.target_format, work_dir, profile_dir
                ),
                timeout=180.0,
            )
            produced = work_dir / f"{input_path.stem}.{options.target_format}"
            os.replace(produced, output_path)
        return output_path
