from pathlib import Path

import pytest

from pdf_tool.core.output_namer import derive_output, ensure_unique


def test_encrypt_suffix():
    assert derive_output(Path("/work/foo.pdf"), "encrypt") == Path(
        "/work/foo-encrypted.pdf"
    )


def test_decrypt_suffix():
    assert derive_output(Path("/work/foo.pdf"), "decrypt") == Path(
        "/work/foo-decrypted.pdf"
    )


@pytest.mark.parametrize(
    "operation,expected_stem",
    [
        ("rotate", "foo-rotated"),
        ("compress", "foo-compressed"),
        ("ocr", "foo-ocr"),
        ("watermark", "foo-watermarked"),
        ("repair", "foo-repaired"),
        ("merge", "foo-merged"),
    ],
)
def test_suffix_style_operations(operation, expected_stem):
    assert derive_output(Path("/work/foo.pdf"), operation) == Path(
        f"/work/{expected_stem}.pdf"
    )


def test_split_returns_pages_directory():
    assert derive_output(Path("/work/foo.pdf"), "split") == Path("/work/foo-pages")


@pytest.mark.parametrize(
    "input_name,target_format,expected_name",
    [
        ("foo.pdf", "docx", "foo.docx"),
        ("foo.pdf", "xlsx", "foo.xlsx"),
        ("foo.pdf", "pptx", "foo.pptx"),
        ("foo.pdf", "odt", "foo.odt"),
        ("foo.pdf", "txt", "foo.txt"),
        ("foo.docx", "pdf", "foo.pdf"),
        ("foo.xlsx", "pdf", "foo.pdf"),
        ("foo.png", "pdf", "foo.pdf"),
    ],
)
def test_convert_swaps_extension(input_name, target_format, expected_name):
    assert derive_output(
        Path(f"/work/{input_name}"), "convert", target_format=target_format
    ) == Path(f"/work/{expected_name}")


@pytest.mark.parametrize("target_format", ["png", "jpeg", "jpg", "tiff"])
def test_convert_pdf_to_image_returns_images_directory(target_format):
    assert derive_output(
        Path("/work/foo.pdf"), "convert", target_format=target_format
    ) == Path("/work/foo-images")


def test_inspect_has_no_output():
    with pytest.raises(ValueError):
        derive_output(Path("/work/foo.pdf"), "inspect")


def test_unknown_operation_rejected():
    with pytest.raises(ValueError):
        derive_output(Path("/work/foo.pdf"), "shred")


def test_convert_without_target_format_rejected():
    with pytest.raises(ValueError):
        derive_output(Path("/work/foo.pdf"), "convert")


def test_ensure_unique_returns_candidate_when_free():
    candidate = Path("/work/foo-encrypted.pdf")
    assert ensure_unique(candidate, exists=lambda _: False) == candidate


def test_ensure_unique_appends_two_on_first_collision():
    candidate = Path("/work/foo-encrypted.pdf")
    taken = {candidate}
    assert ensure_unique(candidate, exists=taken.__contains__) == Path(
        "/work/foo-encrypted-2.pdf"
    )


def test_ensure_unique_walks_past_multiple_collisions():
    candidate = Path("/work/foo-encrypted.pdf")
    taken = {
        candidate,
        Path("/work/foo-encrypted-2.pdf"),
        Path("/work/foo-encrypted-3.pdf"),
    }
    assert ensure_unique(candidate, exists=taken.__contains__) == Path(
        "/work/foo-encrypted-4.pdf"
    )


def test_ensure_unique_works_for_directory_paths():
    candidate = Path("/work/foo-pages")
    taken = {candidate}
    assert ensure_unique(candidate, exists=taken.__contains__) == Path(
        "/work/foo-pages-2"
    )


def test_ensure_unique_dotted_directory_appends_counter_to_full_name():
    candidate = Path("/work/report.v2-pages")
    taken = {candidate}
    assert ensure_unique(
        candidate, exists=taken.__contains__, as_directory=True
    ) == Path("/work/report.v2-pages-2")


def test_ensure_unique_dotted_file_keeps_stem_based_dedup():
    candidate = Path("/work/foo.bar.pdf")
    taken = {candidate}
    assert ensure_unique(candidate, exists=taken.__contains__) == Path(
        "/work/foo.bar-2.pdf"
    )
