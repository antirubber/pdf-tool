from pdf_tool.operations import decrypt as decrypt_op


def test_decrypt_reports_an_unencrypted_input(monkeypatch, capsys, sample_pdf):
    # An unencrypted input is detected before prompting for a password; the
    # password/output prompts must never be reached.
    monkeypatch.setattr(decrypt_op, "prompt_input_file", lambda *a, **k: sample_pdf)

    def _boom(*a, **k):
        raise AssertionError("should not prompt past the encryption check")

    monkeypatch.setattr(decrypt_op.questionary, "password", _boom)
    monkeypatch.setattr(decrypt_op, "prompt_output_path", _boom)

    decrypt_op._run_one()

    out = capsys.readouterr().out.lower()
    assert "not encrypted" in out


def test_decrypt_proceeds_for_a_genuinely_encrypted_input(
    monkeypatch, tmp_path, sample_pdf
):
    from pdf_tool.backends.pikepdf_backend import EncryptOptions, PikepdfBackend

    encrypted = PikepdfBackend().encrypt(
        sample_pdf, tmp_path / "enc.pdf", EncryptOptions(password="s3cret")
    )
    out_path = tmp_path / "unlocked.pdf"

    monkeypatch.setattr(decrypt_op, "prompt_input_file", lambda *a, **k: encrypted)
    monkeypatch.setattr(
        decrypt_op.questionary, "password", lambda *a, **k: _Answer("s3cret")
    )
    monkeypatch.setattr(decrypt_op, "prompt_output_path", lambda *a, **k: out_path)

    decrypt_op._run_one()

    import pikepdf

    with pikepdf.open(out_path) as pdf:  # opens without a password now
        assert len(pdf.pages) == 3


class _Answer:
    def __init__(self, value):
        self._value = value

    def ask(self):
        return self._value
