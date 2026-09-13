from __future__ import annotations

from nanojuris.governance import (
    ProviderPromotionEvidence,
    RolloutMode,
    compare_shadow_results,
    evaluate_provider_promotion,
    evaluate_release_gate,
)
from nanojuris.observability import ProbePolicy, run_allowlisted_probe, summarize_slis


def test_sli_summary_is_honest_and_deterministic() -> None:
    summary = summarize_slis(
        [
            {"status": "valid", "elapsed_ms": 20},
            {"status": "empty", "elapsed_ms": 40},
            {"status": "blocked", "elapsed_ms": 80},
        ]
    )
    assert summary["observed_sources"] == 3
    assert summary["contract_pass_rate"] == 2 / 3
    assert summary["availability_claim"] == "point_in_time_only"
    assert summary["latency_ms_p95"] == 80.0


def test_allowlisted_probe_passes_only_explicit_sources() -> None:
    class Client:
        def validate_sources(self, **kwargs):
            assert kwargs["sources"] == ["source_a"]
            return {
                "complete": True,
                "reports": [
                    {
                        "source": "source_a",
                        "status": "valid",
                        "message": "https://example.test?token=secret",
                        "response_bytes": 12,
                        "checked_at": "2026-09-02T00:00:00+00:00",
                    }
                ],
            }

    payload = run_allowlisted_probe(
        Client(), ProbePolicy(allowed_sources=("source_a",), timeout_seconds=10)
    )
    assert payload["complete"] is True
    assert payload["reports"][0]["message"] == "https://example.test"
    assert payload["summary"]["contract_pass_rate"] == 1.0


def test_release_gate_never_enables_without_human_approval() -> None:
    decision = evaluate_release_gate(
        source="tjrn_jurisprudencia",
        technical_passed=True,
        legal_approved=False,
        requested_mode=RolloutMode.ENABLED,
    )
    assert decision.mode is RolloutMode.OPT_IN
    assert decision.rollback_mode is RolloutMode.OPT_IN
    assert "human_legal_reuse_gate_pending" in decision.reasons


def test_release_gate_blocks_missing_fixture() -> None:
    decision = evaluate_release_gate(
        source="candidate",
        technical_passed=True,
        legal_approved=True,
        has_reproducible_fixture=False,
    )
    assert decision.mode is RolloutMode.OPT_IN
    assert decision.technical_gate is False


def test_promotion_evidence_keeps_live_and_legal_gates_separate() -> None:
    evidence = ProviderPromotionEvidence(
        source="tjes_cjpg",
        contract_valid=True,
        live_validated=True,
        fixtures_complete=True,
        quality_gate_passed=True,
        legal_approved=False,
        access_status="public",
    )

    decision = evaluate_provider_promotion(evidence)

    assert evidence.technical_passed is True
    assert decision.technical_gate is True
    assert decision.legal_gate is False
    assert decision.mode is RolloutMode.OPT_IN
    assert decision.reasons == ("human_legal_reuse_gate_pending",)


def test_promotion_evidence_blocks_transport_before_opt_in() -> None:
    decision = evaluate_provider_promotion(
        ProviderPromotionEvidence(
            source="tjsp_cjsg",
            contract_valid=True,
            live_validated=False,
            fixtures_complete=True,
            quality_gate_passed=True,
            access_status="blocked_access",
        )
    )

    assert decision.mode is RolloutMode.BLOCKED
    assert decision.technical_gate is False
    assert "blocked_access" in decision.reasons
    assert "live_validation_missing" in decision.reasons


def test_promotion_evidence_enables_only_when_every_gate_is_explicit() -> None:
    decision = evaluate_provider_promotion(
        ProviderPromotionEvidence(
            source="fixture",
            contract_valid=True,
            live_validated=True,
            fixtures_complete=True,
            quality_gate_passed=True,
            legal_approved=True,
            access_status="public",
        )
    )

    assert decision.mode is RolloutMode.ENABLED
    assert decision.technical_gate is True
    assert decision.legal_gate is True
    assert decision.reasons == ()


def test_shadow_comparison_is_order_independent_for_stable_ids() -> None:
    comparison = compare_shadow_results(
        [{"id": "b"}, {"id": "a"}],
        [{"id": "a"}, {"id": "b"}],
    )

    assert comparison.equivalent is True
    assert comparison.matched_count == 2
    assert comparison.overlap_ratio == 1.0
    assert comparison.added_ids == ()
    assert comparison.removed_ids == ()
    assert comparison.warnings == ()


def test_shadow_comparison_does_not_claim_equivalence_without_identity() -> None:
    comparison = compare_shadow_results(
        [{"summary": "same text"}],
        [{"summary": "same text"}],
    )

    assert comparison.equivalent is False
    assert comparison.overlap_ratio == 1.0
    assert "rows_without_stable_identity" in comparison.warnings


def test_shadow_comparison_reports_bounded_window_and_count_change() -> None:
    comparison = compare_shadow_results(
        [{"id": "a"}, {"id": "b"}, {"id": "c"}],
        [{"id": "a"}],
        max_ids=2,
    )

    assert comparison.baseline_count == 3
    assert comparison.candidate_count == 1
    assert comparison.matched_count == 1
    assert "comparison_window_truncated" in comparison.warnings
    assert "result_count_changed" in comparison.warnings
