from __future__ import annotations

import errno
import json
from pathlib import Path
from uuid import uuid4

import pytest

from nanojuris.collection import CollectionCheckpoint, CollectionRunner
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


class MixedValidityProvider(FakePagedProvider):
    name = "fake_mixed_validity"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.calls.append(query.page)
        result = self._result("valid")
        return SearchPage(
            source=self.name,
            total=2,
            start=1,
            end=2,
            page=query.page,
            page_size=query.page_size,
            # Providers are expected to return JurisprudenceResult values;
            # this malformed item simulates a broken adapter response.
            results=[result, object()],  # type: ignore[list-item]
            pagination_mode="page",
            is_complete=True,
            completeness_reason="fixture complete",
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


def test_collection_checkpoint_records_contract_query_and_page_fingerprints() -> None:
    checkpoint = Path(".tmp") / f"collection-fingerprint-{uuid4().hex}.json"
    try:
        report = CollectionRunner(
            FakePagedProvider(), checkpoint_path=checkpoint, max_pages=1
        ).collect(
            JurisprudenceQuery(text="responsabilidade", party_document="123456789", oab="SP12345")
        )

        stored = CollectionCheckpoint.from_path(checkpoint)
        assert stored.schema_version == 2
        assert stored.run_id == report.run_id
        assert stored.query_fingerprint == report.query_fingerprint
        assert stored.contract_fingerprint == report.contract_fingerprint
        assert stored.query["party_document"] == "<redacted>"
        assert stored.query["oab"] == "<redacted>"
        assert len(stored.page_fingerprints) == 1
        assert stored.attempts == 1
        assert stored.outcome == "paused"
        assert report.freshness is not None
        assert report.freshness.source_updated_at is None
        assert report.freshness.coverage_end_known is False
        assert report.manifest is not None
        assert report.manifest.schema_version == "nanojuris-collection-manifest-v1"
        assert report.manifest.query_fingerprint == report.query_fingerprint
        assert report.manifest.query["party_document"] == "<redacted>"
        assert report.manifest.complete is False
        assert report.manifest.outcome == "paused"
        assert report.to_dict()["manifest"]["freshness"]["source_updated_at"] is None
    finally:
        checkpoint.unlink(missing_ok=True)


def test_collection_runner_marks_completed_checkpoint_without_deleting_audit() -> None:
    checkpoint = Path(".tmp") / f"collection-complete-{uuid4().hex}.json"
    try:
        report = CollectionRunner(
            FakePagedProvider(), checkpoint_path=checkpoint, max_pages=3
        ).collect(JurisprudenceQuery())
        stored = CollectionCheckpoint.from_path(checkpoint)
        assert report.complete is True
        assert stored.outcome == "complete"
        assert stored.last_error is None
    finally:
        checkpoint.unlink(missing_ok=True)


def test_collection_runner_rejects_contract_changed_checkpoint() -> None:
    class MutableContractProvider(FakePagedProvider):
        def __init__(self) -> None:
            super().__init__()
            self.contract = "v1"

        def get_parameters(self):
            return {"contract": self.contract}

    checkpoint = Path(".tmp") / f"collection-contract-{uuid4().hex}.json"
    try:
        provider = MutableContractProvider()
        CollectionRunner(provider, checkpoint_path=checkpoint, max_pages=1).collect(
            JurisprudenceQuery(text="responsabilidade")
        )
        provider.contract = "v2"
        with pytest.raises(ValueError, match="contrato atual"):
            CollectionRunner(provider, checkpoint_path=checkpoint).collect(
                JurisprudenceQuery(text="responsabilidade")
            )
    finally:
        checkpoint.unlink(missing_ok=True)


def test_collection_runner_rejects_legacy_checkpoint_without_fingerprints() -> None:
    checkpoint = Path(".tmp") / f"collection-legacy-{uuid4().hex}.json"
    try:
        CollectionCheckpoint(
            schema_version=1,
            source=FakePagedProvider.name,
            query={"text": "responsabilidade", "page": 1},
            next_page=2,
        ).write_atomic(checkpoint)
        with pytest.raises(ValueError, match="checkpoint legado"):
            CollectionRunner(FakePagedProvider(), checkpoint_path=checkpoint).collect(
                JurisprudenceQuery(text="responsabilidade")
            )
    finally:
        checkpoint.unlink(missing_ok=True)


def test_collection_checkpoint_atomic_write_cleans_temporary_file_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkpoint = tmp_path / "collection.json"

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr("nanojuris.collection.os.replace", fail_replace)
    with pytest.raises(OSError, match="replace failure"):
        CollectionCheckpoint(
            schema_version=2,
            source="fake",
            query={},
            next_page=1,
        ).write_atomic(checkpoint)

    assert not list(tmp_path.glob("*.tmp"))


def test_collection_checkpoint_atomic_write_surfaces_disk_full(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A durability failure must be visible and leave no staging file behind."""

    checkpoint = tmp_path / "collection.json"

    def fail_fsync(_fd: int) -> None:
        raise OSError(errno.ENOSPC, "simulated disk full")

    monkeypatch.setattr("nanojuris.collection.os.fsync", fail_fsync)
    with pytest.raises(OSError) as error:
        CollectionCheckpoint(
            schema_version=2,
            source="fake",
            query={},
            next_page=1,
        ).write_atomic(checkpoint)

    assert error.value.errno == errno.ENOSPC
    assert not checkpoint.exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_collection_manifest_and_checkpoint_schema_artifacts_are_versioned() -> None:
    root = Path(__file__).parents[1] / "docs" / "schemas"
    checkpoint_schema = json.loads(
        (root / "collection-checkpoint-v2.schema.json").read_text(encoding="utf-8")
    )
    manifest_schema = json.loads(
        (root / "collection-manifest-v1.schema.json").read_text(encoding="utf-8")
    )
    tombstone_schema = json.loads(
        (root / "tombstone-evidence-v1.schema.json").read_text(encoding="utf-8")
    )

    assert checkpoint_schema["properties"]["schema_version"]["const"] == 2
    assert manifest_schema["properties"]["schema_version"]["const"] == (
        "nanojuris-collection-manifest-v1"
    )
    assert tombstone_schema["properties"]["schema_version"]["const"] == (
        "nanojuris-tombstone-evidence-v1"
    )


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


def test_collection_runner_keeps_valid_records_and_quarantines_invalid_items() -> None:
    provider = MixedValidityProvider()

    report = CollectionRunner(provider).collect(JurisprudenceQuery(page_size=2))

    assert report.records_saved == 1
    assert len(report.records) == 1
    assert report.records[0].id == "valid"
    assert report.records_seen == 2
    assert report.invalid_records == 1
    assert report.complete is True
    assert report.stop_reason == "fixture complete"
    assert len(report.failures) == 1
    failure = report.failures[0]
    assert failure.page == 1
    assert failure.record_index == 1
    assert failure.error_type == "AttributeError"
    assert failure.record_identity is not None


def test_collection_runner_does_not_mark_all_invalid_page_complete() -> None:
    class InvalidOnlyProvider(MixedValidityProvider):
        def search(self, query: JurisprudenceQuery) -> SearchPage:
            page = super().search(query)
            page.results = [object()]  # type: ignore[list-item]
            page.total = 1
            page.end = 1
            return page

    report = CollectionRunner(InvalidOnlyProvider()).collect(JurisprudenceQuery())

    assert report.records_saved == 0
    assert report.invalid_records == 1
    assert report.complete is False
    assert report.stop_reason == "invalid_records"


def test_collection_runner_reports_repeated_page_when_no_records_are_invalid() -> None:
    class RepeatingProvider(FakePagedProvider):
        name = "fake_repeating"

        def search(self, query: JurisprudenceQuery) -> SearchPage:
            self.calls.append(query.page)
            return SearchPage(
                source=self.name,
                total=99,
                start=1,
                end=1,
                page=query.page,
                page_size=query.page_size,
                results=[self._result("same")],
                pagination_mode="page",
                is_complete=False,
            )

    report = CollectionRunner(RepeatingProvider(), max_pages=5).collect(JurisprudenceQuery())

    assert report.invalid_records == 0
    assert report.duplicate_records >= 1
    assert report.stop_reason == "repeated_page"


def test_collection_runner_rejects_known_zero_total_with_rows() -> None:
    class ContradictoryTotalProvider(FakePagedProvider):
        name = "fake_contradictory_total"

        def search(self, query: JurisprudenceQuery) -> SearchPage:
            self.calls.append(query.page)
            return SearchPage(
                source=self.name,
                total=0,
                total_known=True,
                start=1,
                end=1,
                page=query.page,
                page_size=query.page_size,
                results=[self._result("row")],
                pagination_mode="page",
                is_complete=False,
            )

    provider = ContradictoryTotalProvider()
    report = CollectionRunner(provider, max_pages=5).collect(JurisprudenceQuery())

    assert report.records_saved == 1
    assert report.complete is False
    assert report.stop_reason == "inconsistent_total"
    assert provider.calls == [1]


def test_collection_runner_invalid_items_do_not_consume_record_cap() -> None:
    provider = MixedValidityProvider()

    report = CollectionRunner(provider, max_records=1).collect(JurisprudenceQuery())

    assert report.records_saved == 1
    assert report.records[0].id == "valid"
    assert report.invalid_records == 1
    assert report.stop_reason == "fixture complete"


class _ScenarioProvider(FakePagedProvider):
    """Configurable provider used to exercise the stop_reason taxonomy."""

    name = "fake_scenario"

    def __init__(self, mode: str) -> None:
        super().__init__()
        self.mode = mode

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.calls.append(query.page)
        if self.mode == "provider_error":
            raise RuntimeError("upstream boom")

        page = query.page
        if self.mode == "no_results":
            results: list = []
            is_complete = False
        elif self.mode == "provider_complete":
            results = [self._result(f"c{page}")]
            is_complete = True
        elif self.mode == "repeated_page":
            results = [self._result("same")]
            is_complete = False
        elif self.mode == "invalid_records":
            results = [object()]  # type: ignore[list-item]
            is_complete = False
        else:  # never_complete: fresh unique records forever
            results = [self._result(f"{self.mode}-{page}-a"), self._result(f"{self.mode}-{page}-b")]
            is_complete = False

        return SearchPage(
            source=self.name,
            total=999,
            start=1,
            end=len(results),
            page=page,
            page_size=query.page_size,
            results=results,
            pagination_mode="page",
            is_complete=is_complete,
            completeness_reason="provider says done" if is_complete else None,
        )


# stop_reason -> (provider mode, runner kwargs, expected complete)
_STOP_REASON_CASES = {
    "no_results": ("no_results", {}, True),
    "provider_complete": ("provider_complete", {}, True),
    "max_pages": ("never_complete", {"max_pages": 2}, False),
    "max_records": ("never_complete", {"max_records": 3}, False),
    "repeated_page": ("repeated_page", {"max_pages": 5}, False),
    "invalid_records": ("invalid_records", {"max_pages": 5}, False),
    "provider_error": ("provider_error", {}, False),
}


@pytest.mark.parametrize("expected_reason", sorted(_STOP_REASON_CASES))
def test_collection_runner_stop_reason_matches_completeness(expected_reason: str) -> None:
    mode, kwargs, expected_complete = _STOP_REASON_CASES[expected_reason]

    report = CollectionRunner(_ScenarioProvider(mode), **kwargs).collect(JurisprudenceQuery())

    if expected_reason == "provider_complete":
        # completeness_reason from the provider is surfaced verbatim.
        assert report.stop_reason == "provider says done"
    else:
        assert report.stop_reason == expected_reason
    assert report.complete is expected_complete
    # A terminated (not completed) collection must never claim completeness.
    assert report.complete is (report.stop_reason in {"no_results", "provider says done"})
