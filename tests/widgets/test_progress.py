from pdf_tool.widgets import progress


def test_spinner_is_a_noop_when_suppressed(monkeypatch):
    monkeypatch.setenv("PDF_TOOL_DEBUG", "1")
    assert progress._suppressed() is True
    ran = []
    with progress.spinner("Working"):
        ran.append(True)
    assert ran == [True]


def test_spinner_runs_body_when_not_suppressed(monkeypatch):
    monkeypatch.setattr(progress, "_suppressed", lambda: False)
    ran = []
    with progress.spinner("Working"):
        ran.append(True)
    assert ran == [True]
