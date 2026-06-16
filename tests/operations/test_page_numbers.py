import pikepdf

from pdf_tool.operations import page_numbers as pn_op


class _Ans:
    def __init__(self, value):
        self._value = value

    def ask(self):
        return self._value


def test_default_run_numbers_every_page(monkeypatch, tmp_path):
    src = tmp_path / "src.pdf"
    doc = pikepdf.new()
    for _ in range(3):
        doc.add_blank_page(page_size=(300, 400))
    doc.save(src)
    out = tmp_path / "src-numbered.pdf"

    monkeypatch.setattr(pn_op, "prompt_input_file", lambda *a, **k: src)
    # Advanced? -> No, so Essentials defaults apply.
    monkeypatch.setattr(pn_op.questionary, "confirm", lambda *a, **k: _Ans(False))
    monkeypatch.setattr(pn_op, "prompt_output_path", lambda *a, **k: out)

    pn_op.run()

    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3
        assert all("/XObject" in p.Resources for p in pdf.pages)
