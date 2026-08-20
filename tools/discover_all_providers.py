"""Run a bounded, evidence-first discovery sweep over registered providers.

The sweep reads runtime capability declarations, probes only declared public
GET routes plus bounded same-origin links, and emits a comparison report. It
does not submit guessed POST payloads, mutate providers, or treat access
controls as empty data.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from nanojuris.client import NanoJurisClient
from nanojuris.discovery.crawler import DiscoveryCrawler
from nanojuris.discovery.http import HttpDiscoveryClient
from nanojuris.discovery.models import DiscoveryPolicy, DiscoveryRun

_ENDPOINT = re.compile(r"^(?P<method>GET|POST|PUT|DELETE|HEAD|PATCH)\s+(?P<route>.+)$", re.I)
_PLACEHOLDER = re.compile(r"<[^>]+>|\{[^}]+\}")
_URL = re.compile(r"https?://[^\s`)>]+")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _materialize_endpoint(source_url: str, declaration: str) -> tuple[str, str] | None:
    match = _ENDPOINT.match(declaration.strip())
    if not match:
        return None
    method = match.group("method").upper()
    route = match.group("route").strip()
    if route.startswith("<") or route in {"...", "<official-pdf>"}:
        return None
    route = _PLACEHOLDER.sub("sample", route)
    return method, urljoin(source_url.rstrip("/") + "/", route.lstrip("/"))


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().rstrip(".")


def _normalize_filter_name(name: str) -> str:
    value = "".join(
        character
        for character in unicodedata.normalize("NFKD", name.lower())
        if not unicodedata.combining(character)
    )
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    aliases = (
        ("text", ("texto", "termo", "palavra", "query", "busca", "pesquisa", "keyword", "q")),
        ("number", ("numero", "processo", "acordao", "documento", "id_processo")),
        ("page", ("pagina", "page", "offset", "inicio")),
        ("types", ("tipo", "especie", "natureza", "classe")),
        ("courts", ("tribunal", "corte", "foro", "orgao_julgador", "camara", "turma")),
        ("rapporteur", ("relator", "magistrado", "ministro")),
        ("published_from", ("data_publicacao_de", "publicado_de", "data_inicial")),
        ("published_to", ("data_publicacao_ate", "publicado_ate", "data_final")),
        ("updated_from", ("data_atualizacao_de", "atualizado_de")),
        ("updated_to", ("data_atualizacao_ate", "atualizado_ate")),
        ("order_by", ("ordenacao", "ordenar", "sort", "order")),
    )
    for canonical, markers in aliases:
        if value in markers or any(value.startswith(marker + "_") for marker in markers):
            return canonical
    return value


def _declared_routes(source_url: str, endpoints: list[str]) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    for declaration in endpoints:
        materialized = _materialize_endpoint(source_url, declaration)
        if materialized is None:
            continue
        method, url = materialized
        if not any(item["method"] == method and item["url"] == url for item in routes):
            routes.append({"method": method, "url": url, "declaration": declaration})
    return routes


def _candidate_source_urls(root: Path, source_id: str) -> list[str]:
    """Read only official-looking URLs from an unregistered provider dossier."""

    dossier = root / "docs" / "providers" / source_id / "README.md"
    if not dossier.is_file():
        return []
    urls: list[str] = []
    for value in _URL.findall(dossier.read_text(encoding="utf-8", errors="replace")):
        value = value.rstrip(".,;)")
        parsed = urlparse(value)
        if parsed.hostname and "github.com" not in parsed.hostname and value not in urls:
            urls.append(value)
    return urls[:3]


def _run_catalog_candidate(
    source_id: str,
    urls: list[str],
    *,
    max_pages: int,
    max_depth: int,
    timeout: float,
    delay: float,
    cache_dir: str | None,
) -> dict[str, Any]:
    """Capture evidence for a documented source that has no runtime adapter."""

    if not urls:
        return {
            "source": source_id,
            "implementation_status": "none",
            "status": "missing_documented_url",
            "urls": [],
        }
    url = urls[0]
    policy = DiscoveryPolicy(
        allowed_domains=(_host(url),),
        max_pages=max_pages,
        max_depth=max_depth,
        max_bytes_per_response=1_500_000,
        max_total_bytes=max(3_000_000, max_pages * 1_500_000),
        timeout_seconds=timeout,
        delay_seconds=delay,
        respect_robots=True,
    )
    try:
        run = DiscoveryCrawler(HttpDiscoveryClient(policy, cache_dir=cache_dir)).crawl(url)
        evidences = run.evidences
        return {
            "source": source_id,
            "implementation_status": "none",
            "status": "observed" if evidences else "no_observation",
            "urls": urls,
            "observations": [evidence.to_dict(include_body=False) for evidence in evidences],
            "metrics": run.metrics(),
            "todo": [
                "criar adapter somente após contrato, fixture de sucesso/vazio/erro e parser canônico",
                "confirmar rotas, filtros, paginação e detalhe a partir da evidência pública",
            ],
        }
    except Exception as exc:
        return {
            "source": source_id,
            "implementation_status": "none",
            "status": "discovery_error",
            "urls": urls,
            "observations": [],
            "metrics": {},
            "errors": [f"{type(exc).__name__}: {exc}"],
            "todo": ["reproduzir a URL documentada com diagnóstico explícito antes de implementar"],
        }


def _run_provider(
    provider_name: str,
    provider: Any,
    *,
    max_pages: int,
    max_depth: int,
    timeout: float,
    delay: float,
    cache_dir: str | None,
) -> dict[str, Any]:
    capabilities = provider.get_capabilities()
    source_url = capabilities.source_url
    if not source_url:
        return {
            "source": provider_name,
            "status": "missing_source_url",
            "declared": capabilities.to_dict(),
        }
    declared_routes = _declared_routes(source_url, capabilities.endpoints)
    allowed_domains = tuple(
        sorted({_host(source_url), *(_host(route["url"]) for route in declared_routes)})
    )
    policy = DiscoveryPolicy(
        allowed_domains=allowed_domains,
        max_pages=max_pages,
        max_depth=max_depth,
        max_bytes_per_response=1_500_000,
        max_total_bytes=max(3_000_000, max_pages * 1_500_000),
        timeout_seconds=timeout,
        delay_seconds=delay,
        respect_robots=True,
    )
    client = HttpDiscoveryClient(policy, cache_dir=cache_dir)
    observations: list[DiscoveryRun] = []
    errors: list[str] = []
    try:
        # Reserve one observation for the declared seed and use the remaining
        # budget for concrete GET contracts. This keeps the sweep bounded even
        # when a provider declares many endpoints.
        seed_budget = min(1, max_pages)
        seed_policy = DiscoveryPolicy(
            allowed_domains=allowed_domains,
            max_pages=seed_budget,
            max_depth=0,
            max_bytes_per_response=1_500_000,
            max_total_bytes=1_500_000,
            timeout_seconds=timeout,
            delay_seconds=delay,
            respect_robots=True,
        )
        observations.append(
            DiscoveryCrawler(HttpDiscoveryClient(seed_policy, cache_dir=cache_dir)).crawl(
                source_url
            )
        )
        remaining = max(0, max_pages - len(observations[0].evidences))
        for route in _declared_routes(source_url, capabilities.endpoints):
            if route["method"] != "GET" or remaining <= 0:
                continue
            try:
                observations.append(client.discover(route["url"], method="GET"))
                remaining -= 1
            except Exception as exc:  # discovery report must preserve per-source progress
                errors.append(f"{route['url']}: {type(exc).__name__}: {exc}")
    except Exception as exc:
        errors.append(f"{source_url}: {type(exc).__name__}: {exc}")

    evidences = [evidence for run in observations for evidence in run.evidences]
    statuses = Counter(evidence.status.value for evidence in evidences)
    routes = {}
    filters = {}
    for evidence in evidences:
        for candidate in evidence.route_candidates:
            key = (candidate.method, candidate.url)
            routes.setdefault(f"{key[0]} {key[1]}", candidate.to_dict())
        for candidate in evidence.filter_candidates:
            filters.setdefault(f"{candidate.source}:{candidate.name}", candidate.to_dict())
    return {
        "source": provider_name,
        "status": "observed" if evidences else "no_observation",
        "declared": capabilities.to_dict(),
        "declared_routes": declared_routes,
        "declared_filters": list(capabilities.supported_filters),
        "observations": [evidence.to_dict(include_body=False) for evidence in evidences],
        "observed_routes": list(routes.values()),
        "observed_filters": list(filters.values()),
        "contract_comparison": {
            "declared_get_routes": [route for route in declared_routes if route["method"] == "GET"],
            "observed_declared_get_routes": [
                route
                for route in declared_routes
                if route["method"] == "GET"
                and any(item.request.url == route["url"] for item in evidences)
            ],
            "unobserved_declared_get_routes": [
                route
                for route in declared_routes
                if route["method"] == "GET"
                and not any(item.request.url == route["url"] for item in evidences)
            ],
            "declared_post_routes": [
                route for route in declared_routes if route["method"] == "POST"
            ],
            "observed_filter_semantics": sorted(
                {
                    _normalize_filter_name(str(item.get("name", "")))
                    for item in filters.values()
                    if item.get("name")
                }
            ),
            "declared_filters_not_observed_semantically": sorted(
                set(capabilities.supported_filters)
                - {
                    _normalize_filter_name(str(item.get("name", "")))
                    for item in filters.values()
                    if item.get("name")
                }
            ),
        },
        "todo": _provider_todo(capabilities, evidences, declared_routes, filters),
        "metrics": {
            "observations": len(evidences),
            "statuses": dict(statuses),
            "route_candidates": len(routes),
            "filter_candidates": len(filters),
            "public_observations": sum(e.access_status.value == "public" for e in evidences),
            "access_controlled_observations": sum(
                e.access_status.value in {"access_control_required", "login_required"}
                for e in evidences
            ),
        },
        "errors": errors,
        "interpretation": [
            "Rotas declaradas com POST não foram submetidas automaticamente; exigem payload e revisão do contrato.",
            "A ausência de observação não representa ausência de dados.",
            "Bloqueios, login, rate limit, timeout e falhas TLS permanecem estados explícitos.",
        ],
    }


def _provider_todo(
    capabilities: Any,
    evidences: list[Any],
    declared_routes: list[dict[str, str]],
    filters: dict[str, Any],
) -> list[str]:
    statuses = {evidence.status.value for evidence in evidences}
    todos: list[str] = []
    if not evidences:
        todos.append("obter evidencia bounded da URL declarada")
    if "robots_disallowed" in statuses:
        todos.append("revisar robots.txt e agendar nova coleta autorizada")
    if statuses.intersection({"access_controlled", "redirect_outside_allowlist"}):
        todos.append("documentar controle de acesso/SSO e confirmar rota pública alternativa")
    if statuses.intersection({"source_unavailable", "timeout", "tls_error"}):
        todos.append("reproduzir indisponibilidade e criar teste de falha explícito")
    if any(route["method"] == "POST" for route in declared_routes):
        todos.append("confirmar payload, filtros e paginação dos endpoints POST com fixture")
    if any(
        route["method"] == "GET" and not any(e.request.url == route["url"] for e in evidences)
        for route in declared_routes
    ):
        todos.append("capturar e validar GETs declarados ainda não observados")
    if not filters:
        todos.append("capturar fixture de formulário/JSON para confirmar filtros")
    if not any(e.legal_signals for e in evidences):
        todos.append("validar sinais de jurisprudência e contrato canônico")
    return todos


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Sweep live de todos os providers",
        "",
        f"Gerado em `{report['generated_at']}`; modo `{report['mode']}`; providers: **{report['provider_count']}**.",
        "",
        "## Resumo",
        "",
        f"- Observados: **{summary['observed']}**; sem observação: **{summary['no_observation']}**.",
        f"- Rotas declaradas: **{summary['declared_routes']}**; candidatas observadas: **{summary['observed_routes']}**.",
        f"- Filtros declarados: **{summary['declared_filters']}**; campos observados: **{summary['observed_filters']}**.",
        f"- Providers com sinais de controle de acesso: **{summary['access_controlled']}**.",
        "",
        "## Matriz de maturação da evidência",
        "",
        "| Provider | Observações | Status | Rotas | Filtros | TODO principal |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for provider in report["providers"]:
        metrics = provider.get("metrics", {})
        statuses = (
            ", ".join(f"{key}:{value}" for key, value in metrics.get("statuses", {}).items())
            or "sem resposta"
        )
        todo = (provider.get("todo") or ["nenhum TODO automático"])[0]
        lines.append(
            f"| `{provider['source']}` | {metrics.get('observations', 0)} | {statuses} | "
            f"{len(provider.get('observed_routes', []))} | {len(provider.get('observed_filters', []))} | {todo} |"
        )
    lines += [
        "",
        "## Interpretação",
        "",
        "Este artefato é evidência de discovery, não promoção automática de parser.",
        "POSTs não foram submetidos sem payload contratado. Bloqueios, robots, SSO, rate limit, timeout e indisponibilidade permanecem estados explícitos.",
        "",
        "O JSON contém hashes, rotas, filtros, comparação de contrato e TODOs por provider.",
        "",
    ]
    candidates = report.get("catalog_candidates", [])
    if candidates:
        lines += [
            "## Candidates do catálogo sem adapter runtime",
            "",
            "| Source | Status live | Observações | Próximo passo |",
            "| --- | --- | ---: | --- |",
        ]
        for candidate in candidates:
            lines.append(
                f"| `{candidate['source']}` | {candidate.get('status', 'unknown')} | "
                f"{candidate.get('metrics', {}).get('observations', 0)} | "
                f"{(candidate.get('todo') or ['revisar contrato'])[0]} |"
            )
        lines.append("")
    return "\n".join(lines)


def sweep(
    *,
    sources: set[str] | None = None,
    max_pages: int = 3,
    max_depth: int = 1,
    timeout: float = 8.0,
    delay: float = 0.25,
    cache_dir: str | None = None,
    root: Path | None = None,
    include_catalog_candidates: bool = False,
) -> dict[str, Any]:
    client = NanoJurisClient()
    selected = sorted(sources or client.providers.keys())
    unknown = sorted(set(selected).difference(client.providers))
    results = []
    for source in selected:
        if source in unknown:
            continue
        results.append(
            _run_provider(
                source,
                client.providers[source],
                max_pages=max_pages,
                max_depth=max_depth,
                timeout=timeout,
                delay=delay,
                cache_dir=cache_dir,
            )
        )
    candidates: list[dict[str, Any]] = []
    if include_catalog_candidates:
        catalog_path = (root or Path.cwd()) / "docs" / "registry" / "provider-catalog.full.json"
        if catalog_path.is_file():
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            for entry in catalog.get("entries", []):
                source = str(entry.get("source_id", ""))
                if entry.get("implementation_status") != "none" or source in client.providers:
                    continue
                candidates.append(
                    _run_catalog_candidate(
                        source,
                        _candidate_source_urls(root or Path.cwd(), source),
                        max_pages=max_pages,
                        max_depth=max_depth,
                        timeout=timeout,
                        delay=delay,
                        cache_dir=cache_dir,
                    )
                )
    return {
        "generated_at": _utc_now(),
        "mode": "live_bounded",
        "provider_count": len(results),
        "catalog_candidate_count": len(candidates),
        "unknown_sources": unknown,
        "limits": {
            "max_pages": max_pages,
            "max_depth": max_depth,
            "timeout": timeout,
            "delay": delay,
        },
        "providers": results,
        "catalog_candidates": candidates,
        "summary": {
            "observed": sum(item["status"] == "observed" for item in results),
            "no_observation": sum(item["status"] != "observed" for item in results),
            "access_controlled": sum(
                item.get("metrics", {}).get("access_controlled_observations", 0) > 0
                for item in results
            ),
            "declared_routes": sum(len(item.get("declared_routes", [])) for item in results),
            "observed_routes": sum(len(item.get("observed_routes", [])) for item in results),
            "declared_filters": sum(len(item.get("declared_filters", [])) for item in results),
            "observed_filters": sum(len(item.get("observed_filters", [])) for item in results),
            "catalog_candidates_observed": sum(
                item.get("status") == "observed" for item in candidates
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="confirmar uso de endpoints públicos")
    parser.add_argument("--sources", nargs="*", help="limitar a source ids específicos")
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--max-depth", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--cache-dir")
    parser.add_argument("--include-catalog-candidates", action="store_true")
    parser.add_argument("--output", default="docs/provider-discovery/all-provider-sweep.json")
    args = parser.parse_args()
    if not args.live:
        parser.error(
            "a varredura de rede exige --live; use audit_provider_discovery_offline.py para modo local"
        )
    report = sweep(
        sources=set(args.sources) if args.sources else None,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        timeout=args.timeout,
        delay=args.delay,
        cache_dir=args.cache_dir,
        root=Path.cwd(),
        include_catalog_candidates=args.include_catalog_candidates,
    )
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    target.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
