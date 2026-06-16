from io import StringIO

from rich.console import Console

from pdf_tool.widgets import summary


def _capture(render) -> str:
    buf = StringIO()
    original = summary._console
    summary._console = Console(file=buf, force_terminal=False, width=200)
    try:
        render()
    finally:
        summary._console = original
    return buf.getvalue()


def test_show_page_count_echoes_count():
    assert "3 pages" in _capture(lambda: summary.show_page_count(3))
    assert "1 page" in _capture(lambda: summary.show_page_count(1))


def test_clipboard_tool_detected_by_injected_which():
    assert summary._clipboard_tool(which=lambda _: None) is None
    found = {"wl-copy": "/usr/bin/wl-copy"}
    assert summary._clipboard_tool(which=found.get) == ["wl-copy"]


def test_offer_post_run_is_a_noop_when_not_interactive(tmp_path):
    # In tests the console is not interactive, so it must not prompt or raise.
    summary.offer_post_run(tmp_path / "x.pdf")


def test_closing_panel_shows_path_size_and_pages(tmp_path):
    out = tmp_path / "result.pdf"
    out.write_bytes(b"%PDF-1.4\n" + b"x" * 2048)
    rendered = _capture(lambda: summary.closing_panel(out, n_pages=5))
    assert "result.pdf" in rendered
    assert "KB" in rendered
    assert "5 pages" in rendered
