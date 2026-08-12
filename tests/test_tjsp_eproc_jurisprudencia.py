from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    UnsupportedQueryError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjsp_eproc_jurisprudencia import (
    TjspEprocJurisprudenciaProvider,
    parse_eproc_jurisprudencia_results,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_tjsp_eproc_rejects_unproven_remote_pagination():
    provider = TjspEprocJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(UnsupportedQueryError, match="paginacao remota comprovada"):
        provider.search(JurisprudenceQuery(text="teste", page=2))


class FakeResponse:
    def __init__(
        self,
        text: str,
        status_code: int = 200,
        url: str = "https://eproc-consulta.tjsp.jus.br/consulta_1g/externo_controlador.php",
    ):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"
        self.url = url


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
    return (FIXTURES / "tjsp_eproc_jurisprudencia_result.html").read_text(encoding="utf-8")


def test_parse_eproc_jurisprudencia_results_maps_fixture():
    trace = SourceTrace(
        provider="tjsp_eproc_jurisprudencia",
        endpoint="/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados",
    )

    results = parse_eproc_jurisprudencia_results(
        _fixture_html(),
        trace=trace,
        source_url="https://eproc-consulta.tjsp.jus.br/consulta_1g/externo_controlador.php",
    )

    assert len(results) == 1
    result = results[0]
    assert result.id == "tjsp-eproc-jurisprudencia-611784722886604694722042384549"
    assert result.source == "tjsp_eproc_jurisprudencia"
    assert result.court == "TJSP"
    assert result.type == "sentenca"
    assert result.number == "4002141-42.2025.8.26.0132"
    assert result.rapporteur == "MARCELO EDUARDO DE SOUZA"
    assert result.updated_at == "22/07/2026"
    assert result.raw["case_class"] == "PJEC - PROCEDIMENTO DO JUIZADO ESPECIAL CÍVEL"
    assert result.raw["judging_body"] == "Vara do Juizado Especial Cível da Comarca de Catanduva"
    assert result.raw["full_text_url"].startswith(
        "https://eproc-consulta.tjsp.jus.br/consulta_1g/externo_controlador.php"
    )


def test_provider_search_posts_eproc_jurisprudencia_payload_and_parses_results():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = TjspEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    page = provider.search(
        JurisprudenceQuery(
            text="infanticidio",
            number="4002141-42.2025.8.26.0132",
            updated_from="01/07/2026",
            updated_to="31/07/2026",
            published_from="01/07/2026",
            published_to="31/07/2026",
            page_size=5,
        )
    )

    assert page.source == "tjsp_eproc_jurisprudencia"
    assert page.results[0].number == "4002141-42.2025.8.26.0132"
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith(
        "externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados"
    )
    payload = call["kwargs"]["data"]
    assert payload["txtPesquisa"] == "infanticidio"
    assert payload["txtProcesso"] == "40021414220258260132"
    assert payload["dtDecisaoInicio"] == "01/07/2026"
    assert payload["dtPublicacaoFim"] == "31/07/2026"


def test_provider_search_uses_exact_phrase_as_summary_query_text():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = TjspEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    provider.search(JurisprudenceQuery(exact_phrase="dano moral", page_size=1))

    payload = session.calls[0]["kwargs"]["data"]
    assert payload["txtPesquisa"] == "dano moral"
    assert payload["rdoCampo"] == "E"


def test_provider_search_maps_source_origin_and_document_types_to_official_filters():
    session = FakeSession([FakeResponse(_fixture_html())])
    provider = TjspEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    provider.search(
        JurisprudenceQuery(
            text="desconsideracao",
            types=["acordao"],
            source_origin="segundo_grau",
            page_size=1,
        )
    )

    payload = session.calls[0]["kwargs"]["data"]
    assert payload["selTipoDocumento[]"] == ["1"]
    assert payload["selOrigem[]"] == ["5"]


def test_eproc_jurisprudencia_canonicalizes_as_decision():
    provider = TjspEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(_fixture_html())]),
    )

    records = search_page_to_canonical(provider.search(JurisprudenceQuery(text="infanticidio")))

    assert len(records) == 1
    assert records[0].source == "tjsp_eproc_jurisprudencia"
    assert records[0].court == "TJSP"
    assert records[0].case_number == "4002141-42.2025.8.26.0132"
    assert records[0].decision_type == "sentenca"
    assert records[0].publication_date == "2026-07-22"


def test_provider_get_decisions_downloads_public_full_text():
    session = FakeSession([FakeResponse("<html>inteiro teor publico</html>")])
    provider = TjspEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    bundle = provider.get_decisions("tjsp-eproc-jurisprudencia-611784722886604694722042384549")

    assert bundle.source == "tjsp_eproc_jurisprudencia"
    assert bundle.raw["id_jurisprudencia"] == "611784722886604694722042384549"
    assert session.calls[0]["kwargs"]["params"] == {
        "id_jurisprudencia": "611784722886604694722042384549"
    }


def test_provider_detects_access_control_without_bypass():
    provider = TjspEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse("<html><div class='g-recaptcha'></div></html>")]),
    )

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_missing_result_cards_are_rejected():
    trace = SourceTrace(provider="tjsp_eproc_jurisprudencia", endpoint="/search")

    with pytest.raises(ParserContractChangedError):
        parse_eproc_jurisprudencia_results(
            "<html><body>sem resultados conhecidos</body></html>",
            trace=trace,
            source_url="https://example.test",
        )


def test_request_exception_becomes_source_error():
    provider = TjspEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )

    with pytest.raises(Exception, match="TJSP/eproc jurisprudence request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_capabilities_describe_jurisprudence_source():
    provider = TjspEprocJurisprudenciaProvider(session=FakeSession([]))

    capabilities = provider.get_capabilities()

    assert capabilities.source == "tjsp_eproc_jurisprudencia"
    assert capabilities.category == "court_jurisprudence"
    assert "full_text" in capabilities.search_modes
    assert "CanonicalDecision" in capabilities.canonical_records
    assert "id_jurisprudencia" in capabilities.extracted_fields
    assert capabilities.supports_full_text is False
