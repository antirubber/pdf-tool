from pdf_tool.backends.pikepdf_backend import EncryptOptions, PikepdfBackend
from pdf_tool.widgets import unlock


class _Ans:
    def __init__(self, value):
        self._value = value

    def ask(self):
        return self._value


def _encrypted(sample_pdf, tmp_path):
    return PikepdfBackend().encrypt(
        sample_pdf, tmp_path / "enc.pdf", EncryptOptions(password="pw")
    )


def test_unlock_returns_pages_for_unencrypted(sample_pdf):
    assert unlock.prompt_unlock(PikepdfBackend(), sample_pdf) == (3, "")


def test_unlock_prompts_and_opens_encrypted(monkeypatch, sample_pdf, tmp_path):
    enc = _encrypted(sample_pdf, tmp_path)
    monkeypatch.setattr(unlock.questionary, "password", lambda *a, **k: _Ans("pw"))
    assert unlock.prompt_unlock(PikepdfBackend(), enc) == (3, "pw")


def test_unlock_wrong_password_returns_none(monkeypatch, sample_pdf, tmp_path):
    enc = _encrypted(sample_pdf, tmp_path)
    monkeypatch.setattr(unlock.questionary, "password", lambda *a, **k: _Ans("nope"))
    assert unlock.prompt_unlock(PikepdfBackend(), enc) is None


def test_unlock_cancel_returns_none(monkeypatch, sample_pdf, tmp_path):
    enc = _encrypted(sample_pdf, tmp_path)
    monkeypatch.setattr(unlock.questionary, "password", lambda *a, **k: _Ans(None))
    assert unlock.prompt_unlock(PikepdfBackend(), enc) is None
