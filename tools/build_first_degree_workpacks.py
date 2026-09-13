"""Build offline CJPG workpacks from the bounded first-degree route inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs" / "provider-discovery" / "first-degree-route-inventory-20260907.json"
DEFAULT_OUTPUT = ROOT / "docs" / "coverage" / "first-degree-workpacks-20260907.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "coverage" / "first-degree-workpacks-20260907.md"


def _same_official_host(route: str, homepage: str) -> bool:
    route_host = (urlparse(route).hostname or "").casefold().rstrip(".")
    homepage_host = (urlparse(homepage).hostname or "").casefold().rstrip(".")
    return bool(
        route_host
        and homepage_host
        and (route_host == homepage_host or route_host.endswith(f".{homepage_host}"))
    )


def _priority(route: dict[str, Any], homepage: dict[str, Any]) -> tuple[int, str]:
    scope = str(route.get("scope"))
    if scope == "jurisprudence_candidate" and _same_official_host(
        str(route.get("url", "")), str(homepage.get("final_url") or homepage.get("url", ""))
    ):
        return (0, "official_jurisprudence_candidate")
    if scope == "jurisprudence_candidate":
        return (1, "external_jurisprudence_reference")
    if scope == "process_surface":
        return (3, "process_surface_excluded")
    return (2, "contextual_or_unknown")


def build(*, input_path: Path = DEFAULT_INPUT) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    workpacks: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        homepage = item.get("homepage") or {}
        routes: list[dict[str, Any]] = []
        for route in item.get("candidate_routes", []):
            priority, reason = _priority(route, homepage)
            routes.append(
                {
                    "url": route.get("url"),
                    "kind": route.get("kind"),
                    "scope": route.get("scope"),
                    "markers": route.get("markers", []),
                    "priority": priority,
                    "priority_reason": reason,
                }
            )
        routes.sort(key=lambda row: (row["priority"], str(row.get("url"))))
        official = [row for row in routes if row["priority"] == 0]
        homepage_classification = str(homepage.get("classification") or "unknown")
        if homepage_classification == "access_controlled":
            status = "blocked_recheck"
        elif homepage_classification != "reachable":
            status = "adapter_discovery"
        elif official:
            status = "route_candidate"
        else:
            status = "research_ready"
        workpacks.append(
            {
                "authority": item.get("authority"),
                "branch": item.get("branch"),
                "state": item.get("state"),
                "official_url": item.get("official_url"),
                "homepage_status": homepage_classification,
                "lifecycle": status,
                "candidate_route_count": len(routes),
                "official_jurisprudence_route_count": len(official),
                "routes": routes,
                "gates": {
                    "source_official": bool(official),
                    "degree_contract": False,
                    "adapter": False,
                    "fixtures": False,
                    "live": False,
                    "quality": False,
                    "federation": False,
                },
                "promotion_decision": "discovery_only",
                "evidence_ids": [
                    str(input_path.relative_to(ROOT)).replace("\\", "/"),
                    f"first-degree-route-inventory:{item.get('authority')}",
                ],
            }
        )
    workpacks.sort(key=lambda row: str(row.get("authority")))
    return {
        "schema_version": "first-degree-workpacks-v1",
        "generated_at": payload.get("observed_at"),
        "source_inventory": str(input_path.relative_to(ROOT)).replace("\\", "/"),
        "network_access": "not_used",
        "summary": {
            "authorities": len(workpacks),
            "route_candidates": sum(row["candidate_route_count"] for row in workpacks),
            "official_jurisprudence_candidates": sum(
                row["official_jurisprudence_route_count"] for row in workpacks
            ),
            "by_lifecycle": {
                status: sum(row["lifecycle"] == status for row in workpacks)
                for status in sorted({row["lifecycle"] for row in workpacks})
            },
        },
        "workpacks": workpacks,
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# First-degree CJPG workpacks",
        "",
        "Generated offline from the bounded official-route inventory. "
        "Candidate routes are not contracts.",
        "",
        f"Authorities: **{payload['summary']['authorities']}**; official jurisprudence candidates: "
        f"**{payload['summary']['official_jurisprudence_candidates']}**.",
        "",
        "| Authority | Homepage | Lifecycle | Official candidates | Total routes |",
        "|---|---|---|---:|---:|",
    ]
    for row in payload["workpacks"]:
        lines.append(
            f"| `{row['authority']}` | `{row['homepage_status']}` | `{row['lifecycle']}` | "
            f"{row['official_jurisprudence_route_count']} | {row['candidate_route_count']} |"
        )
    lines.extend(
        [
            "",
            "Every workpack remains `discovery_only`; degree, fixtures, live, quality, and "
            "federation gates are false.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    payload = build(input_path=args.input)
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        args.markdown_output.write_text(render(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
