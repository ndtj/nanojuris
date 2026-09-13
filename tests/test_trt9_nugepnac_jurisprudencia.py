from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, QueryRejectedError
from nanojuris.models import AccessStatus, JurisprudenceQuery, SourceTrace
from nanojuris.providers.trt9_nugepnac_jurisprudencia import (
    Trt9NugepnacJurisprudenciaProvider,
    parse_trt9_nugepnac_pdf,
)

FIXTURE = Path(__file__).parent / "fixtures" / "trt9_nugepnac_success.json"


def _text() -> str:
    return " ".join(json.loads(FIXTURE.read_text(encoding="utf-8"))["pages"])


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="trt9_nugepnac_jurisprudencia",
        endpoint="GET official TRT9 NUGEP jurisprudence PDF",
        source_url=(
            "https://www.trt9.jus.br/bancojurisprudencia/api/v1/"
            "jurisprudencia/pdf-completo?tribunal=TRT9&listaTipo=DECISOES_IRDR"
        ),
        http_status=200,
        retrieval_status="ok",
    )


def test_parser_maps_curated_second_degree_irdr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nanojuris.providers.trt9_nugepnac_jurisprudencia._extract_pdf_text",
        lambda _content: _text(),
    )
    results = parse_trt9_nugepnac_pdf(
        b"%PDF-1.7 sanitized",
        query=JurisprudenceQuery(text="responsabilidade"),
        trace=_trace(),
        collection="TRT9_NUGEP_IRDR",
    )
    assert len(results) == 1
    result = results[0]
    assert result.authority == "TRT9"
    assert result.branch == "labor"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "TRT9_NUGEP_IRDR"
    assert result.number == "0001615-58.2017.5.09.0000"
    assert result.access_status is AccessStatus.PUBLIC


def test_parser_applies_number_and_negative_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nanojuris.providers.trt9_nugepnac_jurisprudencia._extract_pdf_text",
        lambda _content: _text(),
    )
    result = parse_trt9_nugepnac_pdf(
        b"%PDF-1.7 sanitized",
        query=JurisprudenceQuery(number="0004597-69.2022.5.09.0000"),
        trace=_trace(),
        collection="TRT9_NUGEP_IRDR",
    )
    assert len(result) == 1
    excluded = parse_trt9_nugepnac_pdf(
        b"%PDF-1.7 sanitized",
        query=JurisprudenceQuery(text="responsabilidade", without_words="grupo"),
        trace=_trace(),
        collection="TRT9_NUGEP_IRDR",
    )
    assert excluded == []


def test_invalid_pdf_is_not_empty() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_trt9_nugepnac_pdf(
            b"<!doctype html>",
            query=JurisprudenceQuery(text="x"),
            trace=_trace(),
            collection="TRT9_NUGEP_IRDR",
        )


def test_provider_is_contextual_opt_in() -> None:
    capabilities = Trt9NugepnacJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.pagination_mode == "local_pdf_window"
    assert capabilities.filter_status("text") == "local_postfilter"
    assert capabilities.filter_status("case_class") == "unsupported"


def test_provider_rejects_first_degree_scope() -> None:
    provider = Trt9NugepnacJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="x", degree="first"))


def test_decision_detail_reuses_observed_compilation() -> None:
    provider = Trt9NugepnacJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    provider._observed["trt9-nugepnac-test"] = "https://www.trt9.jus.br/compilacao.pdf"
    provider._observed_text["trt9-nugepnac-test"] = "ementa sanitizada"
    bundle = provider.get_decisions("trt9-nugepnac-test")
    assert bundle.texts == [{"content": "ementa sanitizada", "content_type": "text/plain"}]
    assert bundle.raw["collection"] == "TRT9_NUGEP"
