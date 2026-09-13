from __future__ import annotations

import json
from pathlib import Path

from nanojuris.client import _record_identity
from nanojuris.collection import _result_identity
from nanojuris.identity import match_legal_identities, resolve_legal_identity
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


def test_typed_identity_keeps_process_and_decision_distinct() -> None:
    cnj = "0000001-02.2025.8.26.0001"
    process = resolve_legal_identity(kind="process", source="source-a", case_number=cnj)
    decision_one = resolve_legal_identity(
        kind="decision",
        source="source-a",
        authority="TJSP",
        degree="second",
        case_number=cnj,
        record_type="acordao",
        event_date="2025-03-01",
        text="Primeira decisao",
    )
    decision_two = resolve_legal_identity(
        kind="decision",
        source="source-a",
        authority="TJSP",
        degree="second",
        case_number=cnj,
        record_type="acordao",
        event_date="2025-04-01",
        text="Segunda decisao",
    )

    assert process.key == "process:cnj:00000010220258260001"
    assert match_legal_identities(decision_one, decision_two).relation == "distinct"
    assert match_legal_identities(process, decision_one).relation == "distinct"


def test_typed_identity_returns_unknown_when_decision_evidence_is_insufficient() -> None:
    identity = resolve_legal_identity(
        kind="decision",
        source="source-a",
        case_number="0000001-02.2025.8.26.0001",
    )

    assert identity.key is None
    assert identity.unresolved_reason == "decision_requires_native_or_semantic_evidence"


def test_typed_identity_document_version_uses_parent_and_content_hash() -> None:
    document = resolve_legal_identity(
        kind="document",
        source="source-a",
        parent_key='decision:["source-a","d1"]',
        text="inteiro teor",
    )
    same_document = resolve_legal_identity(
        kind="document",
        source="source-b",
        parent_key='decision:["source-a","d1"]',
        text=" inteiro   teor ",
    )

    assert document.key == same_document.key
    assert document.evidence.rule == "parent_and_content_hash"


def test_collision_corpus_preserves_golden_relationships() -> None:
    fixture = Path(__file__).parent / "fixtures" / "identity_collision_corpus.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    for case in payload["cases"]:
        left = resolve_legal_identity(**case["left"])
        right = resolve_legal_identity(**case["right"])
        match = match_legal_identities(left, right)
        assert match.relation == case["expected_relation"], case["id"]


def test_identity_properties_and_mutation_guards() -> None:
    """Exercise deterministic, symmetric and mutation-resistant invariants."""

    base = resolve_legal_identity(
        kind="decision",
        source="TJSP",
        authority="TJSP",
        degree="Segundo grau",
        native_id="D-42",
        case_number="0000001-02.2025.8.26.0001",
        record_type="Acórdão",
        event_date="2025-03-01",
        text="Ementa estável",
    )
    equivalent = resolve_legal_identity(
        kind="decision",
        source=" tjsp ",
        authority="tjsp",
        degree="segundo   grau",
        native_id="d-42",
        case_number="00000010220258260001",
        record_type="acordao",
        event_date="2025-03-01",
        text=" Ementa   estável ",
    )
    assert base.key == equivalent.key
    forward = match_legal_identities(base, equivalent)
    backward = match_legal_identities(equivalent, base)
    assert forward.relation == backward.relation == "same"
    assert forward.left_key == backward.right_key

    mutated = resolve_legal_identity(
        kind="decision",
        source="tjsp",
        authority="tjsp",
        degree="segundo grau",
        native_id="d-43",
        case_number="00000010220258260001",
        record_type="acordao",
        event_date="2025-03-01",
        text="Ementa estável",
    )
    assert match_legal_identities(base, mutated).relation == "distinct"

    missing_date = resolve_legal_identity(
        kind="decision",
        source="tjsp",
        authority="tjsp",
        degree="segundo grau",
        case_number="00000010220258260001",
        record_type="acordao",
        text="Ementa estável",
    )
    assert missing_date.key is None
    assert match_legal_identities(base, missing_date).relation == "unknown"
