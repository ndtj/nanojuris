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
from nanojuris.providers.tjpi_juspi import (
    TjpiJuspiProvider,
    extract_tjpi_document_text,
    parse_tjpi_results,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


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
    return (FIXTURES / name).read_text(encoding="utf-8")


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="tjpi_juspi",
        endpoint="/jurisprudences/search",
        query={"q": "dano moral"},
        source_url="https://jurisprudencia.tjpi.jus.br/jurisprudences/search",
        limitations=[],
    )


def test_parse_tjpi_results_maps_public_search_html():
    page = parse_tjpi_results(
        load_fixture("tjpi_juspi_dano_moral.html"),
        query=JurisprudenceQuery(text="dano moral", page_size=3),
        trace=_trace(),
        base_url="https://jurisprudencia.tjpi.jus.br",
    )

    assert page.source == "tjpi_juspi"
    assert page.total == 193029
    assert page.start == 1
    assert page.end == 3
    assert len(page.results) == 3
    result = page.results[0]
    assert result.id == "tjpi-juspi-35510999"
    assert result.court == "TJPI"
    assert result.type == "decisao_terminativa"
    assert result.number == "0804974-54.2024.8.18.0026"
    assert result.updated_at == "06/08/2026"
    assert result.rapporteur == "Desembargador DIOCLÉCIO SOUSA DA SILVA"
    assert result.raw["subject"] == "Práticas Abusivas"
    assert result.raw["case_class"] == "EMBARGOS DE DECLARAÇÃO CÍVEL (1689)"
    assert result.raw["full_text_url"].endswith("/jurisprudences/35510999/public")
    assert "AUTOCOMPOSIÇÃO" in (result.summary or "")


def test_parse_tjpi_empty_search_returns_empty_page():
    page = parse_tjpi_results(
        load_fixture("tjpi_juspi_empty.html"),
        query=JurisprudenceQuery(text="zzznanojurissemresultado", page_size=5),
        trace=_trace(),
        base_url="https://jurisprudencia.tjpi.jus.br",
    )

    assert page.total == 0
    assert page.results == []


def test_provider_search_sends_public_get_params():
    provider = TjpiJuspiProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjpi_juspi_dano_moral.html"))]),
    )

    page = provider.search(
        JurisprudenceQuery(
            text="dano moral",
            types=["acordao"],
            updated_from="2026-01-01",
            updated_to="2026-08-07",
            page=2,
            page_size=1,
        )
    )

    assert page.results[0].source == "tjpi_juspi"
    call = provider.session.calls[0]
    assert call["method"] == "GET"
    assert call["url"].endswith("/jurisprudences/search")
    assert call["kwargs"]["params"] == {
        "q": "dano moral",
        "page": 2,
        "tipo": "Acórdão",
        "data_min": "2026-01-01",
        "data_max": "2026-08-07",
    }


def test_extract_tjpi_document_text_maps_public_detail():
    text, metadata = extract_tjpi_document_text(load_fixture("tjpi_juspi_detail.html"))

    assert "Tese de julgamento" in text
    assert metadata["case_number"] == "0804974-54.2024.8.18.0026"
    assert metadata["case_class"] == "EMBARGOS DE DECLARAÇÃO CÍVEL (1689)"
    assert metadata["subject"] == "Tarifas, Práticas Abusivas"
    assert metadata["rapporteur"] == "Desembargador DIOCLÉCIO SOUSA DA SILVA"
    assert metadata["decision_type"] == "decisao_terminativa"
    assert metadata["access_status"] == "public"


def test_get_document_returns_canonical_document_with_hash():
    provider = TjpiJuspiProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjpi_juspi_detail.html"))]),
    )

    document = provider.get_document("tjpi-juspi-35510999")

    assert document.source == "tjpi_juspi"
    assert document.document_type == "decisao_terminativa"
    assert document.text and "Acordo homologado" in document.text
    assert document.sha256
    assert document.raw_bytes is not None
    assert document.byte_size == len(document.raw_bytes)
    assert document.raw_metadata["public_id"] == "35510999"


def test_tjpi_results_canonicalize_as_decisions():
    provider = TjpiJuspiProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(load_fixture("tjpi_juspi_dano_moral.html"))]),
    )

    records = search_page_to_canonical(
        provider.search(JurisprudenceQuery(text="dano moral", page_size=1))
    )

    assert len(records) == 1
    assert records[0].source == "tjpi_juspi"
    assert records[0].court == "TJPI"
    assert records[0].case_number == "0804974-54.2024.8.18.0026"
    assert records[0].decision_type == "decisao_terminativa"
    assert records[0].publication_date == "2026-08-06"


def test_get_document_rejects_invalid_public_id():
    provider = TjpiJuspiProvider(NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]))

    with pytest.raises(ParserContractChangedError):
        provider.get_document("not-a-tjpi-id")


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
    provider = TjpiJuspiProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    with pytest.raises(expected_error):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_request_exception_is_normalized():
    provider = TjpiJuspiProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )

    with pytest.raises(SourceUnavailableError, match="offline"):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_capabilities_describe_tjpi_provider():
    capabilities = TjpiJuspiProvider().get_capabilities()

    assert capabilities.source == "tjpi_juspi"
    assert capabilities.category == "court_jurisprudence"
    assert "full_text" in capabilities.search_modes
    assert "CanonicalDocument" in capabilities.canonical_records
    assert capabilities.supports_full_text is True
