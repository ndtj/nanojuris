from __future__ import annotations

import json
from pathlib import Path

from tools.build_adapter_wave_board import WAVE_ITEMS, build, to_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_board_joins_current_live_evidence_without_promotion() -> None:
    board = build(
        semantic_path=ROOT / "docs/provider-discovery/juscraper-semantic-diff-20260901.json",
        smoke_path=ROOT / "docs/provider-discovery/juscraper-live-smoke-20260901.json",
        recheck_path=ROOT / "docs/provider-discovery/juscraper-live-recheck-20260901.json",
        generated_at="2026-09-01T00:00:00+00:00",
    )

    assert len(board["items"]) == len(WAVE_ITEMS) == 8
    assert board["no_runtime_promotion"] is True
    by_source = {row["source_id"]: row for row in board["items"]}
    assert by_source["tjes_jurisprudencia"]["readiness"] == ("candidate_ready_for_contract_closure")
    assert by_source["tjrn_jurisprudencia"]["readiness"] == "blocked_access"
    assert by_source["tjrn_jurisprudencia"]["live_classification"] == "blocked_access"
    assert by_source["tjro_jurisprudencia"]["live_classification"] == "reachable_empty_data"
    assert by_source["tjro_jurisprudencia"]["live_evidence"] == "dedicated:http_200"
    assert by_source["tjto_ementa_detail"]["readiness"] == "detail_contract_unverified"
    assert by_source["tjes_cjpg"]["readiness"] == "separate_collection_contract"


def test_board_is_deterministic_and_markdown_exposes_resume_rules() -> None:
    kwargs = {
        "semantic_path": ROOT / "docs/provider-discovery/juscraper-semantic-diff-20260901.json",
        "smoke_path": ROOT / "docs/provider-discovery/juscraper-live-smoke-20260901.json",
        "recheck_path": ROOT / "docs/provider-discovery/juscraper-live-recheck-20260901.json",
        "generated_at": "2026-09-01T00:00:00+00:00",
    }
    first = build(**kwargs)
    second = build(**kwargs)

    assert first == second
    rendered = to_markdown(first)
    assert "nao promove providers" in rendered
    assert "TJRN" not in rendered  # source IDs remain machine-stable/lowercase
    assert "tjrn_jurisprudencia" in rendered
    assert "rota publica voltar a responder" in rendered
    json.dumps(first, ensure_ascii=False)
