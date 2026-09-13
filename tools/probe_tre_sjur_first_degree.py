"""Run a bounded, metadata-only SJUR/TRE first-degree sweep.

The command uses the public route already declared by the NanoJuris adapter. It
does not follow challenges, replay cookies, or persist response bodies. A single
small request is made per TRE in series and only sanitized response metadata is
written to the evidence artifact.
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

# Keep the tool executable from a clean checkout without requiring an editable
# install.  This is the same import layout used by the other repository tools.
ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
SOURCE_ROOT_TEXT = str(SOURCE_ROOT)
if SOURCE_ROOT_TEXT in sys.path:
    sys.path.remove(SOURCE_ROOT_TEXT)
sys.path.insert(0, SOURCE_ROOT_TEXT)

from nanojuris.config import NanoJurisConfig, configure_requests_session  # noqa: E402
from nanojuris.models import JurisprudenceQuery  # noqa: E402
from nanojuris.providers.tse_sjur_jurisprudencia import (  # noqa: E402
    TRE_STATES,
    _infer_tre_degree,
    build_tse_query,
)  # noqa: E402

DEFAULT_OUTPUT = (
    ROOT / "docs" / "provider-discovery" / "tre-sjur-first-degree-multi-uf-live-20260912.json"
)
DEFAULT_MARKDOWN = (
    ROOT / "docs" / "provider-discovery" / "tre-sjur-first-degree-multi-uf-live-20260912.md"
)
SEARCH_TEMPLATE = (
    "https://sjur-pesquisa-api.tse.jus.br/{state}/"
    "sjur-pesquisa-backend/rest/public/pesquisa/simples"
)
QUERY_TEXT = "sentença"
# Keep the bounded probe aligned with the provider transport.  TRE-GO and
# TRE-PB legitimately exceed 8 MB for one public window; treating those
# responses as unavailable would hide valid second-degree-only windows and
# make the first-degree audit less informative.
MAX_RESPONSE_BYTES = 16_000_000
MIN_INTERVAL_SECONDS = 2.0
USER_AGENT = "NanoJuris/0.4.0 (+bounded official SJUR/TRE inventory)"


def _payload(state: str) -> dict[str, Any]:
    query = JurisprudenceQuery(text=QUERY_TEXT, page_size=20)
    dsl = build_tse_query(query)
    dsl["bool"]["filter"] = [{"terms": {"siglaTribunalJE.keyword": [f"TRE-{state}"]}}]
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


def _classify_types(content: list[Any]) -> dict[str, Any]:
    types: Counter[str] = Counter()
    degrees: Counter[str] = Counter()
    text_records = 0
    for item in content:
        if not isinstance(item, dict):
            continue
        decision_type = str(item.get("descricaoTipoDecisao") or "").strip() or "unknown"
        types[decision_type] += 1
        degree = _infer_tre_degree(decision_type) or "unknown"
        degrees[degree] += 1
        if item.get("textoEmenta") or item.get("textoDecisao"):
            text_records += 1
    return {
        "decision_types": dict(sorted(types.items())),
        "degree_labels": dict(sorted(degrees.items())),
        "text_records": text_records,
    }


def probe(*, timeout: float, interval: float, observed_at: str) -> dict[str, Any]:
    config = NanoJurisConfig(timeout=timeout, rate_limit_interval=0)
    session = configure_requests_session(requests.Session(), config)
    results: list[dict[str, Any]] = []
    next_allowed = time.monotonic()
    for index, state in enumerate(TRE_STATES):
        if index and time.monotonic() < next_allowed:
            time.sleep(next_allowed - time.monotonic())
        url = SEARCH_TEMPLATE.format(state=f"tre-{state.casefold()}")
        record: dict[str, Any] = {
            "tribunal": f"TRE-{state}",
            "route": url,
            "request_method": "POST",
            "query": QUERY_TEXT,
            "credentials_used": False,
            "bypass_attempted": False,
        }
        response: requests.Response | None = None
        try:
            response = session.post(
                url,
                json=_payload(state),
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
            elif response.status_code is None or response.status_code >= 500:
                record["classification"] = "source_unavailable"
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
                        record.update(
                            {
                                "reported_total": total,
                                "returned": len(content),
                                **_classify_types(content),
                            }
                        )
                        record["classification"] = (
                            "success_with_explicit_first_degree_label"
                            if record["degree_labels"].get("first", 0)
                            else "success_without_first_degree_label"
                            if content
                            else "authoritative_empty"
                        )
        except requests.RequestException as exc:
            record.update({"classification": "transport_error", "error_type": type(exc).__name__})
        finally:
            if response is not None:
                response.close()
        results.append(record)
        next_allowed = time.monotonic() + max(interval, MIN_INTERVAL_SECONDS)
    return {
        "schema_version": "tre-sjur-first-degree-multi-uf-live-v1",
        "observed_at": observed_at,
        "official_frontend": "https://jurisprudencia-tres.tse.jus.br/",
        "route_template": SEARCH_TEMPLATE,
        "scope": "one bounded public page per TRE; metadata only",
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


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SJUR/TRE — sondagem bounded de primeiro grau",
        "",
        f"Observado em `{payload['observed_at']}`; uma requisição pública por TRE.",
        "Corpos não foram persistidos, e nenhum provider foi promovido.",
        "",
        "| TRE | HTTP | Total | Retornos | Graus explícitos | Classificação |",
        "|---|---:|---:|---:|---|---|",
    ]
    for item in payload["results"]:
        degrees = (
            ", ".join(f"{key}:{value}" for key, value in (item.get("degree_labels") or {}).items())
            or "-"
        )
        lines.append(
            f"| `{item['tribunal']}` | {item.get('http_status', '-')} | "
            f"{item.get('reported_total', '-')} | {item.get('returned', '-')} | "
            f"{degrees} | `{item.get('classification', 'unknown')}` |"
        )
    lines.extend(
        [
            "",
            (
                "A classificação `success_with_explicit_first_degree_label` é evidência de "
                "conteúdo rotulado, não de paginação completa, inteiro teor ou promoção."
            ),
            (
                "CAPTCHA, WAF, login, HTTP 403/429, timeout, TLS e schema inválido "
                "permanecem estados explícitos."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--interval", type=float, default=MIN_INTERVAL_SECONDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    payload = probe(
        timeout=args.timeout,
        interval=args.interval,
        observed_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {"output": str(args.output), "results": len(payload["results"])}, ensure_ascii=False
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
