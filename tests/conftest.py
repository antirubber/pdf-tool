from pathlib import Path

import pikepdf
import pytest


@pytest.fixture
def make_pdf(tmp_path: Path):
    def _make(name: str = "sample.pdf", n_pages: int = 3) -> Path:
        path = tmp_path / name
        pdf = pikepdf.new()
        for _ in range(n_pages):
            pdf.add_blank_page(page_size=(72, 72))
        pdf.save(path)
        return path

    return _make


@pytest.fixture
def sample_pdf(make_pdf) -> Path:
    return make_pdf()
