import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class BackendName(Enum):
    PIKEPDF = "pikepdf"
    LIBREOFFICE = "libreoffice"
    GHOSTSCRIPT = "ghostscript"
    OCRMYPDF = "ocrmypdf"
    PDFTOPPM = "pdftoppm"
    PDFTOTEXT = "pdftotext"
    IMG2PDF = "img2pdf"


@dataclass(frozen=True)
class Available:
    pass


@dataclass(frozen=True)
class Missing:
    install_hint: str


BackendStatus = Available | Missing
BackendAvailability = dict[BackendName, BackendStatus]


_BINARY_CANDIDATES: dict[BackendName, tuple[str, ...]] = {
    BackendName.LIBREOFFICE: ("libreoffice", "soffice"),
    BackendName.GHOSTSCRIPT: ("gs",),
    BackendName.OCRMYPDF: ("ocrmypdf",),
    BackendName.PDFTOPPM: ("pdftoppm",),
    BackendName.PDFTOTEXT: ("pdftotext",),
    BackendName.IMG2PDF: ("img2pdf",),
}

# Package name per Backend, keyed by package manager — names differ across
# distros (e.g. poppler vs poppler-utils, libreoffice vs libreoffice-fresh).
_PACKAGES: dict[BackendName, dict[str, str]] = {
    BackendName.LIBREOFFICE: {
        "brew": "libreoffice", "apt": "libreoffice",
        "dnf": "libreoffice", "pacman": "libreoffice-fresh",
    },
    BackendName.GHOSTSCRIPT: {
        "brew": "ghostscript", "apt": "ghostscript",
        "dnf": "ghostscript", "pacman": "ghostscript",
    },
    BackendName.OCRMYPDF: {
        "brew": "ocrmypdf", "apt": "ocrmypdf",
        "dnf": "ocrmypdf", "pacman": "ocrmypdf",
    },
    BackendName.PDFTOPPM: {
        "brew": "poppler", "apt": "poppler-utils",
        "dnf": "poppler-utils", "pacman": "poppler",
    },
    BackendName.PDFTOTEXT: {
        "brew": "poppler", "apt": "poppler-utils",
        "dnf": "poppler-utils", "pacman": "poppler",
    },
    BackendName.IMG2PDF: {
        "brew": "img2pdf", "apt": "img2pdf",
        "dnf": "img2pdf", "pacman": "img2pdf",
    },
}

# (manager key, probe binary, install command). Order is the detection
# preference; brew is last so it is the macOS-friendly fallback.
_MANAGERS: tuple[tuple[str, str, str], ...] = (
    ("apt", "apt-get", "sudo apt install"),
    ("dnf", "dnf", "sudo dnf install"),
    ("pacman", "pacman", "sudo pacman -S"),
    ("brew", "brew", "brew install"),
)


def detect_package_manager(
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[str, str]:
    """Return (manager_key, install_command) for the first manager on PATH.

    Defaults to brew when none is detected, matching the project's macOS roots.
    """
    for key, binary, command in _MANAGERS:
        if which(binary) is not None:
            return key, command
    return "brew", "brew install"


def probe(
    which: Callable[[str], str | None] = shutil.which,
) -> BackendAvailability:
    manager_key, command = detect_package_manager(which)
    result: BackendAvailability = {BackendName.PIKEPDF: Available()}
    for backend, candidates in _BINARY_CANDIDATES.items():
        if any(which(c) is not None for c in candidates):
            result[backend] = Available()
        else:
            package = _PACKAGES[backend][manager_key]
            result[backend] = Missing(install_hint=f"{command} {package}")
    return result
