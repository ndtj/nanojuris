from __future__ import annotations

from nanojuris.contracts import (
    SearchOutcomeStatus,
    search_outcome_from_error,
    search_outcome_from_page,
)
from nanojuris.models import JurisprudenceResult, SearchPage, SourceTrace


def _page(
    *,
    results: list[JurisprudenceResult],
    complete: bool | None,
    total_known: bool,
    access_reason: str | None = None,
) -> SearchPage:
    return SearchPage(
        source="fixture",
        total=len(results),
        start=0,
        end=len(results),
        page=1,
        page_size=10,
        results=results,
        is_complete=complete,
        total_known=total_known,
        access_reason=access_reason,
    )


def test_outcomes_distinguish_authoritative_and_unconfirmed_empty() -> None:
    authoritative = search_outcome_from_page(_page(results=[], complete=True, total_known=True))
    unknown = search_outcome_from_page(_page(results=[], complete=None, total_known=False))

    assert authoritative.status is SearchOutcomeStatus.AUTHORITATIVE_EMPTY
    assert authoritative.total_state == "zero"
    assert unknown.status is SearchOutcomeStatus.UNCONFIRMED_EMPTY
    assert unknown.total_state == "unknown"


def test_outcomes_preserve_partial_and_transport_states() -> None:
    result = JurisprudenceResult(
        id="one", source="fixture", court="TJ", type="decision", summary="texto"
    )
    page = _page(results=[result], complete=False, total_known=False)
    partial = search_outcome_from_page(page)
    page.source_trace = SourceTrace(
        provider="fixture", endpoint="https://example.test", retrieval_status="timeout"
    )
    timeout = search_outcome_from_page(page)

    assert partial.status is SearchOutcomeStatus.PARTIAL
    assert timeout.status is SearchOutcomeStatus.TIMEOUT


def test_error_mapping_never_returns_authoritative_empty() -> None:
    blocked = search_outcome_from_error("tj", "AccessControlRequiredError")
    schema = search_outcome_from_error("tj", "ParserContractChangedError")

    assert blocked.status is SearchOutcomeStatus.ACCESS_BLOCKED
    assert schema.status is SearchOutcomeStatus.SCHEMA_INVALID


def test_page_outcome_prefers_explicit_access_reason() -> None:
    page = _page(
        results=[],
        complete=False,
        total_known=False,
        access_reason="TRE-RR=source_unavailable",
    )
    page.completeness_reason = "A coleta foi parcial."

    outcome = search_outcome_from_page(page)

    assert outcome.status is SearchOutcomeStatus.UNCONFIRMED_EMPTY
    assert outcome.message == "TRE-RR=source_unavailable"
