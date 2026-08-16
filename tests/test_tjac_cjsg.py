from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjac_cjsg import TjacCjsgProvider
from nanojuris.providers.tjsp_cjsg import parse_cjsg_results

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _fixture_html() -> str:
    return (FIXTURES / "tjsp_cjsg_result.html").read_text(encoding="utf-8")


def test_parse_cjsg_results_can_stamp_tjac_source_and_court():
    page = parse_cjsg_results(
        _fixture_html(),
        query=JurisprudenceQuery(text="infanticidio", page_size=2),
        trace=SourceTrace(provider="tjac_cjsg", endpoint="/resultadoCompleta.do"),
        base_url="https://esaj.tjac.jus.br/cjsg",
        source="tjac_cjsg",
        court="TJAC",
        id_prefix="tjac-cjsg",
        source_label="TJAC/CJSG",
    )

    assert page.source == "tjac_cjsg"
    assert page.results[0].id == "tjac-cjsg-20787558-0"
    assert page.results[0].source == "tjac_cjsg"
    assert page.results[0].court == "TJAC"
    assert page.results[0].raw["full_text_url"].startswith("https://esaj.tjac.jus.br/cjsg")


def test_provider_search_posts_tjac_cjsg_payload_and_parses_results():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = TjacCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="infanticidio",
            exact_phrase="homicidio",
            number="0001970-91.2024.8.01.0001",
            types=["acordao"],
            updated_from="01/01/2024",
            updated_to="31/12/2024",
            page_size=2,
        )
    )

    assert page.source == "tjac_cjsg"
    assert page.results[0].id == "tjac-cjsg-20787558-0"
    assert page.results[0].court == "TJAC"
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes == len(_fixture_html().encode("utf-8"))
    call = session.calls[0]
    payload = call["kwargs"]["data"]
    assert call["method"] == "POST"
    assert call["url"] == "https://esaj.tjac.jus.br/cjsg/resultadoCompleta.do"
    assert payload["dados.buscaInteiroTeor"] == "infanticidio"
    assert payload["dados.buscaEmenta"] == "homicidio"
    assert payload["dados.nuProcOrigem"] == "0001970-91.2024.8.01.0001"
    assert payload["tipoDecisaoSelecionados"] == ["A"]


def test_provider_search_page_two_uses_public_cjsg_pagination_route():
    fixture = _fixture_html()
    session = FakeSession([FakeResponse(fixture), FakeResponse(fixture)])
    provider = TjacCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    provider.search(JurisprudenceQuery(text="infanticidio", page=2, page_size=20))

    assert len(session.calls) == 2
    assert session.calls[0]["kwargs"]["data"]["paginaConsulta"] == "1"
    assert "/trocaDePagina.do?" in session.calls[1]["url"]
    assert "pagina=2" in session.calls[1]["url"]


def test_provider_get_decisions_builds_tjac_getarquivo_url():
    session = FakeSession([FakeResponse("<html>inteiro teor publico</html>")])
    provider = TjacCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    bundle = provider.get_decisions("tjac-cjsg-2471822-0")

    assert bundle.precedent_id == "tjac-cjsg-2471822-0"
    assert bundle.source == "tjac_cjsg"
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["url"].endswith("getArquivo.do?cdAcordao=2471822&cdForo=0")


def test_provider_detects_access_control_without_bypass():
    session = FakeSession([FakeResponse("<html><div class='g-recaptcha'></div></html>")])
    provider = TjacCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(AccessControlRequiredError, match="has_recaptcha_widget"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_invalid_tjac_precedent_id_is_rejected():
    provider = TjacCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]))

    with pytest.raises(ParserContractChangedError):
        provider.get_decisions("bad-id")


def test_request_exception_becomes_source_error():
    session = FakeSession([requests.RequestException("offline")])
    provider = TjacCjsgProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    with pytest.raises(Exception, match="TJAC/CJSG request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_capabilities_describe_tjac_contract():
    capabilities = TjacCjsgProvider(NanoJurisConfig(rate_limit_interval=0)).get_capabilities()

    assert capabilities.source == "tjac_cjsg"
    assert capabilities.source_url == "https://esaj.tjac.jus.br/cjsg"
    assert "CanonicalDecision" in capabilities.canonical_records
    assert "case_number" in capabilities.search_modes
