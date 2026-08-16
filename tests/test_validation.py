from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from nanojuris.cli import main
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    UnsupportedQueryError,
)
from nanojuris.models import JurisprudenceQuery, JurisprudenceResult, SearchPage, SourceTrace
from nanojuris.validation import (
    ProviderValidationStatus,
    validate_provider,
    validate_sources,
)


class FakeProvider:
    def __init__(
        self,
        name: str,
        *,
        results: list[JurisprudenceResult] | None = None,
        returned_page_size: int | None = None,
    ):
        self.name = name
        self.results = results or []
        self.returned_page_size = returned_page_size
        self.error: Exception | None = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        assert query.page == 1
        assert query.page_size == 1
        if self.error:
            raise self.error
        trace = SourceTrace(
            provider=self.name, endpoint="fixture", source_url="https://example.test"
        )
        return SearchPage(
            source=self.name,
            total=len(self.results),
            start=1 if self.results else 0,
            end=len(self.results),
            page=query.page,
            page_size=self.returned_page_size or query.page_size,
            results=self.results,
            source_trace=trace,
            pagination_mode="page",
            is_complete=False if self.results else True,
            completeness_reason="fixture",
        )


@dataclass
class FakeConfig:
    unified_max_workers: int = 2
    unified_timeout: float = 1.0


@dataclass
class FakeClient:
    providers: dict[str, FakeProvider]
    config: FakeConfig = field(default_factory=FakeConfig)

    def _default_unified_sources(self) -> list[str]:
        return list(self.providers)


def result(source: str, *, trace: bool = True) -> JurisprudenceResult:
    return JurisprudenceResult(
        id=f"{source}-1",
        source=source,
        court="TJDFT",
        type="acordao",
        summary="Responsabilidade civil",
        source_trace=(SourceTrace(provider=source, endpoint="fixture") if trace else None),
    )


def test_validate_provider_checks_contract_and_content():
    report = validate_provider(FakeProvider("healthy", results=[result("healthy")]))

    assert report.status == ProviderValidationStatus.VALID
    assert report.passed is True
    assert report.failed_checks == []
    assert report.checks["result_content"] is True


def test_validate_provider_reports_empty_as_successful_validation():
    report = validate_provider(FakeProvider("empty"))

    assert report.status == ProviderValidationStatus.EMPTY
    assert report.passed is True


def test_validate_provider_detects_invalid_result_contract():
    report = validate_provider(FakeProvider("broken", results=[result("other", trace=False)]))

    assert report.status == ProviderValidationStatus.CONTRACT_INVALID
    assert "result_sources" in report.failed_checks
    assert "result_traces" in report.failed_checks


def test_validate_provider_contains_malformed_normalized_response():
    report = validate_provider(FakeProvider("malformed", results=[object()]))

    assert report.status == ProviderValidationStatus.CONTRACT_INVALID
    assert report.failed_checks == ["normalized_response"]


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (AccessControlRequiredError("blocked"), ProviderValidationStatus.BLOCKED),
        (ParserContractChangedError("changed"), ProviderValidationStatus.SOURCE_CHANGED),
        (QueryRejectedError("query rejected"), ProviderValidationStatus.QUERY_REJECTED),
        (UnsupportedQueryError("unsupported"), ProviderValidationStatus.UNSUPPORTED_QUERY),
    ],
)
def test_validate_provider_preserves_live_failure_category(error, status):
    provider = FakeProvider("failing")
    provider.error = error

    report = validate_provider(provider)

    assert report.status == status
    assert report.passed is False


def test_validate_provider_accepts_provider_page_size_larger_than_request():
    report = validate_provider(
        FakeProvider(
            "normalizes-page-size",
            results=[result("normalizes-page-size")],
            returned_page_size=20,
        )
    )

    assert report.status == ProviderValidationStatus.VALID
    assert report.checks["page_size"] is True


def test_validate_sources_preserves_order_and_summary():
    client = FakeClient(
        {
            "healthy": FakeProvider("healthy", results=[result("healthy")]),
            "empty": FakeProvider("empty"),
        }
    )

    payload = validate_sources(client, sources=["healthy", "empty"], text="icms")

    assert payload["checked_sources"] == ["healthy", "empty"]
    assert [item["source"] for item in payload["reports"]] == ["healthy", "empty"]
    assert payload["summary"] == {"empty": 1, "valid": 1}
    assert payload["passed"] is True


def test_cli_validation_returns_failure_for_contract_problem(monkeypatch, capsys):
    monkeypatch.setattr("nanojuris.cli.NanoJurisClient", lambda: object())
    monkeypatch.setattr(
        "nanojuris.cli.validate_sources",
        lambda *args, **kwargs: {"passed": False, "summary": {"blocked": 1}},
    )

    assert main(["validar", "--fontes", "stf_juris"]) == 1
    assert '"blocked": 1' in capsys.readouterr().out
