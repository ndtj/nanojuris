"""Build a read-only provider freshness and drift certification manifest."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from nanojuris.certification import (  # noqa: E402
    ProviderEvidenceSnapshot,
    build_certification_manifest,
)

DEFAULT_CATALOG = ROOT / "docs" / "registry" / "provider-catalog.full.json"
DEFAULT_OUTPUT = ROOT / "docs" / "operations" / "provider-certification-20260907.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "operations" / "provider-certification-20260907.md"
DEFAULT_PROMOTION = ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"


def _risk_level(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"alto", "high", "critical"}:
        return "high"
    if normalized in {"baixo", "low"}:
        return "low"
    return "medium"


def _outcome(entry: dict[str, Any]) -> str:
    live = entry.get("live_validation") or entry.get("live_evidence") or {}
    status = str(live.get("status") or entry.get("live_status") or "missing").lower()
    if status in {"valid", "success", "live_validated"}:
        return (
            "success_with_results" if int(live.get("returned") or 0) > 0 else "authoritative_empty"
        )
    if status in {"blocked", "blocked_access", "access_controlled"}:
        return "access_blocked"
    if status in {"blocked_transport", "tls_error", "tls_verification_failed"}:
        return "blocked_transport"
    if status in {"rate_limited", "429"}:
        return "rate_limited"
    if status in {"timeout"}:
        return "timeout"
    if status in {"schema_invalid", "schema_drift"}:
        return "schema_invalid"
    if status in {"source_unavailable", "unavailable", "missing", "not_checked"}:
        return "source_unavailable"
    return status or "source_unavailable"


def snapshots_from_catalog(payload: dict[str, Any]) -> list[ProviderEvidenceSnapshot]:
    snapshots: list[ProviderEvidenceSnapshot] = []
    for entry in payload.get("entries", []):
        if not isinstance(entry, dict) or not entry.get("source_id"):
            continue
        live = entry.get("live_validation") or entry.get("live_evidence") or {}
        date = live.get("date")
        observed_at = f"{date}T23:59:59+00:00" if date else None
        snapshots.append(
            ProviderEvidenceSnapshot(
                provider=str(entry["source_id"]),
                observed_at=observed_at,
                outcome=_outcome(entry),
                evidence_id=str(live.get("evidence")) if live.get("evidence") else None,
                risk_level=_risk_level((entry.get("error_contract") or {}).get("risk_level")),
            )
        )
    return snapshots


def build(
    *,
    catalog_path: Path = DEFAULT_CATALOG,
    promotion_path: Path = DEFAULT_PROMOTION,
    generated_at: str | None = None,
) -> dict[str, Any]:
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    promotion = (
        json.loads(promotion_path.read_text(encoding="utf-8")) if promotion_path.exists() else {}
    )
    technical_gates = {
        str(row.get("source")): bool(row.get("technical_gate"))
        for row in promotion.get("decisions", [])
        if isinstance(row, dict) and row.get("source")
    }
    return build_certification_manifest(
        snapshots_from_catalog(payload),
        technical_gates=technical_gates,
        generated_at=generated_at,
        now=datetime.now(timezone.utc),
    )


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Provider certification manifest",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        f"Providers: **{summary['providers']}**; technically promotable: "
        f"**{summary['promotable']}**; "
        f"blocked by missing or failed evidence: **{summary['blocked']}**.",
        "",
        "This is a read-only technical certification. It does not perform live "
        "calls, legal approval, or deployment.",
        "",
        "| Provider | Freshness | Smoke | Promotable | Alerts |",
        "|---|---|---|---|---|",
    ]
    for report in payload["reports"]:
        alerts = ", ".join(alert["code"] for alert in report["alerts"]) or "none"
        lines.append(
            f"| `{report['provider']}` | `{report['freshness']}` | "
            f"`{report['recommended_smoke']}` | "
            f"`{str(report['can_promote']).lower()}` | {alerts} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--promotion", type=Path, default=DEFAULT_PROMOTION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = build(catalog_path=args.catalog, promotion_path=args.promotion)
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        args.markdown_output.write_text(markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
