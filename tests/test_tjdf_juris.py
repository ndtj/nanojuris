from __future__ import annotations

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
    TjdfJurisProvider,
    parse_tjdf_detail,
    parse_tjdf_result_ids,
    parse_tjdf_total,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = None


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


def test_search_maps_tjdf_jurisprudence_result():
    session = FakeSession(
        [
            FakeResponse(load_fixture("tjdf_juris_initial.html")),
            FakeResponse(load_fixture("tjdf_juris_results.html")),
            FakeResponse(load_fixture("tjdf_juris_detail.html")),
        ]
    )
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="infanticidio", page=1, page_size=1))

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

    assert len(session.calls) == 3
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["kwargs"]["params"]["nomeDaPagina"] == "buscaLivre"
    assert session.calls[1]["kwargs"]["params"]["nomeDaPagina"] == "buscaLivre2"
    assert session.calls[2]["kwargs"]["params"]["numeroDoDocumento"] == "1917641"


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
        )
    )

    initial_params = session.calls[0]["kwargs"]["params"]
    results_params = session.calls[1]["kwargs"]["params"]
    assert initial_params["argumentoDePesquisa"] == "infanticidio"
    assert results_params["argumentoDePesquisa"] == "infanticidio"
    assert results_params["ementa"] == "infanticidio"
    assert results_params["numero"] == ""


def test_search_page_maps_to_canonical_decision():
    session = FakeSession(
        [
            FakeResponse(load_fixture("tjdf_juris_initial.html")),
            FakeResponse(load_fixture("tjdf_juris_results.html")),
            FakeResponse(load_fixture("tjdf_juris_detail.html")),
        ]
    )
    provider = TjdfJurisProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="infanticidio", page_size=1))
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
    assert document.raw_metadata == {"numeroDoDocumento": "1917641"}


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
