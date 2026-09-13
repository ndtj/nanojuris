from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, QueryRejectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.trt4_sumulas_jurisprudencia import (
    Trt4SumulasJurisprudenciaProvider,
    parse_trt4_sumulas_html,
)

FIXTURE = Path(__file__).parent / "fixtures" / "trt4_sumulas_success.html"


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="trt4_sumulas_jurisprudencia",
        endpoint="GET official TRT4 súmulas HTML",
        source_url="https://www.trt4.jus.br/portais/trt4/sumulas",
        http_status=200,
        retrieval_status="ok",
    )


def test_parser_maps_curated_second_degree_records() -> None:
    results = parse_trt4_sumulas_html(
        FIXTURE.read_bytes(), query=JurisprudenceQuery(text="responsabilidade"), trace=_trace()
    )
    assert len(results) == 1
    result = results[0]
    assert result.authority == "TRT4"
    assert result.branch == "labor"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "TRT4_SUMULAS"
    assert result.type == "sumula"
    assert result.document_url is None


def test_parser_supports_exact_number_and_document_link() -> None:
    results = parse_trt4_sumulas_html(
        FIXTURE.read_bytes(),
        query=JurisprudenceQuery(number="0007765-93.2017.5.04.0000"),
        trace=_trace(),
    )
    assert len(results) == 1
    assert results[0].type == "acordao"
    assert results[0].document_url is not None
    assert "pesquisatextual.trt4.jus.br" in results[0].document_url


def test_parser_applies_negative_filter() -> None:
    results = parse_trt4_sumulas_html(
        FIXTURE.read_bytes(),
        query=JurisprudenceQuery(text="responsabilidade", without_words="administração"),
        trace=_trace(),
    )
    assert results == []


def test_parser_applies_document_type_filter() -> None:
    results = parse_trt4_sumulas_html(
        FIXTURE.read_bytes(),
        query=JurisprudenceQuery(document_type="acordao"),
        trace=_trace(),
    )
    assert len(results) == 1
    assert results[0].type == "acordao"


def test_invalid_html_is_not_empty() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_trt4_sumulas_html(
            b"<html><body>sem registros</body></html>",
            query=JurisprudenceQuery(text="x"),
            trace=_trace(),
        )


def test_provider_is_contextual_opt_in() -> None:
    capabilities = Trt4SumulasJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.filter_status("document_type") == "local_postfilter"
    assert capabilities.filter_status("case_class") == "unsupported"


def test_provider_rejects_first_degree_scope() -> None:
    provider = Trt4SumulasJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="x", degree="first"))
