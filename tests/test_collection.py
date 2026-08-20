from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from nanojuris.collection import CollectionRunner
from nanojuris.models import DecisionBundle, JurisprudenceQuery, JurisprudenceResult, SearchPage
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.store import SQLiteStore


class FakePagedProvider(JurisprudenceProvider):
    name = "fake_collection"

    def __init__(self) -> None:
        self.calls: list[int] = []

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.calls.append(query.page)
        pages = {
            1: [self._result("a"), self._result("b")],
            2: [self._result("b"), self._result("c")],
        }
        results = pages.get(query.page, [])
        return SearchPage(
            source=self.name,
            total=3,
            start=((query.page - 1) * 2) + 1 if results else 0,
            end=((query.page - 1) * 2) + len(results) if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            pagination_mode="page",
            is_complete=query.page >= 2,
            completeness_reason="fixture complete" if query.page >= 2 else None,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(precedent_id=precedent_id, source=self.name)

    def _result(self, identifier: str) -> JurisprudenceResult:
        return JurisprudenceResult(
            id=identifier,
            source=self.name,
            court="TJXX",
            type="acordao",
            number=f"0000000-00.2025.8.00.{identifier}",
            summary=f"Ementa {identifier}",
        )


def test_collection_runner_resumes_checkpoint_and_deduplicates() -> None:
    checkpoint = Path(".tmp") / f"collection-{uuid4().hex}.json"
    try:
        query = JurisprudenceQuery(text="responsabilidade", page_size=2)
        provider = FakePagedProvider()
        with SQLiteStore(":memory:") as store:
            first = CollectionRunner(
                provider,
                store=store,
                checkpoint_path=checkpoint,
                max_pages=1,
            ).collect(query)
            assert first.complete is False
            assert first.stop_reason == "max_pages"
            assert first.duplicate_records == 0
            assert store.count() == 2

            second = CollectionRunner(
                provider,
                store=store,
                checkpoint_path=checkpoint,
                max_pages=2,
            ).collect(query)
            assert second.complete is True
            assert second.stop_reason == "fixture complete"
            assert second.duplicate_records == 1
            assert store.count() == 3
            assert provider.calls == [1, 2]
    finally:
        checkpoint.unlink(missing_ok=True)


def test_collection_runner_replays_partially_consumed_page_after_record_cap() -> None:
    checkpoint = Path(".tmp") / f"collection-cap-{uuid4().hex}.json"
    try:
        query = JurisprudenceQuery(text="responsabilidade", page_size=2)
        provider = FakePagedProvider()
        with SQLiteStore(":memory:") as store:
            first = CollectionRunner(
                provider,
                store=store,
                checkpoint_path=checkpoint,
                max_pages=1,
                max_records=1,
            ).collect(query)
            assert first.stop_reason == "max_records"
            assert first.next_page == 1
            assert store.count() == 1

            second = CollectionRunner(
                provider,
                store=store,
                checkpoint_path=checkpoint,
                max_pages=2,
                max_records=10,
            ).collect(query)
            assert second.complete is True
            assert store.count() == 3
            assert provider.calls == [1, 1, 2]
    finally:
        checkpoint.unlink(missing_ok=True)
