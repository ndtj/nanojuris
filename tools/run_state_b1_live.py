"""Run a bounded live recheck for the six state CJSG API adapters (B1)."""

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
from nanojuris.providers.tjba_graphql import TjbaGraphqlProvider
from nanojuris.providers.tjdf_juris import TjdfJurisProvider
from nanojuris.providers.tjmt_jurisprudencia_api import TjmtJurisprudenciaApiProvider
from nanojuris.providers.tjpa_jurisprudencia_bff import TjpaJurisprudenciaBffProvider
from nanojuris.providers.tjpb_pje_jurisprudencia import TjpbPjeJurisprudenciaProvider
from nanojuris.providers.tjrn_jurisprudencia import TjrnJurisprudenciaProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "state-b1-live-20260908-cycle69.json"
PROVIDERS: dict[str, type[Any]] = {
    "tjba_graphql": TjbaGraphqlProvider,
    "tjdf_juris": TjdfJurisProvider,
    "tjmt_jurisprudencia_api": TjmtJurisprudenciaApiProvider,
    "tjpa_jurisprudencia_bff": TjpaJurisprudenciaBffProvider,
    "tjpb_pje_jurisprudencia": TjpbPjeJurisprudenciaProvider,
    "tjrn_jurisprudencia": TjrnJurisprudenciaProvider,
}


def _error_classification(exc: BaseException) -> str:
    if isinstance(exc, AccessControlRequiredError):
        return "access_blocked"
    if isinstance(exc, RateLimitDetectedError):
        return "rate_limited"
    if isinstance(exc, ParserContractChangedError):
        return "schema_invalid"
    if isinstance(exc, SourceUnavailableError):
        return "source_unavailable"
    return "source_unavailable"


def _trace(page: Any) -> dict[str, Any]:
    trace = page.source_trace
    if trace is None:
        return {}
    return {
        "endpoint": trace.endpoint,
        "http_status": trace.http_status,
        "final_url": trace.final_url,
        "content_type": trace.content_type,
        "response_bytes": trace.response_bytes,
        "content_sha256": trace.content_sha256,
    }


def _search(provider: Any, query: JurisprudenceQuery) -> dict[str, Any]:
    try:
        page = provider.search(query)
    except Exception as exc:  # noqa: BLE001 - bounded redacted report
        return {
            "classification": _error_classification(exc),
            "page": query.page,
            "returned": 0,
            "error": {"type": type(exc).__name__, "message": safe_error_message(exc, limit=240)},
        }
    return {
        "classification": "reachable_valid_data" if page.results else "empty_or_unconfirmed",
        "page": page.page,
        "returned": len(page.results),
        "reported_total": page.total if page.total_known else None,
        "total_known": page.total_known,
        "ids": [item.id for item in page.results],
        "identities": [
            {
                "id": item.id,
                "authority": item.authority,
                "degree": item.degree,
                "instance": item.instance,
                "collection": item.collection,
                "document_type": item.document_type,
            }
            for item in page.results
        ],
        "trace": _trace(page),
    }


def run(
    output: Path, *, text: str = "responsabilidade civil", page_size: int = 1
) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    for source, provider_type in PROVIDERS.items():
        provider = provider_type(NanoJurisConfig(timeout=25, rate_limit_interval=0))
        pages = [
            _search(
                provider,
                JurisprudenceQuery(
                    text=text,
                    degree="second",
                    instance="second",
                    page=page,
                    page_size=page_size,
                ),
            )
            for page in (1, 2)
        ]
        reports.append(
            {
                "source_id": source,
                "surface": "cjsg",
                "pages": pages,
                "pagination": {
                    "disjoint": bool(set(pages[0].get("ids", [])) and set(pages[1].get("ids", [])))
                    and set(pages[0].get("ids", [])).isdisjoint(set(pages[1].get("ids", []))),
                },
            }
        )
    payload = {
        "schema_version": "state-b1-live-v1",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "bounded_public_http",
        "query": {
            "text": text,
            "degree": "second",
            "instance": "second",
            "page_size": page_size,
        },
        "credentials_used": False,
        "raw_content_persisted": False,
        "results": reports,
        "summary": {
            "sources": len(reports),
            "search_valid": sum(
                item["pages"][0].get("classification") == "reachable_valid_data" for item in reports
            ),
            "second_pages_valid": sum(
                item["pages"][1].get("classification") == "reachable_valid_data" for item in reports
            ),
            "pagination_disjoint": sum(item["pagination"]["disjoint"] for item in reports),
            "blocked_or_failed": sum(
                item["pages"][0].get("classification") != "reachable_valid_data" for item in reports
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
    if not 1 <= args.page_size <= 2:
        parser.error("--page-size must be between 1 and 2")
    payload = run(args.output.resolve(), text=args.text, page_size=args.page_size)
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
