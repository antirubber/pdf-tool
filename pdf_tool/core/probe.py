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

_INSTALL_HINTS: dict[BackendName, str] = {
    BackendName.LIBREOFFICE: "brew install libreoffice",
    BackendName.GHOSTSCRIPT: "brew install ghostscript",
    BackendName.OCRMYPDF: "brew install ocrmypdf",
    BackendName.PDFTOPPM: "brew install poppler",
    BackendName.PDFTOTEXT: "brew install poppler",
    BackendName.IMG2PDF: "brew install img2pdf",
}


def probe(
    which: Callable[[str], str | None] = shutil.which,
) -> BackendAvailability:
    result: BackendAvailability = {BackendName.PIKEPDF: Available()}
    for backend, candidates in _BINARY_CANDIDATES.items():
        if any(which(c) is not None for c in candidates):
            result[backend] = Available()
        else:
            result[backend] = Missing(install_hint=_INSTALL_HINTS[backend])
    return result
