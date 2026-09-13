"""Build a reproducible court-by-court Juscraper/NanoJuris inventory.

The tool reads a checked-out Juscraper tree and the local NanoJuris runtime
only. It does not import or execute Juscraper code and never makes network
calls. The output is an inventory for SDD prioritization, not an adapter
promotion mechanism.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# This repository uses a ``src`` layout.  Prefer the checkout being audited
# over a globally installed NanoJuris wheel so inventory output is reproducible
# when the tool is invoked directly (without PYTHONPATH or an editable install).
_NANOJURIS_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
_nanojuris_source = str(_NANOJURIS_SOURCE_ROOT)
if _nanojuris_source in sys.path:
    sys.path.remove(_nanojuris_source)
sys.path.insert(0, _nanojuris_source)

UPSTREAM_URL = "https://github.com/jtrecenti/juscraper"
COURT_RE = re.compile(r"^tj[a-z0-9]+$")
TRF_RE = re.compile(r"^trf\d+$")

# A mapping is deliberately explicit: similar names do not prove contract
# equivalence. ``None`` means that no NanoJuris runtime provider currently
# overlaps the Juscraper jurisprudence surface.  Degree-specific overrides are
# kept separately because one court package can expose both CJPG and CJSG.
NANOJURIS_EQUIVALENTS: dict[str, str | None] = {
    "tjac": "tjac_cjsg",
    "tjal": "tjal_cjsg",
    "tjam": "tjam_cjsg",
    # NanoJuris has an independent diagnostic adapter for the same CJSG
    # surface.  It remains blocked at runtime by Turnstile, but mapping it
    # here prevents the parity inventory from falsely reporting no runtime
    # equivalent.
    "tjap": "tjap_tucujuris",
    "tjba": "tjba_graphql",
    "tjce": "tjce_cjsg",
    "tjdft": "tjdf_juris",
    "tjes": "tjes_jurisprudencia",
    "tjgo": "tjgo_projudi_jurisprudencia",
    # The independent adapter preserves TJMG's public form contract while
    # stopping at the numeric CAPTCHA boundary.
    "tjmg": "tjmg_jurisprudencia",
    "tjms": "tjms_cjsg",
    "tjmt": "tjmt_jurisprudencia_api",
    "tjpa": "tjpa_jurisprudencia_bff",
    "tjpb": "tjpb_pje_jurisprudencia",
    "tjpe": "tjpe_jurisprudencia",
    "tjpi": "tjpi_juspi",
    "tjpr": "tjpr_jurisprudencia",
    # Juscraper's TJRJ package is the public EJURIS ASP.NET/XHR surface.
    # The eproc adapter is a separate diagnostic source and is not the
    # upstream equivalent for this package.
    "tjrj": "tjrj_ejuris",
    "tjrn": "tjrn_jurisprudencia",
    "tjro": "tjro_jurisprudencia",
    "tjrr": "tjrr_juris",
    "tjrs": "tjrs_solr",
    "tjsc": "tjsc_eproc_jurisprudencia",
    "tjsp": "tjsp_cjsg",
    "tjto": "tjto_jurisprudencia",
    "trf1": None,
    "trf3": None,
    "trf5": "trf5_jurisprudencia",
    "trf6": "trf6_eproc_jurisprudencia",
}

SURFACE_EQUIVALENT_OVERRIDES: dict[tuple[str, str], str | None] = {
    ("tjes", "cjpg"): "tjes_cjpg",
    ("tjes", "cjsg"): "tjes_jurisprudencia",
    ("tjsp", "cjpg"): "tjsp_cjpg",
    ("tjsp", "cjsg"): "tjsp_cjsg",
}

PARTIAL_OVERLAP = {"tjrj", "tjsc", "trf5", "trf6"}
PROCESS_SURFACES = frozenset({"cpopg", "cposg"})


def _git_commit(source: Path) -> str | None:
    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _client_class(path: Path) -> str | None:
    client = path / "client.py"
    if not client.is_file():
        return None
    match = re.search(r"^class\s+(\w+Scraper)\b", client.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def _runtime_provider_names() -> list[str]:
    # Importing NanoJuris is local-only: provider constructors do not perform
    # requests. Include opt-in diagnostic adapters as registered runtime
    # equivalents; their access state still controls promotion/federation.
    from nanojuris.client import NanoJurisClient

    return sorted(NanoJurisClient(include_candidate_providers=True).providers)


def _federated_runtime_provider_names() -> list[str]:
    """Return only providers in the normal (non-diagnostic) runtime.

    Candidate adapters and the 27 explicit TRE diagnostic instances are useful
    for source discovery, but they must not inflate the runtime count used to
    describe the normal catalog/federation.  Keep both populations in the
    inventory so parity classification can still see blocked equivalents.
    """

    from nanojuris.client import NanoJurisClient

    return sorted(NanoJurisClient().providers)


def _provider_live_statuses() -> dict[str, str]:
    """Return generated live states without making a network request."""

    from nanojuris.catalog import load_provider_catalog

    return {
        str(entry["source_id"]): str(entry.get("live_status") or "not_observed")
        for entry in load_provider_catalog().get("entries", [])
        if isinstance(entry, dict) and entry.get("source_id")
    }


def _nanojuris_court_codes() -> list[str]:
    """Return the local judiciary catalog used for the crosswalk."""

    from nanojuris.brazil import COURTS

    return sorted(court.code.lower() for court in COURTS)


def _surfaces(source_id: str, *, trf: bool) -> list[str]:
    if trf:
        return ["cpopg", "cposg"]
    values = ["cjsg"]
    if source_id in {"tjes", "tjsp", "tjto"}:
        values.append("cjpg")
    if source_id == "tjto":
        values.append("detail")
    values.extend(["cpopg", "cposg"])
    return values


def _surface_equivalents(source_id: str, surfaces: list[str]) -> dict[str, str | None]:
    equivalent = NANOJURIS_EQUIVALENTS[source_id]
    return {
        surface: (
            None
            if surface in PROCESS_SURFACES
            else SURFACE_EQUIVALENT_OVERRIDES.get((source_id, surface), equivalent)
        )
        for surface in surfaces
    }


def _record(
    source_id: str,
    *,
    trf: bool,
    runtime: set[str],
    live_statuses: dict[str, str],
) -> dict[str, Any]:
    equivalent = NANOJURIS_EQUIVALENTS[source_id]
    surfaces = _surfaces(source_id, trf=trf)
    surface_equivalents = _surface_equivalents(source_id, surfaces)
    jurisprudence_equivalents = {
        provider
        for surface, provider in surface_equivalents.items()
        if surface not in PROCESS_SURFACES and provider
    }
    unmatched_jurisprudence = [
        surface
        for surface, provider in surface_equivalents.items()
        if surface not in PROCESS_SURFACES and provider is None
    ]
    missing_runtime = sorted(jurisprudence_equivalents - runtime)
    blocked_runtime = sorted(
        provider
        for provider in jurisprudence_equivalents & runtime
        if live_statuses.get(provider)
        in {
            "access_controlled",
            "blocked_access",
            "blocked_transport",
            "source_unavailable",
            "transport_blocked",
            "unavailable",
        }
    )
    unvalidated_runtime = sorted(
        provider
        for provider in jurisprudence_equivalents & runtime
        if provider not in blocked_runtime
        and live_statuses.get(provider) not in {"implemented", "valid"}
    )
    if trf:
        classification = "out_of_scope_process_surface"
        priority = "out_of_scope"
    elif unmatched_jurisprudence or missing_runtime:
        classification = "candidate_no_runtime_equivalent"
        priority = "P0_gap"
    elif blocked_runtime:
        classification = "runtime_overlap_blocked"
        priority = "P0_access_or_transport"
    elif unvalidated_runtime:
        classification = "runtime_overlap_unvalidated"
        priority = "P1_live_validation"
    elif source_id in PARTIAL_OVERLAP:
        classification = "partial_overlap_review"
        priority = "P2_compare_contracts"
    else:
        classification = "covered_by_existing_runtime"
        priority = "maintenance"
    return {
        "source_id": source_id,
        "upstream_package": f"courts/{source_id}",
        "upstream_client_class": _client_class(
            _SOURCE_ROOT / "src" / "juscraper" / "courts" / source_id
        ),
        "surfaces": surfaces,
        "nanojuris_equivalent": equivalent,
        "nanojuris_equivalents": sorted(jurisprudence_equivalents),
        "surface_equivalents": surface_equivalents,
        "equivalent_registered": bool(jurisprudence_equivalents)
        and not missing_runtime
        and not unmatched_jurisprudence,
        "equivalent_live_statuses": {
            provider: live_statuses.get(provider, "not_observed")
            for provider in sorted(jurisprudence_equivalents)
        },
        "missing_runtime_equivalents": missing_runtime,
        "unmatched_jurisprudence_surfaces": unmatched_jurisprudence,
        "blocked_runtime_equivalents": blocked_runtime,
        "unvalidated_runtime_equivalents": unvalidated_runtime,
        "classification": classification,
        "priority": priority,
        "notes": (
            "Juscraper TRF surface is process consultation; keep in NanoJud."
            if trf
            else "Compare source contract and identity before changing the runtime."
        ),
    }


_SOURCE_ROOT = Path(".")


def build_record(source: Path, generated_at: str) -> dict[str, Any]:
    global _SOURCE_ROOT
    _SOURCE_ROOT = source.resolve()
    courts_root = _SOURCE_ROOT / "src" / "juscraper" / "courts"
    court_ids = sorted(
        path.name for path in courts_root.iterdir() if path.is_dir() and COURT_RE.match(path.name)
    )
    trf_ids = sorted(
        path.name for path in courts_root.iterdir() if path.is_dir() and TRF_RE.match(path.name)
    )
    expected = set(court_ids) | set(trf_ids)
    missing_mapping = sorted(expected - set(NANOJURIS_EQUIVALENTS))
    if missing_mapping:
        raise ValueError(f"court mapping missing: {', '.join(missing_mapping)}")
    runtime = set(_runtime_provider_names())
    federated_runtime = set(_federated_runtime_provider_names())
    live_statuses = _provider_live_statuses()
    nanojuris_courts = _nanojuris_court_codes()
    juscraper_court_set = set(court_ids) | set(trf_ids)
    records = [
        _record(item, trf=False, runtime=runtime, live_statuses=live_statuses) for item in court_ids
    ]
    records.extend(
        _record(item, trf=True, runtime=runtime, live_statuses=live_statuses) for item in trf_ids
    )
    return {
        "schema_version": 2,
        "generated_at": generated_at,
        "audit_mode": "static_inventory_no_network",
        "upstream": {
            "repository": UPSTREAM_URL,
            "commit": _git_commit(_SOURCE_ROOT),
            "court_packages": len(court_ids),
            "trf_packages": len(trf_ids),
        },
        "nanojuris": {
            "court_catalog_source": "nanojuris.brazil.COURTS",
            "court_catalog_exhaustiveness": "cnj_register_snapshot_with_local_metadata",
            "runtime_provider_count": len(runtime),
            "runtime_providers": sorted(runtime),
            "federated_runtime_provider_count": len(federated_runtime),
            "federated_runtime_providers": sorted(federated_runtime),
            "diagnostic_runtime_provider_count": len(runtime - federated_runtime),
            "diagnostic_runtime_providers": sorted(runtime - federated_runtime),
            "court_catalog_count": len(nanojuris_courts),
            "court_catalog_codes": nanojuris_courts,
            "juscraper_overlap_count": len(juscraper_court_set & set(nanojuris_courts)),
            "courts_not_in_juscraper": sorted(set(nanojuris_courts) - juscraper_court_set),
        },
        "records": records,
        "summary": {
            "total_court_packages": len(court_ids) + len(trf_ids),
            "state_court_packages": len(court_ids),
            "trf_packages": len(trf_ids),
            "covered": sum(
                item["classification"] == "covered_by_existing_runtime" for item in records
            ),
            "partial_overlap": sum(
                item["classification"] == "partial_overlap_review" for item in records
            ),
            "live_valid_candidates": sum(
                item["classification"] == "candidate_live_valid_data" for item in records
            ),
            "runtime_overlap_blocked": sum(
                item["classification"] == "runtime_overlap_blocked" for item in records
            ),
            "runtime_overlap_unvalidated": sum(
                item["classification"] == "runtime_overlap_unvalidated" for item in records
            ),
            "other_candidates": sum(
                item["classification"] == "candidate_no_runtime_equivalent" for item in records
            ),
            "out_of_scope_process": sum(
                item["classification"] == "out_of_scope_process_surface" for item in records
            ),
        },
        "promotion_rule": (
            "Inventory never promotes a provider. Each candidate requires an independent "
            "NanoJuris contract, sanitized fixtures, canonical identity, negative tests, "
            "bounded live evidence and reuse review."
        ),
        "scope_note": (
            "Juscraper inventory covers only its checked-out court packages. The NanoJuris "
            "court catalog is broader; courts_not_in_juscraper are explicit coverage gaps, "
            "not evidence that their official sources are unavailable."
        ),
        "evidence_artifacts": [
            "docs/topology/cnj-tribunal-register-20260901.json",
            "docs/topology/court-catalog-url-probe-20260901.json",
        ],
        "catalog_limitations": [
            "The CNJ tribunal directory is a dated web snapshot and must be refreshed "
            "per coverage epoch.",
            "The catalog models tribunal authorities, not every judicial unit, section, "
            "or first-instance court.",
            "Councils and administrative bodies outside the tribunal directory require "
            "separate authority modeling.",
        ],
    }


def _markdown(record: dict[str, Any]) -> str:
    summary = record["summary"]
    lines = [
        "# Inventário Juscraper × NanoJuris — 2026-09-01",
        "",
        "Inventário estático reproduzível do checkout correto `jtrecenti/juscraper`.",
        "Nenhum código upstream é executado, copiado ou promovido; a matriz serve",
        "para priorização SDD.",
        "",
        f"- Commit upstream: `{record['upstream']['commit']}`",
        f"- Pacotes estaduais: **{summary['state_court_packages']}**",
        f"- Pacotes TRF: **{summary['trf_packages']}**",
        "- Bindings runtime no cruzamento (inclui diagnósticos): "
        f"**{record['nanojuris']['runtime_provider_count']}**",
        "- Providers runtime federáveis no cruzamento: "
        f"**{record['nanojuris']['federated_runtime_provider_count']}**",
        "- Bindings diagnósticos opt-in (inclui 27 TRE): "
        f"**{record['nanojuris']['diagnostic_runtime_provider_count']}**",
        f"- Tribunais no catálogo NanoJuris: **{record['nanojuris']['court_catalog_count']}**",
        "- Sobreposição de códigos com Juscraper: "
        f"**{record['nanojuris']['juscraper_overlap_count']}**",
        "- Evidências institucionais/live: `cnj-tribunal-register-20260901.json`, "
        "`court-catalog-url-probe-20260901.json`",
        "",
        "| Pacote | Superfícies Juscraper | Equivalentes NanoJuris | Classificação | Prioridade |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in record["records"]:
        surfaces = ", ".join(f"`{value}`" for value in item["surfaces"])
        equivalent = (
            ", ".join(f"`{value}`" for value in item["nanojuris_equivalents"])
            if item["nanojuris_equivalents"]
            else "—"
        )
        lines.append(
            f"| `{item['source_id']}` | {surfaces} | {equivalent} | "
            f"`{item['classification']}` | `{item['priority']}` |"
        )
    lines.extend(
        [
            "",
            "## Leitura da matriz",
            "",
            f"- **{summary['covered']}** pacotes possuem equivalentes runtime com evidência "
            "live válida para todas as superfícies jurisprudenciais mapeadas.",
            f"- **{summary['runtime_overlap_blocked']}** pacotes possuem ao menos uma "
            "superfície bloqueada; continuam fora da contagem de cobertura.",
            f"- **{summary['runtime_overlap_unvalidated']}** pacotes possuem runtime, mas "
            "carecem de evidência live válida atual.",
            f"- **{summary['other_candidates']}** lacunas não têm equivalente runtime; devem ser "
            "pesquisadas individualmente, sem assumir que o upstream funciona hoje.",
            f"- **{summary['partial_overlap']}** pacotes têm apenas sobreposição parcial "
            "(por exemplo, "
            "eSAJ/eproc); nomes semelhantes não provam equivalência.",
            f"- **{summary['out_of_scope_process']}** pacotes TRF expõem consulta processual "
            "(`cpopg`/`cposg`) "
            "e permanecem fora da NanoJuris, conforme a fronteira com a NanoJud.",
            "- O catálogo NanoJuris possui mais autoridades que o checkout Juscraper; "
            "`courts_not_in_juscraper` explicita essas lacunas sem inferir indisponibilidade.",
            "- A lista nacional foi reconciliada com um snapshot do diretório de tribunais do CNJ; "
            "ela cobre autoridades de tribunal, não cada unidade judicial ou órgão administrativo.",
            "",
            "O estado live é lido do catálogo gerado do NanoJuris; o inventário "
            "não executa rede nem transforma runtime em evidência de disponibilidade.",
            "",
            "## Autoridades no catálogo NanoJuris sem pacote Juscraper",
            "",
            "Estas autoridades fazem parte do catálogo nacional local, mas não "
            "foram encontradas no checkout auditado. A ausência de pacote upstream "
            "não é uma afirmação de indisponibilidade da fonte oficial.",
            "",
            "| Código | Situação |",
            "| --- | --- |",
        ]
    )
    for code in record["nanojuris"]["courts_not_in_juscraper"]:
        lines.append(f"| `{code}` | `not_in_juscraper_catalog_gap` |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--generated-at", default="2026-09-01T00:00:00+00:00")
    args = parser.parse_args()
    record = build_record(args.source, args.generated_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(_markdown(record), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
