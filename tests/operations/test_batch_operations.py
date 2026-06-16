import pikepdf

from pdf_tool.backends.pikepdf_backend import EncryptOptions, PikepdfBackend
from pdf_tool.core.page_selection import All
from pdf_tool.operations import decrypt as decrypt_op
from pdf_tool.operations import rotate as rotate_op
from pdf_tool.widgets.batch import run_per_file


def test_batch_rotate_applies_one_angle_to_all_files(make_pdf, tmp_path):
    a = make_pdf("a.pdf", n_pages=2)
    b = make_pdf("b.pdf", n_pages=3)

    process = rotate_op._make_process((All(), 90))
    outcomes = run_per_file("rotate", [a, b], process)

    assert [o.succeeded for o in outcomes] == [True, True]
    with pikepdf.open(tmp_path / "a-rotated.pdf") as pdf:
        assert int(pdf.pages[0].obj.get("/Rotate", 0)) == 90
    with pikepdf.open(tmp_path / "b-rotated.pdf") as pdf:
        assert int(pdf.pages[2].obj.get("/Rotate", 0)) == 90


def test_batch_decrypt_unlocks_all_files_with_one_password(make_pdf, tmp_path):
    backend = PikepdfBackend()
    a = backend.encrypt(
        make_pdf("a.pdf"), tmp_path / "a-enc.pdf", EncryptOptions(password="pw")
    )
    b = backend.encrypt(
        make_pdf("b.pdf"), tmp_path / "b-enc.pdf", EncryptOptions(password="pw")
    )

    process = decrypt_op._make_process("pw")
    outcomes = run_per_file("decrypt", [a, b], process)

    assert all(o.succeeded for o in outcomes)
    with pikepdf.open(tmp_path / "a-enc-decrypted.pdf") as pdf:  # opens, no password
        assert len(pdf.pages) == 3


def test_batch_decrypt_one_bad_password_yields_a_fail_row(make_pdf, tmp_path):
    backend = PikepdfBackend()
    good = backend.encrypt(
        make_pdf("good.pdf"), tmp_path / "good-enc.pdf", EncryptOptions(password="pw")
    )
    other = backend.encrypt(
        make_pdf("other.pdf"),
        tmp_path / "other-enc.pdf",
        EncryptOptions(password="different"),
    )

    process = decrypt_op._make_process("pw")
    outcomes = run_per_file("decrypt", [good, other], process)

    assert outcomes[0].succeeded is True
    assert outcomes[1].succeeded is False  # wrong password → FAIL, run completes
