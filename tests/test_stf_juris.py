from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.stf_juris import (
    StfJurisProvider,
    build_stf_search_payload,
    parse_stf_search_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        data=None,
        *,
        text: str = "",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ):
        self._data = data
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}
        self.content = text.encode("utf-8")

    def json(self):
        if self._data is None:
            raise ValueError("not json")
        return self._data


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_build_stf_search_payload_maps_query_contract():
    payload = build_stf_search_payload(
        JurisprudenceQuery(
            text="infanticidio",
            page=2,
            page_size=5,
            published_from="2026-01-01",
            published_to="2026-12-31",
        )
    )

    assert payload["size"] == 5
    assert payload["from"] == 5
    assert payload["track_total_hits"] is True
    assert payload["query"]["bool"]["filter"][0]["query_string"]["query"] == "infanticidio"
    assert payload["query"]["bool"]["filter"][1]["range"]["publicacao_data"] == {
        "gte": "2026-01-01",
        "lte": "2026-12-31",
    }
    assert (
        "ementa_texto.plural^3" in payload["query"]["bool"]["filter"][0]["query_string"]["fields"]
    )


def test_build_stf_search_payload_supports_case_number_and_date_sort():
    payload = build_stf_search_payload(
        JurisprudenceQuery(
            text="",
            number="RE 123456",
            page=1,
            page_size=1,
            order_by="date",
            updated_from="2025-01-01",
        )
    )

    assert payload["from"] == 0
    assert payload["sort"] == [{"publicacao_data": {"order": "desc"}}]
    assert payload["query"]["bool"]["filter"][0]["query_string"]["query"] == "RE 123456"
    assert payload["query"]["bool"]["filter"][1]["range"]["publicacao_data"] == {
        "gte": "2025-01-01"
    }


def test_build_stf_search_payload_uses_match_all_marker_for_empty_text():
    payload = build_stf_search_payload(JurisprudenceQuery(text="", page_size=1))

    assert payload["query"]["bool"]["filter"][0]["query_string"]["query"] == "*"


def test_parse_stf_search_response_maps_fixture():
    trace = SourceTrace(provider="stf_juris", endpoint="/api/search/search")

    page = parse_stf_search_response(
        _fixture("stf_juris_infanticidio.json"),
        query=JurisprudenceQuery(text="infanticidio", page_size=2),
        trace=trace,
    )

    assert page.source == "stf_juris"
    assert page.total == 3
    assert page.start == 1
    assert page.end == 2
    assert page.aggregations["base"][0]["key"] == "acordaos"
    first = page.results[0]
    assert first.id == "stf-juris-sjur561554"
    assert first.court == "STF"
    assert first.type == "acordao"
    assert first.number == "ARE 1589201 AgR-segundo"
    assert first.rapporteur == "FLAVIO DINO"
    assert first.updated_at == "2026-05-06"
    assert first.raw["classe"] == "ARE-AgR-segundo"
    assert first.raw["case_class"] == "SEGUNDO AG.REG. NO RECURSO EXTRAORDINARIO COM AGRAVO"
    assert first.raw["orgao_julgador"] == "Primeira Turma"
    assert first.raw["data_julgamento"] == "2026-04-29"
    assert first.raw["document_url"].endswith("idDocumento=797183228")
    assert (
        first.highlights["ementa_texto"]
        == "Desclassificacao para infanticidio. Agravo nao provido."
    )


def test_parse_stf_search_response_accepts_empty_result_page():
    page = parse_stf_search_response(
        {
            "result": {
                "hits": {"total": 0, "hits": []},
                "aggregations": {"base": {"buckets": "unexpected"}},
            }
        },
        query=JurisprudenceQuery(text="termo", page_size=5),
        trace=SourceTrace(provider="stf_juris", endpoint="/api/search/search"),
    )

    assert page.total == 0
    assert page.start == 0
    assert page.end == 0
    assert page.aggregations == {}


def test_parse_stf_search_response_maps_alternate_document_shapes():
    page = parse_stf_search_response(
        {
            "result": {
                "hits": {
                    "total": {"value": 2},
                    "hits": [
                        {
                            "_id": "dec-1",
                            "_source": {
                                "base": "decisoes",
                                "titulo": "Decisao monocratica",
                                "decisao_texto": "Decisao registrada",
                                "relator_acordao_nome": "MINISTRA TESTE",
                                "julgamento_data": "2025-02-03",
                            },
                            "highlight": {"ignored": "not-a-list"},
                        },
                        {
                            "_id": "sum-1",
                            "_source": {
                                "base": "sumulas",
                                "titulo": "Sumula 1",
                                "documental_tese_texto": "Enunciado",
                                "ministro_facet": ["MINISTRO LISTA"],
                            },
                        },
                    ],
                }
            }
        },
        query=JurisprudenceQuery(text="teste", page_size=2),
        trace=SourceTrace(provider="stf_juris", endpoint="/api/search/search"),
    )

    assert page.results[0].type == "decisao"
    assert page.results[0].summary == "Decisao registrada"
    assert page.results[0].rapporteur == "MINISTRA TESTE"
    assert page.results[0].updated_at == "2025-02-03"
    assert page.results[0].highlights == {}
    assert page.results[1].type == "sumula"
    assert page.results[1].summary == "Enunciado"
    assert page.results[1].rapporteur == "MINISTRO LISTA"


def test_parse_stf_search_response_uses_unknown_defaults_for_minimal_hit():
    page = parse_stf_search_response(
        {"result": {"hits": {"total": "unexpected", "hits": [{"_source": {}}]}}},
        query=JurisprudenceQuery(text="teste", page_size=1),
        trace=SourceTrace(provider="stf_juris", endpoint="/api/search/search"),
    )

    result = page.results[0]
    assert page.total == 0
    assert result.id == "stf-juris-unknown"
    assert result.type == "documento"
    assert result.number is None
    assert result.rapporteur is None


def test_provider_search_posts_stf_payload_and_parses_results():
    session = FakeSession([FakeResponse(_fixture("stf_juris_infanticidio.json"))])
    provider = StfJurisProvider(session=session)

    page = provider.search(JurisprudenceQuery(text="infanticidio", page_size=2))

    assert page.results[0].id == "stf-juris-sjur561554"
    call = session.calls[0]
    assert call["url"] == "https://jurisprudencia.stf.jus.br/api/search/search"
    assert call["kwargs"]["headers"]["Accept"] == "application/json, text/plain, */*"
    assert call["kwargs"]["json"]["size"] == 2
    assert (
        call["kwargs"]["json"]["query"]["bool"]["filter"][0]["query_string"]["query"]
        == "infanticidio"
    )
    assert call["kwargs"]["verify"] is True


def test_provider_search_honors_disabled_ssl_verification():
    session = FakeSession([FakeResponse({"result": {"hits": {"total": 0, "hits": []}}})])
    provider = StfJurisProvider(
        session=session,
        config=NanoJurisConfig(verify_ssl=False),
    )

    provider.search(JurisprudenceQuery(text="teste", page_size=1))

    assert session.calls[0]["kwargs"]["verify"] is False


def test_provider_capabilities_describe_stf_contract():
    capabilities = StfJurisProvider(session=FakeSession([])).get_capabilities()

    assert capabilities.source == "stf_juris"
    assert capabilities.category == "court_jurisprudence"
    assert capabilities.endpoints == ["POST /api/search/search"]
    assert capabilities.content_formats == ["json"]
    assert capabilities.canonical_records == ["CanonicalDecision"]
    assert "full_text_url" in capabilities.extracted_fields
    assert capabilities.supports_full_text is False
    assert any("AWS WAF" in item for item in capabilities.limitations)


def test_provider_get_decisions_reports_metadata_only_scope():
    bundle = StfJurisProvider(session=FakeSession([])).get_decisions("sjur561554")

    assert bundle.precedent_id == "sjur561554"
    assert bundle.source == "stf_juris"
    assert bundle.texts == []
    assert "metadata" in bundle.raw["message"]


def test_client_registers_stf_juris_by_default():
    client = NanoJurisClient()

    sources = {capability.source for capability in client.list_sources()}
    assert "stf_juris" in sources
    assert "stj_scon" in sources


def test_client_search_canonical_maps_stf_to_decision():
    session = FakeSession([FakeResponse(_fixture("stf_juris_infanticidio.json"))])
    client = NanoJurisClient(providers=[StfJurisProvider(session=session)])

    records = client.search_canonical("infanticidio", source="stf_juris", page_size=2)

    assert len(records) == 2
    first = records[0]
    assert first.source == "stf_juris"
    assert first.court == "STF"
    assert first.case_number == "ARE 1589201 AgR-segundo"
    assert first.case_class == "ARE-AgR-segundo"
    assert first.subject == "Direito processual penal"
    assert first.judging_body == "Primeira Turma"
    assert first.publication_date == "2026-05-06"
    assert first.document_url.endswith("idDocumento=797183228")


def test_provider_detects_aws_waf_challenge_without_bypass():
    response = FakeResponse(
        None,
        status_code=202,
        headers={"x-amzn-waf-action": "challenge"},
    )
    provider = StfJurisProvider(session=FakeSession([response]))

    with pytest.raises(AccessControlRequiredError, match="AWS WAF"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_provider_detects_waf_marker_in_response_text():
    response = FakeResponse(
        None,
        text="<html>awswaf token</html>",
        status_code=200,
    )
    provider = StfJurisProvider(session=FakeSession([response]))

    with pytest.raises(AccessControlRequiredError, match="AWS WAF"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_provider_reports_ssl_failure_as_source_unavailable():
    provider = StfJurisProvider(session=FakeSession([requests.exceptions.SSLError("cert")]))

    with pytest.raises(Exception, match="SSL verification failed"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_provider_reports_request_failure_as_source_unavailable():
    provider = StfJurisProvider(
        session=FakeSession([requests.exceptions.Timeout("connection timed out")])
    )

    with pytest.raises(SourceUnavailableError, match="request failed"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_provider_reports_rate_limit():
    provider = StfJurisProvider(session=FakeSession([FakeResponse(None, status_code=429)]))

    with pytest.raises(RateLimitDetectedError):
        provider.search(JurisprudenceQuery(text="infanticidio"))


@pytest.mark.parametrize("status_code", [400, 503])
def test_provider_reports_http_errors(status_code):
    provider = StfJurisProvider(session=FakeSession([FakeResponse(None, status_code=status_code)]))

    with pytest.raises(SourceUnavailableError, match=f"HTTP {status_code}"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_provider_rejects_non_json_response():
    provider = StfJurisProvider(session=FakeSession([FakeResponse(None, text="html")]))

    with pytest.raises(ParserContractChangedError, match="non-JSON"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_provider_rejects_non_object_json_response():
    provider = StfJurisProvider(session=FakeSession([FakeResponse(["unexpected"])]))

    with pytest.raises(ParserContractChangedError, match="root"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_parse_stf_search_response_rejects_missing_contract():
    with pytest.raises(ParserContractChangedError):
        parse_stf_search_response(
            {"unexpected": {}},
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="stf_juris", endpoint="/api/search/search"),
        )


def test_parse_stf_search_response_rejects_missing_hits_object():
    with pytest.raises(ParserContractChangedError, match="hits object"):
        parse_stf_search_response(
            {"result": {}},
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="stf_juris", endpoint="/api/search/search"),
        )


def test_parse_stf_search_response_rejects_non_list_hits():
    with pytest.raises(ParserContractChangedError, match="hits is not a list"):
        parse_stf_search_response(
            {"result": {"hits": {"hits": {}}}},
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="stf_juris", endpoint="/api/search/search"),
        )


def test_parse_stf_search_response_rejects_hit_without_source_object():
    with pytest.raises(ParserContractChangedError, match="_source"):
        parse_stf_search_response(
            {"result": {"hits": {"hits": [{"_source": "invalid"}]}}},
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="stf_juris", endpoint="/api/search/search"),
        )
