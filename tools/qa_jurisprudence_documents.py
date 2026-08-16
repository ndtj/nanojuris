"""Probe document/full-text availability for representative live providers."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from nanojuris import NanoJurisClient

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "studio" / "qa-jurisprudence-documents-2026-08-16.json"
SOURCES = [
    "tjdf_juris",
    "tst_jurisprudencia",
    "stj_scon",
    "tjrs_solr",
    "tjba_graphql",
    "trf5_jurisprudencia",
    "tjpa_jurisprudencia_bff",
    "tjpb_pje_jurisprudencia",
    "tjpr_jurisprudencia",
    "tjpi_juspi",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="infanticidio")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    client = NanoJurisClient()
    reports: list[dict[str, Any]] = []
    for source in SOURCES:
        reports.append(_probe_source(client, source, args.query, args.timeout))

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "query": args.query,
        "sources": reports,
        "summary": _summary(reports),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Artefato: {args.output}")
    return 0


def _probe_source(
    client: NanoJurisClient, source: str, query: str, timeout: float
) -> dict[str, Any]:
    report: dict[str, Any] = {"source": source, "query": query}
    try:
        page = client.search(query, source=source, page_size=1)
        report["search"] = {
            "returned": len(page.results),
            "reported_total": page.total,
            "source": page.source,
        }
        if not page.results:
            report["status"] = "empty"
            return report
        result = page.results[0].to_dict()
        raw = result.get("raw") or {}
        document_url = (
            raw.get("document_url")
            or result.get("document_url")
            or result.get("source_trace", {}).get("source_url")
        )
        report["result"] = {
            "id": result.get("id"),
            "case_number": result.get("number") or result.get("case_number"),
            "summary_present": bool(result.get("summary") or result.get("thesis")),
            "full_text_present": bool(result.get("full_text")),
            "full_text_length": len(str(result.get("full_text") or "")),
            "document_url": document_url,
            "access_status": result.get("access_status"),
            "extraction_status": result.get("extraction_status"),
            "raw_keys": sorted(str(key) for key in raw),
        }

        capability = client.get_capabilities(source=source)
        if capability.supports_full_text:
            report["provider_document"] = _provider_document_probe(client, source, result.get("id"))
        if document_url:
            report["public_url"] = _public_url_probe(document_url, timeout)
        report["status"] = "checked"
    except Exception as exc:  # noqa: BLE001 - retain provider-specific failure diagnostics
        report["status"] = "error"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
    return report


def _provider_document_probe(
    client: NanoJurisClient, source: str, document_id: str | None
) -> dict[str, Any]:
    if not document_id:
        return {"status": "not_attempted", "reason": "result has no provider document id"}
    try:
        document = client.get_document(document_id, source=source).to_dict()
        full_text = str(document.get("text") or document.get("full_text") or "")
        return {
            "status": "loaded" if full_text else "empty_document",
            "document_id": document.get("id") or document_id,
            "full_text_length": len(full_text),
            "content_type": document.get("content_type"),
            "source_url": document.get("source_url"),
        }
    except Exception as exc:  # noqa: BLE001 - record unsupported/detail failures
        return {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}


def _public_url_probe(url: str, timeout: float) -> dict[str, Any]:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "NanoJuris/0.3 (+https://github.com/ndtj/nanojuris)"},
            timeout=timeout,
            allow_redirects=True,
            verify=True,
        )
        content = response.content
        content_type = response.headers.get("content-type", "")
        looks_like_document = (
            response.headers.get("content-type", "").lower().startswith("application/pdf")
            or "/document" in response.url.lower()
            or "/jurisprudence/" in response.url.lower()
            or "/jurisprudencia/j/" in response.url.lower()
            or "getinteiroteor" in response.url.lower()
        )
        return {
            "status": "reachable" if response.ok and content else "http_error",
            "http_status": response.status_code,
            "final_url": response.url,
            "content_type": content_type,
            "response_bytes": len(content),
            "is_pdf": content.startswith(b"%PDF"),
            "has_html": b"<html" in content[:10000].lower(),
            "text_like": "text" in content_type.lower() or "json" in content_type.lower(),
            "looks_like_document": looks_like_document,
        }
    except Exception as exc:  # noqa: BLE001 - record TLS/timeout/WAF observations
        return {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}


def _summary(reports: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "sources_checked": len(reports),
        "search_returned": 0,
        "full_text_in_search": 0,
        "provider_document_loaded": 0,
        "public_url_reachable": 0,
        "public_url_document_like": 0,
        "errors": 0,
    }
    for report in reports:
        if report.get("search", {}).get("returned", 0):
            summary["search_returned"] += 1
        if report.get("result", {}).get("full_text_present"):
            summary["full_text_in_search"] += 1
        if report.get("provider_document", {}).get("status") == "loaded":
            summary["provider_document_loaded"] += 1
        if report.get("public_url", {}).get("status") == "reachable":
            summary["public_url_reachable"] += 1
        if report.get("public_url", {}).get("looks_like_document"):
            summary["public_url_document_like"] += 1
        if report.get("status") == "error":
            summary["errors"] += 1
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
