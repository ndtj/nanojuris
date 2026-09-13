from __future__ import annotations

import pytest

from nanojuris.pagination import authoritative_total_reached, page_completeness


@pytest.mark.parametrize(
    ("total", "start", "returned", "authoritative", "expected"),
    [
        (0, 0, 0, True, True),
        (2, 1, 2, True, True),
        (10, 1, 2, True, False),
        (10, 9, 2, True, True),
        (10, 0, 0, True, False),
        (2, 1, 2, False, None),
        (None, 1, 2, True, None),
    ],
)
def test_page_completeness_is_conservative(
    total: int | None,
    start: int,
    returned: int,
    authoritative: bool,
    expected: bool | None,
) -> None:
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=returned,
        total_is_authoritative=authoritative,
    )

    assert complete is expected
    assert reason


@pytest.mark.parametrize(
    ("reported_total", "total_known", "returned", "accumulated", "expected"),
    [
        (0, True, 0, 0, True),
        # A legacy zero sentinel must not truncate a non-empty response.
        (0, True, 2, 2, False),
        (0, True, 0, 2, False),
        (2, True, 2, 2, True),
        (3, True, 2, 2, False),
        (3, False, 3, 3, False),
        (None, True, 3, 3, False),
    ],
)
def test_authoritative_total_never_treats_zero_with_rows_as_complete(
    reported_total: int | None,
    total_known: bool | None,
    returned: int,
    accumulated: int,
    expected: bool,
) -> None:
    assert (
        authoritative_total_reached(
            reported_total=reported_total,
            total_known=total_known,
            returned=returned,
            accumulated=accumulated,
        )
        is expected
    )


def test_provider_iter_pages_never_yields_more_than_max_records() -> None:
    from nanojuris.models import (
        JurisprudenceQuery,
        JurisprudenceResult,
        ProviderCapabilities,
        SearchPage,
    )
    from nanojuris.providers.base import JurisprudenceProvider

    class FakeProvider:
        def search(self, query):
            results = [
                JurisprudenceResult(
                    id=f"id-{index}",
                    source="fake",
                    court="FAKE",
                    type="acordao",
                    summary="fixture",
                )
                for index in range((query.page - 1) * 3, query.page * 3)
            ]
            return SearchPage(
                source="fake",
                total=100,
                start=(query.page - 1) * 3 + 1,
                end=query.page * 3,
                page=query.page,
                page_size=3,
                results=results,
                pagination_mode="page",
                is_complete=False,
            )

        def get_capabilities(self):
            return ProviderCapabilities(
                source="fake",
                display_name="Fake",
                source_url="https://example.test",
                category="jurisprudence",
                pagination_mode="page",
            )

    pages = list(
        JurisprudenceProvider.iter_pages(
            FakeProvider(), JurisprudenceQuery(text="term", page_size=3), max_records=5
        )
    )

    assert [len(page.results) for page in pages] == [3, 2]
    assert pages[-1].is_complete is False
    assert "max_records" in (pages[-1].completeness_reason or "")


def test_provider_iter_pages_stops_on_a_repeated_source_page() -> None:
    from nanojuris.models import (
        JurisprudenceQuery,
        JurisprudenceResult,
        ProviderCapabilities,
        SearchPage,
    )
    from nanojuris.providers.base import JurisprudenceProvider

    class RepeatingProvider:
        def search(self, query):
            result = JurisprudenceResult(
                id="same-id",
                source="fake",
                court="FAKE",
                type="acordao",
                summary="fixture",
            )
            return SearchPage(
                source="fake",
                total=100,
                start=1,
                end=1,
                page=query.page,
                page_size=1,
                results=[result],
                pagination_mode="page",
                is_complete=False,
            )

        def get_capabilities(self):
            return ProviderCapabilities(
                source="fake",
                display_name="Fake",
                source_url="https://example.test",
                category="jurisprudence",
                pagination_mode="page",
            )

    pages = list(
        JurisprudenceProvider.iter_pages(
            RepeatingProvider(), JurisprudenceQuery(text="term", page_size=1)
        )
    )

    assert len(pages) == 2
    assert pages[0].results
    assert pages[1].results == []
    assert pages[1].is_complete is False
    assert "repetiu" in (pages[1].completeness_reason or "")


def test_provider_iter_pages_deduplicates_missing_ids_without_collapsing_distinct_numbers() -> None:
    from nanojuris.models import (
        JurisprudenceQuery,
        JurisprudenceResult,
        ProviderCapabilities,
        SearchPage,
    )
    from nanojuris.providers.base import JurisprudenceProvider

    class ProviderWithUnreliableIds:
        def search(self, query):
            if query.page == 1:
                results = [
                    JurisprudenceResult(
                        id="",
                        source="fake",
                        court="TJXX",
                        type="acordao",
                        number="100/2025",
                    ),
                    JurisprudenceResult(
                        id="",
                        source="fake",
                        court="TJXX",
                        type="acordao",
                        number="101/2025",
                    ),
                ]
            else:
                results = [
                    JurisprudenceResult(
                        id="",
                        source="fake",
                        court="TJXX",
                        type="acordao",
                        number="100/2025",
                    ),
                ]
            return SearchPage(
                source="fake",
                total=100,
                start=1,
                end=len(results),
                page=query.page,
                page_size=2,
                results=results,
                pagination_mode="page",
                is_complete=False,
            )

        def get_capabilities(self):
            return ProviderCapabilities(
                source="fake",
                display_name="Fake",
                source_url="https://example.test",
                category="jurisprudence",
                pagination_mode="page",
            )

    pages = list(
        JurisprudenceProvider.iter_pages(
            ProviderWithUnreliableIds(), JurisprudenceQuery(text="term", page_size=2)
        )
    )

    assert [result.number for result in pages[0].results] == ["100/2025", "101/2025"]
    assert pages[1].results == []
    assert "repetiu" in (pages[1].completeness_reason or "")
