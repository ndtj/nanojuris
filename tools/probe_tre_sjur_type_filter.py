"""Probe the official SJUR/TRE decision-type filter without persisting bodies.

This is a bounded contract check for the filter exposed by the public TSE SPA.
It deliberately samples a small set of TREs, serializes requests, and records
only response metadata and decision-type counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
SOURCE_ROOT_TEXT = str(SOURCE_ROOT)
if SOURCE_ROOT_TEXT in sys.path:
    sys.path.remove(SOURCE_ROOT_TEXT)
sys.path.insert(0, SOURCE_ROOT_TEXT)

from nanojuris.config import NanoJurisConfig, configure_requests_session  # noqa: E402
from nanojuris.models import JurisprudenceQuery  # noqa: E402
from nanojuris.providers.tse_sjur_jurisprudencia import build_tse_query  # noqa: E402

SEARCH_TEMPLATE = (
    "https://sjur-pesquisa-api.tse.jus.br/{state}/"
    "sjur-pesquisa-backend/rest/public/pesquisa/simples"
)
MAX_RESPONSE_BYTES = 8_000_000
MIN_INTERVAL_SECONDS = 2.0
USER_AGENT = "NanoJuris/0.4.0 (+bounded official SJUR/TRE filter check)"
FIRST_DEGREE_LABELS = ("Sentença",)
SECOND_DEGREE_LABELS = (
    "Acórdão",
    "Decisão monocrática",
    "Resolução",
    "Decisão sem resolução",
)


def _payload(state: str, type_labels: tuple[str, ...]) -> dict[str, Any]:
    query = JurisprudenceQuery(text="sentença", page_size=20)
    dsl = build_tse_query(query)
    dsl["bool"]["filter"] = [
        {"terms": {"siglaTribunalJE.keyword": [f"TRE-{state}"]}},
        {"terms": {"descricaoTipoDecisao.keyword": list(type_labels)}},
    ]
    return {
        "termoPesquisa": json.dumps(dsl, ensure_ascii=False, separators=(",", ":")),
        "pagina": 0,
        "tamanho": 20,
        "tribunais": [f"tre-{state.casefold()}"],
    }


def _read_bounded(response: requests.Response) -> bytes | None:
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


def probe(
    states: tuple[str, ...],
    *,
    type_labels: tuple[str, ...],
    scope: str,
    timeout: float,
    interval: float,
) -> dict[str, Any]:
    config = NanoJurisConfig(timeout=timeout, rate_limit_interval=0)
    session = configure_requests_session(requests.Session(), config)
    results: list[dict[str, Any]] = []
    next_allowed = time.monotonic()
    for index, state in enumerate(states):
        if index and time.monotonic() < next_allowed:
            time.sleep(next_allowed - time.monotonic())
        state = state.upper()
        url = SEARCH_TEMPLATE.format(state=f"tre-{state.casefold()}")
        record: dict[str, Any] = {
            "tribunal": f"TRE-{state}",
            "route": url,
            "request_method": "POST",
            "filter_field": "descricaoTipoDecisao.keyword",
            "filter_values": list(type_labels),
            "credentials_used": False,
            "bypass_attempted": False,
        }
        response: requests.Response | None = None
        try:
            response = session.post(
                url,
                json=_payload(state, type_labels),
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
                timeout=timeout,
                allow_redirects=True,
                stream=True,
            )
            body = _read_bounded(response)
            record.update(
                {
                    "http_status": response.status_code,
                    "final_url": response.url,
                    "content_type": response.headers.get("content-type"),
                    "response_bytes": len(body) if body is not None else None,
                    "response_sha256": (
                        hashlib.sha256(body).hexdigest() if body is not None else None
                    ),
                }
            )
            if body is None:
                record["classification"] = "response_too_large"
            elif response.status_code in {401, 403}:
                record["classification"] = "access_controlled"
            elif response.status_code == 429:
                record["classification"] = "rate_limited"
            elif response.status_code >= 400:
                record["classification"] = "request_rejected"
            else:
                try:
                    payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    record["classification"] = "schema_invalid"
                else:
                    content = payload.get("content") if isinstance(payload, dict) else None
                    total = payload.get("totalRegistros") if isinstance(payload, dict) else None
                    if not isinstance(content, list) or not isinstance(total, int) or total < 0:
                        record["classification"] = "schema_invalid"
                    else:
                        types: Counter[str] = Counter(
                            str(item.get("descricaoTipoDecisao") or "unknown")
                            for item in content
                            if isinstance(item, dict)
                        )
                        record.update(
                            {
                                "reported_total": total,
                                "returned": len(content),
                                "decision_types": dict(sorted(types.items())),
                                "contains_requested_type": any(
                                    str(item.get("descricaoTipoDecisao") or "").strip()
                                    in type_labels
                                    for item in content
                                    if isinstance(item, dict)
                                ),
                                "unexpected_types": sorted(
                                    {
                                        str(item.get("descricaoTipoDecisao") or "unknown").strip()
                                        for item in content
                                        if isinstance(item, dict)
                                    }
                                    - set(type_labels)
                                ),
                            }
                        )
                        record["classification"] = (
                            "authoritative_empty" if not content else "success_filtered_window"
                        )
        except requests.RequestException as exc:
            record.update({"classification": "transport_error", "error_type": type(exc).__name__})
        finally:
            if response is not None:
                response.close()
        results.append(record)
        next_allowed = time.monotonic() + max(interval, MIN_INTERVAL_SECONDS)
    return {
        "schema_version": "tre-sjur-type-filter-live-v1",
        "observed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "official_frontend": "https://jurisprudencia-tres.tse.jus.br/",
        "scope": f"{scope}-degree bounded public windows using the SPA decision-type filter",
        "degree_scope": scope,
        "requested_type": type_labels[0] if len(type_labels) == 1 else None,
        "requested_types": list(type_labels),
        "credentials_used": False,
        "bypass_attempted": False,
        "response_bodies_persisted": False,
        "safety": {
            "requests": len(results),
            "spacing_seconds": max(interval, MIN_INTERVAL_SECONDS),
            "max_response_bytes": MAX_RESPONSE_BYTES,
            "same_host_parallelism": 1,
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states", nargs="+", default=["MG", "SP", "AC"])
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--interval", type=float, default=MIN_INTERVAL_SECONDS)
    parser.add_argument("--scope", choices=("first", "second"), default="first")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    args = parser.parse_args()
    type_labels = FIRST_DEGREE_LABELS if args.scope == "first" else SECOND_DEGREE_LABELS
    output = args.output or (
        ROOT
        / "docs"
        / "provider-discovery"
        / (
            "tre-sjur-type-filter-live-20260912.json"
            if args.scope == "first"
            else "tre-sjur-second-degree-type-filter-live-20260912.json"
        )
    )
    payload = probe(
        tuple(args.states),
        type_labels=type_labels,
        scope=args.scope,
        timeout=args.timeout,
        interval=args.interval,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({"output": str(output), "results": len(payload["results"])}, ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
