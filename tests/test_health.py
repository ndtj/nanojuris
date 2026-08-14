from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from nanojuris.cli import main
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.health import (
    ProviderHealthStatus,
    check_provider,
    check_sources,
)
from nanojuris.models import JurisprudenceQuery, JurisprudenceResult, SearchPage


class FakeProvider:
    def __init__(self, name: str, *, results: list[JurisprudenceResult] | None = None):
        self.name = name
        self.results = results or []
        self.error: Exception | None = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        assert query.page == 1
        assert query.page_size == 1
        if self.error:
            raise self.error
        return SearchPage(
            source=self.name,
            total=len(self.results),
            start=1 if self.results else 0,
            end=len(self.results),
            page=query.page,
            page_size=query.page_size,
            results=self.results,
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


def result(source: str) -> JurisprudenceResult:
    return JurisprudenceResult(
        id=f"{source}-1",
        source=source,
        court="TJDFT",
        type="acordao",
        summary="Responsabilidade civil",
    )


def test_check_provider_distinguishes_results_and_empty_success():
    healthy = check_provider(FakeProvider("healthy", results=[result("healthy")]))
    empty = check_provider(FakeProvider("empty"))

    assert healthy.status == ProviderHealthStatus.HEALTHY
    assert healthy.operational is True
    assert healthy.returned == 1
    assert empty.status == ProviderHealthStatus.EMPTY
    assert empty.operational is True


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (AccessControlRequiredError("blocked"), ProviderHealthStatus.BLOCKED),
        (RateLimitDetectedError("limited"), ProviderHealthStatus.RATE_LIMITED),
        (ParserContractChangedError("changed"), ProviderHealthStatus.SOURCE_CHANGED),
        (SourceUnavailableError("offline"), ProviderHealthStatus.SOURCE_UNAVAILABLE),
    ],
)
def test_check_provider_preserves_operational_failure_category(error, status):
    provider = FakeProvider("failing")
    provider.error = error

    report = check_provider(provider)

    assert report.status == status
    assert report.operational is False
    assert report.error_type == type(error).__name__


def test_check_sources_keeps_order_and_summary_for_selected_sources():
    client = FakeClient(
        {
            "empty": FakeProvider("empty"),
            "healthy": FakeProvider("healthy", results=[result("healthy")]),
        }
    )

    payload = check_sources(client, sources=["healthy", "empty"], text="icms")

    assert payload["checked_sources"] == ["healthy", "empty"]
    assert [item["source"] for item in payload["reports"]] == ["healthy", "empty"]
    assert payload["summary"] == {"empty": 1, "healthy": 1}
    assert payload["complete"] is True


def test_cli_health_passes_sources_and_probe_text(monkeypatch, capsys):
    calls: list[dict[str, object]] = []

    monkeypatch.setattr("nanojuris.cli.NanoJurisClient", lambda: object())

    def fake_check_sources(client, *, sources, text, timeout):
        calls.append({"client": client, "sources": sources, "text": text, "timeout": timeout})
        return {"summary": {"healthy": 1}}

    monkeypatch.setattr("nanojuris.cli.check_sources", fake_check_sources)

    assert main(["saude", "--fontes", "tjdf_juris,tst_jurisprudencia", "--texto", "icms"]) == 0
    assert calls[0]["sources"] == ["tjdf_juris", "tst_jurisprudencia"]
    assert calls[0]["text"] == "icms"
    assert '"healthy": 1' in capsys.readouterr().out
