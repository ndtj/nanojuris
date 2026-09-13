from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    ParserContractChangedError,
    SourceUnavailableError,
    UnsupportedQueryError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tce_pr_viajuris import (
    TcePrViaJurisProvider,
    parse_viajuris_csv,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tce_pr_viajuris_acordaos.csv"


class FakeResponse:
    def __init__(
        self, content: bytes, *, status_code: int = 200, url: str = "https://example.test"
    ):
        self.content = content
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": "text/csv; charset=utf-8"}


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"url": url, "kwargs": kwargs})
        return self.responses.pop(0)

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def test_viajuris_parser_preserves_csv_and_normalizes_fields() -> None:
    page = TcePrViaJurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(FIXTURE.read_bytes())]),
    ).search(JurisprudenceQuery(text="controle externo", page_size=5))

    assert page.total == 1
    result = page.results[0]
    assert result.id == "tce-pr-viajuris-2026-27"
    assert result.number == "818074/2025"
    assert result.type == "Acordão"
    assert result.rapporteur == "IVAN LELIS BONILHA"
    assert result.judgment_date == "2026-08-15"
    assert result.publication_date == "2026-08-20"
    assert result.summary.startswith("Controle externo")
    assert result.raw["judging_body"] == "Primeira Câmara"
    assert result.raw["document_url"].endswith("000200472.pdf")
    assert page.source_trace.content_sha256


def test_viajuris_parser_still_accepts_the_legacy_id_schema() -> None:
    legacy = (
        b"ID;NumeroProcesso;Ementa;DataJulgamento;DataPublicacao;UrlPDF\n"
        b"acordao-1;0000000-00.2026.8.16.0000;Controle externo;15/08/2026;20/08/2026;"
        b"https://viajuris.tce.pr.gov.br/Documentos/acordao-1.pdf\n"
    )
    rows = parse_viajuris_csv(legacy)
    assert rows[0]["ID"] == "acordao-1"


def test_viajuris_fetches_official_pdf_url_explicitly() -> None:
    response = FakeResponse(
        b"%PDF-1.4 invalid fixture",
        url="https://viajuris.tce.pr.gov.br/Documentos/acordao-1.pdf",
    )
    response.headers = {"Content-Type": "application/pdf"}
    provider = TcePrViaJurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([response]),
    )

    document = provider.get_document("https://viajuris.tce.pr.gov.br/Documentos/acordao-1.pdf")

    assert document.source == "tce_pr_viajuris"
    assert document.content_type == "application/pdf"
    assert document.raw_bytes == b"%PDF-1.4 invalid fixture"


def test_viajuris_catalog_is_read_only_and_year_selectable() -> None:
    provider = TcePrViaJurisProvider(NanoJurisConfig(rate_limit_interval=0))
    catalog = provider.get_catalog(year=2026)

    assert catalog.courts[0].code == "TCE-PR"
    assert catalog.species[0].code == "acordao"
    assert "2026_acordaos_base_de_dados.csv" in catalog.raw["dataset_url"]


def test_viajuris_rejects_missing_term_and_bad_schema() -> None:
    provider = TcePrViaJurisProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(UnsupportedQueryError, match="exige termo"):
        provider.search(JurisprudenceQuery())
    with pytest.raises(ParserContractChangedError, match="stable identifier"):
        parse_viajuris_csv(b"nome;ementa\nfoo;bar\n")


def test_viajuris_empty_and_invalid_fixtures_keep_states_distinct() -> None:
    empty = (FIXTURE.parent / "tce_pr_viajuris_empty.csv").read_bytes()
    invalid = (FIXTURE.parent / "tce_pr_viajuris_invalid.csv").read_bytes()

    assert parse_viajuris_csv(empty) == []
    with pytest.raises(ParserContractChangedError):
        parse_viajuris_csv(invalid)


def test_viajuris_maps_http_failure() -> None:
    provider = TcePrViaJurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(b"indisponivel", status_code=503)]),
    )
    with pytest.raises(SourceUnavailableError):
        provider.search(JurisprudenceQuery(text="controle"))


def test_viajuris_is_registered_in_client() -> None:
    assert "tce_pr_viajuris" in NanoJurisClient().providers
