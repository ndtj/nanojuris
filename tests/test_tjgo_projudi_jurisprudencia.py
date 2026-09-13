from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjgo_projudi_jurisprudencia import (
    TjgoProjudiJurisprudenciaProvider,
    parse_tjgo_results,
    tjgo_result_to_document,
)
from nanojuris.quality import validate_record

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.content = text.encode("iso-8859-1", errors="replace")
        self.status_code = status_code
        self.encoding = "iso-8859-1"


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


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="iso-8859-1")


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="tjgo_projudi_jurisprudencia",
        endpoint="/ConsultaJurisprudencia",
        query={"Texto": "dano moral"},
        source_url="https://projudi.tjgo.jus.br/ConsultaJurisprudencia",
        limitations=[],
    )


def test_parse_tjgo_results_maps_public_projudi_html_without_redaction():
    page = parse_tjgo_results(
        load_fixture("tjgo_projudi_dano_moral.html"),
        query=JurisprudenceQuery(text="dano moral", page_size=3),
        trace=_trace(),
        base_url="https://projudi.tjgo.jus.br",
    )

    assert page.source == "tjgo_projudi_jurisprudencia"
    assert page.total == 1357644
    assert page.start == 1
    assert page.end == 3
    assert len(page.results) == 3
    result = page.results[0]
    assert result.id == "tjgo-projudi-5692569-32.2026.8.09.0038"
    assert result.court == "TJGO"
    assert result.type == "decisao"
    assert result.number == "5692569-32.2026.8.09.0038"
    assert result.updated_at == "07/08/2026 03:10:24"
    assert result.rapporteur == "GUSTAVO BOIAGO BRIGATTI DIAS - (JUIZ 1º GRAU)"
    assert result.raw["judging_body"] == "Crixás - Vara das Fazendas Públicas"
    assert result.raw["file_id"] == "549973404"
    assert result.judging_body == result.raw["judging_body"]
    assert result.authority == "TJGO"
    assert result.branch == "state"
    assert result.collection == "JURISPRUDENCIA"
    assert result.document_type == result.type
    assert "CPF/CNPJ" in (result.summary or "")


def test_parse_tjgo_empty_search_returns_empty_page():
    page = parse_tjgo_results(
        load_fixture("tjgo_projudi_empty.html"),
        query=JurisprudenceQuery(text="zzznanojurissemresultado", page_size=5),
        trace=_trace(),
        base_url="https://projudi.tjgo.jus.br",
    )

    assert page.total == 0
    assert page.results == []
    assert page.total_known is False
    assert page.effective_total is None
    assert page.is_complete is None


def test_parse_tjgo_does_not_treat_publication_date_as_decision_type():
    html = """
    <html><body>1 resultados encontrados
      <div class="search-result">
        <h4>1234567-89.2026.8.09.0001</h4>
        <p>Unidade judicial</p>
        <p>Magistrado</p>
        <p>Publicado em 07/08/2026 03:10:24</p>
        <p>Decisão</p>
        <p class="conteudoTexto">Texto público da decisão.</p>
      </div>
    </body></html>
    """

    page = parse_tjgo_results(
        html,
        query=JurisprudenceQuery(text="decisao", page_size=1),
        trace=_trace(),
        base_url="https://projudi.tjgo.jus.br",
    )

    assert page.results[0].type == "decisao"
    assert page.results[0].updated_at == "07/08/2026 03:10:24"


def test_provider_search_posts_public_projudi_payload():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )

    page = provider.search(
        JurisprudenceQuery(
            text="dano moral",
            number="5692569-32.2026.8.09.0038",
            source_origin="primeiro grau",
            types=["decisao"],
            updated_from="01/08/2026",
            updated_to="07/08/2026",
            page_size=1,
        )
    )

    assert page.results[0].source == "tjgo_projudi_jurisprudencia"
    call = provider.session.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "https://projudi.tjgo.jus.br/ConsultaJurisprudencia"
    payload = call["kwargs"]["data"]
    assert payload["Texto"] == "dano moral"
    assert payload["PaginaAtual"] == "2"
    assert payload["PosicaoPaginaAtual"] == "0"
    assert payload["ProcessoNumero"] == "5692569-32.2026.8.09.0038"
    assert payload["Id_Instancia"] == "16"
    assert payload["Id_ArquivoTipo"] == "4"
    assert payload["DataInicial"] == "01/08/2026"
    assert payload["DataFinal"] == "07/08/2026"


def test_tjgo_first_degree_binding_promotes_only_first_unit_cards():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", collection="CJPG", page_size=3))

    assert page.results
    assert all(item.degree == "first" for item in page.results)
    assert all(item.instance == "first" for item in page.results)
    assert all(item.collection == "CJPG" for item in page.results)
    assert all(item.source_origin == "16" for item in page.results)
    assert all(item.summary or item.full_text for item in page.results)
    assert provider.session.calls[0]["kwargs"]["data"]["Id_Instancia"] == "16"


def test_tjgo_first_degree_binding_is_available_through_federated_route():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )
    payload = NanoJurisClient(providers=[provider]).search_many(
        sources=["tjgo_projudi_jurisprudencia"],
        text="dano moral",
        collection="CJPG",
        page_size=3,
    )

    assert payload["errors"] == []
    assert payload["searched_sources"] == ["tjgo_projudi_jurisprudencia"]
    assert payload["results"]
    assert all(item.degree == "first" for item in payload["results"])
    assert all(item.collection == "CJPG" for item in payload["results"])


def test_provider_search_maps_one_based_page_to_projudi_position():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )

    provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=1))
    payload = provider.session.calls[0]["kwargs"]["data"]
    assert payload["PaginaAtual"] == "2"
    assert payload["PosicaoPaginaAtual"] == "1"


@pytest.mark.parametrize(
    ("degree", "expected"),
    [("second", "15"), ("second degree", "15"), ("first", "16"), ("first degree", "16")],
)
def test_provider_maps_canonical_degree_aliases_to_projudi_instance(degree, expected):
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )

    provider.search(JurisprudenceQuery(text="dano moral", degree=degree, page_size=1))

    payload = provider.session.calls[0]["kwargs"]["data"]
    assert payload["Id_Instancia"] == expected


def test_provider_search_emits_http_trace_metadata():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes == len(
        load_fixture("tjgo_projudi_dano_moral.html").encode("iso-8859-1")
    )
    assert page.source_trace.elapsed_ms is not None
    assert page.source_trace.retrieval_status == "ok"


def test_provider_fetches_public_document_by_projudi_file_id():
    html = """
    <html><body><div class="conteudoTexto">Inteiro teor público do acórdão.</div></body></html>
    """
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(html)]),
    )

    document = provider.get_document("549973404")

    assert document.text == "Inteiro teor público do acórdão."
    assert document.raw_bytes is not None
    assert document.byte_size == len(document.raw_bytes)
    assert document.url and "Id_Arquivo=549973404" in document.url
    call = provider.session.calls[0]
    assert call["method"] == "POST"
    assert call["kwargs"]["params"]["Id_Arquivo"] == "549973404"


def test_provider_rejects_non_numeric_projudi_document_id():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    )
    with pytest.raises(ValueError, match="numeric"):
        provider.get_document("tjgo-projudi-invalid")


def test_tjgo_results_canonicalize_as_decisions_with_full_text():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )

    records = search_page_to_canonical(
        provider.search(JurisprudenceQuery(text="dano moral", page_size=1))
    )

    assert len(records) == 1
    assert records[0].source == "tjgo_projudi_jurisprudencia"
    assert records[0].court == "TJGO"
    assert records[0].case_number == "5047949-18.2023.8.09.0093"
    assert records[0].decision_type == "decisao"
    assert records[0].degree == "second"
    assert records[0].instance == "second"
    assert records[0].collection == "CJSG"
    assert records[0].document_type == "acordao"
    assert records[0].judging_body == "5ª Câmara Cível"
    assert records[0].summary and "AGRAVO INTERNO" in records[0].summary
    assert records[0].full_text and "AGRAVO INTERNO" in records[0].full_text
    assert validate_record(records[0]) == ()


def test_result_to_document_preserves_embedded_public_text():
    page = parse_tjgo_results(
        load_fixture("tjgo_projudi_dano_moral.html"),
        query=JurisprudenceQuery(text="dano moral", page_size=1),
        trace=_trace(),
        base_url="https://projudi.tjgo.jus.br",
    )

    document = tjgo_result_to_document(page.results[0])

    assert document.source == "tjgo_projudi_jurisprudencia"
    assert document.document_type == "decisao"
    assert document.text and "CPF/CNPJ" in document.text
    assert document.raw_metadata["file_id"] == "549973404"
    assert document.sha256


def test_search_caches_inline_result_for_decisions_and_document():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjgo_projudi_dano_moral.html"))]),
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))
    result = page.results[0]
    bundle = provider.get_decisions(result.id)
    document = provider.get_document(result.id)

    assert bundle.texts and bundle.texts[0]["text"] == result.full_text
    assert document.text == result.full_text
    assert len(provider.session.calls) == 1


def test_decisions_reject_unobserved_id():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    )

    with pytest.raises(ValueError, match="observed"):
        provider.get_decisions("not-observed")


@pytest.mark.parametrize(
    ("response", "expected_error"),
    [
        (FakeResponse("", 429), RateLimitDetectedError),
        (FakeResponse("", 403), AccessControlRequiredError),
        (FakeResponse("", 500), SourceUnavailableError),
        (FakeResponse("", 400), SourceUnavailableError),
        (FakeResponse("<html><div class='g-recaptcha'></div></html>"), AccessControlRequiredError),
    ],
)
def test_search_errors_are_normalized(response, expected_error):
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    with pytest.raises(expected_error):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_request_exception_is_normalized():
    provider = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )

    with pytest.raises(SourceUnavailableError, match="offline"):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_parse_tjgo_raises_when_total_exists_without_parseable_cards():
    html = (
        "<html><body>10 resultados encontrados"
        "<div class='search-result'>sem cnj</div></body></html>"
    )

    with pytest.raises(ParserContractChangedError):
        parse_tjgo_results(
            html,
            query=JurisprudenceQuery(text="dano moral"),
            trace=_trace(),
            base_url="https://projudi.tjgo.jus.br",
        )


def test_capabilities_describe_tjgo_provider():
    capabilities = TjgoProjudiJurisprudenciaProvider().get_capabilities()

    assert capabilities.source == "tjgo_projudi_jurisprudencia"
    assert capabilities.category == "court_jurisprudence"
    assert "full_text" in capabilities.search_modes
    assert "CanonicalDecision" in capabilities.canonical_records
    assert capabilities.supports_full_text is True
    assert capabilities.full_text_access == "inline_result_text"
    assert {"id", "document_url", "updated_at"} <= set(capabilities.extracted_fields)
