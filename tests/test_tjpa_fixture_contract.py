from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.errors import ParserContractChangedError, QueryRejectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjpa_jurisprudencia_bff import (
    TjpaJurisprudenciaBffProvider,
    parse_tjpa_search_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_tjpa_filters_fixture_exposes_catalog_values() -> None:
    class Response:
        status_code = 200
        url = "https://example.test/bff/api/decisoes/filtros"
        text = ""
        content = json.dumps(
            _load("tjpa_jurisprudencia_bff_filters.json"), ensure_ascii=False
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        @staticmethod
        def json():
            return _load("tjpa_jurisprudencia_bff_filters.json")

    class Session:
        def request(self, *args, **kwargs):
            return Response()

    catalog = TjpaJurisprudenciaBffProvider(session=Session()).get_catalog()
    assert {item.code for item in catalog.species} >= {"A", "1", "10"}
    assert catalog.courts[0].code == "O"


def test_tjpa_empty_fixture_is_explicitly_empty() -> None:
    page = parse_tjpa_search_response(
        _load("tjpa_jurisprudencia_bff_empty.json"),
        query=JurisprudenceQuery(text="termo"),
        trace=SourceTrace(provider="tjpa_jurisprudencia_bff", endpoint="/buscar"),
    )
    assert page.results == []
    assert page.total == 0
    assert page.total_known is True
    assert page.is_explicit_empty is True


def test_tjpa_result_exposes_explicit_second_degree_identity() -> None:
    page = parse_tjpa_search_response(
        _load("tjpa_jurisprudencia_bff_results.json"),
        query=JurisprudenceQuery(text="termo"),
        trace=SourceTrace(provider="tjpa_jurisprudencia_bff", endpoint="/buscar"),
    )
    result = page.results[0]
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.branch == "state"
    assert result.authority == "TJPA"
    assert result.collection == "CJSG"
    assert result.document_type == "acordao"


def test_tjpa_inline_document_is_exposed_after_search_parse() -> None:
    trace = SourceTrace(provider="tjpa_jurisprudencia_bff", endpoint="/buscar")
    page = parse_tjpa_search_response(
        _load("tjpa_jurisprudencia_bff_results.json"),
        query=JurisprudenceQuery(text="termo"),
        trace=trace,
    )
    provider = TjpaJurisprudenciaBffProvider()
    result = page.results[0]
    provider._inline_documents[result.id] = (result.full_text or "", result.full_text or "", trace)
    document = provider.get_document(result.id)
    assert document.text == result.full_text
    assert document.raw_metadata["inline"] is True
    bundle = provider.get_decisions(result.id)
    assert bundle.texts[0]["content"] == result.full_text
    assert bundle.raw["inline"] is True


def test_tjpa_rejects_first_degree_scope_before_transport() -> None:
    provider = TjpaJurisprudenciaBffProvider()
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="termo", degree="first"))


def test_tjpa_invalid_fixture_is_rejected() -> None:
    with pytest.raises(ParserContractChangedError, match="stable id"):
        parse_tjpa_search_response(
            _load("tjpa_jurisprudencia_bff_invalid.json"),
            query=JurisprudenceQuery(text="termo"),
            trace=SourceTrace(provider="tjpa_jurisprudencia_bff", endpoint="/buscar"),
        )
