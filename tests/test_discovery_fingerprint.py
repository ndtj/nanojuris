from __future__ import annotations

from nanojuris.discovery import evidence_fingerprint
from nanojuris.discovery.models import (
    DiscoveryEvidence,
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryStatus,
)


def _evidence(token: str) -> DiscoveryEvidence:
    return DiscoveryEvidence(
        run_id="run",
        captured_at="2026-09-06T00:00:00Z",
        seed_url="https://example.test",
        request=DiscoveryRequest(
            method="POST",
            url="https://example.test/search",
            body={"token": token, "q": "direito"},
        ),
        response=DiscoveryResponse(
            status_code=200,
            url="https://example.test/search",
            body=b"same-body",
        ),
        status=DiscoveryStatus.VALID,
    )


def test_fingerprint_redacts_secret_values_and_is_stable() -> None:
    first = evidence_fingerprint(_evidence("secret-a"))
    second = evidence_fingerprint(_evidence("secret-b"))
    assert first == second
    assert len(first) == 64
