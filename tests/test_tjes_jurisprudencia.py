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
from nanojuris.providers.tjes_jurisprudencia import (
    TJES_CJSG_CORE,
    TjesJurisprudenciaProvider,
    build_tjes_cjsg_params,
    parse_tjes_cjsg_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, data: Any, *, status_code: int = 200, url: str = "") -> None:
        self._data = data
        self.status_code = status_code
        self.url = url or "https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/search"
        self.headers = {"Content-Type": "application/json"}
        self.content = (
            data
            if isinstance(data, bytes)
            else json.dumps(data, ensure_ascii=False).encode("utf-8")
        )
        self.text = self.content.decode("utf-8", errors="replace")

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


def fixture_data(name: str = "tjes_cjsg_success.json") -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def trace() -> SourceTrace:
    return SourceTrace(provider="tjes_jurisprudencia", endpoint="GET /api/search")


def test_parser_maps_second_degree_ementa_and_acordao() -> None:
    page = parse_tjes_cjsg_response(
        fixture_data(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=trace(),
        page_size=2,
    )

    assert page.source == "tjes_jurisprudencia"
    assert page.total == 3
    assert page.start == 1
    assert page.end == 2
    assert page.page_size == 2
    assert page.is_complete is False
    assert page.results[0].id == "tjes-cjsg-81000001"
    assert page.results[0].court == "TJES"
    assert page.results[0].type == "acordao"
    assert page.results[0].summary == "Ementa sanitizada de acórdão sobre responsabilidade civil."
    assert page.results[0].full_text == "Acórdão sanitizado com inteiro teor público."
    assert page.results[0].judgment_date == "2024-03-10"
    assert page.results[0].degree == "second"
    assert page.results[0].instance == "second"
    assert page.results[0].branch == "state"
    assert page.results[0].authority == "TJES"
    assert page.results[0].collection == "CJSG"
    assert page.results[0].document_type == "acordao"
    assert page.results[0].extraction_status.value == "complete"
    assert page.results[1].type == "decisao_monocratica"
    assert page.results[1].full_text is None
    assert page.results[1].extraction_status.value == "complete"


def test_search_caches_inline_result_for_decisions_and_document() -> None:
    provider = TjesJurisprudenciaProvider(
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
    provider = TjesJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    )

    with pytest.raises(ValueError, match="observed"):
        provider.get_decisions("not-observed")


def test_parser_uses_html_fallback_without_overwriting_raw_fields() -> None:
    page = parse_tjes_cjsg_response(
        fixture_data("tjes_cjsg_html_only.json"),
        query=JurisprudenceQuery(text="html"),
        trace=trace(),
    )

    result = page.results[0]
    assert result.summary == "EMENTA: Texto de ementa somente em HTML."
    assert result.full_text == "Acordao somente em HTML. Dispositivo preservado."
    assert result.raw["summary_source"] == "ementa_html"
    assert result.raw["full_text_source"] == "acordao_html"
    assert result.raw["ementa_html"].startswith("<p>")
    assert result.raw["acordao_html"].startswith("<div>")
    assert result.extraction_status.value == "complete"


def test_parser_preserves_unknown_fields_and_canonical_mapping() -> None:
    payload = fixture_data()
    payload["docs"][0]["future_source_field"] = {"version": 1}
    result = parse_tjes_cjsg_response(
        payload, query=JurisprudenceQuery(text="teste"), trace=trace()
    )
    first = result.results[0]
    assert first.raw["future_source_field"] == {"version": 1}
    canonical = search_page_to_canonical(result)[0]
    assert canonical.case_class == "APELAÇÃO CÍVEL"
    assert canonical.judging_body == "PRIMEIRA CAMARA DE FIXTURE"
    assert canonical.rapporteur == "RELATOR DE FIXTURE"
    assert canonical.full_text == first.full_text


def test_parser_rejects_wrong_core_shape_and_identity() -> None:
    with pytest.raises(ParserContractChangedError, match="unexpected core"):
        parse_tjes_cjsg_response(
            {**fixture_data(), "core_used": "pje1g"},
            query=JurisprudenceQuery(text="x"),
            trace=trace(),
        )
    with pytest.raises(ParserContractChangedError, match="missing docs"):
        parse_tjes_cjsg_response(
            fixture_data("tjes_cjsg_invalid.json"),
            query=JurisprudenceQuery(text="x"),
            trace=trace(),
        )
    with pytest.raises(ParserContractChangedError, match="non-object"):
        parse_tjes_cjsg_response(
            fixture_data("tjes_cjsg_schema_drift.json"),
            query=JurisprudenceQuery(text="x"),
            trace=trace(),
        )
    payload = fixture_data()
    payload["docs"][0].pop("id")
    payload["docs"][0].pop("id_bin")
    payload["docs"][0].pop("nr_processo")
    with pytest.raises(ParserContractChangedError, match="stable id"):
        parse_tjes_cjsg_response(payload, query=JurisprudenceQuery(text="x"), trace=trace())


def test_empty_page_is_explicitly_complete() -> None:
    page = parse_tjes_cjsg_response(
        fixture_data("tjes_cjsg_empty.json"),
        query=JurisprudenceQuery(text="termo sem ocorrencias"),
        trace=trace(),
    )
    assert page.results == []
    assert page.total == 0
    assert page.is_complete is True
    assert page.completeness_reason


def test_query_contract_fixes_pje2g_and_conservative_page_size() -> None:
    params = build_tjes_cjsg_params(
        JurisprudenceQuery(text="dano moral", page=3, page_size=100), page_size=20
    )
    assert params == {"core": TJES_CJSG_CORE, "q": "dano moral", "page": 3, "per_page": 20}


def test_provider_emits_trace_and_client_registration() -> None:
    session = FakeSession(
        [
            FakeResponse(
                fixture_data(),
                url=(
                    "https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/search"
                    "?core=pje2g&page=1&per_page=2"
                ),
            )
        ]
    )
    provider = TjesJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=2))
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["kwargs"]["params"]["core"] == "pje2g"
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes > 0
    client = NanoJurisClient()
    assert "tjes_jurisprudencia" in client.providers
    capabilities = client.providers["tjes_jurisprudencia"].get_capabilities()
    assert capabilities.semantic_discriminator == "collection=second_degree;core=pje2g"
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert capabilities.max_remote_page_size == 20


def test_provider_is_in_default_federation_after_promotion() -> None:
    client = NanoJurisClient()

    assert "tjes_jurisprudencia" in client._default_unified_sources()


def test_provider_rejects_empty_query_and_transport_error() -> None:
    provider = TjesJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=RaisingSession()
    )
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
def test_provider_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjesJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status) for _ in range(3)]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))
