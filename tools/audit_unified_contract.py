"""Audit the semantic contract exposed by the federated search.

This report is intentionally derived from runtime capability declarations and
versioned live/discovery evidence.  It does not call providers and it does not
edit the generated provider catalog.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

DEFAULT_OUTPUT_DIR = ROOT / "docs" / "provider-discovery"
DEFAULT_SMOKE = DEFAULT_OUTPUT_DIR / "provider-live-search-smoke.json"
DEFAULT_SWEEP = DEFAULT_OUTPUT_DIR / "all-provider-sweep.json"

COMMON_FILTERS = (
    "text",
    "courts",
    "types",
    "all_words",
    "any_words",
    "without_words",
    "exact_phrase",
    "rapporteur",
    "updated_from",
    "updated_to",
    "published_from",
    "published_to",
    "number",
    "party_name",
    "party_document",
    "lawyer_name",
    "oab",
    "precatory_number",
    "police_document",
    "cda",
    "source_origin",
    "source_origins",
    "fetch_details",
)

IDENTIFIER_FILTERS = {
    "number",
    "party_name",
    "party_document",
    "lawyer_name",
    "oab",
    "precatory_number",
    "police_document",
    "cda",
}

REFINEMENT_FILTERS = {
    "all_words",
    "any_words",
    "without_words",
    "exact_phrase",
    "rapporteur",
    "updated_from",
    "updated_to",
    "published_from",
    "published_to",
}


def _semantic_profile(category: str, records: Iterable[str]) -> str:
    record_set = set(records)
    if category in {"qualified_precedents", "court_precedents", "electoral_jurisprudence"}:
        return "precedent"
    if category == "curated_jurisprudence":
        return "curated"
    if {"CanonicalDecision", "CanonicalPrecedent"}.issubset(record_set):
        return "hybrid_decision_precedent"
    if "CanonicalPrecedent" in record_set:
        return "precedent"
    if "CanonicalDecision" in record_set:
        return "decision"
    if "ProviderCatalog" in record_set:
        return "catalog"
    if "CanonicalDocument" in record_set:
        return "document"
    return "unclassified"


def _smoke_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("source", ""): row for row in payload.get("providers", [])}


def _sweep_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("source", ""): row for row in payload.get("providers", [])}


def _row(capability: Any, smoke: dict[str, Any], sweep: dict[str, Any]) -> dict[str, Any]:
    declared = set(capability.supported_filters)
    declared_unsupported = set(getattr(capability, "unsupported_filters", []) or [])
    missing = [name for name in COMMON_FILTERS if name not in declared]
    observed = {
        str(name)
        for name in (sweep.get("contract_comparison", {}) or {}).get(
            "observed_filter_semantics", []
        )
        if str(name)
    }
    observed_not_promoted = sorted(
        set(missing).intersection(observed).difference(declared_unsupported)
    )
    explicitly_unsupported = sorted(
        set(missing).intersection(declared_unsupported).union(set(missing).difference(observed))
    )
    gaps: list[str] = []
    if not capability.supports_unified_search:
        gaps.append("excluded_from_unified_search")
    if not capability.canonical_records:
        gaps.append("canonical_record_not_declared")
    if capability.pagination_mode == "unknown":
        gaps.append("pagination_contract_unknown")
    if capability.completeness_contract == "unknown":
        gaps.append("completeness_contract_unknown")
    if capability.full_text_access == "unknown":
        gaps.append("full_text_access_evidence_unknown")
    if not capability.supports_full_text and capability.full_text_access in {
        "unknown",
        "not_declared",
    }:
        gaps.append("full_text_not_declared")
    if observed_not_promoted:
        gaps.append("observed_filters_not_promoted_to_contract")
    canonical_set = set(capability.canonical_records)
    semantic_discriminator = getattr(capability, "semantic_discriminator", None)
    if {"CanonicalDecision", "CanonicalPrecedent"}.issubset(
        canonical_set
    ) and not semantic_discriminator:
        gaps.append("decision_and_precedent_profiles_need_discriminator")
    if smoke.get("status") not in {None, "valid_data"}:
        gaps.append(f"live_status_{smoke.get('status', 'not_recorded')}")
    support_count = len(COMMON_FILTERS) - len(missing)
    return {
        "source": capability.source,
        "display_name": capability.display_name,
        "category": capability.category,
        "semantic_profile": _semantic_profile(capability.category, capability.canonical_records),
        "supports_unified_search": capability.supports_unified_search,
        "canonical_records": sorted(capability.canonical_records),
        "semantic_discriminator": semantic_discriminator,
        "extracted_fields": sorted(capability.extracted_fields),
        "pagination_mode": capability.pagination_mode,
        "completeness_contract": capability.completeness_contract,
        "full_text_access": capability.full_text_access,
        "supports_full_text": capability.supports_full_text,
        "declared_filter_count": len(declared),
        "native_filter_count": support_count,
        "filter_support_ratio": round(support_count / len(COMMON_FILTERS), 3),
        "supported_filters": sorted(declared),
        "filter_classification": {
            name: (
                "native"
                if name in declared
                else "unsupported"
                if name in declared_unsupported
                else "observed_not_promoted"
                if name in observed_not_promoted
                else "unsupported"
            )
            for name in COMMON_FILTERS
        },
        "missing_common_filters": missing,
        "explicitly_unsupported_filters": explicitly_unsupported,
        "observed_filters_not_promoted": observed_not_promoted,
        "gaps": gaps,
        "live_status": smoke.get("status"),
        "live_error_type": smoke.get("error_type"),
        "live_results": smoke.get("results"),
        "live_quality_records": smoke.get("quality_records"),
        "discovery_status": sweep.get("status"),
        "observed_filter_count": len(sweep.get("observed_filters", []) or []),
        "todo_count": len(sweep.get("todo", []) or []),
    }


def build_report(
    capabilities: Iterable[Any],
    *,
    smoke_payload: dict[str, Any] | None = None,
    sweep_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable unified-contract audit without network calls."""

    smoke = _smoke_map(smoke_payload or {})
    sweep = _sweep_map(sweep_payload or {})
    rows = [_row(cap, smoke.get(cap.source, {}), sweep.get(cap.source, {})) for cap in capabilities]
    unified = [row for row in rows if row["supports_unified_search"]]
    filter_counts = {
        name: sum(name in row["supported_filters"] for row in unified) for name in COMMON_FILTERS
    }
    gap_counts = Counter(gap for row in unified for gap in row["gaps"])
    profile_counts = Counter(row["semantic_profile"] for row in unified)
    pagination_counts = Counter(row["pagination_mode"] for row in unified)
    full_text_counts = Counter(row["full_text_access"] for row in unified)
    completeness_counts = Counter(row["completeness_contract"] for row in unified)
    smoke_summary = dict((smoke_payload or {}).get("summary", {}))
    discovery_summary = dict((sweep_payload or {}).get("summary", {}))
    valid = int(smoke_summary.get("valid_data", 0) or 0)
    provider_count = int((smoke_payload or {}).get("provider_count", len(rows)) or len(rows))

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "contract_version": "unified-search-audit-v1",
        "scope": {
            "provider_count": len(rows),
            "unified_provider_count": len(unified),
            "excluded_provider_count": len(rows) - len(unified),
            "common_filters": list(COMMON_FILTERS),
            "identifier_filters": sorted(IDENTIFIER_FILTERS),
            "refinement_filters": sorted(REFINEMENT_FILTERS),
        },
        "summary": {
            "semantic_profiles": dict(profile_counts),
            "pagination_modes": dict(pagination_counts),
            "full_text_access": dict(full_text_counts),
            "completeness_contracts": dict(completeness_counts),
            "filter_support_counts": filter_counts,
            "gap_counts": dict(gap_counts.most_common()),
            "live_valid_data": valid,
            "live_provider_count": provider_count,
            "live_valid_data_rate": round(valid / provider_count, 3) if provider_count else None,
        },
        "discovery_evidence": {
            "mode": (sweep_payload or {}).get("mode"),
            "runtime_observed": discovery_summary.get("observed"),
            "runtime_no_observation": discovery_summary.get("no_observation"),
            "access_controlled": discovery_summary.get("access_controlled"),
            "declared_routes": discovery_summary.get("declared_routes"),
            "observed_routes": discovery_summary.get("observed_routes"),
            "declared_filters": discovery_summary.get("declared_filters"),
            "observed_filters": discovery_summary.get("observed_filters"),
            "catalog_candidates_observed": discovery_summary.get("catalog_candidates_observed"),
        },
        "interpretation": [
            "Todos os providers compartilham o envelope SearchPage/JurisprudenceResult, mas o perfil semantico e os campos preenchidos variam por fonte.",
            "A lista supported_filters e uma allowlist por provider; filtro ausente e tratado como unsupported e nunca e aplicado silenciosamente.",
            "Precedentes, decisoes, informativos curados e documentos de catalogo nao formam automaticamente um corpus equivalente para jurimetria.",
            "O resultado live e uma fotografia da consulta registrada e nao prova disponibilidade permanente nem cobertura completa.",
        ],
        "providers": rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    scope = report["scope"]
    summary = report["summary"]
    lines = [
        "# Auditoria do contrato de busca unificada",
        "",
        f"Gerado em `{report['generated_at']}` a partir das declarações runtime e dos artefatos locais de smoke/discovery.",
        "",
        "## Resposta executiva",
        "",
        f"A busca unificada compartilha o envelope de saída, mas não oferece filtros nem perfis de dados equivalentes. Há **{scope['unified_provider_count']} providers unificados** entre **{scope['provider_count']} runtime**; **{scope['excluded_provider_count']}** ficam fora por contrato/categoria.",
        f"Na fotografia live registrada, **{summary['live_valid_data']}/{summary['live_provider_count']}** providers entregaram dados válidos (**{summary['live_valid_data_rate']:.1%}**).",
        f"O discovery aprofundado observou **{report['discovery_evidence'].get('observed_routes', 0)} rotas** e **{report['discovery_evidence'].get('observed_filters', 0)} campos de filtro**, com **{report['discovery_evidence'].get('access_controlled', 0)}** sinais de controle de acesso.",
        "",
        "## Lacunas principais",
        "",
        "- `pagination_contract_unknown`: a fonte não comprova como a janela remota termina.",
        "- `completeness_contract_unknown`: total, truncamento ou exaustividade não estão formalizados.",
        "- `full_text_access_evidence_unknown`: texto integral é anunciado ou possível, mas a forma de obtenção não está comprovada.",
        "- `observed_filters_not_promoted_to_contract`: a fonte expos um filtro que ainda nao foi promovido com semantica runtime.",
        "- `decision_and_precedent_profiles_need_discriminator`: a fonte entrega decisão e precedente e exige discriminação semântica.",
        "- estados live de acesso/indisponibilidade/query inválida ainda reduzem a cobertura operacional.",
        "",
        "## Distribuição do contrato",
        "",
        f"Perfis: `{json.dumps(summary['semantic_profiles'], ensure_ascii=False)}`",
        f"Paginação: `{json.dumps(summary['pagination_modes'], ensure_ascii=False)}`",
        f"Texto integral: `{json.dumps(summary['full_text_access'], ensure_ascii=False)}`",
        f"Completude: `{json.dumps(summary['completeness_contracts'], ensure_ascii=False)}`",
        "",
        "## Filtros",
        "",
        "A contagem indica quantos providers declaram o filtro como nativo. Filtros ausentes sao tratados como `unsupported`; nao ha pos-filtro silencioso.",
        "",
        "| Filtro | Providers |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{name}` | {count} |" for name, count in summary["filter_support_counts"].items()
    )
    lines.extend(
        [
            "",
            "## Matriz por provider",
            "",
            "| Provider | Perfil | Canônicos | Filtros | Paginação | Completude | Texto | Live | Lacunas |",
            "|---|---|---|---:|---|---|---|---|---|",
        ]
    )
    for row in report["providers"]:
        live = row["live_status"] or "não registrado"
        gaps = ", ".join(row["gaps"][:5]) or "-"
        records = ", ".join(row["canonical_records"]) or "-"
        lines.append(
            f"| `{row['source']}` | {row['semantic_profile']} | {records} | {row['native_filter_count']}/{len(COMMON_FILTERS)} | {row['pagination_mode']} | {row['completeness_contract']} | {row['full_text_access']} | {live} | {gaps} |"
        )
    lines.extend(
        [
            "",
            "## Critério de maturação",
            "",
            "Um provider só deve ser promovido como plenamente equivalente na busca unificada quando tiver perfil semântico explícito, filtros classificados como nativos/traduzidos/pós-filtro local ou não suportados, paginação e completude comprovadas, identidade estável, fixtures de estados e evidência live válida.",
            "",
            "A matriz JSON é a fonte estruturada deste relatório: `unified-contract-matrix.json`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--smoke-report", type=Path, default=DEFAULT_SMOKE)
    parser.add_argument("--sweep-report", type=Path, default=DEFAULT_SWEEP)
    args = parser.parse_args()

    from nanojuris.client import NanoJurisClient

    def load(path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    report = build_report(
        NanoJurisClient().list_sources(),
        smoke_payload=load(args.smoke_report),
        sweep_payload=load(args.sweep_report),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "unified-contract-matrix.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "unified-contract-matrix.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
