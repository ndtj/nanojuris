from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.errors import InvalidQueryError
from nanojuris.models import (
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
)
from nanojuris.relevance import BM25_VERSION, RANKING_VERSION


class RankingFixtureProvider:
    name = "ranking_fixture"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return SearchPage(
            source=self.name,
            total=2,
            start=0,
            end=2,
            page=query.page,
            page_size=query.page_size,
            results=[
                JurisprudenceResult(
                    id="irrelevant",
                    source=self.name,
                    court="TJSP",
                    type="decision",
                    summary="Divórcio e partilha de bens.",
                ),
                JurisprudenceResult(
                    id="relevant",
                    source=self.name,
                    court="TJSP",
                    type="decision",
                    summary="Responsabilidade civil administrativa por falha do serviço público.",
                    full_text="Responsabilidade civil administrativa e dano decorrente.",
                ),
            ],
            is_complete=True,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="Fixture de ranking",
            source_url="https://example.test/ranking",
            category="jurisprudence",
            search_modes=["text"],
            canonical_records=["CanonicalDecision"],
            supports_unified_search=True,
        )


def test_search_many_opt_in_ranking_orders_records_and_exposes_reasons() -> None:
    payload = NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
        "responsabilidade civil administrativa",
        sources=["ranking_fixture"],
        ranking_version=RANKING_VERSION,
    )

    assert payload["ranking_version"] == RANKING_VERSION
    assert payload["bm25_version"] == BM25_VERSION
    assert payload["ranking_complete"] is True
    assert payload["results"][0].id == "relevant"
    metadata = next(value for value in payload["ranking"].values() if value["relevance_score"] > 0)
    irrelevant = next(
        value for value in payload["ranking"].values() if value["relevance_score"] == 0
    )
    assert metadata["relevance_score"] > irrelevant["relevance_score"]
    assert metadata["match_reasons"]
    assert metadata["native_rank"] == 2
    assert payload["query_intent"]["analyzer_version"] == "legal-intent-v1"


def test_ranking_gold_fixture_preserves_expected_top_result() -> None:
    fixture = json.loads(
        (Path(__file__).parent / "fixtures" / "ranking_gold.json").read_text(encoding="utf-8")
    )
    for case in fixture["cases"]:
        payload = NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
            case["query"],
            sources=["ranking_fixture"],
            ranking_version=RANKING_VERSION,
        )
        assert payload["results"][0].id == case["expected_top_id"]


def test_search_many_keeps_legacy_payload_without_opt_in_ranking() -> None:
    payload = NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
        "responsabilidade civil administrativa",
        sources=["ranking_fixture"],
    )

    assert "ranking_version" not in payload
    assert payload["results"][0].id == "relevant"


def test_search_many_rejects_unknown_ranking_version() -> None:
    with pytest.raises(InvalidQueryError, match="versao de ranking desconhecida"):
        NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
            "divórcio",
            sources=["ranking_fixture"],
            ranking_version="future-v2",
        )


def test_search_many_mode_selects_v1_by_default() -> None:
    payload = NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
        "responsabilidade civil administrativa",
        mode="adaptive",
    )

    assert payload["mode"] == "adaptive"
    assert payload["ranking_version"] == RANKING_VERSION
    assert payload["bm25_version"] == BM25_VERSION
    assert payload["results"][0].id == "relevant"
