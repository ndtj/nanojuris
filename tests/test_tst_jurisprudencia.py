from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tst_jurisprudencia import (
    TstJurisprudenciaProvider,
    _format_case_number,
    _map_type,
    _page_size,
    _parse_aggregations,
    _tst_type,
    _usable_text,
    build_tst_search_payload,
    parse_tst_search_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, data=None, *, text: str = "", status_code: int = 200, url: str = ""):
        self._data = data
        self.text = text
        self.status_code = status_code
        self.url = url

    def json(self):
        if self._data is None:
            raise ValueError("not json")
        return self._data


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _fixture() -> dict:
    return json.loads((FIXTURES / "tst_jurisprudencia_responsabilidade.json").read_text())


def test_build_tst_payload_maps_text_number_and_filters():
    payload = build_tst_search_payload(
        JurisprudenceQuery(
            text="responsabilidade",
            any_words="terceirizacao",
            exact_phrase="culpa in vigilando",
            without_words="prescricao",
            number="0012345-67.2024.5.15.0001",
            published_from="2026-01-01",
            published_to="2026-12-31",
            types=["acordao"],
        )
    )

    assert payload["e"] == "responsabilidade"
    assert payload["ou"] == "terceirizacao"
    assert payload["termoExato"] == "culpa in vigilando"
    assert payload["naoContem"] == "prescricao"
    assert payload["numeracaoUnica"] == {
        "numero": "0012345",
        "digito": "67",
        "ano": "2024",
        "orgao": "5",
        "tribunal": "15",
        "vara": "0001",
    }
    assert payload["tipos"] == ["ACORDAO"]
    assert payload["publicacaoInicial"] == "2026-01-01"


def test_empty_tst_query_is_rejected():
    with pytest.raises(ValueError, match="requires a term"):
        build_tst_search_payload(JurisprudenceQuery())


def test_parse_tst_search_response_maps_fixture():
    page = parse_tst_search_response(
        _fixture(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=5),
        trace=SourceTrace(provider="tst_jurisprudencia", endpoint="/rest/pesquisa-textual/1/5"),
        api_url="https://jurisprudencia-backend2.tst.jus.br",
    )

    assert page.source == "tst_jurisprudencia"
    assert page.total == 1
    assert page.start == 1
    assert page.results[0].id == "tst-jurisprudencia-0123456789abcdef0123456789abcdef"
    assert page.results[0].court == "TST"
    assert page.results[0].type == "acordao"
    assert page.results[0].number == "RR - 0012345-67.2024.5.15.0001"
    assert page.results[0].rapporteur == "Ministro de Exemplo"
    assert page.results[0].raw["orgao_julgador"] == "1a Turma"
    assert (
        page.results[0]
        .raw["document_url"]
        .endswith("/rest/documentos/0123456789abcdef0123456789abcdef")
    )
    assert page.aggregations["items"][0]["valor"] == "ACORDAO"


def test_provider_search_posts_public_tst_payload():
    session = FakeSession(
        [
            FakeResponse(
                _fixture(),
                url="https://jurisprudencia-backend2.tst.jus.br/rest/pesquisa-textual/1/1",
            )
        ]
    )
    provider = TstJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=1))

    assert page.total == 1
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/rest/pesquisa-textual/1/1")
    assert call["kwargs"]["json"]["e"] == "responsabilidade"
    assert call["kwargs"]["json"]["tipos"] == ["ACORDAO"]


def test_provider_get_document_returns_canonical_html_document():
    html = "<html><body><h1>Acordao</h1><p>Inteiro teor publico.</p></body></html>"
    session = FakeSession(
        [
            FakeResponse(
                text=html,
                url="https://jurisprudencia-backend2.tst.jus.br/rest/documentos/0123456789abcdef0123456789abcdef",
            )
        ]
    )
    provider = TstJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    document = provider.get_document("tst-jurisprudencia-0123456789abcdef0123456789abcdef")

    assert document.source == "tst_jurisprudencia"
    assert document.text == "Acordao Inteiro teor publico."
    assert document.content_type == "text/html"


@pytest.mark.parametrize(
    "status,exception",
    [(401, AccessControlRequiredError), (429, RateLimitDetectedError)],
)
def test_provider_maps_access_and_rate_limit(status, exception):
    session = FakeSession([FakeResponse(text="blocked", status_code=status)])
    provider = TstJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(exception):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_rejects_invalid_document_id():
    provider = TstJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    )

    with pytest.raises(ParserContractChangedError):
        provider.get_document("invalid")


def test_client_registers_tst_by_default():
    client = NanoJurisClient()

    assert "tst_jurisprudencia" in client.providers
    assert client.get_capabilities(source="tst_jurisprudencia").supports_full_text is True


def test_tst_normalization_helpers_cover_optional_shapes():
    assert (
        _format_case_number(
            {
                "numero": "1",
                "digito": "2",
                "ano": "2024",
                "orgao": "5",
                "tribunal": "15",
                "vara": "1",
            }
        )
        == "0000001-02.2024.5.15.0001"
    )
    assert _format_case_number({"numero": "incompleto"}) is None
    assert _map_type("Súmula") == "sumula"
    assert _map_type("Despacho") == "decisao"
    assert _map_type("outro") == "outro"
    assert _tst_type("acordãos") == "ACORDAO"
    assert _tst_type("sumulas") == "SUM"
    assert _tst_type("desconhecido") == "DESCONHECIDO"
    assert _usable_text("<p>Texto</p>") == "Texto"
    assert _usable_text("Removido no backend") is None


def test_tst_aggregation_and_page_helpers_accept_multiple_shapes():
    assert _parse_aggregations({"tipo": [{"valor": "ACORDAO"}, "ignorar"]}) == {
        "tipo": [{"valor": "ACORDAO"}]
    }
    assert _parse_aggregations([{"valor": "ACORDAO"}, "ignorar"]) == {
        "items": [{"valor": "ACORDAO"}]
    }
    assert _parse_aggregations(None) == {}
    assert _page_size(0) == 1
    assert _page_size(1000) == 100
