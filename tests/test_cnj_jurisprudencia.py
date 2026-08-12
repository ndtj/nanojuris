from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.cnj_jurisprudencia import (
    CnjJurisprudenciaProvider,
    parse_cnj_results,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        text: str = "",
        status_code: int = 200,
        content: bytes | None = None,
        url: str = "https://atos.cnj.jus.br/jurisprudencia",
        content_type: str = "text/html",
    ):
        self.text = text
        self.content = content if content is not None else text.encode("utf-8")
        self.status_code = status_code
        self.url = url
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.headers = {"content-type": content_type}


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


def trace() -> SourceTrace:
    return SourceTrace(provider="cnj_jurisprudencia", endpoint="GET /jurisprudencia")


def test_parse_cnj_results_maps_curated_rows_and_pdf_links():
    page = parse_cnj_results(
        load_fixture("cnj_jurisprudencia_results.html"),
        query=JurisprudenceQuery(text="cartorios", page_size=5),
        trace=trace(),
        base_url="https://atos.cnj.jus.br",
    )

    assert page.source == "cnj_jurisprudencia"
    assert page.total == 2
    assert page.results[0].court == "CNJ"
    assert page.results[0].type == "informativo"
    assert page.results[0].number == "9"
    assert page.results[0].publication_date == "2026-06-22"
    assert (
        page.results[0].raw["document_url"] == "https://atos.cnj.jus.br/files/original-demo-9.pdf"
    )
    assert page.results[0].raw["curated_source"] is True


def test_provider_sends_documented_filters_and_page():
    session = FakeSession([FakeResponse(load_fixture("cnj_jurisprudencia_results.html"))])
    provider = CnjJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )
    page = provider.search(
        JurisprudenceQuery(
            text="cartorios",
            number="9",
            published_from="01/01/2026",
            published_to="31/12/2026",
            page=2,
        )
    )

    assert page.source == "cnj_jurisprudencia"
    params = session.calls[0]["kwargs"]["params"]
    assert params == {
        "page": 2,
        "numero": "9",
        "argumento": "cartorios",
        "dat_publicacao_inicio": "01/01/2026",
        "dat_publicacao_fim": "31/12/2026",
    }
    assert session.calls[0]["kwargs"]["verify"] is True


def test_provider_get_document_preserves_pdf_bytes_and_hash():
    pdf = b"%PDF-1.4\npublic cnj fixture\n%%EOF"
    session = FakeSession(
        [
            FakeResponse(
                content=pdf,
                url="https://atos.cnj.jus.br/files/demo.pdf",
                content_type="application/pdf",
            )
        ]
    )
    provider = CnjJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    document = provider.get_document("https://atos.cnj.jus.br/files/demo.pdf")
    assert document.content_type == "application/pdf"
    assert document.byte_size == len(pdf)
    assert document.sha256
    assert document.extraction_trace is not None
    assert document.extraction_trace.content_bytes == len(pdf)


def test_client_registers_cnj_provider_and_capabilities_scope_is_curated():
    client = NanoJurisClient()
    assert "cnj_jurisprudencia" in {item.source for item in client.list_sources()}
    capabilities = CnjJurisprudenciaProvider(session=FakeSession([])).get_capabilities()
    assert capabilities.category == "curated_jurisprudence"
    assert capabilities.supports_catalog is True
    assert "number" in capabilities.supported_filters


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (FakeResponse("captcha", 403), AccessControlRequiredError),
        (FakeResponse("", 429), RateLimitDetectedError),
        (FakeResponse("", 503), SourceUnavailableError),
    ],
)
def test_provider_normalizes_http_failures(response, expected):
    provider = CnjJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([response]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))


def test_parser_detects_empty_and_changed_contracts():
    empty = parse_cnj_results(
        "<html><body>Nenhum resultado encontrado.</body></html>",
        query=JurisprudenceQuery(text="sem resultado"),
        trace=trace(),
        base_url="https://atos.cnj.jus.br",
    )
    assert empty.results == []
    with pytest.raises(ParserContractChangedError):
        parse_cnj_results(
            "<html><body>pagina sem estrutura conhecida</body></html>",
            query=JurisprudenceQuery(text="teste"),
            trace=trace(),
            base_url="https://atos.cnj.jus.br",
        )


def test_provider_wraps_transport_failure():
    provider = CnjJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )
    with pytest.raises(SourceUnavailableError, match="CNJ request failed"):
        provider.search(JurisprudenceQuery(text="teste"))
