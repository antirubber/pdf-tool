import pikepdf
import pytest

from pdf_tool.backends.pikepdf_backend import (
    DecryptOptions,
    EncryptOptions,
    PageNumberOptions,
    PdfInfo,
    PikepdfBackend,
    WatermarkOptions,
    _page_stamp_geometry,
    format_page_label,
)
from pdf_tool.core.error_translator import BackendError, PikepdfFailure


def test_encrypt_produces_password_protected_pdf(sample_pdf, tmp_path):
    out = tmp_path / "encrypted.pdf"
    result = PikepdfBackend().encrypt(
        sample_pdf, out, EncryptOptions(password="secret")
    )

    assert result == out
    assert out.exists()
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(out)
    with pikepdf.open(out, password="secret") as pdf:
        assert len(pdf.pages) == 3


def test_encrypt_with_distinct_owner_and_user_passwords(sample_pdf, tmp_path):
    out = tmp_path / "encrypted.pdf"
    PikepdfBackend().encrypt(
        sample_pdf,
        out,
        EncryptOptions(password="user-pw", owner_password="owner-pw"),
    )

    # Both the user and owner passwords open the document...
    with pikepdf.open(out, password="user-pw") as pdf:
        assert len(pdf.pages) == 3
    with pikepdf.open(out, password="owner-pw") as pdf:
        assert len(pdf.pages) == 3
    # ...but an unrelated password does not.
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(out, password="wrong")


def test_decrypt_removes_password(sample_pdf, tmp_path):
    backend = PikepdfBackend()
    encrypted = backend.encrypt(
        sample_pdf, tmp_path / "enc.pdf", EncryptOptions(password="secret")
    )
    decrypted = tmp_path / "dec.pdf"

    result = backend.decrypt(encrypted, decrypted, DecryptOptions(password="secret"))

    assert result == decrypted
    with pikepdf.open(decrypted) as pdf:
        assert len(pdf.pages) == 3


def test_decrypt_with_wrong_password_raises_backend_error(sample_pdf, tmp_path):
    backend = PikepdfBackend()
    encrypted = backend.encrypt(
        sample_pdf, tmp_path / "enc.pdf", EncryptOptions(password="secret")
    )

    with pytest.raises(BackendError) as exc_info:
        backend.decrypt(
            encrypted, tmp_path / "dec.pdf", DecryptOptions(password="wrong")
        )

    failure = exc_info.value.failure
    assert isinstance(failure, PikepdfFailure)
    assert failure.exception_name == "PasswordError"


def test_inspect_reports_page_count_and_unencrypted(sample_pdf):
    info = PikepdfBackend().inspect(sample_pdf)
    assert isinstance(info, PdfInfo)
    assert info.n_pages == 3
    assert info.encrypted is False


def test_inspect_encrypted_pdf_reports_encrypted_without_failing(sample_pdf, tmp_path):
    backend = PikepdfBackend()
    encrypted = backend.encrypt(
        sample_pdf, tmp_path / "enc.pdf", EncryptOptions(password="s3cret")
    )
    info = backend.inspect(encrypted)
    assert info.encrypted is True
    assert info.n_pages is None  # cannot read page count without password


def test_rotate_applies_to_selected_pages(sample_pdf, tmp_path):
    out = tmp_path / "rot.pdf"
    PikepdfBackend().rotate(sample_pdf, out, pages=[1, 3], degrees=90)
    with pikepdf.open(out) as pdf:
        assert int(pdf.pages[0].obj.get("/Rotate", 0)) == 90
        assert int(pdf.pages[1].obj.get("/Rotate", 0)) == 0
        assert int(pdf.pages[2].obj.get("/Rotate", 0)) == 90


def test_rotate_twice_180_is_noop(sample_pdf, tmp_path):
    backend = PikepdfBackend()
    once = backend.rotate(sample_pdf, tmp_path / "1.pdf", pages=[1, 2, 3], degrees=180)
    twice = backend.rotate(once, tmp_path / "2.pdf", pages=[1, 2, 3], degrees=180)
    with pikepdf.open(twice) as pdf:
        for page in pdf.pages:
            assert int(page.obj.get("/Rotate", 0)) % 360 == 0


def test_split_every_page(make_pdf, tmp_path):
    src = make_pdf("src.pdf", n_pages=3)
    out_dir = tmp_path / "out"
    paths = PikepdfBackend().split_every_page(src, out_dir)
    assert len(paths) == 3
    for p in paths:
        with pikepdf.open(p) as pdf:
            assert len(pdf.pages) == 1


def test_split_every_n(make_pdf, tmp_path):
    src = make_pdf("src.pdf", n_pages=5)
    paths = PikepdfBackend().split_every_n(src, tmp_path / "out", n=2)
    assert len(paths) == 3  # 2+2+1
    page_counts = []
    for p in paths:
        with pikepdf.open(p) as pdf:
            page_counts.append(len(pdf.pages))
    assert page_counts == [2, 2, 1]


def test_split_at_boundaries(make_pdf, tmp_path):
    src = make_pdf("src.pdf", n_pages=10)
    paths = PikepdfBackend().split_at_boundaries(
        src, tmp_path / "out", boundaries=[4, 7]
    )
    # boundaries [4, 7] on 10 pages → 1-3 (3), 4-6 (3), 7-10 (4)
    assert len(paths) == 3
    counts = []
    for p in paths:
        with pikepdf.open(p) as pdf:
            counts.append(len(pdf.pages))
    assert counts == [3, 3, 4]


def test_extract_pages_into_one(make_pdf, tmp_path):
    src = make_pdf("src.pdf", n_pages=10)
    out = tmp_path / "extracted.pdf"
    result = PikepdfBackend().extract_pages(src, out, pages=[2, 5, 7])
    assert result == out
    with pikepdf.open(result) as pdf:
        assert len(pdf.pages) == 3


def test_reorder_pages_writes_pages_in_the_given_order(tmp_path):
    src = pikepdf.new()
    for w in (100, 200, 300):
        src.add_blank_page(page_size=(w, 100))
    src.save(tmp_path / "src.pdf")
    out = PikepdfBackend().reorder_pages(
        tmp_path / "src.pdf", tmp_path / "out.pdf", order=[3, 1, 2]
    )
    with pikepdf.open(out) as pdf:
        widths = [float(p.mediabox[2]) - float(p.mediabox[0]) for p in pdf.pages]
    assert widths == [300, 100, 200]


def test_remove_pages_keeps_the_unselected_pages(make_pdf, tmp_path):
    src = make_pdf("src.pdf", n_pages=5)
    out = PikepdfBackend().remove_pages(src, tmp_path / "trim.pdf", pages=[2, 4])
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3  # 1, 3, 5 kept


def test_remove_all_pages_raises_and_writes_nothing(make_pdf, tmp_path):
    src = make_pdf("src.pdf", n_pages=3)
    out = tmp_path / "x.pdf"
    with pytest.raises(BackendError):
        PikepdfBackend().remove_pages(src, out, pages=[1, 2, 3])
    assert not out.exists()


def test_merge_concatenates_page_counts(make_pdf, tmp_path):
    a = make_pdf("a.pdf", n_pages=2)
    b = make_pdf("b.pdf", n_pages=5)
    c = make_pdf("c.pdf", n_pages=1)
    out = tmp_path / "merged.pdf"
    result = PikepdfBackend().merge([a, b, c], out)
    assert result == out
    with pikepdf.open(result) as pdf:
        assert len(pdf.pages) == 2 + 5 + 1


def test_set_metadata_persists_title(sample_pdf, tmp_path):
    out = tmp_path / "tagged.pdf"
    PikepdfBackend().set_metadata(sample_pdf, out, fields={"Title": "My Report"})
    info = PikepdfBackend().inspect(out)
    assert info.metadata.get("Title") == "My Report"


def test_format_page_label_styles():
    assert format_page_label(3, total=10, style="plain") == "3"
    assert format_page_label(3, total=10, style="of_total") == "3 of 10"
    assert format_page_label(3, total=10, style="page_n") == "Page 3"


def test_format_page_label_bates_is_sequential_and_zero_padded():
    labels = [
        format_page_label(
            n, total=3, style="bates", bates_prefix="EX-", bates_width=4
        )
        for n in (1, 2, 3)
    ]
    assert labels == ["EX-0001", "EX-0002", "EX-0003"]


def test_add_page_numbers_stamps_only_target_pages(tmp_path):
    src = pikepdf.new()
    for _ in range(3):
        src.add_blank_page(page_size=(300, 400))
    src.save(tmp_path / "src.pdf")
    out = PikepdfBackend().add_page_numbers(
        tmp_path / "src.pdf", tmp_path / "out.pdf", PageNumberOptions(pages=[1, 3])
    )
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3
        assert "/XObject" in pdf.pages[0].Resources
        assert "/XObject" not in pdf.pages[1].Resources
        assert "/XObject" in pdf.pages[2].Resources


def test_stamp_geometry_uses_page_box_and_origin():
    (w, h), rect = _page_stamp_geometry([100, 200, 700, 1000])
    assert (w, h) == (600.0, 800.0)
    assert rect == (100.0, 200.0, 700.0, 1000.0)


def _page_content_bytes(page):
    c = page.obj.Contents
    if isinstance(c, pikepdf.Array):
        return b"\n".join(s.read_bytes() for s in c)
    return c.read_bytes()


def test_watermark_places_overlay_at_visible_origin_of_offset_page(tmp_path):
    src = pikepdf.new()
    pg = src.add_blank_page(page_size=(400, 400))
    pg.mediabox = [100, 100, 500, 500]
    src.save(tmp_path / "off.pdf")
    out = PikepdfBackend().watermark(
        tmp_path / "off.pdf",
        tmp_path / "wm.pdf",
        WatermarkOptions(text="DRAFT", pages=[1]),
    )
    with pikepdf.open(out) as pdf:
        data = _page_content_bytes(pdf.pages[0])
    # Overlay translated to the page's lower-left origin, not (0,0) off-page.
    assert b"100 100 cm" in data


def test_watermark_handles_mixed_page_sizes(tmp_path):
    src = pikepdf.new()
    src.add_blank_page(page_size=(200, 200))
    src.add_blank_page(page_size=(600, 800))
    src.save(tmp_path / "mixed.pdf")
    out = PikepdfBackend().watermark(
        tmp_path / "mixed.pdf",
        tmp_path / "wm.pdf",
        WatermarkOptions(text="DRAFT", pages=[1, 2]),
    )
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 2
        for page in pdf.pages:
            assert "/XObject" in page.Resources


def test_watermark_preserves_page_count(sample_pdf, tmp_path):
    out = tmp_path / "wm.pdf"
    result = PikepdfBackend().watermark(
        sample_pdf, out, WatermarkOptions(text="DRAFT", pages=[1, 2, 3])
    )
    assert result == out
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3


def test_strip_metadata_clears_existing_fields(sample_pdf, tmp_path):
    backend = PikepdfBackend()
    tagged = backend.set_metadata(
        sample_pdf, tmp_path / "tagged.pdf", fields={"Title": "Confidential"}
    )
    stripped = backend.strip_metadata(tagged, tmp_path / "stripped.pdf")
    info = backend.inspect(stripped)
    assert "Title" not in info.metadata


def test_set_metadata_clears_a_blanked_field_and_keeps_others(sample_pdf, tmp_path):
    backend = PikepdfBackend()
    tagged = backend.set_metadata(
        sample_pdf, tmp_path / "t.pdf", fields={"Title": "Secret", "Author": "Me"}
    )
    cleared = backend.set_metadata(tagged, tmp_path / "c.pdf", fields={"Title": ""})
    info = backend.inspect(cleared)
    assert "Title" not in info.metadata
    assert info.metadata.get("Author") == "Me"


def test_strip_removes_xmp_packet_and_original_document_id(tmp_path):
    src = tmp_path / "src.pdf"
    p = pikepdf.new()
    p.add_blank_page(page_size=(72, 72))
    with p.open_metadata() as m:
        m["dc:title"] = "Secret Title"
    p.save(src)
    with pikepdf.open(src) as pdf:
        original_id = bytes(pdf.trailer["/ID"][0])
        assert "/Metadata" in pdf.Root

    out = PikepdfBackend().strip_metadata(src, tmp_path / "out.pdf")
    with pikepdf.open(out) as pdf:
        assert "/Metadata" not in pdf.Root
        assert bytes(pdf.trailer["/ID"][0]) != original_id


def test_try_repair_preserves_page_count(sample_pdf, tmp_path):
    out = tmp_path / "repaired.pdf"
    result = PikepdfBackend().try_repair(sample_pdf, out)
    assert result == out
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3


def test_try_repair_handles_trailing_garbage(sample_pdf, tmp_path):
    # Append junk after %%EOF — pikepdf should still open via recovery.
    damaged = tmp_path / "damaged.pdf"
    damaged.write_bytes(sample_pdf.read_bytes() + b"\n\n--garbage--\n")
    out = tmp_path / "repaired.pdf"
    PikepdfBackend().try_repair(damaged, out)
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 3


def _pdf_with_version(path, version, n_pages=1):
    pdf = pikepdf.new()
    for _ in range(n_pages):
        pdf.add_blank_page(page_size=(72, 72))
    pdf.save(path, min_version=version)
    return path


def test_merge_carries_forward_highest_source_version(tmp_path):
    a = _pdf_with_version(tmp_path / "a.pdf", "1.4")
    b = _pdf_with_version(tmp_path / "b.pdf", "1.7")
    out = tmp_path / "merged.pdf"
    PikepdfBackend().merge([a, b], out)
    with pikepdf.open(out) as pdf:
        assert pdf.pdf_version >= "1.7"


def test_split_carries_forward_source_version(tmp_path):
    src = _pdf_with_version(tmp_path / "src.pdf", "1.7", n_pages=2)
    paths = PikepdfBackend().split_every_page(src, tmp_path / "out")
    with pikepdf.open(paths[0]) as pdf:
        assert pdf.pdf_version >= "1.7"


def test_extract_carries_forward_source_version(tmp_path):
    src = _pdf_with_version(tmp_path / "src.pdf", "1.7", n_pages=3)
    out = tmp_path / "ex.pdf"
    PikepdfBackend().extract_pages(src, out, pages=[1, 3])
    with pikepdf.open(out) as pdf:
        assert pdf.pdf_version >= "1.7"


def test_corrupt_pdf_is_translated_to_backend_error(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"this is not a pdf at all\n")
    with pytest.raises(BackendError) as exc_info:
        PikepdfBackend().try_repair(bad, tmp_path / "out.pdf")
    failure = exc_info.value.failure
    assert isinstance(failure, PikepdfFailure)
    assert failure.exception_name == "PdfError"
    # The original exception is chained so --debug can show the real traceback.
    assert exc_info.value.__cause__ is not None


def test_inspect_corrupt_pdf_is_translated_to_backend_error(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"this is not a pdf at all\n")
    with pytest.raises(BackendError):
        PikepdfBackend().inspect(bad)


def test_saving_over_the_input_is_translated_to_backend_error(sample_pdf):
    with pytest.raises(BackendError) as exc_info:
        PikepdfBackend().encrypt(sample_pdf, sample_pdf, EncryptOptions(password="x"))
    failure = exc_info.value.failure
    assert isinstance(failure, PikepdfFailure)
    assert failure.exception_name == "ValueError"
