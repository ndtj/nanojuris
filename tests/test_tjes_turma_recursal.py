from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjes_turma_recursal import (
    TJES_TURMA_RECURSAL_CORE,
    TjesTurmaRecursalProvider,
    build_tjes_turma_recursal_params,
    parse_tjes_turma_recursal_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, data: Any, *, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.url = "https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/search"
        self.headers = {"Content-Type": "application/json"}
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        if isinstance(self._data, BaseException):
            raise ValueError("not json")
        return self._data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


class RaisingSession:
    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        raise requests.RequestException("simulated network failure")


def fixture_data(name: str = "tjes_turma_recursal_success.json") -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def trace() -> SourceTrace:
    return SourceTrace(provider="tjes_turma_recursal", endpoint="GET /api/search")


def test_parser_maps_separate_turma_recursal_collection() -> None:
    page = parse_tjes_turma_recursal_response(
        fixture_data(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=trace(),
        page_size=2,
    )

    assert page.source == "tjes_turma_recursal"
    assert page.total == 2
    assert page.is_complete is True
    first = page.results[0]
    assert first.id == "tjes-turma-recursal-fixture-tjes-turma-0001"
    assert first.number == "0000001-00.2024.8.08.0001"
    assert first.case_class == "Recurso Inominado"
    assert first.judging_body == "1a TURMA RECURSAL DE FIXTURE"
    assert first.full_text == "ACORDAO DE FIXTURE SOBRE RESPONSABILIDADE CIVIL E DANO MORAL."
    assert first.judgment_date == "2024-03-10"
    assert first.degree == "specialized"
    assert first.instance == "turma_recursal"
    assert first.collection == "TURMA_RECURSAL"
    assert first.document_type == "acordao"
    assert first.extraction_status.value == "complete"

    provider = TjesTurmaRecursalProvider(NanoJurisConfig(rate_limit_interval=0))
    provider._inline_documents[first.id] = (first.full_text or "", trace())
    document = provider.get_document(first.id)
    assert document.text == first.full_text
    bundle = provider.get_decisions(first.id)
    assert bundle.texts[0]["content"] == first.full_text

    canonical = search_page_to_canonical(page)[0]
    assert canonical.collection == "TURMA_RECURSAL"
    assert canonical.degree == "specialized"


def test_parser_preserves_source_fields_and_rejects_shape_drift() -> None:
    payload = fixture_data()
    payload["docs"][0]["future_source_field"] = {"version": 1}
    result = parse_tjes_turma_recursal_response(
        payload, query=JurisprudenceQuery(text="teste"), trace=trace()
    ).results[0]
    assert result.raw["future_source_field"] == {"version": 1}

    with pytest.raises(ParserContractChangedError, match="missing docs"):
        parse_tjes_turma_recursal_response(
            fixture_data("tjes_turma_recursal_invalid.json"),
            query=JurisprudenceQuery(text="x"),
            trace=trace(),
        )
    with pytest.raises(ParserContractChangedError, match="non-object"):
        parse_tjes_turma_recursal_response(
            fixture_data("tjes_turma_recursal_schema_drift.json"),
            query=JurisprudenceQuery(text="x"),
            trace=trace(),
        )


def test_parser_rejects_wrong_core_and_handles_explicit_empty() -> None:
    with pytest.raises(ParserContractChangedError, match="unexpected core"):
        parse_tjes_turma_recursal_response(
            {**fixture_data(), "core_used": "pje2g"},
            query=JurisprudenceQuery(text="x"),
            trace=trace(),
        )
    page = parse_tjes_turma_recursal_response(
        fixture_data("tjes_turma_recursal_empty.json"),
        query=JurisprudenceQuery(text="sem resultados"),
        trace=trace(),
    )
    assert page.results == []
    assert page.total == 0
    assert page.is_complete is True


def test_query_provider_trace_registration_and_federation() -> None:
    params = build_tjes_turma_recursal_params(
        JurisprudenceQuery(text="dano moral", page=3, page_size=100), page_size=20
    )
    assert params == {
        "core": TJES_TURMA_RECURSAL_CORE,
        "q": "dano moral",
        "page": 3,
        "per_page": 20,
    }
    session = FakeSession([FakeResponse(fixture_data())])
    provider = TjesTurmaRecursalProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=2))
    assert session.calls[0]["kwargs"]["params"]["core"] == TJES_TURMA_RECURSAL_CORE
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    client = NanoJurisClient()
    assert "tjes_turma_recursal" in client.providers
    capabilities = client.providers["tjes_turma_recursal"].get_capabilities()
    assert capabilities.semantic_discriminator == (
        "collection=turma_recursal;core=turma_recursal_legado"
    )
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert "tjes_turma_recursal" in client._default_unified_sources()


def test_provider_rejects_empty_query_and_classifies_http_errors() -> None:
    provider = TjesTurmaRecursalProvider(
        NanoJurisConfig(rate_limit_interval=0), session=RaisingSession()
    )
    with pytest.raises(ValueError, match="requires text"):
        provider.search(JurisprudenceQuery())
    with pytest.raises(SourceUnavailableError):
        provider.search(JurisprudenceQuery(text="teste"))


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (429, RateLimitDetectedError),
        (400, QueryRejectedError),
        (422, QueryRejectedError),
        (500, SourceUnavailableError),
    ],
)
def test_provider_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjesTurmaRecursalProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status) for _ in range(3)]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))
