"""Probe one official SJUR/TRE document per regional electoral court.

The sweep is intentionally serial and bounded.  It searches a single date
window, follows only a document URL returned by the official SJUR API, and
persists metadata and hashes rather than response bodies.  A failure in one
TRE is retained as an explicit access/transport/schema state and never
converted into an empty result.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tse_sjur_jurisprudencia import (
    TRE_STATES,
    TreSjurJurisprudenciaProvider,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "docs" / "provider-discovery" / "tre-sjur-document-uf-sweep-live-20260913.json"
)


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


def _probe_authority(
    authority: str,
    *,
    query: JurisprudenceQuery,
    timeout: float,
) -> dict[str, Any]:
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0, timeout=timeout),
        tribunal=authority,
    )
    try:
        page = provider.search_partitioned(query)
        if not page.results:
            return {
                "authority": authority,
                "classification": "unconfirmed_empty",
                "returned": 0,
                "total": page.total,
                "total_known": page.total_known,
                "search_http_status": page.source_trace.http_status if page.source_trace else None,
            }
        result = page.results[0]
        if not result.document_url:
            return {
                "authority": authority,
                "classification": "document_url_unavailable",
                "returned": len(page.results),
                "result_id": result.id,
                "degree": result.degree,
                "collection": result.collection,
                "search_http_status": page.source_trace.http_status if page.source_trace else None,
            }
        document = provider.get_document(result.id)
        return {
            "authority": authority,
            "classification": "success_with_document",
            "returned": len(page.results),
            "total": page.total,
            "total_known": page.total_known,
            "result_id": result.id,
            "degree": result.degree,
            "instance": result.instance,
            "collection": result.collection,
            "document_url": result.document_url,
            "document_content_type": document.content_type,
            "document_bytes": document.byte_size,
            "document_sha256": document.sha256,
            "document_access_status": document.access_status.value,
            "document_extraction_status": document.extraction_status.value,
            "document_has_text": bool(document.text and document.text.strip()),
            "search_http_status": page.source_trace.http_status if page.source_trace else None,
            "document_http_status": document.source_trace.http_status
            if document.source_trace
            else None,
        }
    except Exception as exc:  # noqa: BLE001 - redacted bounded evidence
        return {
            "authority": authority,
            "classification": _classify(exc),
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
        }


def probe(
    *,
    start: str,
    end: str,
    text: str,
    document_type: str,
    timeout: float,
    interval: float,
    output: Path,
) -> dict[str, Any]:
    query = JurisprudenceQuery(
        text=text,
        document_type=document_type,
        judgment_date_from=start,
        judgment_date_to=end,
        page_size=10,
    )
    results: list[dict[str, Any]] = []
    for index, state in enumerate(TRE_STATES):
        results.append(
            _probe_authority(
                f"TRE-{state}",
                query=query,
                timeout=timeout,
            )
        )
        if index < len(TRE_STATES) - 1:
            time.sleep(max(interval, 0.0))
    counts: dict[str, int] = {}
    for item in results:
        classification = str(item.get("classification") or "unknown")
        counts[classification] = counts.get(classification, 0) + 1
    payload = {
        "schema_version": "tre-sjur-document-uf-sweep-v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "provider": "tre_sjur_jurisprudencia",
        "collection": "SJUR",
        "branch": "electoral",
        "degree": "second",
        "request": query.to_dict(),
        "checked": len(results),
        "results": results,
        "summary": counts,
        "credentials_used": False,
        "bypass_attempted": False,
        "response_bodies_persisted": False,
        "limitations": [
            "Uma janela de data e um resultado por TRE; a sonda nao prova estabilidade permanente.",
            "Somente metadados, hashes e estados de extracao foram persistidos.",
            "A ausencia de URL de documento e distinta de bloqueio e de consulta vazia.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-01-31")
    parser.add_argument("--text", default="direito")
    parser.add_argument("--document-type", default="acordao")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.timeout <= 0 or args.interval < 0:
        parser.error("--timeout must be positive and --interval must be non-negative")
    payload = probe(
        start=args.start,
        end=args.end,
        text=args.text,
        document_type=args.document_type,
        timeout=args.timeout,
        interval=args.interval,
        output=args.output.resolve(),
    )
    print(json.dumps({"checked": payload["checked"], "summary": payload["summary"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
