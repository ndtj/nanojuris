from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
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
    assert payload["ProcessoNumero"] == "5692569-32.2026.8.09.0038"
    assert payload["Id_Instancia"] == "16"
    assert payload["Id_ArquivoTipo"] == "4"
    assert payload["DataInicial"] == "01/08/2026"
    assert payload["DataFinal"] == "07/08/2026"


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
    assert records[0].case_number == "5692569-32.2026.8.09.0038"
    assert records[0].decision_type == "decisao"
    assert records[0].judging_body == "Crixás - Vara das Fazendas Públicas"
    assert records[0].summary and "CPF/CNPJ" in records[0].summary
    assert records[0].full_text and "CPF/CNPJ" in records[0].full_text


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


@pytest.mark.parametrize(
    ("response", "expected_error"),
    [
        (FakeResponse("", 429), RateLimitDetectedError),
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
    assert capabilities.supports_full_text is False
