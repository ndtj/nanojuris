from __future__ import annotations

from pathlib import Path

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tce_sp_jurisprudencia import (
    TceSpJurisprudenciaProvider,
    parse_tce_sp_boletins,
    parse_tce_sp_indice,
    parse_tce_sp_sumulas,
)

FIXTURES = Path(__file__).parent / "fixtures"

SUMULAS_HTML = (FIXTURES / "tce_sp_sumulas.html").read_text(encoding="utf-8")

BOLETINS_HTML = (FIXTURES / "tce_sp_boletins.html").read_text(encoding="utf-8")

INDICE_HTML = (FIXTURES / "tce_sp_indice.html").read_text(encoding="utf-8")


class FakeResponse:
    def __init__(
        self, text: str, url: str, status_code: int = 200, content_type: str = "text/html"
    ):
        self.text = text
        self.content = text.encode("utf-8")
        self.url = url
        self.status_code = status_code
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.headers = {"Content-Type": content_type}
        self.is_redirect = False

    def iter_content(self, chunk_size: int = 65536):
        yield self.content

    def close(self):
        return None


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


def test_parse_tce_sp_sumulas_extracts_statements():
    results = parse_tce_sp_sumulas(
        SUMULAS_HTML,
        source_url="https://www.tce.sp.gov.br/boletim-de-jurisprudencia/sumulas",
        trace=SourceTrace(provider="tce_sp_jurisprudencia", endpoint="/sumulas"),
    )

    assert len(results) == 2
    assert results[0].id == "tce-sp-sumula-1"
    assert results[0].type == "sumula"
    assert results[0].thesis == "Não é lícita a concessão de subvenção personalíssima."
    assert "Resolução" in (results[0].raw["history"] or "")


def test_parse_tce_sp_boletins_extracts_publication_links():
    results = parse_tce_sp_boletins(
        BOLETINS_HTML,
        source_url="https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes",
        trace=SourceTrace(provider="tce_sp_jurisprudencia", endpoint="/publicacoes"),
    )

    assert len(results) == 2
    assert results[0].id == "tce-sp-boletim-53"
    assert results[0].number == 53
    assert results[0].raw["document_url"].endswith("edicao-53-marco2026")


def test_parse_tce_sp_indice_preserves_topic_and_bulletin_link():
    results = parse_tce_sp_indice(
        INDICE_HTML,
        source_url="https://www.tce.sp.gov.br/boletim-de-jurisprudencia/indice-alfabetico-remissivo",
        trace=SourceTrace(provider="tce_sp_jurisprudencia", endpoint="/indice"),
    )

    assert [item.id for item in results] == [
        "tce-sp-indice-licitacao-e-contratos",
        "tce-sp-indice-contas-de-prefeitura",
    ]
    assert results[0].type == "indice_remissivo"
    assert results[0].number == 53
    assert results[0].raw["topic"] == "Licitação e contratos"
    assert results[0].document_url.endswith("edicao-53-marco2026")


def test_provider_search_filters_catalog_results():
    session = FakeSession(
        [
            FakeResponse(
                SUMULAS_HTML, "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/sumulas"
            ),
            FakeResponse(
                BOLETINS_HTML, "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes"
            ),
        ]
    )
    provider = TceSpJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="religioso", page_size=5))

    assert page.source == "tce_sp_jurisprudencia"
    assert len(page.results) == 1
    assert page.results[0].id == "tce-sp-sumula-2"


def test_tce_sp_provider_exposes_index_route():
    provider = TceSpJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(
                    INDICE_HTML,
                    "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/indice-alfabetico-remissivo",
                )
            ]
        ),
    )

    results = provider.get_index()

    assert len(results) == 2
    assert results[1].number == 10


def test_provider_search_marks_local_catalog_window_complete_when_empty() -> None:
    session = FakeSession(
        [
            FakeResponse(
                SUMULAS_HTML,
                "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/sumulas",
            ),
            FakeResponse(
                BOLETINS_HTML,
                "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes",
            ),
        ]
    )
    provider = TceSpJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="termo-inexistente", page_size=5))

    assert page.results == []
    assert page.is_complete is True
    assert page.total_known is True
    assert page.is_explicit_empty is True


def test_tce_sp_canonicalizes_as_precedent():
    session = FakeSession(
        [FakeResponse(SUMULAS_HTML, "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/sumulas")]
    )
    provider = TceSpJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    records = search_page_to_canonical(provider.search(JurisprudenceQuery(types=["sumula"])))

    assert records[0].source == "tce_sp_jurisprudencia"
    assert records[0].precedent_type == "sumula"
    assert records[0].thesis is not None


def test_tce_sp_catalog_exposes_public_collections() -> None:
    session = FakeSession(
        [
            FakeResponse(
                SUMULAS_HTML,
                "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/sumulas",
            ),
            FakeResponse(
                BOLETINS_HTML,
                "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes",
            ),
        ]
    )
    provider = TceSpJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    catalog = provider.get_catalog()

    assert catalog.courts[0].code == "TCE-SP"
    assert [option.code for option in catalog.species] == [
        "sumula",
        "boletim_jurisprudencia",
    ]
    assert catalog.species_groups == [
        {"name": "sumulas", "count": 2},
        {"name": "boletins", "count": 2},
    ]
    assert len(catalog.raw["sumulas"]) == 2
    assert session.calls[0]["method"] == "GET"


def test_tce_sp_fetches_observed_bulletin_document() -> None:
    session = FakeSession(
        [
            FakeResponse(
                BOLETINS_HTML,
                "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes",
            ),
            FakeResponse(
                "<html><body><h1>Boletim 53</h1><p>Texto integral público.</p></body></html>",
                "https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes/boletim-jurisprudencia-edicao-53-marco2026",
            ),
        ]
    )
    provider = TceSpJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(types=["boletim"], page_size=1))
    document = provider.get_document(page.results[0].id)

    assert document.access_status.value == "public"
    assert document.extraction_status.value == "complete"
    assert "Texto integral público" in (document.text or "")
    assert document.source_trace is not None
    assert len(session.calls) == 2


def test_tce_sp_rejects_untrusted_document_url() -> None:
    provider = TceSpJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    )

    try:
        provider.get_document("https://example.invalid/bulletin.html")
    except ValueError as exc:
        assert "allowlist" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("untrusted document URL was accepted")


def test_tce_sp_capabilities_expose_document_fetch_contract() -> None:
    capabilities = TceSpJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    ).get_capabilities()

    assert capabilities.supports_full_text is True
    assert capabilities.full_text_access == "document_link"
    assert "CanonicalDocument" in capabilities.canonical_records
    assert "id" in capabilities.extracted_fields
    assert "indice_remissivo" in capabilities.document_types
