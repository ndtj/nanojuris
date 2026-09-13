from __future__ import annotations

import pytest

from nanojuris.access import AccessAttempt, AccessOutcome, AccessPath, classify_access


def _path() -> AccessPath:
    return AccessPath(
        provider="fixture",
        url="https://juris.example.test/search",
        allowed_hosts=("juris.example.test",),
    )


def test_passive_marker_is_not_a_block() -> None:
    attempt = classify_access(
        path=_path(),
        status_code=200,
        headers={"Content-Type": "application/json"},
        body_marker="results include a captcha component",
    )
    assert attempt.outcome is AccessOutcome.PASSIVE_MARKER
    assert not attempt.blocked
    assert attempt.passive_marker


def test_enforced_challenge_is_explicit() -> None:
    attempt = classify_access(
        path=_path(),
        status_code=200,
        headers={"Content-Type": "text/html"},
        body_marker="verify you are human: challenge required",
    )
    assert attempt.outcome is AccessOutcome.CHALLENGE_ENFORCED
    assert attempt.blocked
    assert attempt.challenge_required


@pytest.mark.parametrize(
    ("status", "outcome"),
    [(403, AccessOutcome.ACCESS_BLOCKED), (429, AccessOutcome.RATE_LIMITED)],
)
def test_access_errors_are_not_empty(status: int, outcome: AccessOutcome) -> None:
    attempt = classify_access(path=_path(), status_code=status)
    assert attempt.outcome is outcome
    assert attempt.outcome is not AccessOutcome.AUTHORITATIVE_EMPTY


@pytest.mark.parametrize(
    "outcome",
    [AccessOutcome.TLS_ERROR, AccessOutcome.SCHEMA_INVALID],
)
def test_tls_and_schema_states_are_explicit(outcome: AccessOutcome) -> None:
    attempt = AccessAttempt(path=_path(), outcome=outcome, error_type=outcome.value)
    assert attempt.blocked
    assert attempt.outcome is not AccessOutcome.AUTHORITATIVE_EMPTY


def test_path_rejects_non_allowlisted_redirect() -> None:
    path = _path()
    with pytest.raises(ValueError):
        classify_access(path=path, status_code=200, final_url="https://other.test/result")


def test_evidence_is_redacted_to_safe_fields() -> None:
    evidence = classify_access(
        path=_path(),
        status_code=200,
        final_url="https://juris.example.test/result?token=secret",
        response_bytes=12,
    ).to_dict()
    assert "token" not in str(evidence)
    assert "secret" not in str(evidence)
