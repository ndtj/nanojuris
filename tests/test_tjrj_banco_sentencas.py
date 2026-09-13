from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, QueryRejectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjrj_banco_sentencas import (
    TjrjBancoSentencasProvider,
    parse_tjrj_banco_sentencas_pages,
)

ROOT = Path(__file__).resolve().parents[1]


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="tjrj_banco_sentencas",
        endpoint="GET /documents/10136/18187/banco-sentencas.pdf",
        source_url="https://portaltj.tjrj.jus.br/documents/10136/18187/banco-sentencas.pdf",
        http_status=200,
        retrieval_status="ok",
    )


def _pages() -> list[tuple[str, list[str]]]:
    payload = json.loads(
        (ROOT / "tests/fixtures/tjrj_banco_sentencas_index.json").read_text(encoding="utf-8")
    )
    return [(str(item["text"]), list(item["document_urls"])) for item in payload["pages"]]


def test_parser_proves_first_degree_and_links_only_allowlisted_documents() -> None:
    results = parse_tjrj_banco_sentencas_pages(
        _pages(),
        query=JurisprudenceQuery(text="responsabilidade administração"),
        trace=_trace(),
    )
    assert len(results) == 2
    assert all(result.degree == "first" for result in results)
    assert all(result.instance == "first" for result in results)
    assert all(result.authority == "TJRJ" for result in results)
    assert all(result.collection == "TJRJ_BANCO_SENTENCAS" for result in results)
    assert results[0].document_url.startswith("https://www4.tjrj.jus.br/")
    assert all(result.raw["source_record_id"] == result.id for result in results)
    assert all("source_record_id" in result.field_provenance for result in results)


def test_parser_applies_local_terms_and_negative_terms() -> None:
    results = parse_tjrj_banco_sentencas_pages(
        _pages(),
        query=JurisprudenceQuery(text="divórcio"),
        trace=_trace(),
    )
    assert len(results) == 1
    assert results[0].number == "0003463-71.2010.8.19.0073"
    excluded = parse_tjrj_banco_sentencas_pages(
        _pages(),
        query=JurisprudenceQuery(text="divórcio", without_words="civil"),
        trace=_trace(),
    )
    assert excluded == []


def test_empty_and_invalid_payloads_are_distinct() -> None:
    empty = parse_tjrj_banco_sentencas_pages(
        [("Banco de Sentencas TJRJ\\nNenhuma entrada publicada.", [])],
        query=JurisprudenceQuery(text="divÃ³rcio"),
        trace=_trace(),
    )
    assert empty == []
    from nanojuris.providers.tjrj_banco_sentencas import parse_tjrj_banco_sentencas_pdf

    with pytest.raises(ParserContractChangedError):
        parse_tjrj_banco_sentencas_pdf(
            b"<!doctype html>", query=JurisprudenceQuery(text="x"), trace=_trace()
        )


def test_untrusted_document_annotations_are_discarded() -> None:
    results = parse_tjrj_banco_sentencas_pages(
        [
            (
                "0003463-71.2010.8.19.0073 divÃ³rcio",
                [
                    "https://example.invalid/processo/1.doc",
                    "https://www4.tjrj.jus.br/AtosOficiais/bancodesentencas/a.doc",
                ],
            )
        ],
        query=JurisprudenceQuery(text="divÃ³rcio"),
        trace=_trace(),
    )
    assert results[0].document_url is None


def test_capabilities_keep_curated_index_opt_in() -> None:
    capabilities = TjrjBancoSentencasProvider(NanoJurisConfig()).get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.completeness_contract == "curated_pdf_index_total_unknown"
    assert capabilities.filter_status("case_class") == "unsupported"


@pytest.mark.parametrize("degree", ["second", "2", "cjsg"])
def test_provider_rejects_non_first_degree_scope(degree: str) -> None:
    provider = TjrjBancoSentencasProvider(NanoJurisConfig())
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="divórcio", degree=degree))
