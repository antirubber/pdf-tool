from pdf_tool.core.error_translator import (
    PikepdfFailure,
    SubprocessFailure,
    translate,
)


def test_password_error_on_decrypt_becomes_wrong_password():
    failure = PikepdfFailure(exception_name="PasswordError")
    friendly = translate("decrypt", failure)
    assert friendly.message == "Wrong password."


def test_unknown_pikepdf_failure_falls_back_to_generic():
    failure = PikepdfFailure(exception_name="SomethingUnanticipated")
    friendly = translate("encrypt", failure)
    assert "encrypt failed" in friendly.message
    assert "--debug" in friendly.message


def test_output_equals_input_translates_to_friendly():
    failure = PikepdfFailure(
        exception_name="ValueError",
        message=(
            "Cannot overwrite input file. Open the file with "
            "pikepdf.open(..., allow_overwriting_input=True) to allow "
            "overwriting the input file."
        ),
    )
    friendly = translate("encrypt", failure)
    assert "same" in friendly.message.lower()
    assert friendly.suggested_action is not None


def test_missing_binary_subprocess_failure_translates():
    failure = SubprocessFailure(
        binary="img2pdf",
        exit_code=-1,
        stderr="img2pdf not found — is it installed?",
    )
    friendly = translate("convert", failure)
    assert "img2pdf is not installed" in friendly.message
    assert friendly.suggested_action is not None
