"""Run a bounded live smoke for the public CJSG providers.

The probe intentionally separates a successful jurisprudence search from the
detail call.  Several e-SAJ deployments expose search results publicly while
requiring a captcha for the full document; that is an access state, never an
empty result and never a reason to bypass the source controls.
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
from nanojuris.providers.tjac_cjsg import TjacCjsgProvider
from nanojuris.providers.tjal_cjsg import TjalCjsgProvider
from nanojuris.providers.tjam_cjsg import TjamCjsgProvider
from nanojuris.providers.tjce_cjsg import TjceCjsgProvider
from nanojuris.providers.tjes_jurisprudencia import TjesJurisprudenciaProvider
from nanojuris.providers.tjms_cjsg import TjmsCjsgProvider
from nanojuris.providers.tjpe_jurisprudencia import TjpeJurisprudenciaProvider
from nanojuris.providers.tjsp_cjsg import TjspCjsgProvider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "cjsg-live-20260905-cycle51.json"
PROVIDERS: dict[str, type[Any]] = {
    "tjac_cjsg": TjacCjsgProvider,
    "tjal_cjsg": TjalCjsgProvider,
    "tjam_cjsg": TjamCjsgProvider,
    # TJES uses a dedicated public JSON/PJe2G contract rather than the e-SAJ
    # adapter family, but it is still a CJSG surface and belongs in the same
    # bounded degree recheck.
    "tjes_jurisprudencia": TjesJurisprudenciaProvider,
    # These e-SAJ/JSF surfaces were historically blocked in an earlier
    # network snapshot.  Keep them in the same bounded probe so a public
    # session recovery is observable and does not require manual promotion.
    "tjce_cjsg": TjceCjsgProvider,
    "tjms_cjsg": TjmsCjsgProvider,
    "tjpe_jurisprudencia": TjpeJurisprudenciaProvider,
    "tjsp_cjsg": TjspCjsgProvider,
}


def _trace_metadata(page: Any) -> dict[str, Any]:
    trace = page.source_trace
    if trace is None:
        return {}
    return {
        "http_status": trace.http_status,
        "content_type": trace.content_type,
        "response_bytes": trace.response_bytes,
        "content_sha256": trace.content_sha256,
        "retrieval_status": trace.retrieval_status,
        "final_url": trace.final_url,
    }


def _detail_observation(provider: Any, result_id: str) -> dict[str, Any]:
    try:
        document = provider.get_document(result_id)
    except AccessControlRequiredError as exc:
        return {
            "status": "access_control_required",
            "error_type": type(exc).__name__,
            "message": str(exc)[:240],
        }
    except Exception as exc:  # noqa: BLE001 - bounded diagnostics
        return {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc)[:240],
        }
    return {
        "status": "valid",
        "byte_size": document.byte_size,
        "content_type": document.content_type,
        "sha256": document.sha256,
        "extraction_status": getattr(
            document.extraction_status, "value", document.extraction_status
        ),
        "has_text": bool(document.text),
        "source_trace": {
            "http_status": (document.source_trace.http_status if document.source_trace else None),
            "content_type": (document.source_trace.content_type if document.source_trace else None),
            "response_bytes": (
                document.source_trace.response_bytes if document.source_trace else None
            ),
            "content_sha256": (
                document.source_trace.content_sha256 if document.source_trace else None
            ),
        },
    }


def _probe(source: str, provider_type: type[Any], query: JurisprudenceQuery) -> dict[str, Any]:
    provider = provider_type(NanoJurisConfig(timeout=20, rate_limit_interval=0))
    observation: dict[str, Any] = {"source": source, "query": query.to_dict()}
    try:
        page = provider.search(query)
    except Exception as exc:  # noqa: BLE001 - bounded diagnostics
        classification = _search_error_classification(exc)
        return {
            "source_id": source,
            "surface": "cjsg",
            "classification": classification,
            "http_status": None,
            "record_count_observed": 0,
            "reported_total": None,
            "pagination_mode": "page",
            "observation": {
                **observation,
                "error": {
                    "type": type(exc).__name__,
                    "message": safe_error_message(exc, limit=240),
                },
            },
        }

    results = list(page.results)
    observation["search"] = {
        **_trace_metadata(page),
        "returned": len(results),
        "total_known": page.total_known,
        "reported_total": page.total,
        "ids": [item.id for item in results[:5]],
        "has_summary": all(bool(item.summary) for item in results),
        "has_identity": all(bool(item.id and item.court and item.source) for item in results),
    }
    if results:
        observation["detail"] = _detail_observation(provider, results[0].id)
    else:
        observation["detail"] = {"status": "not_observed"}
    trace = page.source_trace
    return {
        "source_id": source,
        "surface": "cjsg",
        "endpoint": trace.endpoint if trace else None,
        "classification": "reachable_valid_data" if results else "reachable_empty_data",
        "http_status": trace.http_status if trace else None,
        "content_type": trace.content_type if trace else None,
        "response_bytes": trace.response_bytes if trace else None,
        "content_sha256": trace.content_sha256 if trace else None,
        "record_count_observed": len(results),
        "reported_total": page.total if page.total_known else None,
        "pagination_mode": "page",
        "observation": observation,
    }


def run(
    output: Path, *, text: str = "responsabilidade civil", page_size: int = 2
) -> dict[str, Any]:
    query = JurisprudenceQuery(text=text, page=1, page_size=page_size)
    reports = [_probe(source, provider_type, query) for source, provider_type in PROVIDERS.items()]
    payload = {
        "schema_version": "provider-cjsg-live-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "bounded_public_http_recheck",
        "query": {"text": text, "page": 1, "page_size": page_size},
        "credentials_used": False,
        "raw_content_persisted": False,
        "results": reports,
        "summary": {
            "sources": len(reports),
            "search_valid": sum(
                item["classification"] == "reachable_valid_data" for item in reports
            ),
            "search_empty": sum(
                item["classification"] == "reachable_empty_data" for item in reports
            ),
            "search_errors": sum(
                item["classification"] == "source_unavailable" for item in reports
            ),
            "search_blocked": sum(item["classification"] == "access_blocked" for item in reports),
            "search_rate_limited": sum(
                item["classification"] == "rate_limited" for item in reports
            ),
            "search_schema_invalid": sum(
                item["classification"] == "schema_invalid" for item in reports
            ),
            "detail_access_controlled": sum(
                item.get("observation", {}).get("detail", {}).get("status")
                == "access_control_required"
                for item in reports
            ),
            "detail_valid": sum(
                item.get("observation", {}).get("detail", {}).get("status") == "valid"
                for item in reports
            ),
        },
        "limitations": [
            "A amostra e bounded e nao confirma estabilidade permanente.",
            "Somente metadados, hashes e estados foram persistidos; corpos nao foram gravados.",
            "Controle de acesso no detalhe permanece explicito e nao e contornado.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _search_error_classification(exc: BaseException) -> str:
    """Keep bounded smoke failures distinct from an unavailable source.

    A CAPTCHA/WAF, throttling response or parser drift is actionable evidence;
    collapsing any of those states into ``source_unavailable`` makes a live
    report look like a transport outage and can hide a regression.
    """

    if isinstance(exc, AccessControlRequiredError):
        return "access_blocked"
    if isinstance(exc, RateLimitDetectedError):
        return "rate_limited"
    if isinstance(exc, ParserContractChangedError):
        return "schema_invalid"
    if isinstance(exc, SourceUnavailableError):
        return "source_unavailable"
    return "source_unavailable"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--text", default="responsabilidade civil")
    parser.add_argument("--page-size", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.page_size <= 20:
        parser.error("--page-size must be between 1 and 20")
    payload = run(args.output.resolve(), text=args.text, page_size=args.page_size)
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
