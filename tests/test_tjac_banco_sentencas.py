from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import QueryRejectedError
from nanojuris.models import AccessStatus, JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjac_banco_sentencas import (
    TjacBancoSentencasProvider,
    parse_tjac_banco_sentencas,
)

ROOT = Path(__file__).resolve().parents[1]


def _markup() -> str:
    return (ROOT / "tests/fixtures/tjac_banco_sentencas_index.html").read_text(encoding="utf-8")


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="tjac_banco_sentencas",
        endpoint="GET /coger/banco-de-sentencas/",
        source_url="https://www.tjac.jus.br/coger/banco-de-sentencas/",
        http_status=200,
        retrieval_status="ok",
    )


def test_parser_keeps_first_degree_identity_and_official_links() -> None:
    results = parse_tjac_banco_sentencas(
        _markup(), query=JurisprudenceQuery(text="responsabilidade civil"), trace=_trace()
    )
    assert len(results) == 1
    result = results[0]
    assert result.authority == "TJAC"
    assert result.branch == "state"
    assert result.degree == "first"
    assert result.instance == "first"
    assert result.collection == "CJPG"
    assert result.document_type == "sentenca"
    assert result.number == "0701071-98.2014.8.01.0002"
    assert result.document_url is not None
    assert result.document_url.startswith("https://www.tjac.jus.br/")
    assert result.access_status is AccessStatus.PUBLIC
    assert result.field_provenance["degree"]["source"] == "source_contract:tjac_banco_sentencas"


def test_parser_supports_number_and_rejects_untrusted_links() -> None:
    results = parse_tjac_banco_sentencas(
        _markup(),
        query=JurisprudenceQuery(number="0700001-12.2020.8.01.0001"),
        trace=_trace(),
    )
    assert len(results) == 1
    assert results[0].number == "0700001-12.2020.8.01.0001"
    assert all("example.invalid" not in (item.document_url or "") for item in results)


def test_provider_search_uses_local_html_window_and_unknown_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = TjacBancoSentencasProvider(NanoJurisConfig())
    monkeypatch.setattr(provider, "_request_index", lambda query: (_markup(), _trace()))
    page = provider.search(JurisprudenceQuery(text="sentença", page=1, page_size=1))
    assert page.pagination_mode == "local_html_window"
    assert page.total_known is False
    assert page.access_status is AccessStatus.PUBLIC
    assert len(page.results) == 1
    assert provider._items[page.results[0].id] == page.results[0].document_url


def test_capabilities_keep_curated_surface_opt_in() -> None:
    capabilities = TjacBancoSentencasProvider(NanoJurisConfig()).get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.completeness_contract == "curated_html_index_total_unknown"
    assert capabilities.filter_status("case_class") == "unsupported"


@pytest.mark.parametrize("degree", ["second", "2", "cjsg"])
def test_provider_rejects_non_first_degree_scope(degree: str) -> None:
    provider = TjacBancoSentencasProvider(NanoJurisConfig())
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="divórcio", degree=degree))


def test_provider_rejects_foreign_authority() -> None:
    provider = TjacBancoSentencasProvider(NanoJurisConfig())
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="x", authority="TJSP"))
