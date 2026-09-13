from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, QueryRejectedError
from nanojuris.models import AccessStatus, JurisprudenceQuery, SourceTrace
from nanojuris.providers.trt3_ementario_jurisprudencia import (
    Trt3EmentarioJurisprudenciaProvider,
    _parse_dspace_search_html,
    parse_trt3_ementario_pdf,
)

FIXTURE = Path(__file__).parent / "fixtures" / "trt3_ementario_success.json"


def _text() -> str:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return "\n".join(data["pages"])


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="trt3_ementario_jurisprudencia",
        endpoint="GET official TRT3 ementario PDF",
        source_url="https://as1.trt3.jus.br/bd-trt3/volume-12.pdf",
        http_status=200,
        retrieval_status="ok",
    )


def test_parser_maps_curated_second_degree_ementas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nanojuris.providers.trt3_ementario_jurisprudencia._extract_pdf_text",
        lambda _content: _text(),
    )
    results = parse_trt3_ementario_pdf(
        b"%PDF-1.7 sanitized", query=JurisprudenceQuery(text="responsabilidade"), trace=_trace()
    )

    assert len(results) == 1
    result = results[0]
    assert result.authority == "TRT3"
    assert result.branch == "labor"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "TRT3_EMENTARIO"
    assert result.document_type == "ementario"
    assert result.access_status is AccessStatus.PUBLIC
    assert result.number == "0001234-56.2015.5.03.0001"
    assert result.full_text is None


def test_parser_applies_number_and_negative_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nanojuris.providers.trt3_ementario_jurisprudencia._extract_pdf_text",
        lambda _content: _text(),
    )
    result = parse_trt3_ementario_pdf(
        b"%PDF-1.7 sanitized",
        query=JurisprudenceQuery(number="0009876-54.2014.5.03.0002"),
        trace=_trace(),
    )
    assert len(result) == 1
    assert "0009876" in (result[0].summary or "")

    excluded = parse_trt3_ementario_pdf(
        b"%PDF-1.7 sanitized",
        query=JurisprudenceQuery(text="contrato", without_words="trabalho"),
        trace=_trace(),
    )
    assert excluded == []


def test_invalid_pdf_is_not_empty() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_trt3_ementario_pdf(
            b"<!doctype html>", query=JurisprudenceQuery(text="x"), trace=_trace()
        )


def test_provider_keeps_curated_volume_opt_in() -> None:
    capabilities = Trt3EmentarioJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.pagination_mode == "remote_volume_search_local_pdf_window"
    assert capabilities.filter_status("text") == "local_postfilter"
    assert capabilities.filter_status("case_class") == "unsupported"


def test_provider_rejects_first_degree_scope() -> None:
    provider = Trt3EmentarioJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="x", degree="first"))


def test_decision_detail_reuses_observed_volume_without_refetch() -> None:
    provider = Trt3EmentarioJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    provider._observed["trt3-ementario-test"] = "https://as1.trt3.jus.br/bd-trt3/volume.pdf"
    provider._observed_text["trt3-ementario-test"] = "ementa sanitizada"

    bundle = provider.get_decisions("trt3-ementario-test")

    assert bundle.texts == [{"content": "ementa sanitizada", "content_type": "text/plain"}]
    assert bundle.raw["collection"] == "TRT3_EMENTARIO"


def test_dspace_search_parser_maps_volume_handles_and_total() -> None:
    html = """
    <p class="result-query">Sua requisição produziu 61 resultado(s).</p>
    <ul class="ds-artifact-list">
      <li class="ds-artifact-item"><div class="artifact-title">
        <a href="/bd-trt3/handle/11103/21203">Ementário n. 4</a>
      </div></li>
    </ul>
    """
    items, total = _parse_dspace_search_html(html, source_base="https://sistemas.trt3.jus.br")
    assert total == 61
    assert items == [
        {
            "handle": "https://sistemas.trt3.jus.br/bd-trt3/handle/11103/21203",
            "title": "Ementário n. 4",
        }
    ]


def test_dspace_search_schema_drift_is_not_empty() -> None:
    with pytest.raises(ParserContractChangedError):
        _parse_dspace_search_html(
            "<html><body>unexpected portal markup</body></html>",
            source_base="https://sistemas.trt3.jus.br",
        )


def test_search_materializes_bounded_dspace_volume_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = Trt3EmentarioJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    trace = _trace()
    monkeypatch.setattr(
        provider,
        "_request_dspace_search",
        lambda _query: (
            [
                {
                    "handle": "https://sistemas.trt3.jus.br/bd-trt3/handle/11103/1",
                    "title": "Ementario 2014",
                }
            ],
            trace,
            61,
        ),
    )
    monkeypatch.setattr(
        provider,
        "_request_dspace_volume",
        lambda _item: (
            b"%PDF-1.7 sanitized",
            trace,
            "https://sistemas.trt3.jus.br/x.pdf",
            "Ementario 2014",
        ),
    )
    monkeypatch.setattr(
        "nanojuris.providers.trt3_ementario_jurisprudencia._extract_pdf_text",
        lambda _content: _text(),
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=2))

    assert len(page.results) == 1
    assert page.total_known is False
    assert page.is_complete is False
    assert page.results[0].document_url == "https://sistemas.trt3.jus.br/x.pdf"
    assert page.results[0].publication_date == "2014"
