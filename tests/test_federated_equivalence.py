from __future__ import annotations

from nanojuris.federated import merge_federated_pages
from nanojuris.models import JurisprudenceResult, SearchPage
from nanojuris.relevance import LegalLiveRanker, RankedResult

_TEXT = (
    "Responsabilidade civil administrativa demonstrada em decisão pública com "
    "fundamentação completa, análise de dano, nexo causal, serviço público e "
    "reparação integral para a parte autora."
)


def _page(source: str, result: JurisprudenceResult) -> SearchPage:
    return SearchPage(
        source=source,
        total=1,
        start=0,
        end=1,
        page=1,
        page_size=10,
        results=[result],
        total_known=True,
        is_complete=True,
    )


def test_federated_merge_groups_same_published_text_across_sources() -> None:
    first = JurisprudenceResult(
        id="a",
        source="tj-a",
        court="TJSP",
        type="decision",
        summary=_TEXT,
        judgment_date="2024-01-02",
    )
    second = JurisprudenceResult(
        id="b",
        source="tj-b",
        court="TJSP",
        type="decision",
        summary=_TEXT,
        judgment_date="2024-01-02",
    )

    merged = merge_federated_pages(
        {"tj-a": [_page("tj-a", first)], "tj-b": [_page("tj-b", second)]}
    )

    assert len(merged.results) == 1
    assert merged.duplicate_count == 1
    assert list(merged.duplicate_groups.values()) == [("tj-a", "tj-b")]


def test_republication_type_is_not_merged_by_text_fingerprint() -> None:
    original = JurisprudenceResult(
        id="a",
        source="tj-a",
        court="TJSP",
        type="decision",
        summary=_TEXT,
        judgment_date="2024-01-02",
    )
    republication = JurisprudenceResult(
        id="b",
        source="tj-b",
        court="TJSP",
        type="republicação",
        summary=_TEXT,
        judgment_date="2024-01-02",
    )

    merged = merge_federated_pages(
        {"tj-a": [_page("tj-a", original)], "tj-b": [_page("tj-b", republication)]}
    )

    assert len(merged.results) == 2
    assert merged.duplicate_count == 0


def test_diversity_only_swaps_a_near_tie() -> None:
    def item(source: str, score: float, identifier: str) -> RankedResult:
        return RankedResult(
            record=JurisprudenceResult(id=identifier, source=source, court="TJ", type="decision"),
            relevance_score=score,
        )

    near = LegalLiveRanker.diversify_near_ties(
        [item("a", 80.0, "1"), item("a", 79.0, "2"), item("b", 78.5, "3")]
    )
    far = LegalLiveRanker.diversify_near_ties(
        [item("a", 80.0, "1"), item("a", 70.0, "2"), item("b", 60.0, "3")]
    )

    assert [row.record.source for row in near] == ["a", "b", "a"]
    assert [row.record.source for row in far] == ["a", "a", "b"]
