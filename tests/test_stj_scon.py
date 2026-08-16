from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.stj_scon import StjSconProvider, parse_stj_scon_results

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        text: str,
        status_code: int = 200,
        *,
        content: bytes | None = None,
        url: str = "https://scon.stj.jus.br/SCON/pesquisar.jsp",
        content_type: str = "text/html",
    ):
        self.text = text
        self.content = content if content is not None else text.encode("utf-8")
        self.status_code = status_code
        self.encoding = "utf-8"
        self.url = url
        self.headers = {"Content-Type": content_type}


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
    return (FIXTURES / "stj_scon_acordaos_result.html").read_text(encoding="utf-8")


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_stj_scon_results_maps_fixture():
    trace = SourceTrace(provider="stj_scon", endpoint="/SCON/acordaos/")

    page = parse_stj_scon_results(
        _fixture_html(),
        query=JurisprudenceQuery(text="jurisprudencia publica", page_size=2),
        trace=trace,
        base_url="https://processo.stj.jus.br",
    )

    assert page.source == "stj_scon"
    assert page.total == 125
    assert page.start == 1
    assert page.end == 2
    assert len(page.results) == 2
    first = page.results[0]
    assert first.id == "stj-scon-202400123456"
    assert first.court == "STJ"
    assert first.type == "acordao"
    assert first.number == "1234567/SP"
    assert first.rapporteur == "Ministro Exemplo"
    assert first.updated_at == "18/03/2026"
    assert first.judgment_date == "12/03/2026"
    assert first.publication_date == "18/03/2026"
    assert first.access_status.value == "public"
    assert first.raw["classe"] == "AgInt no REsp"
    assert first.raw["registro"] == "202400123456"
    assert first.raw["registry_number"] == "202400123456"
    assert first.raw["orgao_julgador"] == "Terceira Turma"
    assert first.raw["document_url"].endswith(
        "/SCON/GetInteiroTeorDoAcordao?num_registro=202400123456"
    )


def test_parse_stj_scon_results_maps_real_har_shape_fixture():
    trace = SourceTrace(provider="stj_scon", endpoint="/SCON/pesquisar.jsp")

    page = parse_stj_scon_results(
        _fixture("stj_scon_real_documentos.html"),
        query=JurisprudenceQuery(text="publicidade criancas", page_size=2),
        trace=trace,
        base_url="https://scon.stj.jus.br",
    )

    assert page.source == "stj_scon"
    assert page.total == 2
    assert page.start == 1
    assert page.end == 2
    first = page.results[0]
    assert first.id == "stj-scon-201600171682"
    assert first.number == "REsp 1613561 / SP RECURSO ESPECIAL 2016/0017168-2"
    assert first.rapporteur == "Ministro HERMAN BENJAMIN (1132)"
    assert first.updated_at == "01/09/2020"
    assert first.judgment_date == "25/04/2017"
    assert first.publication_date == "01/09/2020"
    assert first.access_status.value == "public"
    assert first.raw["classe"] == "RESP 1613561"
    assert first.raw["registry_number"] == "201600171682"
    assert first.raw["orgao_julgador"] == "T2 - SEGUNDA TURMA"
    assert first.raw["data_julgamento"] == "25/04/2017"
    assert first.raw["data_publicacao"] == "DJe 01/09/2020"
    assert first.raw["document_url"] == (
        "https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?"
        "num_registro=201600171682&dt_publicacao=01/09/2020"
    )


def test_provider_search_gets_scon_params_and_parses_results():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = StjSconProvider(session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="recurso especial",
            number="1234567/SP",
            page=2,
            page_size=5,
        )
    )

    assert page.results[0].id == "stj-scon-202400123456"
    call = session.calls[0]
    assert call["method"] == "GET"
    assert call["url"] == "https://scon.stj.jus.br/SCON/pesquisar.jsp"
    assert call["kwargs"]["params"] == {
        "b": "ACOR",
        "p": "true",
        "l": 5,
        "i": 2,
        "ordenacao": "-@DOCN",
        "thesaurus": "JURIDICO",
        "O": "JT",
        "livre": "recurso especial",
        "processo": "1234567/SP",
    }
    assert call["kwargs"]["verify"] is True


def test_provider_capabilities_describe_stj_scon_contract():
    capabilities = StjSconProvider(session=FakeSession([])).get_capabilities()

    assert capabilities.source == "stj_scon"
    assert capabilities.source_url == "https://processo.stj.jus.br/SCON/acordaos/"
    assert capabilities.endpoints == [
        "GET /SCON/pesquisar.jsp",
        "GET /SCON/SearchFiltroBRS",
        "GET /SCON/jurisprudencia/pesquisaAjax.jsp",
        "POST /SCON/ActionSelecionaDocumento",
        "GET /SCON/GetInteiroTeorDoAcordao",
    ]
    assert capabilities.canonical_records == ["CanonicalDecision", "CanonicalDocument"]
    assert capabilities.supports_full_text is True
    assert "stj_query_language" in capabilities.search_modes
    assert "document_url" in capabilities.extracted_fields


def test_provider_get_document_preserves_official_pdf_bytes_and_hash():
    pdf = b"%PDF-1.4\nSTJ public document fixture\n%%EOF"
    session = FakeSession(
        [
            FakeResponse(
                "",
                content=pdf,
                url="https://scon.stj.jus.br/SCON/GetInteiroTeorDoAcordao?num_registro=202400123456",
                content_type="application/pdf",
            )
        ]
    )
    provider = StjSconProvider(session=session)

    document = provider.get_document("stj-scon-202400123456")

    assert document.raw_bytes == pdf
    assert document.sha256 == sha256(pdf).hexdigest()
    assert document.byte_size == len(pdf)
    assert document.content_type == "application/pdf"
    assert document.source_trace is not None
    assert document.source_trace.response_bytes == len(pdf)
    assert session.calls[0]["kwargs"]["params"] == {"num_registro": "202400123456"}


def test_client_registers_stj_scon_by_default():
    client = NanoJurisClient()

    sources = {capability.source for capability in client.list_sources()}
    assert "stj_scon" in sources
    assert "tjsp_eproc_jurisprudencia" in sources


def test_client_search_canonical_maps_stj_scon_to_decision():
    session = FakeSession([FakeResponse(_fixture_html())])
    client = NanoJurisClient(providers=[StjSconProvider(session=session)])

    records = client.search_canonical("recurso especial", source="stj_scon")

    assert len(records) == 2
    first = records[0]
    assert first.source == "stj_scon"
    assert first.court == "STJ"
    assert first.case_number == "1234567/SP"
    assert first.registry_number == "202400123456"
    assert first.decision_type == "acordao"
    assert first.case_class == "AgInt no REsp"
    assert first.document_url is not None


def test_parse_stj_scon_results_accepts_empty_result_page():
    page = parse_stj_scon_results(
        _fixture("stj_scon_empty.html"),
        query=JurisprudenceQuery(text="termo sem resultado"),
        trace=SourceTrace(provider="stj_scon", endpoint="/SCON/acordaos/"),
        base_url="https://processo.stj.jus.br",
    )

    assert page.source == "stj_scon"
    assert page.total == 0
    assert page.results == []


def test_provider_detects_access_control_without_bypass():
    session = FakeSession([FakeResponse(_fixture("stj_scon_access_control.html"))])
    provider = StjSconProvider(session=session)

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_detects_stj_challenge_without_bypass():
    session = FakeSession([FakeResponse("<html><div id='challenge-error-text'></div></html>", 403)])
    provider = StjSconProvider(session=session)

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_detects_stj_automatic_verification_without_bypass():
    html = (
        "<html><body>Verificacao automatica em andamento. "
        "Enable JavaScript and cookies to continue</body></html>"
    )
    session = FakeSession([FakeResponse(html, 403)])
    provider = StjSconProvider(session=session)

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_parser_detects_missing_result_contract():
    with pytest.raises(ParserContractChangedError):
        parse_stj_scon_results(
            "<html><body>sem contrato conhecido</body></html>",
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="stj_scon", endpoint="/SCON/acordaos/"),
            base_url="https://processo.stj.jus.br",
        )


def test_request_exception_becomes_source_error():
    provider = StjSconProvider(session=FakeSession([requests.RequestException("offline")]))

    with pytest.raises(Exception, match="STJ/SCON request failed"):
        provider.search(JurisprudenceQuery(text="teste"))
