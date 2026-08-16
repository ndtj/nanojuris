from __future__ import annotations

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
from nanojuris.providers.tjpr_jurisprudencia import (
    TjprJurisprudenciaProvider,
    parse_tjpr_results,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200, url: str = "https://portal.tjpr.jus.br"):
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": "text/html; charset=utf-8"}


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"method": "GET", "url": url, "kwargs": kwargs})
        return self._next()

    def post(self, url, **kwargs):
        self.calls.append({"method": "POST", "url": url, "kwargs": kwargs})
        return self._next()

    def _next(self):
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def trace() -> SourceTrace:
    return SourceTrace(
        provider="tjpr_jurisprudencia",
        endpoint="POST /jurisprudencia/publico/pesquisa.do?actionType=pesquisar",
        source_url="https://portal.tjpr.jus.br",
    )


def test_parse_tjpr_results_maps_decisions_and_excludes_corte_idh():
    page = parse_tjpr_results(
        load_fixture("tjpr_jurisprudencia_results.html"),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=5),
        trace=trace(),
        base_url="https://portal.tjpr.jus.br",
    )

    assert page.source == "tjpr_jurisprudencia"
    assert page.total == 123
    assert len(page.results) == 2
    first = page.results[0]
    assert first.id == "tjpr-2100000000000001"
    assert first.court == "TJPR"
    assert first.type == "acordao"
    assert first.number == "0000001-01.2024.8.16.0001"
    assert first.judgment_date == "2024-03-12"
    assert first.rapporteur == "Des. Ana Exemplo"
    assert first.raw["judging_body"] == "1ª Câmara Cível"
    assert first.source_trace is not None
    assert ";jsessionid" not in (first.source_trace.source_url or "")

    pending = page.results[1]
    assert pending.access_status.value == "partial"
    assert pending.extraction_status.value == "partial"
    assert pending.raw["content_pending_release"] is True


def test_parser_accepts_acordao_link_class_from_live_contract():
    html = load_fixture("tjpr_jurisprudencia_results.html").replace(
        'class="decisao negrito"', 'class="acordao negrito"', 1
    )

    page = parse_tjpr_results(
        html,
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=5),
        trace=trace(),
        base_url="https://portal.tjpr.jus.br",
    )

    assert len(page.results) == 2
    assert page.results[0].id == "tjpr-2100000000000001"


def test_parse_tjpr_empty_page_is_complete():
    html = "<html><body><div>0 registro(s) encontrado(s)</div></body></html>"
    page = parse_tjpr_results(
        html,
        query=JurisprudenceQuery(text="sem resultado"),
        trace=trace(),
        base_url="https://portal.tjpr.jus.br",
    )
    assert page.total == 0
    assert page.results == []
    assert page.is_complete is True


def test_provider_replays_public_form_and_preserves_query_contract():
    fixture = load_fixture("tjpr_jurisprudencia_results.html")
    session = FakeSession(
        [
            FakeResponse(fixture),
            FakeResponse(
                fixture, url="https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do"
            ),
        ]
    )
    provider = TjprJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    page = provider.search(
        JurisprudenceQuery(
            text="responsabilidade civil",
            number="0000001-01.2024.8.16.0001",
            published_from="01/01/2024",
            published_to="31/12/2024",
            page=2,
            page_size=5,
        )
    )

    assert page.results[0].source == "tjpr_jurisprudencia"
    assert [call["method"] for call in session.calls] == ["GET", "POST"]
    payload = session.calls[1]["kwargs"]["data"]
    assert payload["criterioPesquisa"] == "responsabilidade civil"
    assert payload["processo"] == "0000001-01.2024.8.16.0001"
    assert payload["dataPublicacaoInicio"] == "01/01/2024"
    assert payload["pageNumber"] == "2"
    assert session.calls[1]["kwargs"]["verify"] is True
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.response_bytes == len(fixture.encode("utf-8"))
    assert page.source_trace.content_sha256


def test_client_registers_tjpr_provider():
    assert "tjpr_jurisprudencia" in {item.source for item in NanoJurisClient().list_sources()}


def test_provider_capabilities_describe_partial_full_text_contract():
    capabilities = TjprJurisprudenciaProvider(session=FakeSession([])).get_capabilities()
    assert capabilities.source == "tjpr_jurisprudencia"
    assert capabilities.supports_full_text is False
    assert "number" in capabilities.supported_filters
    assert "POST /jurisprudencia/publico/pesquisa.do?actionType=pesquisar" in capabilities.endpoints


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (FakeResponse("captcha", 403), AccessControlRequiredError),
        (FakeResponse("", 429), RateLimitDetectedError),
        (FakeResponse("", 503), SourceUnavailableError),
    ],
)
def test_provider_normalizes_public_route_errors(response, expected):
    provider = TjprJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([response]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))


def test_parser_detects_missing_result_contract():
    with pytest.raises(ParserContractChangedError):
        parse_tjpr_results(
            "<html><body>contrato desconhecido</body></html>",
            query=JurisprudenceQuery(text="teste"),
            trace=trace(),
            base_url="https://portal.tjpr.jus.br",
        )


def test_provider_wraps_transport_failures():
    provider = TjprJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )
    with pytest.raises(SourceUnavailableError, match="TJPR search request failed"):
        provider.search(JurisprudenceQuery(text="teste"))
