from __future__ import annotations

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.stm_jurisprudencia import (
    StmJurisprudenciaProvider,
    parse_stm_jurisprudencia_results,
    parse_stm_total_documents,
)

STM_HTML = """
<html><body>
<div class="container container-fluid">
  <div class="panel panel-default">
    <div class="panel-heading">
            <button title="Exibir Inteiro Teor"
                onclick="tracker.functions.openInteiroTeor('https://eproc2g.stm.jus.br/eproc_2g_prod/externo_controlador.php?acao=visualizar_acordao&amp;uuid=b2b2e8fe7d596c2d8c05de8a290f9ce46881030e41ccf5df17ef3453facfe031')">
                Inteiro Teor
            </button>
            <button data-type="referencia_legislativa"
                data-uuid="f10664ac8095465d5e59d4088b2d3d56"
                data-processo="7000527-63.2025.7.00.0000">
                Referência Legislativa
            </button>
      7000527-63.2025.7.00.0000
    </div>
    <div class="panel-body">
      f10664ac8095465d5e59d4088b2d3d56
            7000527-63.2025.7.00.0000 EMBARGOS INFRINGENTES E DE NULIDADE
            EMBARGOS INFRINGENTES E DE NULIDADE N.º 7000527-63.2025.7.00.0000
      <dl class="dl-horizontal">
        <dt>Relator(a):</dt><dd>CELSO LUIZ NAZARETH</dd>
        <dt>Revisor(a):</dt><dd>JOSÉ BARROSO FILHO</dd>
        <dt>Assuntos:</dt><dd>DIREITO PENAL MILITAR, DESERÇÃO.</dd>
      </dl>
      Data de Autuação: 05/08/2025 Data de Julgamento: 18/06/2026 Data de Publicação: 25/06/2026
      <blockquote>EMENTA: DIREITO PENAL MILITAR. DESERÇÃO. ACOLHIMENTO DOS EMBARGOS.</blockquote>
    </div>
  </div>
</div>
</body></html>
"""


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"
        self.url = "https://jurisprudencia.stm.jus.br/consulta.php"


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


def test_parse_stm_jurisprudencia_results_extracts_panel_fields():
    results = parse_stm_jurisprudencia_results(
        STM_HTML,
        trace=SourceTrace(provider="stm_jurisprudencia", endpoint="/consulta.php"),
        source_url="https://jurisprudencia.stm.jus.br/consulta.php",
    )

    result = results[0]
    assert result.id == (
        "stm-jurisprudencia-b2b2e8fe7d596c2d8c05de8a290f9ce46881030e41ccf5df17ef3453facfe031"
    )
    assert result.source == "stm_jurisprudencia"
    assert result.court == "STM"
    assert result.type == "acordao"
    assert result.number == "7000527-63.2025.7.00.0000"
    assert result.rapporteur == "CELSO LUIZ NAZARETH"
    assert result.updated_at == "25/06/2026"
    assert result.raw["case_class"] == "EMBARGOS INFRINGENTES E DE NULIDADE"
    assert result.raw["judgment_date"] == "18/06/2026"
    assert result.raw["subject"] == "DIREITO PENAL MILITAR, DESERÇÃO."
    assert result.raw["document_url"].endswith(
        "uuid=b2b2e8fe7d596c2d8c05de8a290f9ce46881030e41ccf5df17ef3453facfe031"
    )


def test_parse_stm_jurisprudencia_results_accepts_empty_result_page():
    html = "<html><body><main>Nenhum resultado encontrado.</main></body></html>"

    results = parse_stm_jurisprudencia_results(
        html,
        trace=SourceTrace(provider="stm_jurisprudencia", endpoint="/consulta.php"),
        source_url="https://jurisprudencia.stm.jus.br/consulta.php",
    )

    assert results == []


def test_parse_stm_total_documents_reads_public_count():
    assert parse_stm_total_documents("<html>1 - 2 de 1017 documentos</html>") == 1017


def test_provider_search_gets_stm_query_and_parses_results():
    session = FakeSession([FakeResponse(STM_HTML)])
    provider = StmJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="desercao",
            exact_phrase="deserção",
            number="7000527-63.2025.7.00.0000",
            published_from="01/01/2026",
            published_to="31/12/2026",
            page_size=1,
        )
    )

    assert page.source == "stm_jurisprudencia"
    assert page.total == 1
    assert page.results[0].number == "7000527-63.2025.7.00.0000"
    call = session.calls[0]
    assert call["method"] == "GET"
    assert call["url"] == "https://jurisprudencia.stm.jus.br/consulta.php"
    params = call["kwargs"]["params"]
    assert params["search_filter_option"] == "jurisprudencia"
    assert params["search_filter"] == "busca_avancada"
    assert params["q"] == "desercao"
    assert params["start"] == "0"
    assert params["rows"] == "1"
    assert params["fqx_ementa"] == "deserção"
    assert params["fqx_numero_jurisprudencia"] == "7000527-63.2025.7.00.0000"
    assert params["fqx_data_publicacao_inicio"] == "01/01/2026"


def test_provider_get_decisions_builds_stm_full_text_url():
    session = FakeSession([FakeResponse("<html>inteiro teor</html>")])
    provider = StmJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    bundle = provider.get_decisions(
        "stm-jurisprudencia-b2b2e8fe7d596c2d8c05de8a290f9ce46881030e41ccf5df17ef3453facfe031"
    )

    assert bundle.source == "stm_jurisprudencia"
    assert bundle.texts[0]["content"] == "<html>inteiro teor</html>"
    assert session.calls[0]["url"].endswith(
        "acao=visualizar_acordao&uuid=b2b2e8fe7d596c2d8c05de8a290f9ce46881030e41ccf5df17ef3453facfe031"
    )


def test_provider_detects_stm_access_control_without_bypass():
    session = FakeSession([FakeResponse("<html><div class='g-recaptcha'></div></html>")])
    provider = StmJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_invalid_stm_precedent_id_is_rejected():
    provider = StmJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([]),
    )

    with pytest.raises(ParserContractChangedError):
        provider.get_decisions("bad-id")


def test_request_exception_becomes_stm_source_error():
    session = FakeSession([requests.RequestException("offline")])
    provider = StmJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(Exception, match="STM jurisprudence request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_capabilities_describe_stm_contract():
    capabilities = StmJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()

    assert capabilities.source == "stm_jurisprudencia"
    assert capabilities.source_url == "https://jurisprudencia.stm.jus.br"
    assert "CanonicalDecision" in capabilities.canonical_records
    assert "summary" in capabilities.search_modes
