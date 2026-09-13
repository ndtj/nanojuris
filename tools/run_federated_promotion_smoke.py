"""Run a bounded live smoke for sources enabled by the technical manifest.

The command is intentionally small and safe to rerun.  It calls only the
manifest-enabled public providers, limits the collection to one page, and
writes a redacted envelope containing no result bodies, cookies or tokens.
"""

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

# Import only after putting this checkout first.  When a different NanoJuris
# wheel is installed in the interpreter, importing before this adjustment can
# silently omit newly registered providers (for example TJRJ eJURIS) from the
# federated smoke and report a false unsupported-provider error.
from nanojuris import NanoJurisClient, NanoJurisConfig  # noqa: E402

DEFAULT_MANIFEST = ROOT / "docs" / "operations" / "technical-promotion-manifest-20260905.json"
DEFAULT_OUTPUT = (
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260905-cycle47.json"
)


def _manifest_sources(path: Path, override: list[str] | None = None) -> list[str]:
    if override is not None:
        if not override or not all(isinstance(value, str) and value.strip() for value in override):
            raise ValueError("source override must contain non-empty source ids")
        return list(dict.fromkeys(value.strip() for value in override))
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("summary", {}).get("enabled_sources", [])
    if not isinstance(sources, list) or not all(isinstance(value, str) for value in sources):
        raise ValueError("manifest summary.enabled_sources must be a list of strings")
    return list(dict.fromkeys(value for value in sources if value))


def _safe_status(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return getattr(value, "value", str(value))


def _redact_completeness(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for source, value in payload.get("source_completeness", {}).items():
        if not isinstance(value, dict):
            continue
        output[str(source)] = {
            key: _safe_status(value.get(key))
            for key in (
                "returned",
                "reported_total",
                "pagination_mode",
                "complete",
                "reason",
                "pages_fetched",
                "invalid_records",
                "error_type",
                "error_message",
            )
            if key in value
        }
    return output


def _redact_source_items(payload: Any) -> list[dict[str, Any]]:
    """Keep routing diagnostics while excluding provider payloads.

    ``search_many`` already exposes a structured outcome for every requested
    source.  The smoke artifact is intentionally smaller than the response
    envelope, but it must not silently drop sources skipped by routing (for
    example a candidate without a proven unified-search contract).  Copy only
    the stable, human-readable routing fields; no result body, URL, cookie or
    token is accepted here.
    """

    if not isinstance(payload, list):
        return []
    allowed = {
        "source",
        "category",
        "status",
        "action",
        "reason",
        "message",
        "hint",
        "warning_count",
    }
    output: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        safe = {
            str(key): _safe_status(value)
            for key, value in item.items()
            if key in allowed and value is not None
        }
        if safe:
            output.append(safe)
    return output


def build_smoke(
    *,
    manifest: Path,
    output: Path,
    text: str,
    page_size: int,
    sources: list[str] | None = None,
) -> dict[str, Any]:
    explicit_source_override = sources is not None
    sources = _manifest_sources(manifest, sources)
    config = NanoJurisConfig(
        timeout=30,
        unified_timeout=90,
        unified_max_pages=1,
        unified_max_workers=max(1, min(16, len(sources))),
        rate_limit_interval=0,
        # An explicit ``--sources`` invocation is an opt-in diagnostic.  Make
        # that opt-in visible to the router without changing the default
        # federation rollout.  Providers marked opt-in remain excluded when
        # this command is run without an explicit source list.
        unified_opt_in_sources=tuple(sources),
    )
    # Explicit source overrides are diagnostics for candidate providers as
    # well as runtime providers.  Keep candidates out of the default path,
    # but expose them when the operator names them explicitly.
    client = NanoJurisClient(config=config, include_candidate_providers=explicit_source_override)
    payload = client.search_many(text, sources=sources, page=1, page_size=page_size)
    completeness = _redact_completeness(payload)
    errors = [
        {
            key: _safe_status(error.get(key))
            for key in ("source", "error_type", "message")
            if key in error
        }
        for error in payload.get("errors", [])
        if isinstance(error, dict)
    ]
    unknown_totals = sorted(
        source for source, total in payload.get("source_totals", {}).items() if total is None
    )
    try:
        manifest_ref = manifest.relative_to(ROOT).as_posix()
    except ValueError:
        manifest_ref = manifest.name
    result = {
        "schema_version": "federated-promotion-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_bounded",
        "query": {"text": text, "page": 1, "page_size": page_size},
        "limits": {"max_pages_per_source": 1, "bodies_persisted": False},
        "manifest": manifest_ref,
        "manifest_enabled_sources": len(sources),
        "manifest_sources": sources,
        "default_capability_sources": len(client._default_unified_sources()),
        "default_contains_manifest_sources": set(sources).issubset(
            set(client._default_unified_sources())
        ),
        "sources_searched": payload.get("searched_sources", []),
        "sources_skipped": _redact_source_items(payload.get("skipped_sources", [])),
        "routing_warnings": _redact_source_items(payload.get("routing_warnings", [])),
        "source_outcomes": _redact_source_items(payload.get("source_outcomes", [])),
        "source_completeness": completeness,
        "source_totals": payload.get("source_totals", {}),
        "source_total_known": payload.get("source_total_known", {}),
        "source_access_status": payload.get("source_access_status", {}),
        "source_extraction_status": payload.get("source_extraction_status", {}),
        "errors": errors,
        "summary": {
            "sources_requested": len(sources),
            "sources_searched": len(payload.get("searched_sources", [])),
            "sources_skipped": len(payload.get("skipped_sources", [])),
            "sources_with_warnings": len(payload.get("routing_warnings", [])),
            "sources_with_errors": len(errors),
            "invalid_records": sum(
                int(item.get("invalid_records", 0) or 0) for item in completeness.values()
            ),
            "total_returned": payload.get("total_returned", 0),
            "deduplicated_total": payload.get("deduplicated_total", 0),
            "collection_complete": payload.get("collection_complete"),
            "unknown_total_sources": unknown_totals,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--text", default="responsabilidade")
    parser.add_argument("--page-size", type=int, default=1)
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Override the manifest source set for an explicit opt-in smoke.",
    )
    args = parser.parse_args()
    if args.page_size < 1 or args.page_size > 100:
        parser.error("--page-size must be between 1 and 100")
    result = build_smoke(
        manifest=args.manifest.resolve(),
        output=args.output.resolve(),
        text=args.text,
        page_size=args.page_size,
        sources=args.sources,
    )
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
