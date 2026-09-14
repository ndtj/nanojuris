"""Build and validate NanoJuris' canonical institutional coverage projections."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = str(ROOT / "src")
if SRC in sys.path:
    sys.path.remove(SRC)
sys.path.insert(0, SRC)

from nanojuris import NanoJurisClient  # noqa: E402
from nanojuris.brazil import COURTS  # noqa: E402
from nanojuris.catalog import load_provider_catalog  # noqa: E402
from nanojuris.coverage_matrix import build_degree_matrix  # noqa: E402

CANONICAL = ROOT / "coverage"
AUTHORITY_SOURCE = CANONICAL / "authority-registry.yaml"
MATRIX_SOURCE = CANONICAL / "coverage-matrix.yaml"
AUTHORITY_SCHEMA = CANONICAL / "authority-registry.schema.json"
MATRIX_SCHEMA = CANONICAL / "coverage-matrix.schema.json"
JSON_OUTPUT = ROOT / "docs" / "coverage" / "coverage-matrix.json"
MARKDOWN_OUTPUT = ROOT / "docs" / "coverage" / "coverage-matrix.md"
QUEUE_OUTPUT = ROOT / "docs" / "coverage" / "development-queue.json"
README = ROOT / "README.md"
README_START = "<!-- coverage-summary:start -->"
README_END = "<!-- coverage-summary:end -->"

ALIASES = {"TJDF": "TJDFT", "TRE-SP": "TRESP"}
JUDICIAL_BRANCHES = {
    "constitutional",
    "superior",
    "federal",
    "state",
    "labor",
    "electoral",
    "military",
    "national_council",
}
FAMILY_LABELS = {
    "state": "Justiça estadual",
    "federal": "Justiça federal",
    "labor": "Justiça do trabalho",
    "electoral": "Justiça eleitoral",
    "military": "Justiça militar",
    "superior": "Tribunais superiores",
    "context": "Conselhos e contexto",
    "control": "Controle externo",
}


def _read(path: Path) -> dict[str, Any]:
    # JSON is a strict YAML subset. Keeping canonical YAML in this subset makes
    # builds deterministic and avoids adding a YAML parser to the runtime.
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def _canonical_authority(value: str) -> str:
    return ALIASES.get(value, value)


def _family(branch: str, role: str = "") -> str:
    if branch in {"state", "federal", "labor", "electoral", "military"}:
        return branch
    if branch in {"constitutional", "superior"}:
        return "superior"
    if branch in {"control", "accounts"}:
        return "control"
    if role in {"administrative_context"}:
        return "control"
    return "context"


def bootstrap_authorities() -> dict[str, Any]:
    authorities = []
    for court in COURTS:
        authorities.append(
            {
                "authority_id": court.code,
                "name": court.name,
                "kind": "court" if court.code != "CNJ" else "council",
                "family": _family(court.branch),
                "branch": court.branch,
                "jurisdiction": court.jurisdiction,
                "state": court.state,
                "region": court.region,
                "official_url": court.official_url,
                "aliases": ["TJDF"] if court.code == "TJDFT" else [],
                "primary_judicial_denominator": court.code != "CNJ",
            }
        )
    authorities.extend(
        [
            {
                "authority_id": "BNP",
                "name": "Banco Nacional de Precedentes",
                "kind": "aggregator",
                "family": "context",
                "branch": "national",
                "jurisdiction": "national",
                "state": None,
                "region": None,
                "official_url": None,
                "aliases": [],
                "primary_judicial_denominator": False,
            },
            {
                "authority_id": "EPROC-FEDERAL",
                "name": "Família eproc federal",
                "kind": "provider_family",
                "family": "federal",
                "branch": "federal",
                "jurisdiction": "national",
                "state": None,
                "region": None,
                "official_url": None,
                "aliases": [],
                "primary_judicial_denominator": False,
            },
            {
                "authority_id": "TRE",
                "name": "Família SJUR dos Tribunais Regionais Eleitorais",
                "kind": "provider_family",
                "family": "electoral",
                "branch": "electoral",
                "jurisdiction": "national",
                "state": None,
                "region": None,
                "official_url": None,
                "aliases": [],
                "primary_judicial_denominator": False,
            },
            {
                "authority_id": "TCE-PR",
                "name": "Tribunal de Contas do Estado do Paraná",
                "kind": "control_body",
                "family": "control",
                "branch": "control",
                "jurisdiction": "state",
                "state": "PR",
                "region": None,
                "official_url": None,
                "aliases": [],
                "primary_judicial_denominator": False,
            },
            {
                "authority_id": "TCE-SP",
                "name": "Tribunal de Contas do Estado de São Paulo",
                "kind": "control_body",
                "family": "control",
                "branch": "control",
                "jurisdiction": "state",
                "state": "SP",
                "region": None,
                "official_url": None,
                "aliases": [],
                "primary_judicial_denominator": False,
            },
            {
                "authority_id": "TCU",
                "name": "Tribunal de Contas da União",
                "kind": "control_body",
                "family": "control",
                "branch": "accounts",
                "jurisdiction": "national",
                "state": None,
                "region": None,
                "official_url": None,
                "aliases": [],
                "primary_judicial_denominator": False,
            },
        ]
    )
    return {"schema_version": "authority-registry-v1", "authorities": authorities}


def _provider_entry(source_id: str) -> dict[str, Any]:
    entries = load_provider_catalog()["entries"]
    return next((entry for entry in entries if entry["source_id"] == source_id), {})


def _cell_from_surface(surface: Any) -> dict[str, Any]:
    entry = _provider_entry(surface.provider) if surface.provider else {}
    identity = entry.get("surface_identity") or {}
    authority = _canonical_authority(surface.authority)
    role = entry.get("coverage_role") or "unmapped_gap"
    return {
        "surface_id": surface.surface_id,
        "authority_id": authority,
        "family": _family(surface.branch, role),
        "branch": surface.branch,
        "degree": surface.degree,
        "instance": identity.get("instance", surface.degree),
        "collection": surface.collection,
        "document_scope": identity.get("document_scope", "unknown"),
        "role": role,
        "required": surface.required,
        "scope": surface.scope,
        "provider": surface.provider,
        "states": {
            "implementation": "implemented" if surface.provider else "gap",
            "verification": surface.status,
            "promotion": _promotion(entry),
        },
        "document_types": list(surface.document_types),
        "contract_ref": f"provider:{surface.provider}" if surface.provider else None,
        "evidence_ids": list(surface.evidence_ids),
        "owner": entry.get("owner", "team:coverage"),
        "priority": entry.get("development_priority", "normal"),
        "blocking_reason": surface.notes if surface.status != "implemented" else None,
        "next_action": entry.get("next_action")
        or (surface.notes if not surface.provider else None),
    }


def _promotion(entry: dict[str, Any]) -> str:
    interfaces = entry.get("interfaces") or {}
    if interfaces.get("unified_search"):
        return "unified"
    if interfaces.get("opt_in_unified_search"):
        return "opt_in"
    return "excluded"


def bootstrap_matrix() -> dict[str, Any]:
    cells = [_cell_from_surface(surface) for surface in build_degree_matrix().surfaces]
    runtime = {item.source for item in NanoJurisClient().list_sources()}
    mapped = {cell["provider"] for cell in cells if cell["provider"]}
    for source_id in sorted(runtime - mapped):
        entry = _provider_entry(source_id)
        identity = entry.get("surface_identity") or {}
        authority = _canonical_authority(identity.get("authority") or "UNKNOWN")
        branch = identity.get("branch") or "unknown"
        role = entry.get("coverage_role") or "specialized_context"
        collection = identity.get("collection") or "UNKNOWN"
        degree = identity.get("degree") or "unknown"
        cells.append(
            {
                "surface_id": (
                    f"surface:{authority.lower()}:{collection.lower()}:{degree}:{source_id}"
                ),
                "authority_id": authority,
                "family": _family(branch, role),
                "branch": branch,
                "degree": degree,
                "instance": identity.get("instance", degree),
                "collection": collection,
                "document_scope": identity.get("document_scope", entry.get("category", "unknown")),
                "role": role,
                "required": False,
                "scope": "aggregator" if "context" in role else "tribunal",
                "provider": source_id,
                "states": {
                    "implementation": "implemented",
                    "verification": entry.get("live_status", "unverified"),
                    "promotion": _promotion(entry),
                },
                "document_types": (entry.get("document_contract") or {}).get("document_types", []),
                "contract_ref": f"provider:{source_id}",
                "evidence_ids": entry.get("evidence_ids", []),
                "owner": entry.get("owner", "team:provider-engineering"),
                "priority": entry.get("development_priority", "normal"),
                "blocking_reason": None,
                "next_action": entry.get("next_action"),
            }
        )
    return {"schema_version": "coverage-matrix-v1", "cells": cells}


def validate(authorities: dict[str, Any], matrix: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    authority_ids = {item["authority_id"] for item in authorities["authorities"]}
    aliases = {alias for item in authorities["authorities"] for alias in item.get("aliases", [])}
    runtime = {item.source for item in NanoJurisClient().list_sources()}
    providers = {cell["provider"] for cell in matrix["cells"] if cell.get("provider")}
    surface_ids = [cell["surface_id"] for cell in matrix["cells"]]
    if len(surface_ids) != len(set(surface_ids)):
        errors.append("surface_id duplicado")
    missing_authorities = sorted(
        {cell["authority_id"] for cell in matrix["cells"] if cell["scope"] != "judicial_unit_gap"}
        - authority_ids
        - aliases
    )
    if missing_authorities:
        errors.append(f"autoridades desconhecidas: {missing_authorities}")
    missing_providers = sorted(runtime - providers)
    if missing_providers:
        errors.append(f"providers runtime sem superficie: {missing_providers}")
    judicial = {
        item["authority_id"]
        for item in authorities["authorities"]
        if item["branch"] in JUDICIAL_BRANCHES and item["kind"] in {"court", "council"}
    }
    if len(judicial) != 94:
        errors.append(f"universo judicial esperado=94 observado={len(judicial)}")
    tre = {
        cell["authority_id"]
        for cell in matrix["cells"]
        if cell.get("provider") == "tre_sjur_jurisprudencia"
    }
    if len(tre) != 27:
        errors.append(f"familia TRE esperada=27 observada={len(tre)}")
    for cell in matrix["cells"]:
        if (
            cell["role"] != "primary_textual_jurisprudence"
            and cell.get("required")
            and cell["states"]["implementation"] == "implemented"
        ):
            # Context may be required as a surface, but never claims primary coverage.
            cell.setdefault("coverage_credit", "context_only")
    return errors


def materialize(authorities: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    entries = {entry["source_id"]: entry for entry in load_provider_catalog()["entries"]}
    cells = []
    for source in matrix["cells"]:
        cell = dict(source)
        provider = cell.get("provider")
        entry = entries.get(provider, {})
        cell["contracts"] = {
            "search": entry.get("search_contract", {}),
            "pagination": entry.get("pagination_contract", {}),
            "document": entry.get("document_contract", {}),
            "errors": entry.get("error_contract", {}),
            "interfaces": entry.get("interfaces", {}),
        }
        cells.append(cell)
    by_family: dict[str, Any] = {}
    for family in FAMILY_LABELS:
        subset = [cell for cell in cells if cell["family"] == family]
        providers = {cell["provider"] for cell in subset if cell.get("provider")}
        primary = {
            cell["provider"]
            for cell in subset
            if cell.get("provider") and cell["role"] == "primary_textual_jurisprudence"
        }
        verified = [cell for cell in subset if cell["states"]["verification"] == "implemented"]
        blocked = [
            cell
            for cell in subset
            if cell["states"]["verification"]
            in {"blocked_access", "blocked_transport", "source_unavailable"}
        ]
        gaps = [cell for cell in subset if cell["states"]["implementation"] == "gap"]
        full_text = {
            cell["provider"]
            for cell in subset
            if cell.get("provider")
            and (entries.get(cell["provider"], {}).get("document_contract") or {}).get(
                "supports_full_text"
            )
        }
        authorities_set = {cell["authority_id"] for cell in subset if cell["scope"] == "tribunal"}
        by_family[family] = {
            "label": FAMILY_LABELS[family],
            "authority_count": len(authorities_set),
            "surface_count": len(subset),
            "verified_count": len(verified),
            "blocked_count": len(blocked),
            "gap_count": len(gaps),
            "primary_provider_count": len(primary),
            "context_provider_count": len(providers - primary),
            "full_text_provider_count": len(full_text),
        }
    return {
        "schema_version": "coverage-matrix-materialized-v1",
        "authority_count": len(authorities["authorities"]),
        "judicial_authority_count": 94,
        "runtime_provider_count": len(NanoJurisClient().list_sources()),
        "summary": {
            "by_family": by_family,
            "states": Counter(cell["states"]["verification"] for cell in cells),
        },
        "authorities": authorities["authorities"],
        "cells": cells,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Matriz canônica de cobertura",
        "",
        "Esta página é gerada de `coverage/coverage-matrix.yaml`. Não edite manualmente.",
        "",
        _summary_table(payload),
        "",
        "## Superfícies",
        "",
        "| Autoridade | Família | Grau | Coleção | Provider | Papel | "
        "Implementação | Verificação | Promoção |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for cell in payload["cells"]:
        states = cell["states"]
        provider = f"`{cell['provider']}`" if cell.get("provider") else "—"
        lines.append(
            f"| `{cell['authority_id']}` | "
            f"{FAMILY_LABELS.get(cell['family'], cell['family'])} | "
            f"`{cell['degree']}` | `{cell['collection']}` | {provider} | "
            f"`{cell['role']}` | `{states['implementation']}` | "
            f"`{states['verification']}` | `{states['promotion']}` |"
        )
    return "\n".join(lines) + "\n"


def _summary_table(payload: dict[str, Any]) -> str:
    lines = [
        "| Família | Autoridades | Superfícies | Verificadas | Bloqueadas | "
        "Lacunas | Providers primários/contexto | Inteiro teor |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family in FAMILY_LABELS:
        row = payload["summary"]["by_family"][family]
        lines.append(
            f"| {row['label']} | {row['authority_count']} | {row['surface_count']} | "
            f"{row['verified_count']} | {row['blocked_count']} | {row['gap_count']} | "
            f"{row['primary_provider_count']}/{row['context_provider_count']} | "
            f"{row['full_text_provider_count']} |"
        )
    return "\n".join(lines)


def readme_block(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            README_START,
            "## Cobertura por família",
            "",
            _summary_table(payload),
            "",
            "[Abra a matriz completa](docs/coverage/coverage-matrix.md).",
            "",
            "> **Leitura correta:** provider não equivale a tribunal coberto; "
            "implementação não equivale a validação live; informativo, precedente "
            "ou catálogo não substitui jurisprudência textual geral.",
            README_END,
        ]
    )


def _replace_readme(text: str, block: str) -> str:
    if README_START in text and README_END in text:
        prefix, rest = text.split(README_START, 1)
        _, suffix = rest.split(README_END, 1)
        return prefix.rstrip() + "\n\n" + block + suffix
    anchor = "## Comece pelo seu objetivo"
    if anchor not in text:
        raise ValueError(f"README sem ancora: {anchor}")
    return text.replace(anchor, block + "\n\n" + anchor, 1)


def outputs() -> dict[Path, str]:
    authorities = _read(AUTHORITY_SOURCE)
    matrix = _read(MATRIX_SOURCE)
    errors = validate(authorities, matrix)
    if errors:
        raise ValueError("; ".join(errors))
    payload = materialize(authorities, matrix)
    queue = {
        "schema_version": "coverage-development-queue-v1",
        "items": [
            {
                "surface_id": cell["surface_id"],
                "owner": cell["owner"],
                "priority": cell["priority"],
                "blocking_reason": cell.get("blocking_reason"),
                "next_action": cell.get("next_action"),
            }
            for cell in payload["cells"]
            if cell["states"]["implementation"] == "gap"
            or cell["states"]["verification"] != "implemented"
        ],
    }
    return {
        JSON_OUTPUT: _dump(payload),
        MARKDOWN_OUTPUT: render_markdown(payload),
        QUEUE_OUTPUT: _dump(queue),
        README: _replace_readme(README.read_text(encoding="utf-8"), readme_block(payload)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--refresh-authorities", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.refresh_authorities:
        CANONICAL.mkdir(parents=True, exist_ok=True)
        AUTHORITY_SOURCE.write_text(_dump(bootstrap_authorities()), encoding="utf-8")
    if args.bootstrap:
        CANONICAL.mkdir(parents=True, exist_ok=True)
        if not AUTHORITY_SOURCE.exists():
            AUTHORITY_SOURCE.write_text(_dump(bootstrap_authorities()), encoding="utf-8")
        if not MATRIX_SOURCE.exists():
            MATRIX_SOURCE.write_text(_dump(bootstrap_matrix()), encoding="utf-8")
    rendered = outputs()
    stale = [
        str(path.relative_to(ROOT))
        for path, content in rendered.items()
        if not path.exists() or path.read_text(encoding="utf-8") != content
    ]
    if args.check:
        if stale:
            print("stale canonical coverage outputs: " + ", ".join(stale))
            return 1
        print("canonical coverage is synchronized")
        return 0
    if args.write or args.bootstrap or args.refresh_authorities:
        for path, content in rendered.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(f"wrote {len(rendered)} projections")
        return 0
    print(_dump(materialize(_read(AUTHORITY_SOURCE), _read(MATRIX_SOURCE))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
