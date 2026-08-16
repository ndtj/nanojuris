from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjam_cjsg import TjamCjsgProvider
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


def test_parse_cjsg_results_can_stamp_tjam_source_and_court():
    page = parse_cjsg_results(
        _fixture_html(),
        query=JurisprudenceQuery(text="infanticidio", page_size=2),
        trace=SourceTrace(provider="tjam_cjsg", endpoint="/resultadoCompleta.do"),
        base_url="https://consultasaj.tjam.jus.br/cjsg",
        source="tjam_cjsg",
        court="TJAM",
        id_prefix="tjam-cjsg",
        source_label="TJAM/CJSG",
    )

    assert page.source == "tjam_cjsg"
    assert page.results[0].id == "tjam-cjsg-20787558-0"
    assert page.results[0].source == "tjam_cjsg"
    assert page.results[0].court == "TJAM"
    assert page.results[0].raw["full_text_url"].startswith("https://consultasaj.tjam.jus.br/cjsg")


def test_provider_search_posts_tjam_cjsg_payload_and_parses_results():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = TjamCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="infanticidio",
            exact_phrase="homicidio",
            number="0003949-10.2024.8.04.0000",
            types=["acordao"],
            updated_from="01/01/2024",
            updated_to="31/12/2024",
            page_size=2,
        )
    )

    assert page.source == "tjam_cjsg"
    assert page.results[0].id == "tjam-cjsg-20787558-0"
    assert page.results[0].court == "TJAM"
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes == len(_fixture_html().encode("utf-8"))
    call = session.calls[0]
    payload = call["kwargs"]["data"]
    assert call["method"] == "POST"
    assert call["url"] == "https://consultasaj.tjam.jus.br/cjsg/resultadoCompleta.do"
    assert payload["dados.buscaInteiroTeor"] == "infanticidio"
    assert payload["dados.buscaEmenta"] == "homicidio"
    assert payload["dados.nuProcOrigem"] == "0003949-10.2024.8.04.0000"
    assert payload["tipoDecisaoSelecionados"] == ["A"]


def test_provider_search_page_two_uses_public_cjsg_pagination_route():
    fixture = _fixture_html()
    session = FakeSession([FakeResponse(fixture), FakeResponse(fixture)])
    provider = TjamCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    provider.search(JurisprudenceQuery(text="infanticidio", page=2, page_size=20))

    assert len(session.calls) == 2
    assert "/trocaDePagina.do?" in session.calls[1]["url"]
    assert "pagina=2" in session.calls[1]["url"]


def test_provider_get_decisions_builds_tjam_getarquivo_url():
    session = FakeSession([FakeResponse("<html>inteiro teor publico</html>")])
    provider = TjamCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    bundle = provider.get_decisions("tjam-cjsg-3287961-0")

    assert bundle.precedent_id == "tjam-cjsg-3287961-0"
    assert bundle.source == "tjam_cjsg"
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["url"].endswith("getArquivo.do?cdAcordao=3287961&cdForo=0")


def test_provider_detects_access_control_without_bypass():
    session = FakeSession([FakeResponse("<html><div class='g-recaptcha'></div></html>")])
    provider = TjamCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(AccessControlRequiredError, match="has_recaptcha_widget"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_invalid_tjam_precedent_id_is_rejected():
    provider = TjamCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]))

    with pytest.raises(ParserContractChangedError):
        provider.get_decisions("bad-id")


def test_request_exception_becomes_source_error():
    session = FakeSession([requests.RequestException("offline")])
    provider = TjamCjsgProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    with pytest.raises(Exception, match="TJAM/CJSG request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_capabilities_describe_tjam_contract():
    capabilities = TjamCjsgProvider(NanoJurisConfig(rate_limit_interval=0)).get_capabilities()

    assert capabilities.source == "tjam_cjsg"
    assert capabilities.source_url == "https://consultasaj.tjam.jus.br/cjsg"
    assert "CanonicalDecision" in capabilities.canonical_records
    assert "case_number" in capabilities.search_modes
    assert capabilities.max_remote_page_size == 10
