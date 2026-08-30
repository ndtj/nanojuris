from __future__ import annotations

from nanojuris.client import _record_identity
from nanojuris.collection import _result_identity
from nanojuris.models import CanonicalDecision, JurisprudenceResult


def _result(
    *,
    source: str,
    court: str = "TJXX",
    identifier: str = "",
    number: str = "",
    summary: str = "Ementa de teste",
) -> JurisprudenceResult:
    return JurisprudenceResult(
        id=identifier,
        source=source,
        court=court,
        type="acordao",
        number=number or None,
        summary=summary or None,
    )


def test_collection_identity_scopes_local_number_to_source_and_court() -> None:
    first = _result(source="source-a", number="123/2025")
    other_source = _result(source="source-b", number="123/2025")
    other_court = _result(source="source-a", court="TJYY", number="123/2025")

    assert _result_identity(first) != _result_identity(other_source)
    assert _result_identity(first) != _result_identity(other_court)


def test_collection_identity_keeps_same_source_id_deduplicated() -> None:
    first = _result(source="source-a", identifier="provider-id", number="123/2025")
    changed_metadata = _result(
        source="source-a",
        identifier="provider-id",
        number="different-local-number",
        summary="Outra representação do mesmo item",
    )

    assert _result_identity(first) == _result_identity(changed_metadata)


def test_cnj_identity_is_shared_across_sources() -> None:
    cnj = "0000001-02.2025.8.26.0001"
    first = _result(source="source-a", number=cnj)
    second = _result(source="source-b", court="TJSP", number=cnj)

    assert _result_identity(first) == _result_identity(second)


def test_fallback_identity_is_deterministic_and_distinguishes_semantics() -> None:
    first = _result(source="source-a", summary="Primeira ementa")
    same = _result(source="source-a", summary="  PRIMEIRA   EMENTA ")
    different = _result(source="source-a", summary="Segunda ementa")

    first.id = ""
    same.id = ""
    different.id = ""
    first.number = None
    same.number = None
    different.number = None

    first_key = _result_identity(first)
    assert first_key == _result_identity(same)
    assert first_key != _result_identity(different)
    assert "Primeira" not in first_key


def test_canonical_identity_uses_source_for_provider_ids_and_local_numbers() -> None:
    first = CanonicalDecision(
        id="same-id",
        source="source-a",
        court="TJXX",
        case_number="123/2025",
    )
    other_source = CanonicalDecision(
        id="same-id",
        source="source-b",
        court="TJXX",
        case_number="123/2025",
    )
    assert _record_identity(first) != _record_identity(other_source)


def test_canonical_identity_keeps_provider_ids_scoped_to_source() -> None:
    first = CanonicalDecision(
        id="same-id",
        source="source-a",
        court="TJXX",
        case_number="123/2025",
    )
    second = CanonicalDecision(
        id="same-id",
        source="source-b",
        court="TJSP",
        case_number="123/2025",
    )
    assert _record_identity(first) != _record_identity(second)


def test_canonical_identity_shares_formatted_cnj_without_provider_ids() -> None:
    first = CanonicalDecision(
        id="",
        source="source-a",
        court="TJXX",
        case_number="0000001-02.2025.8.26.0001",
    )
    second = CanonicalDecision(
        id="",
        source="source-b",
        court="TJSP",
        case_number="00000010220258260001",
    )
    assert _record_identity(first) == _record_identity(second)
