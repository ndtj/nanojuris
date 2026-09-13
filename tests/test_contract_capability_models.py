from __future__ import annotations

import pytest

from nanojuris.contracts import (
    CanonicalFilterRegistry,
    CapabilityEvidence,
    DocumentContract,
    EvidenceKind,
    FieldContract,
)


def test_canonical_filter_registry_resolves_aliases_without_inventing_names() -> None:
    registry = CanonicalFilterRegistry.default()
    assert registry.canonicalize("court_code") == "courts"
    assert registry.canonicalize("class") == "case_class"
    assert registry.canonicalize("not_a_filter") is None


def test_capability_evidence_is_serializable_and_requires_reference() -> None:
    evidence = CapabilityEvidence(
        source="tj_example",
        kind=EvidenceKind.FIXTURE,
        reference="fixtures/tj_example/success.json",
        captured_at="2026-09-06T00:00:00Z",
        metadata={"redacted": True},
    )
    assert evidence.to_dict()["kind"] == "fixture"
    assert evidence.to_dict()["metadata"]["redacted"] is True
    with pytest.raises(ValueError):
        CapabilityEvidence(
            source="tj_example",
            kind=EvidenceKind.TEST,
            reference="",
            captured_at="2026-09-06T00:00:00Z",
        )


def test_field_and_document_contracts_preserve_explicit_unknowns() -> None:
    field = FieldContract("judgment_date", value_type="date", provenance="raw.date")
    document = DocumentContract(
        "decision_pdf",
        access="unknown",
        content_types=("application/pdf",),
    )
    assert field.to_dict()["normalized"] is True
    assert document.to_dict()["access"] == "unknown"
    assert document.to_dict()["content_types"] == ["application/pdf"]
