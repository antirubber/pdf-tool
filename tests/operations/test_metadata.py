from pdf_tool.operations.metadata import _resolve_field_edits


def test_blanked_field_is_marked_for_clearing():
    edits = _resolve_field_edits({"Title": "Secret"}, {"Title": ""})
    assert edits == {"Title": ""}


def test_unchanged_field_is_omitted():
    edits = _resolve_field_edits({"Title": "Keep"}, {"Title": "Keep"})
    assert edits == {}


def test_changed_field_is_set():
    edits = _resolve_field_edits({"Title": "Old"}, {"Title": "New"})
    assert edits == {"Title": "New"}


def test_new_field_on_blank_document_is_set():
    edits = _resolve_field_edits({}, {"Author": "Ada", "Title": ""})
    assert edits == {"Author": "Ada"}
