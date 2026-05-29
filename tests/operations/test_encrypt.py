import pytest

from pdf_tool.backends.pikepdf_backend import EncryptOptions
from pdf_tool.operations.encrypt import collect_encrypt_options


def test_same_password_uses_one_prompt_for_both(monkeypatch):
    asked_labels: list[str] = []

    def ask_password(label: str) -> str | None:
        asked_labels.append(label)
        return "shared-pw"

    options = collect_encrypt_options(
        ask_same=lambda: True, ask_password=ask_password
    )

    assert options == EncryptOptions(password="shared-pw")
    assert len(asked_labels) == 1  # prompted only once


def test_different_passwords_prompts_for_both():
    answers = iter(["the-user-pw", "the-owner-pw"])

    options = collect_encrypt_options(
        ask_same=lambda: False,
        ask_password=lambda label: next(answers),
    )

    assert options == EncryptOptions(
        password="the-user-pw", owner_password="the-owner-pw"
    )


def test_cancelling_same_question_aborts():
    options = collect_encrypt_options(
        ask_same=lambda: None,
        ask_password=lambda label: pytest.fail("should not prompt for a password"),
    )
    assert options is None


def test_cancelling_a_password_aborts():
    options = collect_encrypt_options(
        ask_same=lambda: True,
        ask_password=lambda label: None,
    )
    assert options is None
