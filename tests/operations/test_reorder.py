import pikepdf

from pdf_tool.operations import reorder as reorder_op


def test_reorder_operation_writes_reordered_output(monkeypatch, tmp_path):
    src = tmp_path / "src.pdf"
    doc = pikepdf.new()
    for w in (100, 200, 300):
        doc.add_blank_page(page_size=(w, 100))
    doc.save(src)
    out = tmp_path / "src-reordered.pdf"

    monkeypatch.setattr(reorder_op, "prompt_input_file", lambda *a, **k: src)
    monkeypatch.setattr(reorder_op, "reorder_items", lambda items, **k: [3, 2, 1])
    monkeypatch.setattr(reorder_op, "prompt_output_path", lambda *a, **k: out)

    reorder_op.run()

    with pikepdf.open(out) as pdf:
        widths = [float(p.mediabox[2]) - float(p.mediabox[0]) for p in pdf.pages]
    assert widths == [300, 200, 100]
