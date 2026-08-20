from __future__ import annotations

import importlib.util
from pathlib import Path


def _module():
    path = Path(__file__).parents[1] / "tools" / "build_provider_closure_ledger.py"
    spec = importlib.util.spec_from_file_location("build_provider_closure_ledger", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ledger_preserves_external_blocks_and_candidate_pending_state():
    ledger = _module().build_ledger(
        {
            "generated_at": "2026-08-20T00:00:00+00:00",
            "mode": "live_bounded",
            "providers": [
                {
                    "source": "does_not_exist",
                    "todo": ["revisar robots.txt e agendar nova coleta autorizada"],
                    "metrics": {"statuses": {"robots_disallowed": 1}},
                    "observations": [{"status": "robots_disallowed"}],
                }
            ],
            "catalog_candidates": [
                {"source": "candidate_missing", "todo": ["criar adapter somente após contrato"]}
            ],
        }
    )

    assert ledger["summary"]["by_status"]["blocked_external"] == 1
    assert ledger["summary"]["by_status"]["candidate_pending_adapter"] == 1
    assert {item["status"] for item in ledger["items"]} == {
        "blocked_external",
        "candidate_pending_adapter",
    }


def test_ledger_reconciles_promoted_candidate_from_registry():
    ledger = _module().build_ledger(
        {
            "generated_at": "2026-08-20T00:00:00+00:00",
            "mode": "live_bounded",
            "catalog_candidates": [
                {
                    "source": "justica_eleitoral_sjur",
                    "todo": [
                        "criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico",
                        "confirmar rotas, filtros, paginação e detalhe a partir da evidência pública",
                    ],
                }
            ],
        }
    )

    assert ledger["summary"]["runtime_items"] == 2
    assert ledger["summary"]["candidate_items"] == 0
    assert all(item["status"] == "implemented_with_local_evidence" for item in ledger["items"])
