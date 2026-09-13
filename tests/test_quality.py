from __future__ import annotations

from nanojuris.models import CanonicalDecision, SourceTrace
from nanojuris.quality import compare_golden, duplicate_identity_keys, validate_record


def _decision(**overrides: object) -> CanonicalDecision:
    values: dict[str, object] = {
        "id": "native-1",
        "source": "fixture_provider",
        "court": "TJXX",
        "case_number": "0000001-00.2024.8.00.0001",
        "judgment_date": "2024-05-10",
        "summary": "Ementa de teste sem marcacao HTML.",
        "document_url": "https://tribunal.jus.br/decisao/1",
        "source_trace": SourceTrace(
            provider="fixture_provider",
            endpoint="https://tribunal.jus.br/api/search",
            content_sha256="a" * 64,
        ),
    }
    values.update(overrides)
    return CanonicalDecision(**values)


def test_validate_record_accepts_complete_decision() -> None:
    assert validate_record(_decision()) == ()


def test_validate_record_accepts_canonical_jurisprudencia_collection() -> None:
    assert validate_record(_decision(collection="JURISPRUDENCIA")) == ()


def test_validate_record_reports_critical_invariants() -> None:
    issues = validate_record(
        _decision(
            source_trace=None,
            judgment_date="31/13/2024",
            summary="<div>ementa</div>",
            document_url="javascript:alert(1)",
        )
    )
    codes = {issue.code for issue in issues}
    assert {"missing_provenance", "invalid_date", "html_in_canonical_text", "unsafe_url"} <= codes


def test_duplicate_identity_keys_is_deterministic() -> None:
    records = [_decision(), _decision(), _decision(id="native-2")]
    duplicates = duplicate_identity_keys(records)
    assert len(duplicates) == 1
    assert next(iter(duplicates.values())) == (0, 1)


def test_compare_golden_ignores_volatile_timestamps() -> None:
    expected = {"id": "1", "retrieved_at": "2024-01-01T00:00:00Z", "fields": {"a": 1}}
    actual = {"id": "1", "retrieved_at": "2024-01-02T00:00:00Z", "fields": {"a": 1}}
    assert compare_golden(expected, actual) == ()
    assert compare_golden(expected, {**actual, "fields": {"a": 2}}) == ("$.fields.a",)
