import hashlib
import hmac
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable

from rich.console import Console

from pdf_tool import __version__

_console = Console()

# Release assets are pinned to the immutable tag behind "latest"; both the
# installer and its checksum are fetched from there and verified before exec.
RELEASE_BASE = "https://github.com/antirubber/pdf-tool/releases/latest/download"
INSTALLER_NAME = "install.sh"
CHECKSUMS_NAME = "SHA256SUMS"


def _http_get(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310
            return resp.read()
    except (urllib.error.URLError, OSError):
        return None


def _verify(data: bytes, expected_hex: str) -> bool:
    actual = hashlib.sha256(data).hexdigest()
    return hmac.compare_digest(actual, expected_hex.strip().lower())


def _expected_sha256(checksums: bytes, filename: str) -> str | None:
    """Pull the digest for ``filename`` from a `sha256sum`-format file."""
    for line in checksums.decode("utf-8", "replace").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == filename:
            return parts[0]
    return None


def _run_verified(script: bytes) -> int:
    result = subprocess.run(["sh", "-s"], input=script)
    return result.returncode


def run(fetch: Callable[[str], bytes | None] = _http_get) -> int:
    """Download the latest installer, verify its checksum, then run it.

    Fails closed: if the download fails or the SHA256 does not match the
    published digest, nothing is executed.
    """
    _console.print(f"Updating pdf-tool (current v{__version__})…")
    script = fetch(f"{RELEASE_BASE}/{INSTALLER_NAME}")
    checksums = fetch(f"{RELEASE_BASE}/{CHECKSUMS_NAME}")
    if script is None or checksums is None:
        _console.print(
            "[red]Could not download the verified installer from the latest "
            "release.[/red]"
        )
        return 1

    expected = _expected_sha256(checksums, INSTALLER_NAME)
    if expected is None or not _verify(script, expected):
        _console.print(
            "[red]Installer integrity check failed; aborting without running "
            "anything.[/red]"
        )
        return 1

    returncode = _run_verified(script)
    if returncode != 0:
        _console.print(f"[red]Update failed (exit {returncode}).[/red]")
    return returncode
