"""Build a static semantic diff between Juscraper and NanoJuris.

The upstream checkout is inspected with :mod:`ast` only.  This tool never
imports or executes Juscraper, performs network calls, copies source files, or
promotes a provider.  It records what can be observed statically and labels
the remaining dimensions as requiring an independent contract/fixture.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

# Keep direct tool execution pinned to this source checkout.  Without this,
# an older globally installed wheel can silently change the local capability
# map and produce a false Juscraper parity result.
_NANOJURIS_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
_nanojuris_source = str(_NANOJURIS_SOURCE_ROOT)
if _nanojuris_source in sys.path:
    sys.path.remove(_nanojuris_source)
sys.path.insert(0, _nanojuris_source)

SURFACE_METHODS: dict[str, tuple[str, ...]] = {
    "cjsg": ("cjsg", "cjsg_download", "cjsg_parse"),
    "cjpg": ("cjpg", "cjpg_download", "cjpg_parse"),
    "detail": ("cjsg_ementa",),
    "cpopg": ("cpopg",),
    "cposg": ("cposg",),
}
IDENTITY_RE = re.compile(r"(?:^|_)(?:id|uuid|registro|processo|numero|cnj)(?:$|_)", re.I)
ROUTE_NAME_RE = re.compile(r"(?:url|path|endpoint|action|route)", re.I)
ERROR_NAME_RE = re.compile(r"(?:error|exception|captcha|challenge|rate|timeout|http)", re.I)

# The intake artifact intentionally stores the upstream inventory and the
# collection decisions separately.  Keep the equivalence map explicit so a
# newer intake shape can still produce the same 29-package/87-surface matrix
# without guessing from module names.
SURFACE_EQUIVALENTS: dict[str, dict[str, str | None]] = {
    "cjsg": {
        "tjac": "tjac_cjsg",
        "tjal": "tjal_cjsg",
        "tjam": "tjam_cjsg",
        "tjap": "tjap_tucujuris",
        "tjba": "tjba_graphql",
        "tjce": "tjce_cjsg",
        "tjdft": "tjdf_juris",
        "tjes": "tjes_jurisprudencia",
        "tjgo": "tjgo_projudi_jurisprudencia",
        "tjmg": "tjmg_jurisprudencia",
        "tjms": "tjms_cjsg",
        "tjmt": "tjmt_jurisprudencia_api",
        "tjpa": "tjpa_jurisprudencia_bff",
        "tjpb": "tjpb_pje_jurisprudencia",
        "tjpe": "tjpe_jurisprudencia",
        "tjpi": "tjpi_juspi",
        "tjpr": "tjpr_jurisprudencia",
        # Juscraper/courts/tjrj targets the public EJURIS ASP.NET/XHR
        # surface; keep the independent eproc adapter out of this mapping.
        "tjrj": "tjrj_ejuris",
        "tjrn": "tjrn_jurisprudencia",
        "tjro": "tjro_jurisprudencia",
        "tjrr": "tjrr_juris",
        "tjrs": "tjrs_solr",
        "tjsc": "tjsc_eproc_jurisprudencia",
        "tjsp": "tjsp_cjsg",
        "tjto": "tjto_jurisprudencia",
        "trf1": "cjf_jurisprudencia",
        "trf3": "trf3_jurisprudencia",
        "trf5": "trf5_jurisprudencia",
        "trf6": "trf6_eproc_jurisprudencia",
    },
    # TJTO exposes both CJSG and CJPG through the same official search
    # surface. Keep the equivalence explicit even when an older inventory
    # omits the per-surface override; otherwise regeneration could regress
    # a proven first-degree binding to ``no_runtime_equivalent``.
    "cjpg": {
        "tjes": "tjes_cjpg",
        "tjsp": "tjsp_cjpg",
        "tjto": "tjto_jurisprudencia",
    },
    "detail": {"tjto": "tjto_jurisprudencia"},
}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _literal_strings(node: ast.AST) -> list[str]:
    return [
        item.value
        for item in ast.walk(node)
        if isinstance(item, ast.Constant) and isinstance(item.value, str)
    ]


def _callable_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    return {arg.arg for arg in arguments if arg.arg not in {"self", "cls"}}


def _schema_fields(tree: ast.Module) -> set[str]:
    fields: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {base.id for base in node.bases if isinstance(base, ast.Name)}
        schema_like = bool(bases & {"BaseModel", "BaseSchema"}) or node.name.endswith(
            ("Input", "Output", "Schema")
        )
        if not schema_like:
            continue
        for child in node.body:
            if isinstance(child, (ast.AnnAssign, ast.Assign)):
                targets = [child.target] if isinstance(child, ast.AnnAssign) else child.targets
                for target in targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        fields.add(target.id)
    return fields


def _package_snapshot(package: Path) -> dict[str, Any]:
    files = sorted(package.rglob("*.py"))
    methods: dict[str, set[str]] = {surface: set() for surface in SURFACE_METHODS}
    arguments: dict[str, set[str]] = {surface: set() for surface in SURFACE_METHODS}
    source_files: dict[str, set[str]] = {surface: set() for surface in SURFACE_METHODS}
    fields: set[str] = set()
    identity_signals: set[str] = set()
    error_symbols: set[str] = set()
    routes: set[str] = set()

    for path in files:
        try:
            tree = ast.parse(_read(path), filename=str(path))
        except SyntaxError:
            continue
        fields.update(_schema_fields(tree))
        relative = path.relative_to(package).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for surface, names in SURFACE_METHODS.items():
                    if node.name in names:
                        methods[surface].add(node.name)
                        arguments[surface].update(_callable_args(node))
                        source_files[surface].add(relative)
            elif isinstance(node, ast.Name):
                if IDENTITY_RE.search(node.id):
                    identity_signals.add(node.id)
                if ERROR_NAME_RE.search(node.id):
                    error_symbols.add(node.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and ROUTE_NAME_RE.search(target.id):
                        routes.update(_literal_strings(node.value))

        text = _read(path)
        for match in re.finditer(
            r"(?i)(?:https?://[^'\"\s]+|/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]*)", text
        ):
            value = match.group(0).rstrip(")],")
            if len(value) <= 240:
                routes.add(value)

    return {
        "source_files": {key: sorted(value) for key, value in source_files.items()},
        "methods": {key: sorted(value) for key, value in methods.items()},
        "input_arguments": {key: sorted(value) for key, value in arguments.items()},
        "schema_fields": sorted(fields),
        "identity_signals": sorted(identity_signals),
        "error_symbols": sorted(error_symbols),
        "route_literals": sorted(routes),
    }


def _surface_local_status(
    surface: str, source_id: str, equivalent: str | None, *, blocked: bool = False
) -> str:
    if surface in {"cpopg", "cposg"}:
        return "out_of_scope"
    if not equivalent:
        return "no_runtime_equivalent"
    if blocked:
        return "runtime_overlap_blocked"
    if surface == "cjpg":
        return "covered_requires_differential_fixture"
    if surface == "detail":
        return "detail_contract_unverified"
    return "covered_requires_differential_fixture"


def _load_capabilities() -> dict[str, dict[str, Any]]:
    """Load local declarations without constructing or calling upstream code."""

    try:
        from nanojuris.client import NanoJurisClient

        return {
            name: capability.to_dict()
            for name, capability in (
                (item.source, item)
                for item in NanoJurisClient(include_candidate_providers=True).list_sources()
            )
        }
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        return {"__load_error__": {"error": type(exc).__name__}}


def _local_contract(
    surface: str, equivalent: str | None, capabilities: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    if not equivalent or equivalent not in capabilities:
        return {
            "provider": equivalent,
            "declared": False,
            "supported_filters": [],
            "extracted_fields": [],
            "pagination_mode": None,
            "access_statuses": [],
            "identity": "not_declared",
        }
    capability = capabilities[equivalent]
    return {
        "provider": equivalent,
        "declared": True,
        "supported_filters": sorted(capability.get("supported_filters", [])),
        "filter_semantics": dict(sorted(capability.get("filter_semantics", {}).items())),
        "extracted_fields": sorted(capability.get("extracted_fields", [])),
        "pagination_mode": capability.get("pagination_mode"),
        "ordering_modes": sorted(capability.get("ordering_modes", [])),
        "detail_modes": sorted(capability.get("detail_modes", [])),
        "access_statuses": sorted(capability.get("access_statuses", [])),
        "identity": "source-scoped native identifier; fixture required",
        "surface": surface,
    }


def _inventory_records(inventory_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize both v1 ``records`` and v2 intake artifacts."""

    records = inventory_data.get("records")
    if isinstance(records, list):
        return records
    scope = inventory_data.get("observed_scope", {})
    court_packages = scope.get("court_packages", [])
    source_ids = [
        str(item.get("source_id"))
        for item in court_packages
        if isinstance(item, dict) and item.get("source_id")
    ]
    source_ids.extend(str(item) for item in scope.get("trf_source_ids", []) if item)
    rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        if source_id.startswith("trf"):
            surfaces = ["cpopg", "cposg"]
        else:
            surfaces = ["cjsg", "cpopg", "cposg"]
            if source_id in {"tjes", "tjsp", "tjto"}:
                surfaces.append("cjpg")
            if source_id == "tjto":
                surfaces.append("detail")
        rows.append(
            {
                "source_id": source_id,
                "upstream_package": f"juscraper.courts.{source_id}",
                "surfaces": surfaces,
                "classification": "candidate",
            }
        )
    return rows


def _equivalent(source_id: str, surface: str, declared: str | None = None) -> str | None:
    if declared is not None:
        return declared
    return SURFACE_EQUIVALENTS.get(surface, {}).get(source_id)


def _dimensions(snapshot: dict[str, Any], local: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "fields": {
            "upstream_schema_fields": snapshot["schema_fields"],
            "nanojuris_extracted_fields": local["extracted_fields"],
            "status": "requires_field_mapping" if status.startswith("covered") else status,
        },
        "filters": {
            "upstream_input_arguments": snapshot["input_arguments"],
            "nanojuris_supported_filters": local["supported_filters"],
            "nanojuris_filter_semantics": local.get("filter_semantics", {}),
            "status": "requires_name_and_behavior_mapping"
            if status.startswith("covered")
            else status,
        },
        "pagination": {
            "upstream_signals": snapshot["input_arguments"],
            "nanojuris_mode": local["pagination_mode"],
            "status": "requires_replay" if status.startswith("covered") else status,
        },
        "errors": {
            "upstream_symbols": snapshot["error_symbols"],
            "nanojuris_access_statuses": local["access_statuses"],
            "status": "static_only_requires_negative_fixture",
        },
        "identity": {
            "upstream_signals": snapshot["identity_signals"],
            "nanojuris_contract": local["identity"],
            "status": "requires_native_id_fixture",
        },
    }


def build_record(source: Path, inventory: Path, generated_at: str) -> dict[str, Any]:
    source = source.resolve()
    upstream_root = source / "src" / "juscraper" / "courts"
    inventory_data = json.loads(inventory.read_text(encoding="utf-8"))
    capabilities = _load_capabilities()
    records: list[dict[str, Any]] = []
    inventory_records = _inventory_records(inventory_data)
    for item in inventory_records:
        source_id = str(item["source_id"])
        package = upstream_root / source_id
        snapshot = (
            _package_snapshot(package)
            if package.is_dir()
            else {
                "source_files": {},
                "methods": {},
                "input_arguments": {},
                "schema_fields": [],
                "identity_signals": [],
                "error_symbols": [],
                "route_literals": [],
            }
        )
        for surface in item["surfaces"]:
            equivalent = _equivalent(source_id, surface, item.get("nanojuris_equivalent"))
            status = _surface_local_status(
                surface,
                source_id,
                equivalent,
                blocked=equivalent in set(item.get("blocked_runtime_equivalents") or []),
            )
            local = _local_contract(
                surface,
                equivalent if status != "out_of_scope" else None,
                capabilities,
            )
            records.append(
                {
                    "source_id": source_id,
                    "upstream_package": item["upstream_package"],
                    "surface": surface,
                    "classification": item["classification"],
                    "nanojuris_equivalent": equivalent,
                    "status": status,
                    "evidence": {
                        "mode": "static_ast_and_local_capability",
                        "upstream_commit": inventory_data["upstream"].get("commit"),
                        "source_files": snapshot["source_files"].get(surface, []),
                        "methods": snapshot["methods"].get(surface, []),
                        "route_literals": snapshot["route_literals"],
                    },
                    "upstream": snapshot,
                    "nanojuris": local,
                    "dimensions": _dimensions(snapshot, local, status),
                    "promotion": (
                        "defer_until_independent_contract_fixture_live_replay_and_reuse_review"
                    ),
                }
            )
    counts: dict[str, int] = {}
    for row in records:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "audit_mode": "static_semantic_diff_no_network",
        "upstream": inventory_data["upstream"],
        "source_repository": "https://github.com/jtrecenti/juscraper",
        "records": records,
        "summary": {
            "source_packages": len(inventory_records),
            "surface_records": len(records),
            "by_status": dict(sorted(counts.items())),
            "no_runtime_promotion": True,
        },
        "limitations": [
            "AST extraction does not prove the HTTP payload or live availability.",
            "Field and filter names are not equivalent until a source-specific replay "
            "maps behavior.",
            "Process surfaces remain out of scope for NanoJuris and are not adapters.",
            "No upstream code, fixture, cookie, credential or response body is copied.",
        ],
    }


def markdown(record: dict[str, Any]) -> str:
    summary = record["summary"]
    lines = [
        "# Juscraper x NanoJuris - semantic diff (2026-09-01)",
        "",
        "Auditoria estatica por AST do checkout fixado. Nao executa Juscraper,",
        "nao chama a rede e nao promove adapters.",
        "",
        f"- Commit upstream: `{record['upstream'].get('commit')}`",
        f"- Pacotes: **{summary['source_packages']}**; "
        f"registros de superficie: **{summary['surface_records']}**",
        f"- Estados: `{json.dumps(summary['by_status'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "| Tribunal | Superficie | Equivalente | Estado | Evidencia estatica |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in record["records"]:
        equivalent = f"`{row['nanojuris_equivalent']}`" if row["nanojuris_equivalent"] else "-"
        files = ", ".join(f"`{value}`" for value in row["evidence"]["source_files"]) or "-"
        lines.append(
            f"| `{row['source_id']}` | `{row['surface']}` | {equivalent} | "
            f"`{row['status']}` | {files} |"
        )
    lines.extend(
        ["", "## Regra de leitura", "", *[f"- {item}" for item in record["limitations"]], ""]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--generated-at", default="2026-09-01T00:00:00+00:00")
    args = parser.parse_args()
    record = build_record(args.source, args.inventory, args.generated_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown(record), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
