import pikepdf

from pdf_tool.backends.pikepdf_backend import EncryptOptions, PikepdfBackend
from pdf_tool.core.page_selection import All
from pdf_tool.operations import rotate as rotate_op
from pdf_tool.widgets import unlock


class _Ans:
    def __init__(self, value):
        self._value = value

    def ask(self):
        return self._value


def test_rotate_operation_unlocks_and_rotates_encrypted_input(
    monkeypatch, sample_pdf, tmp_path
):
    enc = PikepdfBackend().encrypt(
        sample_pdf, tmp_path / "enc.pdf", EncryptOptions(password="pw")
    )
    out = tmp_path / "enc-rotated.pdf"

    monkeypatch.setattr(rotate_op, "prompt_input_file", lambda *a, **k: enc)
    monkeypatch.setattr(unlock.questionary, "password", lambda *a, **k: _Ans("pw"))
    monkeypatch.setattr(rotate_op, "prompt_page_selection", lambda n: All())
    monkeypatch.setattr(rotate_op.questionary, "select", lambda *a, **k: _Ans(90))
    monkeypatch.setattr(rotate_op, "prompt_output_path", lambda *a, **k: out)

    rotate_op.run()

    with pikepdf.open(out) as pdf:  # decrypted output opens without a password
        assert int(pdf.pages[0].obj.get("/Rotate", 0)) == 90
