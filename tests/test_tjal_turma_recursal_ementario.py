from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, QueryRejectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjal_turma_recursal_ementario import (
    TjalTurmaRecursalEmentarioProvider,
    parse_tjal_turma_recursal_pdf,
    parse_tjal_turma_recursal_text,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="tjal_turma_recursal_ementario",
        endpoint="GET /juizados/relatorios/Ementas-3.pdf",
        source_url="https://aceco.tjal.jus.br/juizados/relatorios/Ementas-3.pdf",
    )


def test_parser_preserves_recursal_identity_and_filters() -> None:
    text = (FIXTURES / "tjal_turma_recursal_success.txt").read_text(encoding="utf-8")
    records = parse_tjal_turma_recursal_text(
        text,
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=10),
        trace=_trace(),
    )
    assert len(records) == 1
    record = records[0]
    assert record.authority == "TJAL"
    assert record.branch == "state"
    assert record.degree == "recursal"
    assert record.instance == "turma_recursal"
    assert record.collection == "TJAL_TURMAS_RECURSAIS"
    assert record.number == "0001234-56.2024.8.02.0001"
    assert record.type == "acordao"
    assert "responsabilidade civil" in (record.summary or "").casefold()


def test_parser_applies_number_and_negative_terms() -> None:
    text = (FIXTURES / "tjal_turma_recursal_success.txt").read_text(encoding="utf-8")
    trace = _trace()
    exact = parse_tjal_turma_recursal_text(
        text,
        query=JurisprudenceQuery(number="0009876-54.2023.8.02.0002"),
        trace=trace,
    )
    assert len(exact) == 1
    assert exact[0].number == "0009876-54.2023.8.02.0002"
    excluded = parse_tjal_turma_recursal_text(
        text,
        query=JurisprudenceQuery(text="divorcio", without_words="homologacao"),
        trace=trace,
    )
    assert excluded == []


def test_provider_rejects_non_recursal_scope() -> None:
    provider = TjalTurmaRecursalEmentarioProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError, match="recursal"):
        provider.search(JurisprudenceQuery(text="divorcio", degree="second"))
    with pytest.raises(QueryRejectedError, match="colecao"):
        provider.search(JurisprudenceQuery(text="divorcio", collection="CJSG"))


def test_provider_capability_is_opt_in_and_summary_only() -> None:
    capabilities = TjalTurmaRecursalEmentarioProvider().get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.supports_full_text is False
    assert capabilities.full_text_access == "summary_only"
    assert capabilities.completeness_contract == "static_volume_total_unknown"
    assert "case_class" in capabilities.unsupported_filters


def test_empty_fixture_is_not_an_authoritative_national_empty() -> None:
    empty = (FIXTURES / "tjal_turma_recursal_empty.txt").read_text(encoding="utf-8")
    records = parse_tjal_turma_recursal_text(
        empty, query=JurisprudenceQuery(text="divorcio"), trace=_trace()
    )
    assert records == []


def test_invalid_pdf_fixture_is_rejected() -> None:
    invalid = (FIXTURES / "tjal_turma_recursal_invalid.pdf").read_bytes()
    with pytest.raises(ParserContractChangedError, match="malformado"):
        parse_tjal_turma_recursal_pdf(
            invalid, query=JurisprudenceQuery(text="divorcio"), trace=_trace()
        )
