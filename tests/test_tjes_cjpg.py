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
from nanojuris.providers.tjes_cjpg import (
    TJES_CJPG_CORE,
    TjesCjpgProvider,
    build_tjes_cjpg_params,
    parse_tjes_cjpg_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, data: Any, *, status_code: int = 200, url: str = "") -> None:
        self._data = data
        self.status_code = status_code
        self.url = url or "https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/search"
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


def fixture_data(name: str = "tjes_cjpg_success.json") -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_tjes_cjpg_parser_maps_first_degree_inline_text() -> None:
    trace = SourceTrace(
        provider="tjes_cjpg",
        endpoint="GET /api/search",
        http_status=200,
        content_sha256="fixture-sha256",
    )
    page = parse_tjes_cjpg_response(
        fixture_data(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=trace,
        page_size=2,
    )

    assert page.source == "tjes_cjpg"
    assert page.total == 3
    assert page.start == 1
    assert page.end == 2
    assert page.page_size == 2
    assert page.is_complete is False
    assert page.results[0].id == "tjes-cjpg-90000001"
    assert page.results[0].court == "TJES"
    assert page.results[0].type == "decisao_1g"
    assert page.results[0].number == "0000001-00.2024.8.08.0001"
    assert page.results[0].full_text == (
        "Sentenca publica de fixture sobre responsabilidade civil."
    )
    assert page.results[0].summary == page.results[0].full_text
    assert page.results[0].judgment_date == "2024-03-10"
    assert page.results[0].degree == "first"
    assert page.results[0].instance == "first"
    assert page.results[0].branch == "state"
    assert page.results[0].authority == "TJES"
    assert page.results[0].collection == "CJPG"
    assert page.results[0].document_type == "decisao_1g"
    assert page.results[0].extraction_status.value == "complete"
    assert page.results[0].raw["classe_judicial"] == "PROCEDIMENTO COMUM"
    assert page.results[0].raw["case_class"] == "PROCEDIMENTO COMUM"
    assert page.results[1].summary == "Ementa publica de fixture."
    assert page.results[1].judgment_date == "2024-03-10"


def test_search_caches_inline_result_for_decisions_and_document() -> None:
    provider = TjesCjpgProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(fixture_data())]),
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=1))
    result = page.results[0]
    bundle = provider.get_decisions(result.id)
    document = provider.get_document(result.id)

    assert bundle.texts and bundle.texts[0]["text"] == result.full_text
    assert document.text == result.full_text
    assert len(provider.session.calls) == 1


def test_decisions_reject_unobserved_id() -> None:
    provider = TjesCjpgProvider(NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]))

    with pytest.raises(ValueError, match="observed"):
        provider.get_decisions("not-observed")


def test_tjes_cjpg_preserves_unknown_source_fields() -> None:
    payload = fixture_data()
    payload["docs"][0]["future_source_field"] = {"version": 1}
    trace = SourceTrace(provider="tjes_cjpg", endpoint="GET /api/search")
    result = parse_tjes_cjpg_response(
        payload,
        query=JurisprudenceQuery(text="teste"),
        trace=trace,
    ).results[0]

    assert result.raw["future_source_field"] == {"version": 1}
    assert result.raw["inteiro_teor_html"].startswith("<p>")


def test_tjes_cjpg_rejects_wrong_collection_and_invalid_root() -> None:
    trace = SourceTrace(provider="tjes_cjpg", endpoint="GET /api/search")
    with pytest.raises(ParserContractChangedError, match="unexpected core"):
        parse_tjes_cjpg_response(
            {**fixture_data(), "core_used": "pje2g"},
            query=JurisprudenceQuery(text="teste"),
            trace=trace,
        )
    with pytest.raises(ParserContractChangedError, match="missing docs"):
        parse_tjes_cjpg_response(
            fixture_data("tjes_cjpg_invalid.json"),
            query=JurisprudenceQuery(text="teste"),
            trace=trace,
        )
    with pytest.raises(ParserContractChangedError, match="non-object"):
        parse_tjes_cjpg_response(
            {**fixture_data(), "docs": ["not-a-document"]},
            query=JurisprudenceQuery(text="teste"),
            trace=trace,
        )
    with pytest.raises(ParserContractChangedError, match="missing docs"):
        parse_tjes_cjpg_response(
            fixture_data("tjes_cjpg_schema_drift.json"),
            query=JurisprudenceQuery(text="teste"),
            trace=trace,
        )


def test_tjes_cjpg_empty_page_is_explicitly_complete() -> None:
    trace = SourceTrace(provider="tjes_cjpg", endpoint="GET /api/search")
    page = parse_tjes_cjpg_response(
        fixture_data("tjes_cjpg_empty.json"),
        query=JurisprudenceQuery(text="termo sem ocorrencias"),
        trace=trace,
    )
    assert page.results == []
    assert page.total == 0
    assert page.start == 0
    assert page.end == 0
    assert page.is_complete is True
    assert page.completeness_reason


def test_tjes_cjpg_builds_observed_query_contract() -> None:
    params = build_tjes_cjpg_params(
        JurisprudenceQuery(
            text="dano moral",
            exact_phrase="responsabilidade civil",
            rapporteur="MAGISTRADO",
            updated_from="2024-01-01",
            updated_to="31/01/2024",
            order_by="date_desc",
            page=3,
            page_size=100,
        ),
        page_size=20,
    )
    assert params == {
        "core": TJES_CJPG_CORE,
        "q": "dano moral",
        "page": 3,
        "per_page": 20,
        "exact_match": "true",
        "magistrado": "MAGISTRADO",
        "dataIni": "2024-01-01",
        "dataFim": "31/01/2024",
        "sort": "date_desc",
    }


def test_tjes_cjpg_provider_emits_http_trace_and_canonical_fields() -> None:
    session = FakeSession(
        [
            FakeResponse(
                fixture_data(),
                url=(
                    "https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/search"
                    "?core=pje1g&page=1&per_page=2"
                ),
            )
        ]
    )
    provider = TjesCjpgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=2))

    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["kwargs"]["params"]["core"] == "pje1g"
    assert session.calls[0]["kwargs"]["params"]["per_page"] == 2
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.response_bytes > 0
    assert page.source_trace.content_sha256
    assert page.source_trace.retrieval_status == "ok"
    canonical = search_page_to_canonical(page)[0]
    assert canonical.case_class == "PROCEDIMENTO COMUM"
    assert canonical.judging_body == "VARA DE FIXTURE"
    assert canonical.origin_county == "COMARCA DE FIXTURE"
    assert canonical.full_text == page.results[0].full_text


def test_tjes_cjpg_rejects_empty_query_and_transport_errors() -> None:
    provider = TjesCjpgProvider(NanoJurisConfig(rate_limit_interval=0), session=RaisingSession())
    with pytest.raises(ValueError, match="requires text"):
        provider.search(JurisprudenceQuery())
    with pytest.raises(SourceUnavailableError, match="request failed"):
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
def test_tjes_cjpg_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjesCjpgProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status)]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))


def test_tjes_cjpg_declares_first_degree_federated_contract() -> None:
    client = NanoJurisClient()
    assert "tjes_cjpg" in client.providers
    capabilities = client.providers["tjes_cjpg"].get_capabilities()
    assert capabilities.semantic_discriminator == "collection=first_degree;core=pje1g"
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert capabilities.supports_studio is True
    assert capabilities.supports_full_text is True
    assert capabilities.full_text_access == "inline"
    assert capabilities.max_remote_page_size == 20
    assert capabilities.filter_status("updated_from") == "translated"
    assert capabilities.filter_status("published_from") == "unsupported"


def test_promoted_source_is_default_and_remains_selectable_by_config() -> None:
    from nanojuris.client import NanoJurisClient

    provider = TjesCjpgProvider(NanoJurisConfig(rate_limit_interval=0))
    default = NanoJurisClient(providers=[provider])
    assert default._default_unified_sources() == ["tjes_cjpg"]

    opted_in = NanoJurisClient(
        config=NanoJurisConfig(
            rate_limit_interval=0,
            unified_opt_in_sources=("tjes_cjpg",),
        ),
        providers=[provider],
    )
    assert opted_in._default_unified_sources() == ["tjes_cjpg"]
