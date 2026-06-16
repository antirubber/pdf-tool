import pikepdf

from pdf_tool.core.page_selection import All, CustomRange
from pdf_tool.operations import remove as remove_op


def _no(*a, **k):
    raise AssertionError("should not be reached")


def test_remove_operation_refuses_to_remove_every_page(
    monkeypatch, capsys, sample_pdf
):
    monkeypatch.setattr(remove_op, "prompt_input_file", lambda *a, **k: sample_pdf)
    monkeypatch.setattr(remove_op, "prompt_page_selection", lambda n: All())
    monkeypatch.setattr(remove_op, "prompt_output_path", _no)

    remove_op.run()

    assert "every page" in capsys.readouterr().out.lower()


def test_remove_operation_writes_trimmed_output(monkeypatch, tmp_path, make_pdf):
    src = make_pdf("doc.pdf", n_pages=4)
    out = tmp_path / "doc-trimmed.pdf"
    monkeypatch.setattr(remove_op, "prompt_input_file", lambda *a, **k: src)
    monkeypatch.setattr(remove_op, "prompt_page_selection", lambda n: CustomRange("2"))
    monkeypatch.setattr(remove_op, "prompt_output_path", lambda *a, **k: out)

    remove_op.run()

    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3
