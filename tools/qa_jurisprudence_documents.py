"""Probe document/full-text availability for representative live providers."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from nanojuris import NanoJurisClient  # noqa: E402
from nanojuris.documents import assess_document_content  # noqa: E402

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
MAX_DOCUMENT_PROBE_BYTES = 4_000_000


def _select_sources(
    client: NanoJurisClient,
    requested: list[str] | None = None,
    all_supported: bool = False,
    pending_documents: bool = False,
) -> list[str]:
    """Resolve a bounded source list without silently adding candidates."""

    if requested:
        available = {capability.source for capability in client.list_sources()}
        unknown = sorted(set(requested) - available)
        if unknown:
            raise ValueError(f"unknown runtime providers: {', '.join(unknown)}")
        return list(dict.fromkeys(requested))
    if all_supported:
        return [
            capability.source
            for capability in client.list_sources()
            if capability.supports_full_text
        ]
    if pending_documents:
        return [
            capability.source
            for capability in client.list_sources()
            if capability.endpoints
            and capability.full_text_access
            in {"link_only", "unknown", "not_implemented", "not_available"}
        ]
    return list(SOURCES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="infanticidio")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="runtime provider to check; repeat for multiple providers",
    )
    parser.add_argument(
        "--all-supported",
        action="store_true",
        help="check every runtime provider that declares full-text support",
    )
    parser.add_argument(
        "--pending-documents",
        action="store_true",
        help="check runtime providers with declared link-only/unknown document routes",
    )
    parser.add_argument("--offset", type=int, default=0, help="skip this many selected providers")
    parser.add_argument(
        "--max-sources",
        type=int,
        help="check at most this many selected providers in the current bounded batch",
    )
    args = parser.parse_args()
    if args.offset < 0:
        parser.error("--offset must be non-negative")
    if args.max_sources is not None and args.max_sources < 1:
        parser.error("--max-sources must be positive")

    client = NanoJurisClient()
    reports: list[dict[str, Any]] = []
    try:
        sources = _select_sources(client, args.sources, args.all_supported, args.pending_documents)
    except ValueError as exc:
        parser.error(str(exc))
    sources = sources[args.offset :]
    if args.max_sources is not None:
        sources = sources[: args.max_sources]
    for source in sources:
        reports.append(_probe_source(client, source, args.query, args.timeout))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query": args.query,
        "source_selection": {
            "mode": "all_supported"
            if args.all_supported
            else "pending_documents"
            if args.pending_documents
            else "explicit"
            if args.sources
            else "default",
            "sources": sources,
        },
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
            if report["result"]["full_text_present"]:
                # Inline content already is the document surface.  Calling a
                # nonexistent detail method would misclassify a healthy
                # provider as an error (for example TJPA's BFF).
                report["provider_document"] = {
                    "status": "inline_text",
                    "document_id": result.get("id"),
                    "full_text_length": report["result"]["full_text_length"],
                }
            else:
                report["provider_document"] = _provider_document_probe(
                    client, source, result.get("id")
                )
        if document_url and not _is_search_endpoint(str(document_url)):
            report["public_url"] = _public_url_probe(document_url, timeout)
        failures: list[dict[str, Any]] = []
        provider_document = report.get("provider_document") or {}
        public_url = report.get("public_url") or {}
        if provider_document.get("status") in {"error", "empty_document"}:
            failures.append(
                {
                    "surface": "provider_document",
                    "status": provider_document.get(
                        "error_type", provider_document.get("status", "error")
                    ),
                }
            )
        if public_url and public_url.get("status") not in {"reachable"}:
            failures.append(
                {
                    "surface": "public_url",
                    "status": public_url.get("http_status", public_url.get("error_type", "error")),
                }
            )
        if failures:
            report["document_failures"] = failures
            report["status"] = "partial"
        else:
            report["status"] = "checked"
    except Exception as exc:  # noqa: BLE001 - retain provider-specific failure diagnostics
        report["status"] = "error"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
    return report


def _is_search_endpoint(url: str) -> bool:
    """Return whether a result URL is the search transport, not a document."""

    parsed = urlparse(url)
    path = parsed.path.casefold()
    return any(marker in path for marker in ("/buscar", "/search", "/pesquisar", "/ajax.php"))


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
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return {
            "status": "invalid_url",
            "error_type": "url_not_allowlisted",
        }
    response: requests.Response | None = None
    try:
        current_url = url
        redirects: list[dict[str, str | int]] = []
        for _ in range(4):
            response = requests.get(
                current_url,
                headers={"User-Agent": "NanoJuris/0.3 (+https://github.com/ndtj/nanojuris)"},
                timeout=timeout,
                allow_redirects=False,
                verify=True,
                stream=True,
            )
            location = response.headers.get("location")
            if response.is_redirect and location:
                next_url = urljoin(current_url, location)
                next_parsed = urlparse(next_url)
                if (
                    next_parsed.scheme != "https"
                    or not next_parsed.hostname
                    or not _host_is_allowlisted(next_parsed.hostname, parsed.hostname)
                ):
                    return {
                        "status": "redirect_outside_allowlist",
                        "http_status": response.status_code,
                        "final_url": next_url,
                        "redirects": redirects,
                    }
                redirects.append(
                    {
                        "status": response.status_code,
                        "url": current_url,
                        "location": next_url,
                    }
                )
                response.close()
                response = None
                current_url = next_url
                continue
            break
        else:
            return {
                "status": "redirect_limit",
                "final_url": current_url,
                "redirects": redirects,
            }
        final_url = current_url
        declared_content_type = response.headers.get("content-type", "")
        declared_length = _header_int(response.headers.get("content-length"))
        if declared_length is not None and declared_length > MAX_DOCUMENT_PROBE_BYTES:
            return {
                "status": "too_large",
                "http_status": response.status_code,
                "final_url": final_url,
                "content_type": declared_content_type,
                "response_bytes": declared_length,
                "max_bytes": MAX_DOCUMENT_PROBE_BYTES,
            }
        chunks: list[bytes] = []
        total = 0
        exceeded = False
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_DOCUMENT_PROBE_BYTES:
                exceeded = True
                break
            chunks.append(chunk)
        content = b"".join(chunks)
        if exceeded:
            return {
                "status": "too_large",
                "http_status": response.status_code,
                "final_url": final_url,
                "content_type": declared_content_type,
                "response_bytes": total,
                "max_bytes": MAX_DOCUMENT_PROBE_BYTES,
            }
        content_type = response.headers.get("content-type", "")
        quality = assess_document_content(
            content,
            content_type,
            max_bytes=MAX_DOCUMENT_PROBE_BYTES,
        )
        looks_like_document = (
            quality["detected_content_type"] in {"application/pdf", "text/html", "text/plain"}
            or "/document" in final_url.lower()
            or "/jurisprudence/" in final_url.lower()
            or "/jurisprudencia/j/" in final_url.lower()
            or "getinteiroteor" in final_url.lower()
        )
        status = "reachable" if response.ok and content else "http_error"
        if quality["status"] in {"invalid", "empty", "empty_text"}:
            status = "invalid_document" if response.ok else status
        return {
            "status": status,
            "http_status": response.status_code,
            "final_url": final_url,
            "redirects": redirects,
            "content_type": content_type,
            "response_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "is_pdf": quality["detected_content_type"] == "application/pdf",
            "has_html": quality["detected_content_type"] == "text/html",
            "text_like": quality["detected_content_type"].startswith("text/"),
            "looks_like_document": looks_like_document,
            "quality": quality,
        }
    except Exception as exc:  # noqa: BLE001 - record TLS/timeout/WAF observations
        return {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}
    finally:
        if response is not None:
            response.close()


def _header_int(value: str | None) -> int | None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _host_is_allowlisted(hostname: str, original: str | None) -> bool:
    if not original:
        return False
    current = hostname.casefold().rstrip(".")
    expected = original.casefold().rstrip(".")
    return current == expected or current.endswith(f".{expected}")


def _summary(reports: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "sources_checked": len(reports),
        "search_returned": 0,
        "full_text_in_search": 0,
        "provider_document_loaded": 0,
        "public_url_reachable": 0,
        "public_url_document_like": 0,
        "document_probe_failures": 0,
        "partial": 0,
        "errors": 0,
    }
    for report in reports:
        if report.get("search", {}).get("returned", 0):
            summary["search_returned"] += 1
        if report.get("result", {}).get("full_text_present"):
            summary["full_text_in_search"] += 1
        if report.get("provider_document", {}).get("status") in {"loaded", "inline_text"}:
            summary["provider_document_loaded"] += 1
        if report.get("public_url", {}).get("status") == "reachable":
            summary["public_url_reachable"] += 1
        if report.get("public_url", {}).get("looks_like_document"):
            summary["public_url_document_like"] += 1
        if report.get("document_failures"):
            summary["document_probe_failures"] += 1
        if report.get("status") == "partial":
            summary["partial"] += 1
        if report.get("status") == "error":
            summary["errors"] += 1
    return summary


if __name__ == "__main__":
    raise SystemExit(main())
