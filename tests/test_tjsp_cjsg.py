from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import AccessStatus, ExtractionStatus, JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjsp_cjsg import (
    TjspCjsgProvider,
    decode_cjsg_response_text,
    diagnose_cjsg_access,
    extract_cjsg_document_text,
    parse_cjsg_results,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"
        self.headers = {}


def test_decode_cjsg_response_uses_detected_encoding_without_charset():
    response = requests.Response()
    response.status_code = 200
    response._content = "FEMINICÍDIO contra mulher GRÁVIDA".encode("windows-1252")
    response.headers["Content-Type"] = "text/html"
    response.encoding = None

    assert decode_cjsg_response_text(response) == "FEMINICÍDIO contra mulher GRÁVIDA"


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


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _cjsg_page_fragment() -> str:
    return """
    <span style="display: none;" id="nomeAbaRetornoFiltro-A">Acordaos(858)</span>
    <input id="totalResultadoAbaRetornoFiltro-A" type="hidden" value="858" />
    <table>
      <tr class="fundocinza1">
        <td class="ementaClass"><strong>21 -</strong></td>
        <td>
          <table>
            <tr class="ementaClass">
              <td colspan="2">
                <a class="esajLinkLogin downloadEmenta"
                   cdAcordao="20588041"
                   cdForo="0">1500209-12.2025.8.26.0585</a>
              </td>
            </tr>
            <tr class="ementaClass2">
              <td><strong>Classe/Assunto:</strong> Apelacao Criminal / Furto</td>
            </tr>
            <tr class="ementaClass2">
              <td><strong>Relator(a):</strong> Fulano de Tal</td>
            </tr>
            <tr class="ementaClass2">
              <td><strong>Comarca:</strong> Sao Paulo</td>
            </tr>
            <tr class="ementaClass2">
              <td><strong>Orgao julgador:</strong> 1a Camara Criminal</td>
            </tr>
            <tr class="ementaClass2">
              <td><strong>Data de publicacao:</strong> 06/08/2026</td>
            </tr>
            <tr class="ementaClass">
              <td>
                <textarea id="textAreaDados_20588041">
                  Ementa publica extraida do fragmento paginado do CJSG.
                </textarea>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
    """


def test_parse_cjsg_results_maps_fixture():
    trace = SourceTrace(provider="tjsp_cjsg", endpoint="/resultadoCompleta.do")

    page = parse_cjsg_results(
        _fixture_html(),
        query=JurisprudenceQuery(text="homicidio", page_size=2),
        trace=trace,
        base_url="https://esaj.tjsp.jus.br/cjsg",
    )

    assert page.source == "tjsp_cjsg"
    assert page.total == 854
    assert page.start == 1
    assert page.end == 2
    assert len(page.results) == 2
    first = page.results[0]
    assert first.id == "tjsp-cjsg-20787558-0"
    assert first.court == "TJSP"
    assert first.type == "acordao"
    assert first.number == "0003938-14.2017.8.26.0323"
    assert first.rapporteur == "Airton Vieira"
    assert first.updated_at == "30/07/2026"
    assert first.publication_date is None
    assert first.access_status.value == "public"
    assert first.raw["classe"] == "Apelacao Criminal"
    assert first.raw["assunto"] == "Homicidio Qualificado"
    assert first.raw["comarca"] == "Lorena"
    assert first.raw["orgao_julgador"] == "3a Camara de Direito Criminal"
    assert first.raw["full_text_url"].endswith("getArquivo.do?cdAcordao=20787558&cdForo=0")


def test_provider_search_posts_cjsg_payload_and_parses_results():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = TjspCjsgProvider(session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="infanticidio",
            exact_phrase="homicidio",
            number="0003938-14.2017.8.26.0323",
            types=["acordao"],
            updated_from="01/01/2026",
            updated_to="31/12/2026",
            page_size=2,
        )
    )

    assert page.results[0].id == "tjsp-cjsg-20787558-0"
    call = session.calls[0]
    payload = call["kwargs"]["data"]
    assert call["method"] == "POST"
    assert call["url"] == "https://esaj.tjsp.jus.br/cjsg/resultadoCompleta.do"
    assert payload["dados.buscaInteiroTeor"] == "infanticidio"
    assert payload["dados.buscaEmenta"] == "homicidio"
    assert payload["dados.nuProcOrigem"] == "0003938-14.2017.8.26.0323"
    assert payload["tipoDecisaoSelecionados"] == ["A"]
    assert payload["dados.dtJulgamentoInicio"] == "01/01/2026"


def test_provider_search_uses_troca_de_pagina_after_public_result_session():
    session = FakeSession([FakeResponse(_fixture_html()), FakeResponse(_cjsg_page_fragment())])
    provider = TjspCjsgProvider(session=session)

    page = provider.search(JurisprudenceQuery(text="infanticidio", page=2, page_size=5))

    assert len(page.results) == 1
    assert page.total == 858
    assert page.start == 21
    assert page.end == 21
    assert page.results[0].id == "tjsp-cjsg-20588041-0"
    assert page.results[0].source_trace is not None
    assert page.results[0].source_trace.endpoint == "/trocaDePagina.do"
    assert session.calls[0]["method"] == "POST"
    assert session.calls[1]["method"] == "GET"
    assert session.calls[1]["url"].endswith("trocaDePagina.do?tipoDeDecisao=A&pagina=2")


def test_provider_get_decisions_builds_getarquivo_url_and_extracts_text():
    session = FakeSession([FakeResponse(_fixture("tjsp_cjsg_document.html"))])
    provider = TjspCjsgProvider(session=session)

    bundle = provider.get_decisions("tjsp-cjsg-20787558-0")

    assert bundle.precedent_id == "tjsp-cjsg-20787558-0"
    assert bundle.texts[0]["content_type"] == "text/plain"
    assert "Apelacao Criminal n. 0003938-14.2017.8.26.0323" in bundle.texts[0]["content"]
    assert "window.analytics" not in bundle.texts[0]["content"]
    assert bundle.raw["source_content_type"] == "text/html"
    assert bundle.raw["text_characters"] > 120
    assert bundle.raw["raw_content_sha256"]
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["url"].endswith("getArquivo.do?cdAcordao=20787558&cdForo=0")


def test_provider_get_document_returns_canonical_document():
    session = FakeSession([FakeResponse(_fixture("tjsp_cjsg_document.html"))])
    provider = TjspCjsgProvider(session=session)

    document = provider.get_document("tjsp-cjsg-20787558-0")

    assert document.id == "tjsp-cjsg-20787558-0"
    assert document.source == "tjsp_cjsg"
    assert document.document_type == "acordao"
    assert document.content_type == "text/html"
    assert document.title == "Inteiro Teor - TJSP"
    assert document.text is not None
    assert "Homicidio qualificado" in document.text
    assert document.sha256 is not None
    assert document.byte_size == document.raw_metadata["raw_content_bytes"]
    assert document.raw_bytes is not None
    assert document.extraction_trace is not None
    assert document.extraction_trace.metadata["cd_acordao"] == "20787558"
    assert document.raw_metadata["cd_foro"] == "0"


def test_extract_cjsg_document_text_marks_pdf_as_unparsed():
    text, metadata = extract_cjsg_document_text("%PDF-1.4 fake public bytes")

    assert text == ""
    assert metadata["source_content_type"] == "application/pdf"
    assert metadata["warnings"] == [
        "CJSG returned PDF bytes; NanoJuris preserves metadata but does not parse PDF text yet."
    ]


def test_extract_cjsg_document_text_marks_short_access_control_text():
    text, metadata = extract_cjsg_document_text("<html><body>captcha</body></html>")

    assert text == "captcha"
    assert metadata["access_status"] == AccessStatus.ACCESS_CONTROL_REQUIRED.value
    assert metadata["warnings"] == [
        "CJSG document response contains captcha/access-control text.",
        "CJSG document text is unusually short for a full-text decision.",
    ]


def test_extract_cjsg_document_text_marks_login_verification_page():
    html = """
    <html>
      <script src="https://esaj.tjsp.jus.br/sajcas/verificarLogin.js"></script>
      <script>
        if (window.sajcas && window.sajcas.usuarioLogadoNoCasServer) {
          var urlRetornoSistema = '/cjsg/getArquivo.do?cdAcordao=20787558&cdForo=0';
        }
      </script>
    </html>
    """

    text, metadata = extract_cjsg_document_text(html)

    assert text == ""
    assert metadata["access_status"] == AccessStatus.LOGIN_REQUIRED.value
    assert metadata["warnings"] == [
        "CJSG document response is a login/access verification page.",
        "CJSG document text is unusually short for a full-text decision.",
    ]


def test_provider_get_document_marks_short_document_as_partial():
    session = FakeSession([FakeResponse("<html><body>curto</body></html>")])
    provider = TjspCjsgProvider(session=session)

    document = provider.get_document("tjsp-cjsg-20787558-0")

    assert document.text == "curto"
    assert document.extraction_trace is not None
    assert document.extraction_trace.status == ExtractionStatus.PARTIAL
    assert document.extraction_trace.warnings == [
        "CJSG document text is unusually short for a full-text decision."
    ]


def test_provider_get_document_marks_login_verification_status():
    html = """
    <html>
      <script src="https://esaj.tjsp.jus.br/sajcas/verificarLogin.js"></script>
      <script>
        if (window.sajcas && window.sajcas.usuarioLogadoNoCasServer) {
          var urlRetornoSistema = '/cjsg/getArquivo.do?cdAcordao=20787558&cdForo=0';
        }
      </script>
    </html>
    """
    session = FakeSession([FakeResponse(html)])
    provider = TjspCjsgProvider(session=session)

    document = provider.get_document("tjsp-cjsg-20787558-0")

    assert document.access_status == AccessStatus.LOGIN_REQUIRED
    assert document.extraction_trace is not None
    assert document.extraction_trace.access_status == AccessStatus.LOGIN_REQUIRED
    assert document.extraction_trace.status == ExtractionStatus.PARTIAL


def test_provider_detects_access_control_without_bypass():
    session = FakeSession([FakeResponse(_fixture("tjsp_cjsg_access_control.html"))])
    provider = TjspCjsgProvider(session=session)

    with pytest.raises(AccessControlRequiredError, match="has_recaptcha_field"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_diagnose_cjsg_access_identifies_returned_form_with_captcha_fields():
    html = _fixture("tjsp_cjsg_access_control.html")

    diagnostic = diagnose_cjsg_access(html)

    assert diagnostic.access_control_required is True
    assert diagnostic.returned_to_search_form is True
    assert diagnostic.has_search_form is True
    assert diagnostic.has_recaptcha_field is True
    assert diagnostic.has_uuid_captcha_field is True
    assert diagnostic.has_access_control_route is True
    assert diagnostic.has_login_script is True
    assert diagnostic.has_empty_session is False


def test_provider_classifies_empty_session_pagination_as_access_control():
    html = """
    <html>
      <body>
        <h1>HTTP Status 404</h1>
        <p>Message JSP file [/jsp/completa/emptySession.jsp] not found</p>
      </body>
    </html>
    """
    provider = TjspCjsgProvider(session=FakeSession([FakeResponse(html, status_code=404)]))

    with pytest.raises(AccessControlRequiredError, match="active public search session"):
        provider.search(JurisprudenceQuery(text="teste", page=2))


def test_parse_cjsg_results_accepts_empty_result_page():
    page = parse_cjsg_results(
        _fixture("tjsp_cjsg_empty.html"),
        query=JurisprudenceQuery(text="termo sem resultado"),
        trace=SourceTrace(provider="tjsp_cjsg", endpoint="/resultadoCompleta.do"),
        base_url="https://esaj.tjsp.jus.br/cjsg",
    )

    assert page.source == "tjsp_cjsg"
    assert page.total == 0
    assert page.results == []


def test_diagnose_cjsg_access_does_not_flag_result_page_as_blocked():
    html = """
    <html>
        <div id="divDadosResultado-A">
            <a class="downloadEmenta" cdAcordao="1" cdForo="0">
                0000000-00.2026.8.26.0000
            </a>
        </div>
        <input name="recaptcha_response_token" />
    </html>
    """

    diagnostic = diagnose_cjsg_access(html)

    assert diagnostic.has_result_container is True
    assert diagnostic.has_download_links is True
    assert diagnostic.access_control_required is False


def test_parser_detects_missing_result_contract():
    with pytest.raises(ParserContractChangedError):
        parse_cjsg_results(
            "<html><body>sem resultados</body></html>",
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="tjsp_cjsg", endpoint="/resultadoCompleta.do"),
            base_url="https://esaj.tjsp.jus.br/cjsg",
        )


def test_invalid_tjsp_precedent_id_is_rejected():
    provider = TjspCjsgProvider(session=FakeSession([]))

    with pytest.raises(ParserContractChangedError):
        provider.get_decisions("bad-id")


def test_request_exception_becomes_source_error():
    provider = TjspCjsgProvider(session=FakeSession([requests.RequestException("offline")]))

    with pytest.raises(Exception, match="TJSP/CJSG request failed"):
        provider.search(JurisprudenceQuery(text="teste"))
