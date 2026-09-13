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
from nanojuris.providers.tjma_informativos import (
    TjmaInformativosProvider,
    parse_tjma_informativos,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        content: bytes,
        status_code: int = 200,
        content_type: str = "text/html; charset=utf-8",
        url: str = "https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874",
    ) -> None:
        self.content = content
        self.text = content.decode("utf-8", errors="replace")
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.url = url
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"


class FakeSession:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": "GET", "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        assert isinstance(response, FakeResponse)
        return response

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        return self.get(url, **kwargs)


def fixture_html() -> str:
    return (FIXTURES / "tjma_informativos_success.html").read_text(encoding="utf-8")


def trace() -> SourceTrace:
    return SourceTrace(
        provider="tjma_informativos",
        endpoint="GET /midia/pje/pagina/hotsite/509874",
    )


def test_parser_keeps_only_official_pdf_editions_and_scope():
    page = parse_tjma_informativos(
        fixture_html(),
        query=JurisprudenceQuery(page_size=10),
        trace=trace(),
        base_url="https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874",
    )

    assert page.source == "tjma_informativos"
    assert page.total == 2
    assert page.total_known is False
    assert [item.raw["edition_period"] for item in page.results] == ["2026-08", "2026-07"]
    assert [item.publication_date for item in page.results] == ["2026-08", "2026-07"]
    assert all(item.raw["source_record_id"] == item.id for item in page.results)
    assert all("source_record_id" in item.field_provenance for item in page.results)
    assert all(item.authority == "TJMA" for item in page.results)
    assert all(item.degree == "second" for item in page.results)
    assert all(item.collection == "INFORMATIVO" for item in page.results)
    assert all(
        item.document_url.startswith("https://novogerenciador.tjma.jus.br/")
        for item in page.results
    )
    assert page.filters_applied["text"] == "unsupported_document_body_not_scanned"


def test_parser_applies_only_proven_scope_filters():
    page = parse_tjma_informativos(
        fixture_html(),
        query=JurisprudenceQuery(collection="CJSG", page_size=10),
        trace=trace(),
        base_url="https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874",
    )
    assert page.results == []
    assert page.total_known is True
    assert page.is_explicit_empty


def test_provider_registers_document_and_fetches_pdf_on_demand():
    listing = FakeResponse(fixture_html().encode())
    pdf = FakeResponse(
        b"%PDF-1.7\n1 0 obj\n",
        content_type="application/pdf",
        url="https://novogerenciador.tjma.jus.br/a.pdf",
    )
    session = FakeSession([listing, pdf])
    provider = TjmaInformativosProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(page_size=1))
    document = provider.get_document(page.results[0].id)

    assert document.access_status.value == "public"
    assert document.content_type == "application/pdf"
    assert len(session.calls) == 2
    assert session.calls[0]["url"] == "https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874"


def test_provider_capabilities_are_curated_and_opt_in():
    provider = TjmaInformativosProvider(session=FakeSession([]))
    capabilities = provider.get_capabilities()

    assert capabilities.category == "curated_jurisprudence"
    assert capabilities.supports_full_text is True
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.filter_status("text") == "unsupported"
    assert capabilities.filter_status("degree") == "validated_scope"


def test_client_registers_tjma_informativos():
    client = NanoJurisClient()
    assert "tjma_informativos" in {item.source for item in client.list_sources()}


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (FakeResponse(b"captcha", 403), AccessControlRequiredError),
        (FakeResponse(b"", 429), RateLimitDetectedError),
        (FakeResponse(b"", 503), SourceUnavailableError),
    ],
)
def test_provider_keeps_external_failures_explicit(
    response: FakeResponse, expected: type[Exception]
):
    provider = TjmaInformativosProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([response]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery())


def test_parser_rejects_schema_without_pdf_links():
    with pytest.raises(ParserContractChangedError):
        parse_tjma_informativos(
            "<html><body><h1>estrutura alterada</h1></body></html>",
            query=JurisprudenceQuery(),
            trace=trace(),
            base_url="https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874",
        )


def test_provider_keeps_transport_exception_explicit():
    provider = TjmaInformativosProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )
    with pytest.raises(SourceUnavailableError):
        provider.search(JurisprudenceQuery())
