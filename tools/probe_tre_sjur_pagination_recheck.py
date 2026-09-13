"""Recheck official SJUR/TRE pagination without persisting response bodies.

The public SPA sends a zero-based ``pagina`` field.  This probe compares two
adjacent requests for one regional court and records only bounded metadata,
hashes and stable-id samples.  It deliberately does not follow challenges,
request credentials, or retry a blocked response.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "tre-sjur-pagination-recheck-20260912.json"
MAX_RESPONSE_BYTES = 16_000_000
USER_AGENT = "NanoJuris/0.4.0 (+bounded official SJUR/TRE pagination recheck)"
SEARCH_TEMPLATE = (
    "https://sjur-pesquisa-api.tse.jus.br/{slug}/sjur-pesquisa-backend/rest/public/pesquisa/simples"
)


def _payload(tribunal: str, page: int) -> dict[str, Any]:
    # Keep the query deliberately broad enough to exercise the source window,
    # but constrain it to an explicit appellate decision type.
    dsl = {
        "bool": {
            "must": [
                {
                    "query_string": {
                        "query": "jurisprudencia",
                        "fields": [
                            "textoEmenta",
                            "textoDecisao",
                            "indexacoes",
                            "assuntos.nomeAssunto",
                        ],
                        "default_operator": "AND",
                    }
                }
            ],
            "filter": [
                {"terms": {"siglaTribunalJE.keyword": [tribunal]}},
                {"terms": {"descricaoTipoDecisao.keyword": ["Acórdão"]}},
            ],
            "must_not": [],
            "should": [],
        }
    }
    slug = tribunal.casefold()
    return {
        "termoPesquisa": json.dumps(dsl, ensure_ascii=False, separators=(",", ":")),
        "pagina": page,
        "tamanho": 1,
        "tribunais": [slug],
    }


def _bounded_body(response: requests.Response) -> bytes | None:
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def _probe(tribunal: str, page: int, timeout: float) -> dict[str, Any]:
    slug = tribunal.casefold()
    url = SEARCH_TEMPLATE.format(slug=slug)
    started = time.perf_counter()
    record: dict[str, Any] = {
        "tribunal": tribunal,
        "page": page,
        "request_method": "POST",
        "url": url,
        "credentials_used": False,
        "bypass_attempted": False,
    }
    try:
        response = requests.post(
            url,
            json=_payload(tribunal, page),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            timeout=timeout,
            stream=True,
        )
        body = _bounded_body(response)
        record.update(
            {
                "http_status": response.status_code,
                "content_type": response.headers.get("content-type"),
                "response_bytes": len(body) if body is not None else None,
                "response_sha256": hashlib.sha256(body).hexdigest() if body is not None else None,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            }
        )
        if body is None:
            record["classification"] = "response_too_large"
            return record
        if response.status_code in {401, 403}:
            record["classification"] = "access_controlled"
            return record
        if response.status_code == 429:
            record["classification"] = "rate_limited"
            return record
        if response.status_code >= 400:
            record["classification"] = "request_rejected"
            return record
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            record["classification"] = "schema_invalid"
            return record
        content = payload.get("content") if isinstance(payload, dict) else None
        if not isinstance(content, list):
            record["classification"] = "schema_invalid"
            return record
        record.update(
            {
                "classification": "success_with_results" if content else "authoritative_empty",
                "reported_total": payload.get("totalRegistros"),
                "returned": len(content),
                "first_ids": [
                    str(item.get("codigoDecisao")) for item in content[:5] if isinstance(item, dict)
                ],
                "last_ids": [
                    str(item.get("codigoDecisao"))
                    for item in content[-5:]
                    if isinstance(item, dict)
                ],
            }
        )
        return record
    except requests.Timeout:
        record["classification"] = "timeout"
    except requests.RequestException as exc:
        record["classification"] = "transport_error"
        record["error_type"] = type(exc).__name__
    finally:
        record.setdefault("elapsed_ms", round((time.perf_counter() - started) * 1000, 2))
    return record


def probe(*, tribunal: str, timeout: float, interval: float) -> dict[str, Any]:
    first = _probe(tribunal, 0, timeout)
    time.sleep(max(interval, 0.0))
    second = _probe(tribunal, 1, timeout)
    comparable = all(
        item.get("classification") == "success_with_results" for item in (first, second)
    )
    duplicate_window = comparable and (
        first.get("response_sha256") == second.get("response_sha256")
        or first.get("first_ids") == second.get("first_ids")
    )
    return {
        "schema_version": "tre-sjur-pagination-recheck-v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "response_bodies_persisted": False,
        "max_remote_bytes": MAX_RESPONSE_BYTES,
        "tribunal": tribunal,
        "results": [first, second],
        "pagination_classification": (
            "remote_page_ignored_duplicate_window" if duplicate_window else "not_proven"
        ),
        "decision": (
            "keep_page_gt_1_rejected_and_total_unknown"
            if duplicate_window
            else "manual_review_required"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tribunal", default="TRE-SP")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = probe(tribunal=args.tribunal.upper(), timeout=args.timeout, interval=args.interval)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: payload[key] for key in ("tribunal", "pagination_classification", "decision")}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
