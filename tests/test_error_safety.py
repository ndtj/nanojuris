from __future__ import annotations

from nanojuris.errors import safe_error_message


def test_safe_error_message_redacts_credentials_urls_and_email_addresses() -> None:
    message = (
        "request failed for https://user:password@example.test/search?access_token=secret "
        "Authorization=Bearer abc.def.ghi contact admin@example.test "
        '{"password":"json-secret","message":"legal response body"}'
    )

    safe = safe_error_message(message)

    assert len(safe) <= 500
    assert "password@example" not in safe
    assert "secret" not in safe
    assert "abc.def.ghi" not in safe
    assert "json-secret" not in safe
    assert "admin@example.test" not in safe
    assert "https://example.test/search" in safe
    assert "[REDACTED_EMAIL]" in safe


def test_safe_error_message_is_bounded_and_keeps_error_class_for_empty_messages() -> None:
    assert safe_error_message("x" * 10_000) == ("x" * 486) + "...[truncated]"
    assert safe_error_message(RuntimeError()) == "RuntimeError"
