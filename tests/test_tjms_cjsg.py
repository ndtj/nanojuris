from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjms_cjsg import TjmsCjsgProvider
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


def test_parse_cjsg_results_can_stamp_tjms_source_and_court():
    page = parse_cjsg_results(
        _fixture_html(),
        query=JurisprudenceQuery(text="infanticidio", page_size=2),
        trace=SourceTrace(provider="tjms_cjsg", endpoint="/resultadoCompleta.do"),
        base_url="https://esaj.tjms.jus.br/cjsg",
        source="tjms_cjsg",
        court="TJMS",
        id_prefix="tjms-cjsg",
        source_label="TJMS/CJSG",
    )

    assert page.source == "tjms_cjsg"
    assert page.results[0].id == "tjms-cjsg-20787558-0"
    assert page.results[0].source == "tjms_cjsg"
    assert page.results[0].court == "TJMS"
    assert page.results[0].raw["full_text_url"].startswith("https://esaj.tjms.jus.br/cjsg")


def test_provider_search_posts_tjms_cjsg_payload_and_parses_results():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = TjmsCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="infanticidio",
            exact_phrase="homicidio",
            number="0000008-16.2011.8.12.0055",
            types=["acordao"],
            updated_from="01/01/2011",
            updated_to="31/12/2011",
            page_size=2,
        )
    )

    assert page.source == "tjms_cjsg"
    assert page.results[0].id == "tjms-cjsg-20787558-0"
    assert page.results[0].court == "TJMS"
    call = session.calls[0]
    payload = call["kwargs"]["data"]
    assert call["method"] == "POST"
    assert call["url"] == "https://esaj.tjms.jus.br/cjsg/resultadoCompleta.do"
    assert payload["dados.buscaInteiroTeor"] == "infanticidio"
    assert payload["dados.buscaEmenta"] == "homicidio"
    assert payload["dados.nuProcOrigem"] == "0000008-16.2011.8.12.0055"
    assert payload["tipoDecisaoSelecionados"] == ["A"]


def test_provider_get_decisions_builds_tjms_getarquivo_url():
    session = FakeSession([FakeResponse("<html>inteiro teor publico</html>")])
    provider = TjmsCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    bundle = provider.get_decisions("tjms-cjsg-224478-0")

    assert bundle.precedent_id == "tjms-cjsg-224478-0"
    assert bundle.source == "tjms_cjsg"
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["url"].endswith("getArquivo.do?cdAcordao=224478&cdForo=0")


def test_provider_get_document_returns_canonical_document():
    session = FakeSession([FakeResponse("<html>inteiro teor publico</html>")])
    provider = TjmsCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    document = provider.get_document("tjms-cjsg-224478-0")

    assert document.id == "tjms-cjsg-224478-0"
    assert document.source == "tjms_cjsg"
    assert document.document_type == "acordao"
    assert document.text == "<html>inteiro teor publico</html>"
    assert document.raw_metadata["cd_acordao"] == "224478"
    assert document.raw_metadata["cd_foro"] == "0"
    assert document.raw_metadata["raw_content_preserved"] is True


def test_provider_detects_access_control_without_bypass():
    session = FakeSession([FakeResponse("<html><div class='g-recaptcha'></div></html>")])
    provider = TjmsCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(AccessControlRequiredError, match="has_recaptcha_widget"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_invalid_tjms_precedent_id_is_rejected():
    provider = TjmsCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]))

    with pytest.raises(ParserContractChangedError):
        provider.get_decisions("bad-id")


def test_request_exception_becomes_source_error():
    session = FakeSession([requests.RequestException("offline")])
    provider = TjmsCjsgProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    with pytest.raises(Exception, match="TJMS/CJSG request failed"):
        provider.search(JurisprudenceQuery(text="teste"))
