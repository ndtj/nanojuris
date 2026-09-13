"""Run a bounded public second-degree smoke for state eproc providers.

The probe sends the canonical degree request through the installation-specific
``selOrigem[]`` vocabulary and persists only redacted metadata.  It is an
evidence aid, not a promotion or deployment command.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    safe_error_message,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjsc_eproc_jurisprudencia import TjscEprocJurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "state-eproc-degree-live-20260906.json"
PROVIDERS: dict[str, type[Any]] = {
    "tjrj_eproc_jurisprudencia": TjrjEprocJurisprudenciaProvider,
    "tjsc_eproc_jurisprudencia": TjscEprocJurisprudenciaProvider,
}


def _classify(exc: BaseException) -> str:
    if isinstance(exc, AccessControlRequiredError):
        return "access_blocked"
    if isinstance(exc, RateLimitDetectedError):
        return "rate_limited"
    if isinstance(exc, ParserContractChangedError):
        return "schema_invalid"
    if isinstance(exc, SourceUnavailableError):
        return "source_unavailable"
    return "source_unavailable"


def _probe(source: str, provider_type: type[Any], query: JurisprudenceQuery) -> dict[str, Any]:
    provider = provider_type(NanoJurisConfig(timeout=20, rate_limit_interval=0))
    try:
        page = provider.search(query)
    except Exception as exc:  # noqa: BLE001 - bounded diagnostic envelope
        return {
            "source_id": source,
            "classification": _classify(exc),
            "returned": 0,
            "error": {"type": type(exc).__name__, "message": safe_error_message(exc, limit=240)},
        }
    trace = page.source_trace
    return {
        "source_id": source,
        "classification": "reachable_valid_data" if page.results else "reachable_empty_data",
        "returned": len(page.results),
        "reported_total": page.total if page.total_known else None,
        "total_known": page.total_known,
        "degrees": sorted({result.degree for result in page.results if result.degree}),
        "identities": [
            {"id": result.id, "court": result.court, "source": result.source}
            for result in page.results[:3]
        ],
        "trace": {
            "endpoint": trace.endpoint if trace else None,
            "http_status": trace.http_status if trace else None,
            "final_url": trace.final_url if trace else None,
            "response_bytes": trace.response_bytes if trace else None,
            "content_sha256": trace.content_sha256 if trace else None,
        },
    }


def run(
    output: Path, *, text: str = "responsabilidade civil", page_size: int = 1
) -> dict[str, Any]:
    query = JurisprudenceQuery(text=text, degree="second", page=1, page_size=page_size)
    results = [_probe(source, provider, query) for source, provider in PROVIDERS.items()]
    payload = {
        "schema_version": "state-eproc-degree-live-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "bounded_public_http",
        "query": query.to_dict(),
        "credentials_used": False,
        "raw_content_persisted": False,
        "results": results,
        "summary": {
            "sources": len(results),
            "search_valid": sum(
                item["classification"] == "reachable_valid_data" for item in results
            ),
            "search_empty": sum(
                item["classification"] == "reachable_empty_data" for item in results
            ),
            "search_blocked": sum(item["classification"] == "access_blocked" for item in results),
            "search_schema_invalid": sum(
                item["classification"] == "schema_invalid" for item in results
            ),
            "search_errors": sum(
                item["classification"] == "source_unavailable" for item in results
            ),
        },
        "limitations": [
            "A amostra e bounded e nao prova estabilidade permanente.",
            "Somente metadados, identidades e hashes foram persistidos; corpos nao foram gravados.",
            "O filtro de segundo grau e validado pelo parser; o total remoto pode "
            "ficar desconhecido.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--text", default="responsabilidade civil")
    parser.add_argument("--page-size", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.page_size <= 5:
        parser.error("--page-size must be between 1 and 5")
    payload = run(args.output.resolve(), text=args.text, page_size=args.page_size)
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
