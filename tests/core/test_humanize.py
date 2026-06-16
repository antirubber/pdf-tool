from pdf_tool.core.humanize import humanize_bytes


def test_humanize_bytes_scales_units():
    assert humanize_bytes(500) == "500.0 B"
    assert humanize_bytes(1536) == "1.5 KB"
    assert humanize_bytes(5 * 1024 * 1024) == "5.0 MB"
