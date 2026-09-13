"""Discover candidate first-degree jurisprudence routes from official TJ sites.

This is a bounded *discovery* tool, not a scraper.  It performs one homepage
request per state court and, optionally, a very small number of public
JavaScript requests.  It records only route metadata and hashes; response
bodies are never persisted.  A candidate route is not evidence of a CJPG
contract and must pass the normal NanoJuris contract/live/fixture gates before
it can be implemented or federated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from nanojuris.brazil import COURTS  # noqa: E402

DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "first-degree-route-inventory-20260906.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "provider-discovery" / "first-degree-route-inventory-20260906.md"
USER_AGENT = "NanoJuris-discovery/1.0 (+bounded official-route inventory)"
MAX_BODY_BYTES = 2_000_000

# These markers identify a possible first-degree jurisprudence surface.  They
# intentionally include broad terms because many tribunals use local names;
# the output is a candidate inventory, never an automatic promotion.
_MARKER_RE = re.compile(
    r"(?:cjpg|jurisprud|ement[aá]rio|senten[cç]|decis[aã]o.{0,30}(?:1g|1º|primeiro)|"
    r"(?:1g|1º|primeiro).{0,30}(?:grau|inst[aâ]ncia))",
    re.IGNORECASE,
)
_SCRIPT_RE = re.compile(r"(?:\.js(?:\?|$)|javascript:)", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class _Candidate:
    url: str
    source_url: str
    kind: str
    markers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "source_url": self.source_url,
            "kind": self.kind,
            "markers": list(self.markers),
            "scope": _route_scope(self.url),
        }


def _state_courts() -> list[Any]:
    return [court for court in COURTS if court.branch == "state" and court.code.startswith("TJ")]


def _classification(status: int | None) -> str:
    if status is None:
        return "transport_error"
    if 200 <= status < 400:
        return "reachable"
    if status in {401, 403, 429}:
        return "access_controlled"
    if status >= 500:
        return "source_unavailable"
    return "unexpected_status"


def _markers(value: str) -> tuple[str, ...]:
    found: list[str] = []
    for match in _MARKER_RE.finditer(value):
        token = re.sub(r"\s+", " ", match.group(0)).strip()[:80]
        if token and token.casefold() not in {item.casefold() for item in found}:
            found.append(token)
    return tuple(found[:8])


def _candidate_urls(html: bytes, source_url: str) -> tuple[list[_Candidate], list[str]]:
    """Extract route and script candidates without following arbitrary links."""

    text = html.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(text, "html.parser")
    candidates: list[_Candidate] = []
    scripts: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href", "")).strip()
        label = anchor.get_text(" ", strip=True)
        joined = urljoin(source_url, href)
        markers = _markers(f"{label} {href}")
        if markers:
            candidates.append(_Candidate(joined, source_url, "link", markers))
    for script in soup.find_all("script", src=True):
        src = urljoin(source_url, str(script.get("src", "")).strip())
        scripts.append(src)
    # Some portals put endpoint strings directly in inline scripts or data
    # attributes.  Keep only short URL-like tokens with a relevant marker.
    for match in re.finditer(r"https?://[^\"'\s<>]{1,500}", text):
        value = match.group(0)
        markers = _markers(value)
        if markers:
            candidates.append(_Candidate(value, source_url, "inline_url", markers))
    return _dedupe(candidates), list(dict.fromkeys(scripts))


def _dedupe(candidates: list[_Candidate]) -> list[_Candidate]:
    seen: set[tuple[str, str]] = set()
    output: list[_Candidate] = []
    for item in candidates:
        key = (item.kind, item.url)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _is_likely_first_degree_route(candidate: _Candidate) -> bool:
    """Select route-shaped candidates while excluding news/process links."""

    parsed = urlparse(candidate.url)
    path = parsed.path.casefold()
    host = (parsed.hostname or "").casefold()
    if any(
        token in path
        for token in (
            "/noticia",
            "/imprensa",
            "/sala-de-imprensa",
            "/mutirao",
            "/comissao",
            "/projetos/peticao",
            "/comunicacao/acoes",
            "/wp-content/",
        )
    ):
        return False
    if "corteidh" in host:
        return False
    return bool(re.search(r"cjpg|senten[cç]|ement[aá]rio", f"{host}{path}", re.IGNORECASE))


def _route_scope(url: str) -> str:
    """Classify route shape without claiming that it is a valid contract."""

    parsed = urlparse(url)
    value = f"{parsed.hostname or ''}{parsed.path}".casefold()
    if re.search(
        r"cpopg|cposg|/cpo/|/processo|consulta-processual|pje/login|projudi/processo", value
    ):
        return "process_surface"
    if re.search(r"cjpg|senten[cç]|ement[aá]rio|jurisprud", value):
        return "jurisprudence_candidate"
    return "contextual_or_unknown"


def _fetch(session: requests.Session, url: str, timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {
        "url": url,
        "request_method": "GET",
        "credentials_used": False,
    }
    try:
        response = session.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        body = response.raw.read(MAX_BODY_BYTES + 1)
    except requests.RequestException as exc:
        result.update(
            {
                "status": None,
                "classification": "transport_error",
                "error_type": type(exc).__name__,
            }
        )
        return result
    truncated = len(body) > MAX_BODY_BYTES
    if truncated:
        body = body[:MAX_BODY_BYTES]
    result.update(
        {
            "status": response.status_code,
            "final_url": response.url,
            "content_type": response.headers.get("content-type"),
            "response_bytes_observed": len(body),
            "truncated": truncated,
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "classification": _classification(response.status_code),
        }
    )
    return result


def discover(
    *,
    timeout: float,
    max_scripts: int,
    probe_candidates: bool,
    max_candidate_probes: int,
    observed_at: str,
) -> dict[str, Any]:
    session = requests.Session()
    results: list[dict[str, Any]] = []
    for court in _state_courts():
        homepage = _fetch(session, court.official_url, timeout)
        item: dict[str, Any] = {
            "authority": court.code,
            "branch": court.branch,
            "state": court.state,
            "official_url": court.official_url,
            "homepage": homepage,
            "candidate_routes": [],
            "candidate_probes": [],
            "script_probes": [],
            "promotion_decision": "discovery_only",
        }
        if homepage.get("status") and 200 <= int(homepage["status"]) < 400:
            try:
                response = session.get(
                    court.official_url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=timeout,
                    allow_redirects=True,
                )
                body = response.content[: MAX_BODY_BYTES + 1]
            except requests.RequestException:
                body = b""
            routes, scripts = _candidate_urls(
                body, str(homepage.get("final_url") or court.official_url)
            )
            item["candidate_routes"] = [candidate.to_dict() for candidate in routes[:100]]
            if probe_candidates:
                # Probe only the bounded number of likely first-degree routes
                # requested by the caller. This does not follow forms or
                # submit searches; it only records route reachability.
                likely = [
                    candidate for candidate in routes if _is_likely_first_degree_route(candidate)
                ]
                for candidate in likely[: max(0, max_candidate_probes)]:
                    item["candidate_probes"].append(_fetch(session, candidate.url, timeout))
            for script_url in scripts[:max_scripts]:
                probe = _fetch(session, script_url, timeout)
                # A script probe records metadata only.  It is deliberately
                # not parsed recursively to keep the operation bounded.
                item["script_probes"].append(probe)
        results.append(item)
    return {
        "schema_version": 1,
        "observed_at": observed_at,
        "scope": "state_court_first_degree_route_discovery",
        "network_access": "bounded_one_homepage_plus_limited_public_scripts_per_tj",
        "credentials_used": False,
        "response_bodies_persisted": False,
        "marker_policy": (
            "candidate markers only; no route is a CJPG contract without independent validation"
        ),
        "limits": {
            "courts": len(results),
            "max_scripts_per_court": max_scripts,
            "max_candidate_probes_per_court": max(0, max_candidate_probes)
            if probe_candidates
            else 0,
            "max_body_bytes": MAX_BODY_BYTES,
        },
        "results": results,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Inventário bounded de rotas de primeiro grau",
        "",
        f"Observado em `{payload['observed_at']}`. Foram consultadas "
        f"**{len(payload['results'])}** páginas oficiais de TJs.",
        "",
        "Este artefato é descoberta de rotas, não prova de jurisprudência CJPG. "
        "Cada candidato precisa de contrato, fixture, chamada live, qualidade e "
        "federação independentes.",
        "",
        "| Tribunal | Homepage | Candidatos | Scripts sondados | Classificação |",
        "|---|---:|---:|---:|---|",
    ]
    for item in payload["results"]:
        home = item["homepage"]
        lines.append(
            f"| `{item['authority']}` | `{home.get('classification', 'unknown')}` | "
            f"{len(item['candidate_routes'])} | {len(item['script_probes'])} | "
            f"`{item['promotion_decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Regras",
            "",
            "- `CPOPG` é consulta processual e não é contado como jurisprudência textual.",
            "- CAPTCHA, Turnstile, WAF, login, timeout e HTTP 403 permanecem estados de acesso.",
            "- Marcadores encontrados em HTML/JS não são evidência suficiente de um endpoint.",
            "- Nenhuma resposta foi persistida; somente metadados e hashes foram registrados.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--max-scripts", type=int, default=2)
    parser.add_argument(
        "--probe-candidates",
        action="store_true",
        help="faz GETs bounded em rotas candidatas por tribunal",
    )
    parser.add_argument(
        "--max-candidate-probes",
        type=int,
        default=1,
        help="maximo de GETs candidatos por tribunal quando habilitado",
    )
    parser.add_argument(
        "--observed-at",
        default=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    )
    args = parser.parse_args()
    if args.max_scripts < 0 or args.max_scripts > 5:
        parser.error("--max-scripts deve estar entre 0 e 5")
    if args.max_candidate_probes < 0 or args.max_candidate_probes > 10:
        parser.error("--max-candidate-probes deve estar entre 0 e 10")
    payload = discover(
        timeout=args.timeout,
        max_scripts=args.max_scripts,
        probe_candidates=args.probe_candidates,
        max_candidate_probes=args.max_candidate_probes,
        observed_at=args.observed_at,
    )
    output = args.output if args.output.is_absolute() else ROOT / args.output
    markdown_output = (
        args.markdown_output if args.markdown_output.is_absolute() else ROOT / args.markdown_output
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps({"output": str(output), "courts": len(payload["results"])}, ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
