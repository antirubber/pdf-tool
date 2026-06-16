import pytest

from pdf_tool.backends.pikepdf_backend import EncryptOptions
from pdf_tool.operations.encrypt import (
    _validate_non_empty_password,
    collect_advanced_options,
    collect_encrypt_options,
)


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


def test_empty_same_password_is_refused():
    options = collect_encrypt_options(
        ask_same=lambda: True,
        ask_password=lambda label: "",
    )
    assert options is None  # never produce an unprotected file


def test_empty_user_password_is_refused():
    answers = iter(["", "owner-pw"])
    options = collect_encrypt_options(
        ask_same=lambda: False,
        ask_password=lambda label: next(answers),
    )
    assert options is None


def test_non_empty_password_validator_messages():
    assert _validate_non_empty_password("secret") is True
    msg = _validate_non_empty_password("   ")
    assert isinstance(msg, str) and "empty" in msg.lower()


def test_advanced_declined_keeps_base_defaults():
    base = EncryptOptions(password="x")
    out = collect_advanced_options(
        base,
        ask_advanced=lambda: False,
        ask_strength=lambda: None,
        ask_permissions=lambda: None,
    )
    assert out == base  # AES-256, all allowed


def test_advanced_applies_strength_and_permissions():
    base = EncryptOptions(password="x")
    out = collect_advanced_options(
        base,
        ask_advanced=lambda: True,
        ask_strength=lambda: 128,
        ask_permissions=lambda: ["print"],
    )
    assert out.strength == 128
    assert (out.allow_print, out.allow_copy, out.allow_modify, out.allow_annotate) == (
        True,
        False,
        False,
        False,
    )


def test_advanced_cancel_aborts():
    base = EncryptOptions(password="x")
    assert (
        collect_advanced_options(
            base,
            ask_advanced=lambda: None,
            ask_strength=lambda: None,
            ask_permissions=lambda: None,
        )
        is None
    )
