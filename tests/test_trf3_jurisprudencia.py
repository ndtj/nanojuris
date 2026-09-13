from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    UnsupportedQueryError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.trf3_jurisprudencia import (
    Trf3JurisprudenciaProvider,
    parse_trf3_process_results,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, url: str, status_code: int = 200) -> None:
        self.text = text
        self.url = url
        self.status_code = status_code
        self.encoding = "utf-8"
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.content = text.encode("utf-8")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def _trace() -> SourceTrace:
    return SourceTrace(provider="trf3_jurisprudencia", endpoint="/acordaos")


def test_parse_trf3_process_results_maps_each_appellate_date() -> None:
    html = (FIXTURES / "trf3_jurisprudencia_process_results.html").read_text(encoding="utf-8")

    results = parse_trf3_process_results(
        html,
        trace=_trace(),
        base_url="https://web.trf3.jus.br",
    )

    assert [item.judgment_date for item in results] == ["16/12/2025", "07/10/2025"]
    assert all(item.degree == "second" for item in results)
    assert all(item.instance == "second" for item in results)
    assert results[0].number == "0007979-91.2005.4.03.6119"
    assert results[0].document_url.endswith("/BuscarDocumentoPje/346757387")


def test_trf3_parser_accepts_authoritative_empty_fixture() -> None:
    html = (FIXTURES / "trf3_jurisprudencia_process_empty.html").read_text(encoding="utf-8")

    assert (
        parse_trf3_process_results(html, trace=_trace(), base_url="https://web.trf3.jus.br") == []
    )


def test_trf3_parser_rejects_unknown_shape() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_trf3_process_results(
            "<html><body>Resposta inesperada</body></html>",
            trace=_trace(),
            base_url="https://web.trf3.jus.br",
        )


def test_trf3_search_uses_exact_process_route() -> None:
    listing = (FIXTURES / "trf3_jurisprudencia_process_results.html").read_text(encoding="utf-8")
    session = FakeSession(
        [
            FakeResponse(
                listing,
                "https://web.trf3.jus.br/acordaos/Acordao/PesquisarDocumento?processo=00079799120054036119",
            )
        ]
    )
    provider = Trf3JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    page = provider.search(JurisprudenceQuery(number="0007979-91.2005.4.03.6119", page_size=1))

    assert page.total == 2
    assert len(page.results) == 1
    assert page.total_known is True
    assert page.is_complete is False
    assert session.calls[0]["url"].endswith("/PesquisarDocumento")
    assert session.calls[0]["kwargs"]["params"] == {"processo": "00079799120054036119"}


def test_trf3_shared_transport_preserves_access_control_status() -> None:
    session = FakeSession(
        [
            FakeResponse(
                "<html><body>Forbidden</body></html>",
                "https://web.trf3.jus.br/acordaos/Acordao/PesquisarDocumento",
                status_code=403,
            )
        ]
    )
    provider = Trf3JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(number="0007979-91.2005.4.03.6119"))


def test_trf3_rejects_free_text_as_unverified_contract() -> None:
    provider = Trf3JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(UnsupportedQueryError):
        provider.search(JurisprudenceQuery(text="responsabilidade civil"))


def test_trf3_get_document_preserves_html_and_extracts_visible_text() -> None:
    detail = (FIXTURES / "trf3_jurisprudencia_detail.html").read_text(encoding="utf-8")
    session = FakeSession(
        [
            FakeResponse(
                detail, "https://web.trf3.jus.br/acordaos/Acordao/BuscarDocumentoPje/346757387"
            )
        ]
    )
    provider = Trf3JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    document = provider.get_document("trf3-jurisprudencia-346757387")

    assert document.access_status.value == "public"
    assert document.extraction_status.value == "complete"
    assert "EMENTA" in (document.text or "")
    assert document.raw_bytes == detail.encode("utf-8")


def test_trf3_provider_is_registered_without_default_federation() -> None:
    client = NanoJurisClient()
    provider = client.providers["trf3_jurisprudencia"]

    assert provider.get_capabilities().supports_unified_search is False
    assert provider.get_capabilities().opt_in_unified_search is True
