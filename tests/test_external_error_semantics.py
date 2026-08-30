"""Regression gates for failures returned by external jurisprudence sources."""

from __future__ import annotations

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, ProviderCapabilities


class FailingExternalProvider:
    """Small deterministic provider used to test the federated error envelope."""

    name = "failing_external"

    def __init__(self, failure: Exception) -> None:
        self.failure = failure

    def search(self, query: JurisprudenceQuery):
        raise self.failure

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="Falha externa de teste",
            source_url="https://example.test/jurisprudencia",
            category="court_jurisprudence",
            search_modes=["text"],
            canonical_records=["CanonicalDecision"],
            supports_unified_search=True,
        )


@pytest.mark.parametrize(
    ("failure", "expected_type"),
    [
        (AccessControlRequiredError("captcha or login required"), "AccessControlRequiredError"),
        (SourceUnavailableError("upstream unavailable"), "SourceUnavailableError"),
        (QueryRejectedError("provider rejected the query"), "QueryRejectedError"),
        (ParserContractChangedError("response schema changed"), "ParserContractChangedError"),
        (requests.exceptions.SSLError("certificate verify failed"), "SslVerificationError"),
    ],
)
def test_external_failure_is_never_classified_as_empty(failure: Exception, expected_type: str):
    client = NanoJurisClient(providers=[FailingExternalProvider(failure)])

    payload = client.search_many("dano moral", sources=["failing_external"])

    assert payload["results"] == []
    assert payload["total_returned"] == 0
    assert payload["pagination_complete"] is False
    assert payload["collection_complete"] is False
    assert payload["errors"][0]["error_type"] == expected_type
    assert payload["source_completeness"]["failing_external"]["complete"] is False
    assert payload["source_completeness"]["failing_external"]["pagination_mode"] == "failed"
    outcome = payload["source_outcomes"][0]
    assert outcome["source"] == "failing_external"
    assert outcome["status"] == "failed"
    assert outcome["reason"] == expected_type
    # Some classified failures intentionally include remediation hints. The
    # important invariant is that the outcome remains failed and never empty.
    assert outcome["message"]
