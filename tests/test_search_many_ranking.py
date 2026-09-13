from __future__ import annotations

import threading
import time

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import InvalidQueryError
from nanojuris.models import (
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
)
from nanojuris.relevance import BM25_VERSION, RANKING_VERSION


class WaveFixtureProvider:
    """Small provider used to prove that explicit waves are real boundaries."""

    def __init__(self, name: str, events: list[tuple[str, str]], lock: threading.Lock) -> None:
        self.name = name
        self._events = events
        self._lock = lock

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        with self._lock:
            self._events.append(("start", self.name))
        time.sleep(0.01)
        with self._lock:
            self._events.append(("end", self.name))
        return SearchPage(
            source=self.name,
            total=1,
            start=1,
            end=1,
            page=query.page,
            page_size=query.page_size,
            results=[
                JurisprudenceResult(
                    id=f"{self.name}-result",
                    source=self.name,
                    court=self.name.upper(),
                    type="acordao",
                    summary="Responsabilidade civil administrativa.",
                )
            ],
            is_complete=True,
            total_known=True,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name=self.name,
            source_url=f"https://{self.name}.example",
            category="jurisprudence",
            search_modes=["text"],
            supported_filters=["text"],
            supports_unified_search=True,
        )


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
                    raw={"_score": 0.1},
                ),
                JurisprudenceResult(
                    id="relevant",
                    source=self.name,
                    court="TJSP",
                    type="decision",
                    summary="Responsabilidade civil administrativa por falha do serviço público.",
                    full_text="Responsabilidade civil administrativa e dano decorrente.",
                    raw={"_score": 2.0},
                ),
            ],
            ordering="source_relevance",
            is_complete=True,
            total_known=True,
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


class LegacyOnlyFixtureProvider:
    """Provider kept outside the unified contract for compatibility tests."""

    name = "legacy_only_fixture"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return SearchPage(
            source=self.name,
            total=1,
            start=0,
            end=1,
            page=query.page,
            page_size=query.page_size,
            results=[
                JurisprudenceResult(
                    id="legacy-result",
                    source=self.name,
                    court="TJSP",
                    type="decision",
                    summary="Responsabilidade civil em contrato administrativo.",
                )
            ],
            is_complete=True,
            total_known=True,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="Fixture legado",
            source_url="https://example.test/legacy",
            category="jurisprudence",
            search_modes=["text"],
            supported_filters=["text"],
            supports_unified_search=False,
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
    metadata = next(
        value for key, value in payload["ranking"].items() if key.endswith('"relevant"]')
    )
    irrelevant = next(
        value for key, value in payload["ranking"].items() if key.endswith('"irrelevant"]')
    )
    assert metadata["relevance_score"] > irrelevant["relevance_score"]
    assert metadata["match_reasons"]
    assert metadata["native_rank"] == 1
    assert irrelevant["native_rank"] == 2
    assert payload["ranking"]["ranking_fixture:relevant"] == metadata
    assert payload["query_intent"]["analyzer_version"] == "legal-intent-v1"


def test_search_many_keeps_legacy_payload_without_opt_in_ranking() -> None:
    payload = NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
        "responsabilidade civil administrativa",
        sources=["ranking_fixture"],
    )

    assert "ranking_version" not in payload
    assert payload["results"][0].id == "relevant"


def test_search_many_legacy_mode_calls_explicit_non_unified_provider() -> None:
    payload = NanoJurisClient(providers=[LegacyOnlyFixtureProvider()]).search_many(
        "responsabilidade civil",
        sources=["legacy_only_fixture"],
        mode="legacy",
    )

    assert payload["searched_sources"] == ["legacy_only_fixture"]
    assert payload["skipped_sources"] == []
    assert payload["results"][0].id == "legacy-result"
    assert payload["source_outcomes"][0]["status"] == "searched"


def test_search_many_rejects_unknown_ranking_version() -> None:
    with pytest.raises(InvalidQueryError, match="versao de ranking desconhecida"):
        NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
            "divórcio",
            sources=["ranking_fixture"],
            ranking_version="future-v2",
        )


def test_search_many_adaptive_mode_emits_bounded_plan_and_uses_v1_by_default() -> None:
    payload = NanoJurisClient(providers=[RankingFixtureProvider()]).search_many(
        "responsabilidade civil administrativa",
        mode="adaptive",
    )

    assert payload["mode"] == "adaptive"
    assert payload["search_plan"]["sources"] == ["ranking_fixture"]
    assert payload["ranking_version"] == RANKING_VERSION
    assert payload["bm25_version"] == BM25_VERSION
    assert payload["results"][0].id == "relevant"
    assert payload["source_outcomes_v2"]["ranking_fixture"]["status"] == "success_with_results"


def test_search_many_executes_explicit_plan_waves_sequentially() -> None:
    events: list[tuple[str, str]] = []
    lock = threading.Lock()
    names = [f"wave_{index}" for index in range(6)]
    providers = [WaveFixtureProvider(name, events, lock) for name in names]
    config = NanoJurisConfig(unified_max_workers=6, unified_timeout=5.0)

    payload = NanoJurisClient(config=config, providers=providers).search_many(
        "responsabilidade civil",
        mode="selected",
        sources=names,
    )

    assert [
        source for wave in payload["search_plan"]["waves"] for source in wave["sources"]
    ] == names
    first_wave = set(names[:3])
    second_wave = set(names[3:])
    # Every source in the first wave must have completed before any second-wave
    # request starts.  This is the observable invariant that the old all-at-once
    # executor violated.
    first_wave_end = max(
        index
        for index, (kind, source) in enumerate(events)
        if kind == "end" and source in first_wave
    )
    second_wave_start = min(
        index
        for index, (kind, source) in enumerate(events)
        if kind == "start" and source in second_wave
    )
    assert first_wave_end < second_wave_start
    assert [item.id for item in payload["results"]] == [f"{name}-result" for name in names]
