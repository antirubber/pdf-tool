import subprocess
from dataclasses import dataclass
from typing import ClassVar

from pdf_tool.core.error_translator import BackendError, SubprocessFailure


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


class SubprocessBackend:
    binary: ClassVar[str]

    def _run(self, args: list[str], *, timeout: float = 300.0) -> CommandResult:
        try:
            completed = subprocess.run(
                [self.binary, *args],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
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
