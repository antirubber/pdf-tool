import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from pdf_tool.core.error_translator import BackendError, SubprocessFailure


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class SubprocessBackend:
    binary: ClassVar[str]

    @contextmanager
    def _atomic_path(self, final_path: Path) -> Iterator[Path]:
        """Yield a temp path in the destination dir; replace ``final_path`` only on success.

        The child writes to the temp path, so a non-zero exit or a timeout
        leaves the destination untouched rather than a truncated file. The
        staging directory is always cleaned up.
        """
        final_path.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(
                dir=final_path.parent, prefix=f".{final_path.stem}-tmp-"
            )
        )
        try:
            tmp = staging / final_path.name
            yield tmp
            os.replace(tmp, final_path)
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    @contextmanager
    def _atomic_dir(self, final_dir: Path) -> Iterator[Path]:
        """Yield a staging dir; move it onto ``final_dir`` atomically on success.

        For Backends whose product is a directory of files (e.g. one image per
        page): a mid-run failure leaves no partial directory at the destination.
        """
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(
            tempfile.mkdtemp(
                dir=final_dir.parent, prefix=f".{final_dir.name}-tmp-"
            )
        )
        try:
            yield staging
            os.replace(staging, final_dir)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise

    def _run(self, args: list[str], *, timeout: float = 300.0) -> CommandResult:
        try:
            completed = subprocess.run(
                [self.binary, *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except FileNotFoundError as e:
            raise BackendError(
                SubprocessFailure(
                    binary=self.binary,
                    exit_code=-1,
                    stderr=f"{self.binary} not found — is it installed?",
                )
            ) from e
        except subprocess.TimeoutExpired as e:
            raise BackendError(
                SubprocessFailure(
                    binary=self.binary,
                    exit_code=-1,
                    stderr=f"timed out after {timeout}s",
                )
            ) from e
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
        )

    def _check(self, args: list[str], *, timeout: float = 300.0) -> CommandResult:
        result = self._run(args, timeout=timeout)
        if result.returncode != 0:
            raise BackendError(
                SubprocessFailure(
                    binary=self.binary,
                    exit_code=result.returncode,
                    stderr=result.stderr,
                )
            )
        return result
