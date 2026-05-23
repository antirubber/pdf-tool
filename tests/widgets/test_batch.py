from pathlib import Path

import pytest

from pdf_tool.widgets.batch import collect_directory_files


@pytest.fixture
def doc_dir(tmp_path: Path) -> Path:
    """A directory with a mix of office, image, and unsupported files."""
    (tmp_path / "report.docx").write_bytes(b"")
    (tmp_path / "budget.xlsx").write_bytes(b"")
    (tmp_path / "photo.png").write_bytes(b"")
    (tmp_path / "notes.txt").write_bytes(b"")
    (tmp_path / "presentation.pptx").write_bytes(b"")
    return tmp_path


@pytest.fixture
def nested_dir(doc_dir: Path) -> Path:
    """doc_dir with a subdirectory containing additional files."""
    sub = doc_dir / "subdir"
    sub.mkdir()
    (sub / "memo.docx").write_bytes(b"")
    (sub / "scan.tiff").write_bytes(b"")
    (sub / "readme.md").write_bytes(b"")
    return doc_dir


class TestCollectDirectoryFilesFlat:
    def test_returns_only_files_matching_exts(self, doc_dir: Path):
        office_exts = {".docx", ".xlsx", ".pptx"}
        result = collect_directory_files(doc_dir, office_exts, recursive=False)
        names = sorted(p.name for p in result)
        assert names == ["budget.xlsx", "presentation.pptx", "report.docx"]

    def test_excludes_unmatched_extensions(self, doc_dir: Path):
        image_exts = {".png", ".jpg"}
        result = collect_directory_files(doc_dir, image_exts, recursive=False)
        assert [p.name for p in result] == ["photo.png"]

    def test_empty_directory(self, tmp_path: Path):
        result = collect_directory_files(tmp_path, {".docx"}, recursive=False)
        assert result == []

    def test_empty_extension_set(self, doc_dir: Path):
        result = collect_directory_files(doc_dir, set(), recursive=False)
        assert result == []


class TestCollectDirectoryFilesRecursive:
    def test_includes_subdirectory_files(self, nested_dir: Path):
        office_exts = {".docx", ".xlsx", ".pptx"}
        result = collect_directory_files(nested_dir, office_exts, recursive=True)
        names = sorted(p.name for p in result)
        assert "memo.docx" in names
        assert names.count("memo.docx") == 1

    def test_flat_skips_subdirectory(self, nested_dir: Path):
        office_exts = {".docx", ".xlsx", ".pptx"}
        result = collect_directory_files(nested_dir, office_exts, recursive=False)
        names = [p.name for p in result]
        assert "memo.docx" not in names

    def test_recursive_image_exts(self, nested_dir: Path):
        image_exts = {".png", ".tiff", ".jpg"}
        result = collect_directory_files(nested_dir, image_exts, recursive=True)
        names = sorted(p.name for p in result)
        assert names == ["photo.png", "scan.tiff"]
