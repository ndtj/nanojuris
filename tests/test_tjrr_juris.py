from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjrr_juris import (
    TjrrJurisProvider,
    extract_tjrr_document_text,
    parse_tjrr_results,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        body: str,
        url: str = "https://jurisprudencia.tjrr.jus.br/index.xhtml",
        status_code: int = 200,
    ):
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": "text/html; charset=UTF-8"}
        self._content = body.encode("utf-8")
        self.text = body
        self.content = self._content


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_tjrr_result_maps_metadata_and_full_text():
    page = parse_tjrr_results(
        _fixture("tjrr_juris_result.html"),
        query=JurisprudenceQuery(text="dano moral", page_size=1),
        trace=SourceTrace(provider="tjrr_juris", endpoint="/index.xhtml"),
        base_url="https://jurisprudencia.tjrr.jus.br",
    )

    result = page.results[0]
    assert page.total == 2
    assert page.pagination_mode == "page"
    assert page.is_complete is False
    assert result.id == "tjrr-juris-321"
    assert result.number == "0000001-23.2026.8.23.0001"
    assert result.summary == "Ementa publica de fixture."
    assert result.full_text == "Texto integral publico de fixture."
    assert result.raw["case_class"] == "Apelacao Civel"
    assert result.raw["judging_body"] == "Câmara de Fixture"
    assert result.raw["document_url"] == "/inteiroTeor.xhtml?id=321"


def test_provider_posts_public_form_and_supports_primefaces_page_request():
    result = _fixture("tjrr_juris_result.html")
    page_two_result = result.replace("(1 of 2)", "(2 of 2)").replace("id=321", "id=320")
    partial = (
        '<partial-response><changes><update id="table"><![CDATA['
        f"{page_two_result}"
        "]]></update></changes></partial-response>"
    )
    session = FakeSession(
        [
            FakeResponse(_fixture("tjrr_juris_form.html")),
            FakeResponse(result),
            FakeResponse(partial),
        ]
    )
    provider = TjrrJurisProvider(session=session)

    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=1))

    assert page.results[0].number == "0000001-23.2026.8.23.0001"
    assert [call["method"] for call in session.calls] == ["GET", "POST", "POST"]
    ajax = session.calls[2]["kwargs"]
    assert isinstance(ajax, dict)
    assert ajax["headers"]["Faces-Request"] == "partial/ajax"
    assert ajax["data"]["formPesquisa:j_idt155:dataTablePesquisa_first"] == "1"


def test_provider_reuses_public_result_form_for_second_page_in_same_session():
    result = _fixture("tjrr_juris_result.html")
    page_two_result = result.replace("(1 of 2)", "(2 of 2)").replace("id=321", "id=320")
    partial = (
        '<partial-response><changes><update id="table"><![CDATA['
        f"{page_two_result}"
        "]]></update></changes></partial-response>"
    )
    session = FakeSession(
        [
            FakeResponse(_fixture("tjrr_juris_form.html")),
            FakeResponse(result),
            FakeResponse(result),
            FakeResponse(partial),
        ]
    )
    provider = TjrrJurisProvider(session=session)

    provider.search(JurisprudenceQuery(text="dano moral", page=1, page_size=1))
    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=1))

    assert page.results[0].id == "tjrr-juris-320"
    assert [call["method"] for call in session.calls] == ["GET", "POST", "GET", "POST"]
    assert session.calls[-1]["kwargs"]["headers"]["Faces-Request"] == "partial/ajax"


def test_parser_caps_rows_to_source_reported_page_size():
    fixture = _fixture("tjrr_juris_result.html")
    page = parse_tjrr_results(
        fixture + fixture,
        query=JurisprudenceQuery(text="dano moral", page_size=1),
        trace=SourceTrace(provider="tjrr_juris", endpoint="/index.xhtml"),
        base_url="https://jurisprudencia.tjrr.jus.br",
    )

    assert page.page_size == 1
    assert len(page.results) == 1


def test_provider_get_document_uses_observed_public_id():
    session = FakeSession([FakeResponse(_fixture("tjrr_juris_detail.html"))])
    provider = TjrrJurisProvider(session=session)

    document = provider.get_document("tjrr-juris-321")

    assert document.text == "Inteiro teor Texto integral publico de fixture TJRR."
    assert session.calls[0]["url"].endswith("/inteiroTeor.xhtml?id=321")


def test_provider_rejects_unbounded_empty_search():
    provider = TjrrJurisProvider(session=FakeSession([]))

    with pytest.raises(QueryRejectedError, match="exige termo"):
        provider.search(JurisprudenceQuery())


def test_provider_exposes_explicit_capabilities():
    capabilities = TjrrJurisProvider(session=FakeSession([])).get_capabilities()

    assert capabilities.source == "tjrr_juris"
    assert capabilities.supports_full_text is True
    assert capabilities.supports_unified_search is True
    assert capabilities.pagination_mode == "page"
    assert capabilities.max_remote_page_size == 10
    assert "number" in capabilities.supported_filters
    assert "GET /inteiroTeor.xhtml?id=<id>" in capabilities.endpoints


def test_provider_maps_number_and_query_filters_into_public_form():
    session = FakeSession(
        [
            FakeResponse(_fixture("tjrr_juris_form.html")),
            FakeResponse(_fixture("tjrr_juris_result.html")),
        ]
    )
    provider = TjrrJurisProvider(session=session)

    provider.search(
        JurisprudenceQuery(
            number="0000001-23.2026.8.23.0001",
            exact_phrase="dano moral",
            published_from="01/01/2026",
            published_to="31/12/2026",
        )
    )

    data = session.calls[1]["kwargs"]["data"]
    assert isinstance(data, dict)
    assert data["menuinicial:j_idt28"] == "dano moral"
    assert data["menuinicial:j_idt42"] == "0000001-23.2026.8.23.0001"


def test_provider_rejects_missing_public_form_and_invalid_document_id():
    provider = TjrrJurisProvider(session=FakeSession([FakeResponse("<html></html>")]))

    with pytest.raises(ParserContractChangedError, match="formulario publico"):
        provider.search(JurisprudenceQuery(text="termo"))

    with pytest.raises(ParserContractChangedError, match="id deve usar"):
        provider.get_decisions("tjrr-juris-invalid")


def test_parser_handles_empty_access_control_and_contract_change():
    query = JurisprudenceQuery(text="termo", page_size=10)
    trace = SourceTrace(provider="tjrr_juris", endpoint="/index.xhtml")

    empty = parse_tjrr_results(
        "<html><body>Nenhum resultado encontrado</body></html>",
        query=query,
        trace=trace,
        base_url="https://jurisprudencia.tjrr.jus.br",
    )
    assert empty.results == []
    assert empty.total == 0

    with pytest.raises(AccessControlRequiredError):
        parse_tjrr_results(
            "<html><body>captcha necessário</body></html>",
            query=query,
            trace=trace,
            base_url="https://jurisprudencia.tjrr.jus.br",
        )

    with pytest.raises(ParserContractChangedError, match="containers"):
        parse_tjrr_results(
            "<html><body>resposta inesperada</body></html>",
            query=query,
            trace=trace,
            base_url="https://jurisprudencia.tjrr.jus.br",
        )


def test_document_text_preserves_access_diagnostics():
    text, metadata = extract_tjrr_document_text("<html><body>captcha</body></html>")

    assert text == ""
    assert metadata["access_status"] == "access_control_required"
    assert metadata["warnings"]


def test_provider_classifies_http_failures_and_transport_errors():
    for status, expected in (
        (429, RateLimitDetectedError),
        (500, SourceUnavailableError),
        (400, SourceUnavailableError),
    ):
        provider = TjrrJurisProvider(session=FakeSession([FakeResponse("", status_code=status)]))
        with pytest.raises(expected):
            provider._request("GET", "/index.xhtml")

    class BrokenSession:
        def request(self, method: str, url: str, **kwargs: object) -> object:
            raise requests.RequestException("fixture transport failure")

    provider = TjrrJurisProvider(session=BrokenSession())  # type: ignore[arg-type]
    with pytest.raises(SourceUnavailableError, match="request failed"):
        provider._request("GET", "/index.xhtml")


def test_primefaces_pagination_uses_fallback_form_when_markup_has_no_form():
    partial = '<partial-response><changes><![CDATA[<div id="resultados1"></div>]]></changes>'
    session = FakeSession([FakeResponse(partial + "</partial-response>")])
    provider = TjrrJurisProvider(session=session)

    provider._request_page(
        "<html><body>sem formulario</body></html>",
        JurisprudenceQuery(text="termo", page=3, page_size=2),
        fallback_fields={"javax.faces.ViewState": "fixture"},
    )

    data = session.calls[0]["kwargs"]["data"]
    assert isinstance(data, dict)
    assert data["formPesquisa:j_idt155:dataTablePesquisa_first"] == "4"
    assert data["formPesquisa:j_idt155:dataTablePesquisa_rows"] == "2"
