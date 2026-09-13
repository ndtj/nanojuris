from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

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
from nanojuris.providers.tjpe_jurisprudencia import (
    TjpeJurisprudenciaProvider,
    build_tjpe_jsf_form_body,
    build_tjpe_search_parameters,
    extract_tjpe_jsf_pagination_ids,
    extract_tjpe_jsf_submit_id,
    extract_tjpe_jsf_viewstate,
    parse_tjpe_jsf_results,
    parse_tjpe_search_response,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjpe_jurisprudencia_results.json"


class FakeResponse:
    def __init__(
        self,
        data: Any = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        url: str = "https://consultajurisprudencia.app.tjpe.jus.br/api/v1/jurisprudencias",
    ) -> None:
        self._data = data
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}
        self.url = url
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        if self._data is None:
            raise ValueError("not json")
        return self._data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


class HtmlResponse:
    def __init__(self, html: str, url: str) -> None:
        self.status_code = 200
        self.url = url
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.content = html.encode("utf-8")
        self.text = html
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"


def load_html_fixture(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


def load_fixture() -> list[dict[str, Any]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def trace() -> SourceTrace:
    return SourceTrace(
        provider="tjpe_jurisprudencia",
        endpoint="GET /api/v1/jurisprudencias",
        source_url="https://consultajurisprudencia.app.tjpe.jus.br/api/v1/jurisprudencias",
    )


def test_tjpe_parser_preserves_text_and_normalizes_dates() -> None:
    page = parse_tjpe_search_response(
        load_fixture(),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=2),
        trace=trace(),
        reported_total=2,
    )

    assert page.total == 2
    assert page.is_complete is True
    assert [result.id for result in page.results] == [
        "tjpe-juris-fixture-1",
        "tjpe-juris-fixture-2",
    ]
    first = page.results[0]
    assert first.judgment_date == "2026-08-15"
    assert first.publication_date == "2026-08-16"
    assert first.summary == "Ementa publica de fixture."
    assert first.full_text == "Inteiro teor publico de fixture."
    assert (first.degree, first.instance, first.branch, first.authority, first.collection) == (
        "second",
        "second",
        "state",
        "TJPE",
        "CJSG",
    )
    assert first.raw["textoAcordao"].startswith("<p>")
    assert first.access_status.value == "public"


def test_search_caches_inline_result_for_decisions_and_document() -> None:
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture())]),
        transport="rest",
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page_size=1))
    result = page.results[0]
    bundle = provider.get_decisions(result.id)
    document = provider.get_document(result.id)

    assert bundle.texts and bundle.texts[0]["text"] == result.full_text
    assert document.text == result.full_text
    assert len(provider.session.calls) == 1


def test_decisions_reject_unobserved_id() -> None:
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]), transport="rest"
    )
    with pytest.raises(ValueError, match="observed"):
        provider.get_decisions("not-observed")


def test_tjpe_builds_observed_zero_based_parameters() -> None:
    params = build_tjpe_search_parameters(
        JurisprudenceQuery(
            text="dano moral",
            number="0000001-23.2024.8.17.0001",
            published_from="01/01/2024",
            published_to="31/12/2024",
            types=["A"],
            order_by="date_desc",
            page=2,
            page_size=25,
        )
    )

    assert params["page"] == 1
    assert params["size"] == 25
    assert params["pesquisaLivre.contains"] == "dano moral"
    assert params["npuSemFormatacao.equals"] == "00000012320248170001"
    assert params["dataJulgamento.greaterThanOrEqual"] == "2024-01-01"
    assert params["dataJulgamento.lessThanOrEqual"] == "2024-12-31"
    assert params["tipoSentenca.in"] == ["A"]
    assert params["sort"] == "dataJulgamento,desc"


def test_tjpe_canonical_class_and_rapporteur_filters_use_jsf_contract() -> None:
    from nanojuris.providers.tjpe_jurisprudencia import build_tjpe_jsf_form_body

    body = build_tjpe_jsf_form_body(
        JurisprudenceQuery(
            text="dano moral",
            case_class="APELAÇÃO CÍVEL",
            rapporteur="Desembargador Exemplo",
        ),
        viewstate="state-token",
        submit_id="formPesquisaJurisprudencia:submit",
    )

    assert body["formPesquisaJurisprudencia:selectClasseCNJ"] == "APELAÇÃO CÍVEL"
    assert body["formPesquisaJurisprudencia:selectRelator"] == "Desembargador Exemplo"


def test_tjpe_provider_preserves_trace_and_remote_total() -> None:
    session = FakeSession(
        [
            FakeResponse(
                load_fixture(),
                headers={"X-Total-Count": "42", "Content-Type": "application/json"},
            )
        ]
    )
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=2))

    assert page.total == 42
    assert page.page == 2
    assert page.start == 3
    assert page.source_trace is not None
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes
    assert session.calls[0]["kwargs"]["params"]["page"] == 1
    assert session.calls[0]["kwargs"]["verify"] is True


def test_tjpe_rejects_missing_stable_key_and_wrong_root() -> None:
    with pytest.raises(ParserContractChangedError, match="stable key"):
        parse_tjpe_search_response(
            [{"textoEmenta": "sem chave"}],
            query=JurisprudenceQuery(text="teste"),
            trace=trace(),
        )

    with pytest.raises(ParserContractChangedError, match="result root"):
        parse_tjpe_search_response(  # type: ignore[arg-type]
            {}, query=JurisprudenceQuery(text="teste"), trace=trace()
        )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (429, RateLimitDetectedError),
        (400, QueryRejectedError),
        (500, SourceUnavailableError),
    ],
)
def test_tjpe_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status)]),
    )

    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_tjpe_is_registered_and_declares_public_contract() -> None:
    client = NanoJurisClient()
    assert "tjpe_jurisprudencia" in client.providers
    assert client.providers["tjpe_jurisprudencia"].transport == "auto"
    assert TjpeJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0)).transport == "auto"
    capabilities = client.providers["tjpe_jurisprudencia"].get_capabilities()
    assert capabilities.pagination_mode == "offset"
    assert capabilities.supports_full_text is True
    assert capabilities.supports_unified_search is True
    assert capabilities.filter_status("rapporteur") == "translated"
    assert capabilities.filter_status("case_class") == "translated"
    assert capabilities.filter_status("judgment_date_from") == "translated"
    assert "GET /api/v1/jurisprudencias" in capabilities.endpoints


def test_tjpe_jsf_helpers_build_stateful_form_without_exposing_viewstate() -> None:
    search_html = load_html_fixture("tjpe_juscraper_search.html")
    assert extract_tjpe_jsf_viewstate(search_html) == "VIEWSTATE-SEARCH"
    assert extract_tjpe_jsf_submit_id(search_html) == "formPesquisaJurisprudencia:j_id101"
    form = build_tjpe_jsf_form_body(
        JurisprudenceQuery(text="dano moral", published_from="2026-01-02"),
        viewstate="VIEWSTATE-SEARCH",
        submit_id="formPesquisaJurisprudencia:j_id101",
    )
    assert form["formPesquisaJurisprudencia:inputBuscaSimples"] == "dano moral"
    assert form["formPesquisaJurisprudencia:j_id59InputDate"] == "02/01/2026"
    assert form["javax.faces.ViewState"] == "VIEWSTATE-SEARCH"


def test_tjpe_jsf_transport_maps_results_and_preserves_route_trace() -> None:
    session = FakeSession(
        [
            HtmlResponse(
                load_html_fixture("tjpe_juscraper_search.html"),
                "https://www.tjpe.jus.br/consultajurisprudenciaweb/xhtml/consulta/consulta.xhtml",
            ),
            HtmlResponse(
                load_html_fixture("tjpe_juscraper_results_ascii.html"),
                "https://www.tjpe.jus.br/consultajurisprudenciaweb/xhtml/consulta/consulta.xhtml",
            ),
        ]
    )
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session, transport="jsf"
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page_size=2))

    assert page.total == 2
    assert page.results[0].id == "tjpe-juris-00000012320268170001"
    assert page.results[0].summary == "Ementa publica de fixture."
    assert page.results[0].full_text == "Inteiro teor publico de fixture."
    assert page.results[0].degree == "second"
    assert page.results[0].instance == "second"
    assert page.results[0].collection == "CJSG"
    assert page.source_trace is not None
    assert page.source_trace.endpoint == "POST /consulta.xhtml"
    assert page.source_trace.query["transport"] == "jsf"
    assert len(session.calls) == 2
    assert session.calls[1]["kwargs"]["data"]["javax.faces.ViewState"] == "VIEWSTATE-SEARCH"


def test_tjpe_jsf_choice_and_ajax_pagination_follow_juscraper_contract() -> None:
    result_html = load_html_fixture("tjpe_juscraper_results_ascii.html")
    session = FakeSession(
        [
            HtmlResponse(
                load_html_fixture("tjpe_juscraper_search.html"), "https://tjpe.test/consulta.xhtml"
            ),
            HtmlResponse(
                load_html_fixture("tjpe_juscraper_choice_ascii.html"),
                "https://tjpe.test/consulta.xhtml",
            ),
            HtmlResponse(result_html, "https://tjpe.test/escolhaResultado.xhtml"),
            HtmlResponse(result_html, "https://tjpe.test/resultado.xhtml"),
        ]
    )
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session, transport="jsf"
    )

    page = provider.search(JurisprudenceQuery(text="teste", types=["acordao", "decisao"], page=2))

    assert page.page == 2
    assert len(page.results) == 2
    assert [call["method"] for call in session.calls] == ["GET", "POST", "POST", "POST"]
    assert session.calls[2]["url"].endswith("/escolhaResultado.xhtml")
    assert session.calls[3]["url"].endswith("/resultado.xhtml")
    assert session.calls[3]["kwargs"]["headers"]["X-Requested-With"] == "XMLHttpRequest"
    assert extract_tjpe_jsf_pagination_ids(result_html) == ("j_id81", "j_id81:j_id87")


def test_tjpe_jsf_empty_is_explicit_and_not_parser_failure() -> None:
    trace_value = SourceTrace(provider="tjpe_jurisprudencia", endpoint="POST /consulta.xhtml")
    page = parse_tjpe_jsf_results(
        load_html_fixture("tjpe_juscraper_empty.html"),
        query=JurisprudenceQuery(text="sem resultado"),
        trace=trace_value,
    )
    assert page.results == []
    assert page.total == 0
    assert page.completeness_reason == "explicit_zero_marker"


def test_tjpe_auto_falls_back_only_for_transport_failure() -> None:
    class RestThenJsfSession(FakeSession):
        def request(self, method: str, url: str, **kwargs: Any) -> Any:
            self.calls.append({"method": method, "url": url, "kwargs": kwargs})
            if "/api/v1/" in url:
                import requests

                raise requests.RequestException("TLS handshake failed")
            if method == "GET":
                fixture_name = "tjpe_juscraper_search.html"
            else:
                fixture_name = "tjpe_juscraper_results_ascii.html"
            return HtmlResponse(
                load_html_fixture(fixture_name),
                url,
            )

    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=RestThenJsfSession([]),
        transport="auto",
    )
    page = provider.search(JurisprudenceQuery(text="teste"))
    assert page.results
    assert page.source_trace is not None
    assert page.source_trace.query["fallback"] == "rest_transport_failure"


def test_tjpe_auto_preserves_jsf_access_control_signal() -> None:
    class FailingRestThenBlockedJsf:
        def __init__(self) -> None:
            self.calls = 0

        def request(self, method: str, url: str, **kwargs: Any) -> Any:
            self.calls += 1
            if "/api/v1/" in url:
                import requests

                raise requests.RequestException("TLS handshake failed")
            return HtmlResponse("<html><body>captcha</body></html>", url)

    session = FailingRestThenBlockedJsf()
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session, transport="auto"
    )

    with pytest.raises(AccessControlRequiredError, match="TJPE JSF"):
        provider.search(JurisprudenceQuery(text="teste"))
