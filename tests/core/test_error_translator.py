from pdf_tool.core.error_translator import (
    PikepdfFailure,
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
