"""Test harness for install.sh.

We exercise install.sh through its public interface: running it with
`--dry-run` against a *fabricated* system. The fabrication is a single bin
directory placed on PATH that contains stub executables for whatever we want
the script to "find" (brew, apt-get, gs, uv, ...), plus fake `uname` and `id`
so we control the OS and uid the script sees.

Because PATH points only at the stub dir, `command -v X` finds X iff we stubbed
it. install.sh is written to use only shell builtins plus `uname`/`id`, so it
runs cleanly under this minimal PATH. The plan it prints (RUN/MANUAL/SKIP/ERROR
lines) is the contract these tests assert on.
"""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "install.sh"
REAL_SH = shutil.which("sh")


def _make_stub(bindir: Path, name: str, body: str = "exit 0") -> None:
    path = bindir / name
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(0o755)


@dataclass
class Result:
    returncode: int
    stdout: str
    stderr: str

    @property
    def lines(self) -> list[str]:
        return [ln for ln in self.stdout.splitlines() if ln.strip()]

    def of_kind(self, kind: str) -> list[str]:
        """Plan payloads of a given kind, e.g. of_kind('RUN')."""
        prefix = kind + " "
        return [ln[len(prefix):] for ln in self.lines if ln.startswith(prefix)]


@pytest.fixture
def run_install(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    def _run(
        *,
        os_name: str = "Darwin",
        uid: int = 501,
        present=(),
        dry_run: bool = True,
        stub_bodies=None,
    ) -> Result:
        bodies = stub_bodies or {}
        _make_stub(bindir, "uname", f"echo {os_name}")
        _make_stub(bindir, "id", f"echo {uid}")
        for binary in present:
            _make_stub(bindir, binary, bodies.get(binary, "exit 0"))
        env = {"PATH": str(bindir), "HOME": str(home)}
        args = [REAL_SH, str(SCRIPT)]
        if dry_run:
            args.append("--dry-run")
        proc = subprocess.run(args, env=env, capture_output=True, text=True)
        return Result(proc.returncode, proc.stdout, proc.stderr)

    return _run
