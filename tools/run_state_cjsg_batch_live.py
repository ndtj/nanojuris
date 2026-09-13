"""Run a bounded live recheck for the remaining state CJSG portal adapters.

Only public search pages are requested.  The report stores redacted trace
metadata and identities, never response bodies, cookies or challenge tokens.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    safe_error_message,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjgo_projudi_jurisprudencia import TjgoProjudiJurisprudenciaProvider
from nanojuris.providers.tjpi_juspi import TjpiJuspiProvider
from nanojuris.providers.tjpr_jurisprudencia import TjprJurisprudenciaProvider
from nanojuris.providers.tjrr_juris import TjrrJurisProvider
from nanojuris.providers.tjrs_solr import TjrsSolrProvider
from nanojuris.providers.tjto_jurisprudencia import TjtoJurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "state-cjsg-live-20260908-cycle68.json"
PROVIDERS: dict[str, type[Any]] = {
    "tjgo_projudi_jurisprudencia": TjgoProjudiJurisprudenciaProvider,
    "tjpi_juspi": TjpiJuspiProvider,
    "tjpr_jurisprudencia": TjprJurisprudenciaProvider,
    "tjrr_juris": TjrrJurisProvider,
    "tjrs_solr": TjrsSolrProvider,
    "tjto_jurisprudencia": TjtoJurisprudenciaProvider,
}


def _trace(trace: Any) -> dict[str, Any]:
    if trace is None:
        return {}
    return {
        "endpoint": trace.endpoint,
        "http_status": trace.http_status,
        "final_url": trace.final_url,
        "content_type": trace.content_type,
        "response_bytes": trace.response_bytes,
        "content_sha256": trace.content_sha256,
        "retrieval_status": trace.retrieval_status,
    }


def _classification(exc: BaseException) -> str:
    if isinstance(exc, AccessControlRequiredError):
        return "access_blocked"
    if isinstance(exc, RateLimitDetectedError):
        return "rate_limited"
    if isinstance(exc, ParserContractChangedError):
        return "schema_invalid"
    if isinstance(exc, SourceUnavailableError):
        return "source_unavailable"
    return "source_unavailable"


def _page(provider: Any, query: JurisprudenceQuery) -> dict[str, Any]:
    try:
        result = provider.search(query)
    except Exception as exc:  # noqa: BLE001 - redacted bounded diagnostic
        return {
            "classification": _classification(exc),
            "page": query.page,
            "returned": 0,
            "error": {"type": type(exc).__name__, "message": safe_error_message(exc, limit=240)},
        }
    return {
        "classification": "reachable_valid_data"
        if result.results
        else "authoritative_or_unconfirmed_empty",
        "page": result.page,
        "returned": len(result.results),
        "reported_total": result.total if result.total_known else None,
        "total_known": result.total_known,
        "ids": [item.id for item in result.results],
        "identities": [
            {
                "id": item.id,
                "authority": item.authority,
                "degree": item.degree,
                "instance": item.instance,
                "collection": item.collection,
                "document_type": item.document_type,
            }
            for item in result.results
        ],
        "trace": _trace(result.source_trace),
    }


def run(
    output: Path, *, text: str = "responsabilidade civil", page_size: int = 1
) -> dict[str, Any]:
    query = JurisprudenceQuery(
        text=text,
        degree="second",
        instance="second",
        page=1,
        page_size=page_size,
    )
    reports: list[dict[str, Any]] = []
    for source, provider_type in PROVIDERS.items():
        provider = provider_type(NanoJurisConfig(timeout=25, rate_limit_interval=0))
        first = _page(provider, query)
        second = _page(
            provider,
            JurisprudenceQuery(
                text=text,
                degree="second",
                instance="second",
                page=2,
                page_size=page_size,
            ),
        )
        reports.append(
            {
                "source_id": source,
                "surface": "cjsg",
                "first_page": first,
                "second_page": second,
                "pagination": {
                    "disjoint": bool(set(first.get("ids", [])) and set(second.get("ids", [])))
                    and set(first.get("ids", [])).isdisjoint(set(second.get("ids", []))),
                },
            }
        )
    payload = {
        "schema_version": "state-cjsg-live-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "bounded_public_http",
        "query": query.to_dict(),
        "credentials_used": False,
        "raw_content_persisted": False,
        "results": reports,
        "summary": {
            "sources": len(reports),
            "search_valid": sum(
                item["first_page"].get("classification") == "reachable_valid_data"
                for item in reports
            ),
            "second_pages_valid": sum(
                item["second_page"].get("classification") == "reachable_valid_data"
                for item in reports
            ),
            "pagination_disjoint": sum(item["pagination"]["disjoint"] for item in reports),
            "blocked_or_failed": sum(
                item["first_page"].get("classification") not in {"reachable_valid_data"}
                for item in reports
            ),
        },
        "limitations": [
            "A amostra e bounded e nao prova estabilidade permanente.",
            "Somente metadados, identidades e hashes foram persistidos; corpos nao foram gravados.",
            "Detalhes e documentos nao foram requisitados nesta rechecagem.",
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
    if not 1 <= args.page_size <= 3:
        parser.error("--page-size must be between 1 and 3")
    payload = run(args.output.resolve(), text=args.text, page_size=args.page_size)
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
