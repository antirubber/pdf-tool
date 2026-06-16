import hashlib

from pdf_tool import updater


class _Completed:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def _sums(script: bytes, name: str = "install.sh") -> bytes:
    digest = hashlib.sha256(script).hexdigest()
    return f"{digest}  {name}\n".encode()


def test_verify_accepts_matching_digest():
    data = b"echo hello\n"
    assert updater._verify(data, hashlib.sha256(data).hexdigest())


def test_verify_rejects_tampered_payload():
    assert not updater._verify(b"evil", "0" * 64)


def test_expected_sha256_extracts_named_entry():
    sums = b"aaaa  other.txt\nbbbb  install.sh\n"
    assert updater._expected_sha256(sums, "install.sh") == "bbbb"
    assert updater._expected_sha256(sums, "missing") is None


def test_run_aborts_when_download_fails():
    assert updater.run(fetch=lambda url: None) == 1


def test_run_aborts_on_integrity_mismatch(monkeypatch):
    script = b"echo hi\n"
    bad_sums = b"%s  install.sh\n" % (b"0" * 64)

    def fetch(url: str) -> bytes:
        return script if url.endswith("install.sh") else bad_sums

    def _explode(*a, **k):
        raise AssertionError("must not execute an unverified script")

    monkeypatch.setattr(updater.subprocess, "run", _explode)
    assert updater.run(fetch=fetch) == 1


def test_run_executes_verified_script(monkeypatch):
    script = b"echo verified\n"
    sums = _sums(script)

    def fetch(url: str) -> bytes:
        return script if url.endswith("install.sh") else sums

    captured = {}

    def fake_run(args, **kw):
        captured["args"] = args
        captured["input"] = kw.get("input")
        return _Completed(0)

    monkeypatch.setattr(updater.subprocess, "run", fake_run)
    assert updater.run(fetch=fetch) == 0
    assert captured["args"][:2] == ["sh", "-s"]
    assert captured["input"] == script


def test_run_returns_installer_exit_code(monkeypatch):
    script = b"exit 3\n"
    sums = _sums(script)

    def fetch(url: str) -> bytes:
        return script if url.endswith("install.sh") else sums

    monkeypatch.setattr(updater.subprocess, "run", lambda *a, **kw: _Completed(3))
    assert updater.run(fetch=fetch) == 3
