from __future__ import annotations

import json
from pathlib import Path

from tools import run_federated_promotion_smoke as smoke
from tools import run_federated_shadow as shadow


def test_redact_completeness_keeps_only_safe_scalar_fields() -> None:
    value = smoke._redact_completeness(
        {
            "source_completeness": {
                "tj": {
                    "returned": 1,
                    "reported_total": None,
                    "complete": False,
                    "reason": "bounded",
                    "raw_body": "must not be copied",
                }
            }
        }
    )

    assert value == {
        "tj": {
            "returned": 1,
            "reported_total": None,
            "complete": False,
            "reason": "bounded",
        }
    }


def test_build_smoke_writes_redacted_manifest_envelope(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"summary": {"enabled_sources": ["tj"]}}), encoding="utf-8")
    output = tmp_path / "smoke.json"

    class FakeClient:
        def __init__(self, config, **kwargs) -> None:
            assert config.unified_max_pages == 1

        def _default_unified_sources(self) -> list[str]:
            return ["tj"]

        def search_many(self, text: str, **kwargs):
            assert text == "responsabilidade"
            assert kwargs["sources"] == ["tj"]
            return {
                "searched_sources": ["tj"],
                "source_completeness": {
                    "tj": {
                        "returned": 1,
                        "reported_total": None,
                        "pagination_mode": "page",
                        "complete": False,
                        "reason": "bounded",
                        "pages_fetched": 1,
                        "invalid_records": 0,
                    }
                },
                "source_totals": {"tj": None},
                "source_total_known": {"tj": None},
                "source_access_status": {"tj": "public"},
                "source_extraction_status": {"tj": "complete"},
                "skipped_sources": [
                    {
                        "source": "candidate",
                        "category": "court_jurisprudence",
                        "reason": "unified_search_not_supported",
                        "message": "contract pending",
                        "raw_body": "must not be copied",
                    }
                ],
                "routing_warnings": [
                    {
                        "source": "tj",
                        "action": "searched",
                        "reason": "filter_not_supported",
                        "message": "warning",
                    }
                ],
                "source_outcomes": [
                    {
                        "source": "tj",
                        "status": "searched",
                        "reason": "source_called",
                        "message": "called",
                    }
                ],
                "errors": [],
                "total_returned": 1,
                "deduplicated_total": 1,
                "collection_complete": False,
            }

    monkeypatch.setattr(smoke, "NanoJurisClient", FakeClient)
    result = smoke.build_smoke(
        manifest=manifest, output=output, text="responsabilidade", page_size=1
    )

    assert result["summary"]["unknown_total_sources"] == ["tj"]
    assert result["summary"]["sources_skipped"] == 1
    assert result["summary"]["sources_with_warnings"] == 1
    assert result["sources_skipped"][0]["reason"] == "unified_search_not_supported"
    assert result["source_outcomes"][0]["status"] == "searched"
    serialized = output.read_text(encoding="utf-8").lower()
    assert "raw_body" not in serialized
    assert "token" not in serialized
    assert "cookie" not in serialized


def test_build_smoke_accepts_explicit_opt_in_source_override(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"summary": {"enabled_sources": ["default"]}}), encoding="utf-8")
    output = tmp_path / "smoke.json"

    class FakeClient:
        def __init__(self, config, **kwargs) -> None:
            assert config.unified_max_pages == 1

        def _default_unified_sources(self) -> list[str]:
            return ["optin"]

        def search_many(self, text: str, **kwargs):
            assert kwargs["sources"] == ["optin"]
            return {
                "searched_sources": ["optin"],
                "source_completeness": {"optin": {"returned": 0, "complete": False}},
                "source_totals": {"optin": None},
                "source_total_known": {"optin": False},
                "source_access_status": {"optin": "public"},
                "source_extraction_status": {"optin": "complete"},
                "skipped_sources": [],
                "routing_warnings": [],
                "source_outcomes": [
                    {
                        "source": "optin",
                        "status": "searched",
                        "reason": "source_called",
                        "message": "called",
                    }
                ],
                "errors": [],
                "total_returned": 0,
                "deduplicated_total": 0,
                "collection_complete": False,
            }

    monkeypatch.setattr(smoke, "NanoJurisClient", FakeClient)
    result = smoke.build_smoke(
        manifest=manifest,
        output=output,
        text="responsabilidade",
        page_size=1,
        sources=["optin"],
    )

    assert result["manifest_sources"] == ["optin"]
    assert result["summary"]["sources_searched"] == 1


def test_shadow_window_compares_ids_and_never_serializes_bodies(
    tmp_path: Path, monkeypatch
) -> None:
    baseline_manifest = tmp_path / "baseline.json"
    candidate_manifest = tmp_path / "candidate.json"
    for path in (baseline_manifest, candidate_manifest):
        path.write_text(json.dumps({"summary": {"enabled_sources": ["tj"]}}), encoding="utf-8")
    output = tmp_path / "shadow.json"

    class FakeClient:
        calls = 0

        def __init__(self, config, **kwargs) -> None:
            assert config.unified_max_pages == 1

        def search_many(self, text: str, **kwargs):
            assert text == "responsabilidade"
            FakeClient.calls += 1
            return {
                "collected_results": (
                    [{"id": "decision-1", "summary": "secret baseline"}]
                    if FakeClient.calls == 1
                    else [{"id": "decision-1", "summary": "secret candidate"}]
                ),
                "searched_sources": ["tj"],
                "source_completeness": {"tj": {"returned": 1, "complete": True}},
                "errors": [],
                "collection_complete": True,
            }

    monkeypatch.setattr(shadow, "NanoJurisClient", FakeClient)
    result = shadow.build_shadow(
        baseline_manifest=baseline_manifest,
        candidate_manifest=candidate_manifest,
        output=output,
        text="responsabilidade",
        page_size=1,
        max_ids=10,
    )

    assert result["comparison"]["equivalent"] is True
    serialized = output.read_text(encoding="utf-8").lower()
    assert "secret baseline" not in serialized
    assert "secret candidate" not in serialized
    assert result["limits"]["bodies_persisted"] is False
