"""Run a bounded local provider discovery and emit SDD drafts.

Examples:
    python tools/provider_discovery.py --url https://example.org/jurisprudencia --domain example.org --output .tmp/discovery
    python tools/provider_discovery.py --url https://example.org --domain example.org --browser --output .tmp/discovery
"""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import urlparse

from nanojuris.discovery.browser import BrowserDiscoveryClient
from nanojuris.discovery.crawler import DiscoveryCrawler
from nanojuris.discovery.draft import write_sdd_artifacts
from nanojuris.discovery.http import HttpDiscoveryClient
from nanojuris.discovery.models import DiscoveryPolicy


def main() -> int:
    parser = argparse.ArgumentParser(description="Descoberta bounded de provider público")
    parser.add_argument("--url", required=True, help="URL pública inicial")
    parser.add_argument("--domain", action="append", help="Domínio permitido; pode ser repetido")
    parser.add_argument("--output", required=True, help="Diretório de saída dos artefatos")
    parser.add_argument("--browser", action="store_true", help="Usar Playwright opcional")
    parser.add_argument(
        "--no-robots", action="store_true", help="Não consultar robots.txt; uso excepcional"
    )
    parser.add_argument("--max-bytes", type=int, default=5_000_000)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    parsed = urlparse(args.url)
    domains = tuple(args.domain or ([parsed.hostname] if parsed.hostname else []))
    policy = DiscoveryPolicy(
        allowed_domains=domains,
        max_bytes_per_response=args.max_bytes,
        max_total_bytes=max(args.max_bytes, args.max_bytes * 5),
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        timeout_seconds=args.timeout,
        respect_robots=not args.no_robots,
    )
    if args.browser:
        run = BrowserDiscoveryClient(policy).discover(args.url)
    else:
        run = DiscoveryCrawler(HttpDiscoveryClient(policy)).crawl(args.url)
    output = write_sdd_artifacts(run, Path(args.output))
    print(f"run_id={run.run_id}")
    print(f"output={output}")
    print(f"metrics={run.metrics()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
