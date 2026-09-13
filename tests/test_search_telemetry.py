from __future__ import annotations

import pytest

from nanojuris import build_search_event, fingerprint_query


def test_query_fingerprint_is_stable_but_not_plaintext() -> None:
    first = fingerprint_query("responsabilidade civil", secret=b"test-secret")
    second = fingerprint_query("responsabilidade civil", secret=b"test-secret")
    assert first == second
    assert "responsabilidade" not in first


def test_search_event_is_allowlisted_and_redacted() -> None:
    event = build_search_event(
        query="responsabilidade civil",
        secret=b"test-secret",
        ranking_version="legal-live-v1",
        provider="tjdf_juris",
        position=1,
        canonical_id="decision-1",
        action="click",
        latency_ms=12.345,
        source_status="success_with_results",
    )
    assert event["raw_query"] is None
    assert event["latency_ms"] == 12.35
    assert set(event) == {
        "schema_version",
        "query_hmac_sha256",
        "ranking_version",
        "provider",
        "position",
        "canonical_id",
        "action",
        "latency_ms",
        "source_status",
        "raw_query",
    }


@pytest.mark.parametrize("kwargs", [{"position": 0}, {"latency_ms": -1}])
def test_search_event_rejects_invalid_measurements(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        build_search_event(
            query="x",
            secret=b"secret",
            ranking_version="legacy",
            provider="test",
            **kwargs,
        )
