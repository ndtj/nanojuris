from __future__ import annotations

import importlib.util
from pathlib import Path

from nanojuris.models import ProviderCapabilities


def _load_audit_module():
    path = Path(__file__).parents[1] / "tools" / "audit_unified_contract.py"
    spec = importlib.util.spec_from_file_location("audit_unified_contract", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_matrix_distinguishes_semantic_profiles_and_filter_gaps():
    audit = _load_audit_module()
    capabilities = [
        ProviderCapabilities(
            source="decision",
            display_name="Decision",
            source_url="https://example.test/decision",
            category="court_jurisprudence",
            canonical_records=["CanonicalDecision"],
            extracted_fields=["summary", "full_text"],
            supports_unified_search=True,
            supports_full_text=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            full_text_access="inline",
            supported_filters=["text", "courts", "types", "exact_phrase"],
        ),
        ProviderCapabilities(
            source="precedent",
            display_name="Precedent",
            source_url="https://example.test/precedent",
            category="qualified_precedents",
            canonical_records=["CanonicalPrecedent"],
            supports_unified_search=True,
            pagination_mode="unknown",
            completeness_contract="unknown",
            full_text_access="unknown",
            supported_filters=["text", "number", "types"],
        ),
    ]
    report = audit.build_report(
        capabilities,
        smoke_payload={
            "provider_count": 2,
            "summary": {"valid_data": 1},
            "providers": [{"source": "decision", "status": "valid_data"}],
        },
    )

    assert report["scope"]["unified_provider_count"] == 2
    assert report["summary"]["semantic_profiles"] == {"decision": 1, "precedent": 1}
    assert report["summary"]["filter_support_counts"]["text"] == 2
    assert report["summary"]["filter_support_counts"]["exact_phrase"] == 1
    precedent = next(row for row in report["providers"] if row["source"] == "precedent")
    assert "pagination_contract_unknown" in precedent["gaps"]
    assert "completeness_contract_unknown" in precedent["gaps"]
    assert "full_text_access_evidence_unknown" in precedent["gaps"]
    assert precedent["semantic_profile"] == "precedent"


def test_markdown_explains_non_equivalence():
    audit = _load_audit_module()
    capability = ProviderCapabilities(
        source="curated",
        display_name="Curated",
        source_url="https://example.test/curated",
        category="curated_jurisprudence",
        canonical_records=["CanonicalDecision"],
        supports_unified_search=True,
        supported_filters=["text"],
    )
    markdown = audit.render_markdown(audit.build_report([capability]))

    assert "não oferece filtros nem perfis de dados equivalentes" in markdown
    assert "`unsupported`" in markdown
    assert "curated" in markdown


def test_declared_unsupported_filter_is_not_reported_as_unpromoted():
    audit = _load_audit_module()
    capability = ProviderCapabilities(
        source="facets",
        display_name="Facets",
        source_url="https://example.test/facets",
        category="court_jurisprudence",
        canonical_records=["CanonicalDecision"],
        supports_unified_search=True,
        supported_filters=["text"],
        unsupported_filters=["types"],
    )
    report = audit.build_report(
        [capability],
        sweep_payload={
            "providers": [
                {
                    "source": "facets",
                    "contract_comparison": {"observed_filter_semantics": ["types"]},
                }
            ]
        },
    )

    row = report["providers"][0]
    assert "observed_filters_not_promoted_to_contract" not in row["gaps"]
    assert row["filter_classification"]["types"] == "unsupported"
