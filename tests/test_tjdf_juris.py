from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import CanonicalDecision, JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjdf_juris import (
    TJDF_JURIS_API_ENDPOINT,
    TjdfJurisProvider,
    _build_api_payload,
    _build_initial_params,
    _build_results_params,
    _decode_response_text,
    parse_tjdf_api_response,
    parse_tjdf_detail,
    parse_tjdf_list_results,
    parse_tjdf_result_ids,
    parse_tjdf_total,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = None


class JsonFakeResponse(FakeResponse):
    def __init__(self, payload, status_code: int = 200):
        super().__init__(json.dumps(payload), status_code=status_code)
        self.headers = {"Content-Type": "application/json"}

    def json(self):
        return json.loads(self.text)


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


class RaisingSession:
    def request(self, method, url, **kwargs):
        raise requests.RequestException("offline")


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_tjdf_search_contract():
    assert parse_tjdf_total(load_fixture("tjdf_juris_initial.html")) == 31
    assert parse_tjdf_result_ids(load_fixture("tjdf_juris_results.html")) == ["1917641", "1907747"]


def test_decode_tjdf_prefers_utf8_when_server_omits_or_misreports_charset() -> None:
    payload = "Ação civil pública — responsabilidade".encode()

    assert _decode_response_text(payload, "text/html; charset=ISO-8859-1") == (
        "Ação civil pública — responsabilidade"
    )


def test_search_maps_tjdf_jurisprudence_result():
    session = FakeSession(
        [
            FakeResponse(load_fixture("tjdf_juris_initial.html")),
            FakeResponse(load_fixture("tjdf_juris_results.html")),
            FakeResponse(load_fixture("tjdf_juris_detail.html")),
        ]
    )
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(
        JurisprudenceQuery(text="infanticidio", page=1, page_size=1, fetch_details=True)
    )

    assert page.source == "tjdf_juris"
    assert page.total == 31
    assert page.start == 1
    assert page.end == 1
    assert len(page.results) == 1
    result = page.results[0]
    assert result.id == "tjdf-acordao-1917641"
    assert result.source == "tjdf_juris"
    assert result.court == "TJDFT"
    assert result.type == "acordao"
    assert result.number == "0722671-67.2024.8.07.0000"
    assert result.rapporteur == "SANDRA REVES"
    assert result.updated_at == "16/09/2024"
    assert result.status == "CONHECIDO. DESPROVIDO. UNANIME."
    assert "Infanticidio" in (result.summary or "")
    assert result.raw["registry_number"] == "1917641"
    assert result.raw["judging_body"] == "7 Turma Civel"
    assert result.raw["judgment_date"] == "04/09/2024"
    assert result.source_trace is not None
    assert result.source_trace.http_status == 200
    assert result.source_trace.response_bytes > 0
    assert result.source_trace.content_sha256
    assert result.source_trace.retrieval_status == "ok"
    assert result.access_status.value == "public"

    assert len(session.calls) == 3
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["kwargs"]["params"]["nomeDaPagina"] == "buscaLivre"
    assert session.calls[1]["kwargs"]["params"]["nomeDaPagina"] == "buscaLivre2"
    assert session.calls[2]["kwargs"]["params"]["numeroDoDocumento"] == "1917641"


def test_search_api_maps_zero_based_page_and_canonical_fields():
    payload = json.loads(load_fixture("tjdf_juris_api_results.json"))
    session = FakeSession([JsonFakeResponse(payload)])
    provider = TjdfJurisProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session, use_api=True
    )

    page = provider.search(
        JurisprudenceQuery(
            text="responsabilidade civil",
            page=2,
            page_size=2,
            number="0700001-00.2024.8.07.0001",
            rapporteur="MARIA TESTE",
        )
    )

    assert page.page == 2
    assert page.page_size == 2
    assert page.total == 2
    assert page.start == 3
    assert page.end == 4
    assert page.aggregations["base"][0]["nome"] == "ACORDAOS"
    result = page.results[0]
    assert result.id == "tjdf-api-11111111-1111-4111-8111-111111111111"
    assert result.number == "0700001-00.2024.8.07.0001"
    assert result.judgment_date == "2024-09-04"
    assert result.publication_date == "2024-09-16"
    assert result.updated_at == "2024-09-16"
    assert result.source_updated_at == "2024-09-16"
    assert result.judging_body == "1a Turma Civel"
    assert result.full_text == "Texto integral publico de teste."
    assert result.raw["campoDesconhecido"] == "preservar"
    assert result.source_trace is not None
    assert result.source_trace.endpoint == TJDF_JURIS_API_ENDPOINT
    assert result.source_trace.transformations == ["pagina_api_zero_based_convertida"]

    request = session.calls[0]
    assert request["method"] == "POST"
    assert request["url"].endswith("/api/v1/pesquisa")
    assert request["kwargs"]["json"]["pagina"] == 1
    assert request["kwargs"]["json"]["tamanho"] == 2
    assert request["kwargs"]["json"]["inteiroTeor"] is True
    assert request["kwargs"]["json"]["retornaInteiroTeor"] is True
    assert request["kwargs"]["json"]["espelho"] is True
    assert request["kwargs"]["json"]["termosAcessorios"] == [
        {"campo": "processo", "valor": "0700001-00.2024.8.07.0001"},
        {"campo": "nomeRelator", "valor": "MARIA TESTE"},
    ]
    assert page.results[1].full_text is None


def test_build_tjdf_api_payload_maps_documented_date_fields():
    payload = _build_api_payload(
        JurisprudenceQuery(
            text="dano moral",
            updated_from="2024-01-01",
            updated_to="2024-01-31",
            published_from="2024-02-01",
            published_to="2024-02-29",
            source_origin="PJe",
        )
    )

    assert payload["pagina"] == 0
    assert payload["termosAcessorios"] == [
        {"campo": "origem", "valor": "PJe"},
        {"campo": "dataJulgamento", "valor": "2024-01-01"},
        {"campo": "dataJulgamento", "valor": "2024-01-31"},
        {"campo": "dataPublicacao", "valor": "2024-02-01"},
        {"campo": "dataPublicacao", "valor": "2024-02-29"},
    ]


def test_build_tjdf_api_payload_maps_structured_filters_and_normalizes_dates():
    payload = _build_api_payload(
        JurisprudenceQuery(
            text="dano moral",
            source_origins=["PJe", "SISTJ"],
            case_class="Apelação Cível",
            judging_body="Segunda Turma Cível",
            judgment_date_from="01/02/2024",
            judgment_date_to="29/02/2024",
        )
    )

    assert payload["termosAcessorios"] == [
        {"campo": "descricaoClasseCnj", "valor": "Apelação Cível"},
        {"campo": "descricaoOrgaoJulgador", "valor": "Segunda Turma Cível"},
        {"campo": "dataJulgamento", "valor": "2024-02-01"},
        {"campo": "dataJulgamento", "valor": "2024-02-29"},
        {"campo": "origem", "valor": "PJe"},
        {"campo": "origem", "valor": "SISTJ"},
    ]


def test_parse_tjdf_api_empty_page_is_not_a_contract_failure():
    payload = json.loads(load_fixture("tjdf_juris_api_empty.json"))
    trace = SourceTrace(provider="tjdf_juris", endpoint=TJDF_JURIS_API_ENDPOINT)

    page = parse_tjdf_api_response(payload, trace=trace, page=1, page_size=2)

    assert page.total == 0
    assert page.results == []
    assert page.start == 0
    assert page.end == 0
    assert page.is_complete is True
    assert page.completeness_reason


def test_parse_tjdf_api_rejects_missing_required_envelope_fields():
    payload = json.loads(load_fixture("tjdf_juris_api_contract_changed.json"))
    trace = SourceTrace(provider="tjdf_juris", endpoint=TJDF_JURIS_API_ENDPOINT)

    with pytest.raises(ParserContractChangedError, match="hits or registros"):
        parse_tjdf_api_response(payload, trace=trace, page=1, page_size=2)


def test_search_sends_tjdf_summary_filter():
    session = FakeSession(
        [
            FakeResponse(load_fixture("tjdf_juris_initial.html")),
            FakeResponse(load_fixture("tjdf_juris_results.html")),
            FakeResponse(load_fixture("tjdf_juris_detail.html")),
        ]
    )
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    provider.search(
        JurisprudenceQuery(
            exact_phrase="infanticidio",
            page_size=1,
            fetch_details=True,
        )
    )

    initial_params = session.calls[0]["kwargs"]["params"]
    results_params = session.calls[1]["kwargs"]["params"]
    assert initial_params["argumentoDePesquisa"] == "infanticidio"
    assert results_params["argumentoDePesquisa"] == "infanticidio"
    assert results_params["ementa"] == "infanticidio"
    assert results_params["numero"] == ""


def test_tjdf_maps_boolean_and_date_filters_to_public_contract():
    query = JurisprudenceQuery(
        text="dano moral",
        all_words="transporte aereo",
        any_words="voo",
        without_words="penal",
        published_from="2021-01-01",
        published_to="2021-12-31",
        rapporteur="SANDRA REVES",
    )

    initial = _build_initial_params(query)
    results = _build_results_params(query, total=10)
    blob = str(initial) + str(results)

    assert all(term in blob for term in ("transporte aereo", "voo", "penal"))
    assert results["tipoDeData"] == "DataPublicacao"
    assert results["dataInicio"] == "2021-01-01"
    assert results["dataFim"] == "2021-12-31"
    assert results["desembargador"] == "SANDRA REVES"


def test_tjdf_maps_judgment_date_filter_separately():
    results = _build_results_params(
        JurisprudenceQuery(updated_from="2021-01-01", updated_to="2021-12-31"), total=10
    )

    assert results["tipoDeData"] == "DataJulgamento"
    assert results["dataInicio"] == "2021-01-01"


def test_search_page_maps_to_canonical_decision():
    session = FakeSession(
        [
            FakeResponse(load_fixture("tjdf_juris_initial.html")),
            FakeResponse(load_fixture("tjdf_juris_results.html")),
            FakeResponse(load_fixture("tjdf_juris_detail.html")),
        ]
    )
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="infanticidio", page_size=1, fetch_details=True))
    records = search_page_to_canonical(page)

    assert len(records) == 1
    record = records[0]
    assert isinstance(record, CanonicalDecision)
    assert record.source == "tjdf_juris"
    assert record.court == "TJDFT"
    assert record.case_number == "0722671-67.2024.8.07.0000"
    assert record.registry_number == "1917641"
    assert record.decision_type == "acordao"
    assert record.case_class == "Segredo de Justica"
    assert record.rapporteur == "SANDRA REVES"
    assert record.judging_body == "7 Turma Civel"
    assert record.judgment_date == "2024-09-04"
    assert record.publication_date == "2024-09-16"


def test_parse_tjdf_detail_accepts_fallback_document_id():
    trace = SourceTrace(
        provider="tjdf_juris",
        endpoint="/IndexadorAcordaos-web/sistj",
        source_url="https://pesquisajuris.tjdft.jus.br/IndexadorAcordaos-web/sistj",
        limitations=[],
    )

    result = parse_tjdf_detail(
        load_fixture("tjdf_juris_detail.html"), document_id="1917641", trace=trace
    )

    assert result.id == "tjdf-acordao-1917641"
    assert result.source_trace is not None


def test_search_without_fetch_details_avoids_detail_requests():
    session = FakeSession(
        [
            FakeResponse(load_fixture("tjdf_juris_initial.html")),
            FakeResponse(load_fixture("tjdf_juris_results.html")),
        ]
    )
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="infanticidio", page_size=2))

    assert [result.id for result in page.results] == [
        "tjdf-acordao-1917641",
        "tjdf-acordao-1907747",
    ]
    assert all(result.extraction_status.value == "partial" for result in page.results)
    assert len(session.calls) == 2


def test_list_results_extract_ementa_from_row_blob():
    """The live list row concatenates identifiers, rapporteur and the CNJ number
    before the ementa; the canonical summary must contain only the ementa."""

    html = (
        "<ul><li>"
        '<span id="id_link_abrir_dados_acordao_0">2162430</span>'
        " 1 2162430 460 Relator(a): EVANDRO NEIVA DE AMORIM"
        " Processo: 07180024920268070016"
        " DIREITO TRIBUTARIO E RESPONSABILIDADE CIVIL. EXECUCAO FISCAL. NULIDADE."
        "</li></ul>"
    )
    trace = SourceTrace(provider="tjdf_juris", endpoint="/consultaBaseAcordaos")

    results = parse_tjdf_list_results(
        html, trace=trace, base_url="https://pesquisajuris.tjdft.jus.br"
    )

    assert len(results) == 1
    result = results[0]
    assert result.summary is not None
    assert result.summary.startswith("DIREITO TRIBUTARIO E RESPONSABILIDADE CIVIL")
    assert "Relator(a)" not in result.summary
    assert "2162430" not in result.summary
    assert result.rapporteur == "EVANDRO NEIVA DE AMORIM"
    assert result.number == "2162430"
    assert result.raw["registry_number"] == "2162430"
    assert result.raw["process_number"] == "07180024920268070016"
    assert result.raw["document_url"].startswith(
        "https://pesquisajuris.tjdft.jus.br/IndexadorAcordaos-web/sistj?"
    )
    assert "numeroDoDocumento=2162430" in result.raw["document_url"]
    assert result.id == "tjdf-acordao-2162430"


def test_list_results_extract_trailing_dates_without_polluting_summary():
    html = (
        "<ul><li>"
        '<span id="id_link_abrir_dados_acordao_0">2171882</span>'
        " 1 2171882 1689 Relator(a): JANSEN FIALHO DE ALMEIDA "
        "Processo: 07195792720248070018 Ementa: RESPONSABILIDADE CIVIL. "
        "DANOS MORAIS. 02/09/2026 12/09/2026 7ª Turma Cível"
        "</li></ul>"
    )
    trace = SourceTrace(provider="tjdf_juris", endpoint="/IndexadorAcordaos-web/sistj")

    results = parse_tjdf_list_results(html, trace=trace)

    assert len(results) == 1
    result = results[0]
    assert result.judgment_date == "02/09/2026"
    assert result.publication_date == "12/09/2026"
    assert result.updated_at == "12/09/2026"
    assert result.source_updated_at == "12/09/2026"
    assert result.raw["judgment_date"] == "02/09/2026"
    assert result.raw["publication_date"] == "12/09/2026"
    assert "02/09/2026" not in (result.summary or "")
    assert "7ª Turma Cível" not in (result.summary or "")


def test_list_results_relocate_rows_when_the_id_selector_breaks():
    """If SISTJ renames the acordao link id, the rows are relocated by structure
    and the recovery is recorded on the trace instead of returning nothing."""

    from nanojuris.adaptive_selectors import SelectorMemory

    memory = SelectorMemory(":memory:", seed=False)
    trace = SourceTrace(provider="tjdf_juris", endpoint="/IndexadorAcordaos-web/sistj")

    # Prime the fingerprint from a page where the selector still works.
    parse_tjdf_list_results(load_fixture("tjdf_juris_results.html"), trace=trace, memory=memory)

    changed = load_fixture("tjdf_juris_results.html").replace(
        "id_link_abrir_dados_acordao", "lnkAbrirAcordao"
    )
    recovery_trace = SourceTrace(provider="tjdf_juris", endpoint="/IndexadorAcordaos-web/sistj")
    results = parse_tjdf_list_results(changed, trace=recovery_trace, memory=memory)

    assert [result.raw["registry_number"] for result in results] == ["1917641", "1907747"]
    assert any(
        "relocated by structural similarity" in note for note in recovery_trace.transformations
    )


def test_get_document_rejects_detail_without_acordao_fields():
    provider = TjdfJurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse("<html><title>SISTJWEB</title></html>")]),
    )

    with pytest.raises(ParserContractChangedError, match="returned no acórdão fields"):
        provider.get_document("not-a-real-id")


def test_get_document_accepts_search_result_id_prefix():
    provider = TjdfJurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjdf_juris_detail.html"))]),
    )

    document = provider.get_document("tjdf-acordao-1917641")

    assert document.id == "tjdf-acordao-1917641"
    assert document.raw_metadata["numeroDoDocumento"] == "1917641"
    assert document.raw_metadata["raw_content_preserved"] is True


@pytest.mark.parametrize(
    ("response", "expected_error"),
    [
        (FakeResponse("", 429), RateLimitDetectedError),
        (FakeResponse("", 500), SourceUnavailableError),
        (FakeResponse("", 400), SourceUnavailableError),
    ],
)
def test_search_errors_are_normalized(response, expected_error):
    provider = TjdfJurisProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    with pytest.raises(expected_error):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_request_exception_is_normalized():
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0), session=RaisingSession())

    with pytest.raises(SourceUnavailableError, match="offline"):
        provider.search(JurisprudenceQuery(text="infanticidio"))


def test_capabilities_include_promoted_filters():
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0))

    capabilities = provider.get_capabilities()

    assert capabilities.source == "tjdf_juris"
    assert "summary" in capabilities.search_modes
    assert "json" in capabilities.content_formats
    assert "POST https://jurisdf.tjdft.jus.br/api/v1/pesquisa" in capabilities.endpoints
