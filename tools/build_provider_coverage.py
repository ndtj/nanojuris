"""Build the human and AI provider coverage catalog."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, is_dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nanojuris.client import NanoJurisClient  # noqa: E402
from tools.audit_provider_docs import audit as audit_provider_docs  # noqa: E402

REGISTRY_PATH = ROOT / "docs" / "registry" / "providers.json"
CATALOG_PATH = ROOT / "docs" / "registry" / "provider-catalog.full.json"
COVERAGE_DIR = ROOT / "docs" / "coverage"
LATEST_LIVE_PATH = ROOT / "docs" / "live-validation-2026-08-15.md"

GENERATED_NOTE = (
    "Gerado por `python tools/build_provider_coverage.py --write`. "
    "Nao edite manualmente os dados tabulares."
)

FIELD_GROUPS = {
    "identity": {
        "court",
        "source",
        "number",
        "case_number",
        "registry_number",
        "precedent_type",
        "id",
    },
    "legal_content": {
        "summary",
        "full_text",
        "question",
        "thesis",
        "status",
        "decision_type",
        "case_class",
        "subject",
    },
    "actors": {
        "rapporteur",
        "judging_body",
        "origin_county",
        "party",
        "parties",
        "lawyer",
    },
    "dates": {
        "judgment_date",
        "publication_date",
        "updated_at",
        "source_updated_at",
        "retrieved_at",
    },
    "trace": {
        "source_trace",
        "extraction_trace",
        "document_url",
        "url",
        "sha256",
        "raw",
        "aggregations",
    },
}

TEXTUAL_SEARCH_MODES = {"text", "full_text", "summary"}


def build_catalog() -> dict[str, Any]:
    """Return the consolidated provider coverage catalog."""

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    client = NanoJurisClient()
    capabilities = {item.source: item for item in client.list_sources()}
    contracts = {item.source: item for item in client.list_source_contracts()}
    docs = {row["source_id"]: row for row in audit_provider_docs()}
    live = _parse_latest_live_validation()

    source_ids = sorted(
        set(registry["implemented"]) | set(registry["candidates"]) | set(registry["families"])
    )
    entries = []
    for source_id in source_ids:
        lifecycle = _lifecycle(registry, source_id)
        capability = capabilities.get(source_id)
        contract = contracts.get(source_id)
        doc = docs.get(source_id, {})
        live_status = live.get(source_id, _default_live_status())
        entry = {
            "source_id": source_id,
            "lifecycle": lifecycle,
            "display_name": getattr(capability, "display_name", _display_name(source_id)),
            "category": getattr(capability, "category", "research_candidate"),
            "coverage_role": _coverage_role(capability, lifecycle),
            "maturity_tier": _maturity_tier(capability, contract, doc, live_status, lifecycle),
            "development_priority": _development_priority(
                capability, contract, doc, live_status, lifecycle
            ),
            "documentation": {
                "human_doc": f"docs/providers/{source_id}/README.md",
                "legacy_doc": f"docs/source-contracts/{source_id}.md",
                "readiness": doc.get("readiness", "missing"),
                "missing_sections": doc.get("missing_sections", []),
                "open_items": doc.get("unchecked", 0),
                "fixture_references": len(doc.get("fixture_references", [])),
                "canonical_legacy_parity": bool(doc.get("parity", False)),
            },
            "live_validation": live_status,
            "input_contract": _input_contract(capability),
            "output_contract": _output_contract(capability),
            "interfaces": _interfaces(capability),
            "jurimetry": _jurimetry_contract(capability, contract),
            "ai_usage": _ai_usage(capability, contract, lifecycle),
            "source_contract": _normalize(asdict(contract)) if contract else None,
        }
        entries.append(entry)

    return {
        "schema_version": "1.0",
        "generated_at": date.today().isoformat(),
        "scope": {
            "product": "NanoJuris",
            "primary_goal": (
                "unificar acesso, normalizacao e rastreabilidade de jurisprudencia "
                "publica brasileira para pesquisa juridica, jurimetria, dados e agentes de IA"
            ),
            "out_of_scope": [
                "consulta processual",
                "comunicacoes judiciais",
                "andamentos",
                "partes",
                "timeline processual",
                "bypass de captcha, login, WAF ou segredo de justica",
            ],
        },
        "summary": _summary(entries),
        "entries": entries,
    }


def render_docs(catalog: dict[str, Any]) -> dict[Path, str]:
    """Return generated documentation files keyed by path."""

    entries = catalog["entries"]
    return {
        COVERAGE_DIR / "README.md": _render_index(catalog),
        COVERAGE_DIR / "matrix.md": _render_matrix(catalog),
        COVERAGE_DIR / "maturity.md": _render_maturity(catalog),
        COVERAGE_DIR / "inputs.md": _render_inputs(entries),
        COVERAGE_DIR / "outputs.md": _render_outputs(entries),
        COVERAGE_DIR / "field-coverage.md": _render_field_coverage(entries),
        COVERAGE_DIR / "live-status.md": _render_live_status(entries),
    }


def _summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    lifecycle = Counter(entry["lifecycle"] for entry in entries)
    tiers = Counter(entry["maturity_tier"] for entry in entries)
    roles = Counter(entry["coverage_role"] for entry in entries)
    live = Counter(entry["live_validation"]["status"] for entry in entries)
    implemented = [entry for entry in entries if entry["lifecycle"] == "implemented"]
    unified = [
        entry
        for entry in implemented
        if entry["interfaces"]["unified_search"] and entry["coverage_role"] != "out_of_scope"
    ]
    primary = [
        entry
        for entry in unified
        if entry["coverage_role"] == "primary_textual_jurisprudence"
    ]
    return {
        "total_sources": len(entries),
        "by_lifecycle": dict(sorted(lifecycle.items())),
        "by_maturity_tier": dict(sorted(tiers.items())),
        "by_coverage_role": dict(sorted(roles.items())),
        "by_latest_live_status": dict(sorted(live.items())),
        "implemented_sources": len(implemented),
        "unified_search_sources": len(unified),
        "primary_textual_sources": len(primary),
        "sources_with_full_text": sum(
            1 for entry in implemented if entry["output_contract"]["supports_full_text"]
        ),
    }


def _render_index(catalog: dict[str, Any]) -> str:
    summary = catalog["summary"]
    lines = [
        "# Coverage",
        "",
        GENERATED_NOTE,
        "",
        "Esta area e o indice operacional do NanoJuris para humanos e agentes de IA.",
        "Ela responde, em uma leitura curta, quais fontes existem, o que entram, o que saem,",
        "quais estao maduras para busca unificada e quais ainda exigem aprofundamento.",
        "",
        "## Resumo Atual",
        "",
        f"- Fontes documentadas: **{summary['total_sources']}**.",
        f"- Providers implementados: **{summary['implemented_sources']}**.",
        f"- Fontes na busca unificada: **{summary['unified_search_sources']}**.",
        f"- Fontes primarias de jurisprudencia textual: **{summary['primary_textual_sources']}**.",
        "- Fontes com algum suporte a inteiro teor/documento: "
        f"**{summary['sources_with_full_text']}**.",
        "",
        "## Como Usar",
        "",
        "| Pergunta | Arquivo |",
        "| --- | --- |",
        "| Quais fontes existem e em que estado estao? | [matrix.md](matrix.md) |",
        "| Quais entradas e filtros cada provider aceita? | [inputs.md](inputs.md) |",
        "| Quais campos e formatos cada provider entrega? | [outputs.md](outputs.md) |",
        "| Quais campos canonicos estao cobertos? | [field-coverage.md](field-coverage.md) |",
        "| O que significa ouro, prata, bronze e experimental? | [maturity.md](maturity.md) |",
        "| Qual foi a ultima validacao live focada? | [live-status.md](live-status.md) |",
        "| Qual catalogo uma IA deve ler? | "
        "[../registry/provider-catalog.full.json](../registry/provider-catalog.full.json) |",
        "",
        "## Regra De Produto",
        "",
        "NanoJuris deve priorizar jurisprudencia textual, precedentes, informativos e",
        "decisoes publicas com rastreabilidade. Consulta processual, DJEN, DataJud,",
        "andamentos e timeline processual pertencem ao NanoJud.",
        "",
        "## Fluxo De Maturidade",
        "",
        "```text",
        "fonte oficial -> contrato observado -> fixture -> parser -> campos canonicos",
        "              -> validacao live opcional -> busca unificada -> jurimetria",
        "```",
        "",
        "O objetivo nao e apenas chamar tribunais. O objetivo e saber, com precisao,",
        "qual campo veio de onde, em qual formato, com qual limite e com qual grau de",
        "confianca operacional.",
    ]
    return "\n".join(lines) + "\n"


def _render_matrix(catalog: dict[str, Any]) -> str:
    lines = [
        "# Coverage Matrix",
        "",
        GENERATED_NOTE,
        "",
        "| Fonte | Ciclo | Papel | Maturidade | Prioridade | Live | "
        "Busca Unificada | Inteiro Teor | Doc |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for entry in catalog["entries"]:
        doc = entry["documentation"]
        lines.append(
            f"| [`{entry['source_id']}`](../providers/{entry['source_id']}/README.md) "
            f"| {entry['lifecycle']} | `{entry['coverage_role']}` | "
            f"`{entry['maturity_tier']}` | `{entry['development_priority']}` | "
            f"`{entry['live_validation']['status']}` | "
            f"{_yes(entry['interfaces']['unified_search'])} "
            f"| {_yes(entry['output_contract']['supports_full_text'])} | "
            f"`{doc['readiness']}` |"
        )
    return "\n".join(lines) + "\n"


def _render_maturity(catalog: dict[str, Any]) -> str:
    summary = catalog["summary"]
    lines = [
        "# Maturity",
        "",
        GENERATED_NOTE,
        "",
        "## Taxonomia",
        "",
        "| Nivel | Uso recomendado | Criterio operacional |",
        "| --- | --- | --- |",
        "| `gold` | referencia para Studio, MCP, demos e jurimetria inicial | "
        "contrato forte, baixo/medio risco, busca unificada e documentacao "
        "sem pendencia critica |",
        "| `silver` | uso produtivo com cautela | contrato bom, mas ainda com "
        "lacunas de live, inteiro teor, filtros ou docs |",
        "| `bronze` | pesquisa tecnica e amadurecimento | provider existe, mas ainda "
        "precisa de fixtures, erros ou contrato mais profundo |",
        "| `context` | fonte complementar | precedentes, informativos, catalogos "
        "ou datasets que ajudam a pesquisa, mas nao sao busca textual ampla |",
        "| `mapped` | backlog de desenvolvimento | fonte documentada sem provider runtime |",
        "| `blocked` | nao rotear automaticamente | WAF, captcha, login, timeout "
        "recorrente ou contrato instavel |",
        "| `family` | especificacao reutilizavel | familia tecnica compartilhada, "
        "nao fonte executavel isolada |",
        "",
        "## Contagem Atual",
        "",
        "| Nivel | Quantidade |",
        "| --- | ---: |",
    ]
    for key, value in summary["by_maturity_tier"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Principio De Qualidade",
            "",
            "Uma fonte so deve virar referencia para jurimetria quando a biblioteca consegue",
            "distinguir resultado vazio, falha de rede, controle de acesso, mudanca de",
            "contrato, coleta parcial e resposta completa.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_inputs(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Inputs",
        "",
        GENERATED_NOTE,
        "",
        "Esta matriz mostra as entradas declaradas por fonte. Ela e util para humanos",
        "planejarem coletas e para IAs escolherem providers sem inventar filtros.",
        "",
        "| Fonte | Texto | Filtros | Paginacao | Catalogo | Sugestoes |",
        "| --- | ---: | --- | --- | ---: | ---: |",
    ]
    for entry in entries:
        input_contract = entry["input_contract"]
        filters = ", ".join(input_contract["supported_filters"]) or "-"
        lines.append(
            f"| `{entry['source_id']}` | {_yes(input_contract['text_query'])} | "
            f"{filters} | `{input_contract['pagination_mode']}` | "
            f"{_yes(input_contract['supports_catalog'])} | "
            f"{_yes(input_contract['supports_suggestions'])} |"
        )
    return "\n".join(lines) + "\n"


def _render_outputs(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Outputs",
        "",
        GENERATED_NOTE,
        "",
        "| Fonte | Registros Canonicos | Tipos | Formatos | Campos | Inteiro Teor | Trace |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for entry in entries:
        output = entry["output_contract"]
        lines.append(
            f"| `{entry['source_id']}` | {', '.join(output['canonical_records']) or '-'} "
            f"| {', '.join(output['document_types']) or '-'} "
            f"| {', '.join(output['content_formats']) or '-'} "
            f"| {len(output['extracted_fields'])} | "
            f"{_yes(output['supports_full_text'])} | {_yes(output['trace_expected'])} |"
        )
    return "\n".join(lines) + "\n"


def _render_field_coverage(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Field Coverage",
        "",
        GENERATED_NOTE,
        "",
        "A matriz agrupa campos declarados por finalidade. Ela nao mede qualidade",
        "semantica do campo; mede declaracao objetiva no contrato do provider.",
        "",
        "| Fonte | Identificacao | Conteudo Juridico | Atores | Datas | Trace | "
        "Campos Declarados |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for entry in entries:
        fields = set(entry["output_contract"]["extracted_fields"])
        grouped = {group: len(fields & names) for group, names in FIELD_GROUPS.items()}
        lines.append(
            f"| `{entry['source_id']}` | {grouped['identity']} | "
            f"{grouped['legal_content']} | {grouped['actors']} | {grouped['dates']} | "
            f"{grouped['trace']} | {len(fields)} |"
        )
    return "\n".join(lines) + "\n"


def _render_live_status(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Live Status",
        "",
        GENERATED_NOTE,
        "",
        "Status live e uma fotografia de validacao, nao garantia de disponibilidade.",
        "Chamadas a tribunais podem variar por rede, horario, WAF, captcha, TLS e",
        "alteracao do proprio portal.",
        "",
        "| Fonte | Status | Data | Retornados | Total Informado | Paginacao | "
        "Latencia | Observacao |",
        "| --- | --- | --- | ---: | ---: | --- | ---: | --- |",
    ]
    for entry in entries:
        live = entry["live_validation"]
        lines.append(
            f"| `{entry['source_id']}` | `{live['status']}` | {live['date'] or '-'} | "
            f"{live['returned'] if live['returned'] is not None else '-'} | "
            f"{live['reported_total'] if live['reported_total'] is not None else '-'} | "
            f"`{live['pagination_mode'] or '-'}` | {live['latency'] or '-'} | "
            f"{live['note'] or '-'} |"
        )
    return "\n".join(lines) + "\n"


def _parse_latest_live_validation() -> dict[str, dict[str, Any]]:
    if not LATEST_LIVE_PATH.is_file():
        return {}
    text = LATEST_LIVE_PATH.read_text(encoding="utf-8")
    rows: dict[str, dict[str, Any]] = {}
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 7:
            continue
        source = parts[0].strip("`")
        rows[source] = {
            "status": parts[1].strip("`"),
            "date": "2026-08-15",
            "returned": _int_or_none(parts[2]),
            "reported_total": _int_or_none(parts[3]),
            "pagination_mode": parts[4].strip("`") if parts[4] != "-" else None,
            "latency": parts[5],
            "note": parts[6],
            "evidence": "docs/live-validation-2026-08-15.md",
        }
    return rows


def _default_live_status() -> dict[str, Any]:
    return {
        "status": "not_checked_in_latest_focused_run",
        "date": None,
        "returned": None,
        "reported_total": None,
        "pagination_mode": None,
        "latency": None,
        "note": "sem validacao focada nesta rodada",
        "evidence": None,
    }


def _input_contract(capability: Any | None) -> dict[str, Any]:
    if capability is None:
        return {
            "text_query": False,
            "search_modes": [],
            "supported_filters": [],
            "pagination_mode": "unknown",
            "supports_catalog": False,
            "supports_suggestions": False,
        }
    return {
        "text_query": "text" in capability.search_modes,
        "search_modes": capability.search_modes,
        "supported_filters": capability.supported_filters,
        "pagination_mode": capability.pagination_mode,
        "supports_catalog": capability.supports_catalog,
        "supports_suggestions": capability.supports_suggestions,
    }


def _output_contract(capability: Any | None) -> dict[str, Any]:
    if capability is None:
        return {
            "document_types": [],
            "content_formats": [],
            "canonical_records": [],
            "extracted_fields": [],
            "supports_full_text": False,
            "trace_expected": False,
        }
    return {
        "document_types": capability.document_types,
        "content_formats": capability.content_formats,
        "canonical_records": capability.canonical_records,
        "extracted_fields": capability.extracted_fields,
        "supports_full_text": capability.supports_full_text,
        "trace_expected": bool(capability.endpoints),
    }


def _interfaces(capability: Any | None) -> dict[str, bool]:
    if capability is None:
        return {
            "cli": False,
            "unified_search": False,
            "mcp": False,
            "studio": False,
            "live_tests": False,
        }
    return {
        "cli": capability.supports_cli,
        "unified_search": capability.supports_unified_search,
        "mcp": capability.supports_mcp,
        "studio": capability.supports_studio,
        "live_tests": capability.supports_live_tests,
    }


def _jurimetry_contract(capability: Any | None, contract: Any | None) -> dict[str, Any]:
    if capability is None:
        return {
            "fit": "aguarda implementacao",
            "dataset_ready": False,
            "minimum_requirements": [
                "contrato HTTP reproduzido",
                "fixture de sucesso",
                "campos canonicos mapeados",
            ],
        }
    fit = getattr(contract, "jurimetry_fit", "")
    fields = set(capability.extracted_fields)
    dataset_ready = (
        capability.supports_unified_search
        and bool(fields & FIELD_GROUPS["identity"])
        and bool(fields & FIELD_GROUPS["legal_content"])
        and bool(fields & FIELD_GROUPS["dates"])
    )
    return {
        "fit": fit,
        "dataset_ready": dataset_ready,
        "minimum_requirements": [
            "identificador juridico estavel",
            "conteudo juridico textual",
            "data normalizada ou preservada em campo raw",
            "trace de fonte",
            "estado de completude da pagina",
        ],
    }


def _ai_usage(capability: Any | None, contract: Any | None, lifecycle: str) -> dict[str, Any]:
    if capability is None:
        return {
            "safe_to_route": False,
            "preflight": ["ler dossie", "nao executar como provider runtime"],
            "recommendation": f"Fonte {lifecycle}; usar apenas para planejamento.",
        }
    return {
        "safe_to_route": capability.supports_mcp and capability.supports_unified_search,
        "preflight": [
            "list_sources",
            "source_contracts",
            "validar fonte quando a coleta exigir dado live",
        ],
        "recommendation": getattr(contract, "mcp_recommendation", ""),
    }


def _coverage_role(capability: Any | None, lifecycle: str) -> str:
    if lifecycle == "family":
        return "implementation_family"
    if capability is None:
        return "mapped_candidate"
    category = capability.category
    if (
        category == "court_jurisprudence"
        and bool(set(capability.search_modes) & TEXTUAL_SEARCH_MODES)
        and "CanonicalDecision" in capability.canonical_records
        and capability.supports_unified_search
    ):
        return "primary_textual_jurisprudence"
    if category in {"qualified_precedents", "court_precedents"}:
        return "precedent_context"
    if category in {"curated_jurisprudence", "electoral_jurisprudence"}:
        return "curated_context"
    if category == "administrative_jurisprudence":
        return "administrative_context"
    if category.endswith("_dataset"):
        return "dataset_pipeline"
    return "specialized_context"


def _maturity_tier(
    capability: Any | None,
    contract: Any | None,
    doc: dict[str, Any],
    live_status: dict[str, Any],
    lifecycle: str,
) -> str:
    if lifecycle == "family":
        return "family"
    if capability is None:
        return "mapped"
    level = getattr(contract, "contract_level", 1)
    risk = getattr(contract, "risk_level", "alto")
    has_doc_gap = bool(doc.get("missing_sections")) or int(doc.get("unchecked", 0)) > 0
    live = live_status["status"]
    if risk == "alto" and live in {"blocked", "source_unavailable"}:
        return "blocked"
    if capability.category not in {"court_jurisprudence", "administrative_jurisprudence"}:
        return "context"
    if level >= 5 and risk in {"baixo", "medio"} and capability.supports_unified_search:
        return "silver" if has_doc_gap else "gold"
    if level >= 4 and capability.supports_unified_search:
        return "silver" if not has_doc_gap else "bronze"
    if capability.supports_unified_search:
        return "bronze"
    return "context"


def _development_priority(
    capability: Any | None,
    contract: Any | None,
    doc: dict[str, Any],
    live_status: dict[str, Any],
    lifecycle: str,
) -> str:
    if lifecycle == "family":
        return "P1_family_reuse"
    if capability is None:
        return "P1_candidate_contract"
    role = _coverage_role(capability, lifecycle)
    level = getattr(contract, "contract_level", 1)
    risk = getattr(contract, "risk_level", "alto")
    has_doc_gap = bool(doc.get("missing_sections")) or int(doc.get("unchecked", 0)) > 0
    if role == "primary_textual_jurisprudence" and (level < 5 or risk == "alto" or has_doc_gap):
        return "P0_harden_for_unified_search"
    if role == "primary_textual_jurisprudence":
        return "P0_reference_provider"
    if role in {"precedent_context", "curated_context", "dataset_pipeline"}:
        return "P1_contextual_value"
    if live_status["status"] in {"blocked", "source_unavailable"}:
        return "P1_access_diagnostics"
    return "P2_maintain"


def _lifecycle(registry: dict[str, Any], source_id: str) -> str:
    if source_id in registry["implemented"]:
        return "implemented"
    if source_id in registry["candidates"]:
        return "candidate"
    if source_id in registry["families"]:
        return "family"
    return "unknown"


def _display_name(source_id: str) -> str:
    return source_id.replace("_", " ").upper()


def _yes(value: bool) -> str:
    return "sim" if value else "nao"


def _int_or_none(value: str) -> int | None:
    cleaned = re.sub(r"[^0-9]", "", value)
    return int(cleaned) if cleaned else None


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_normalize(item) for item in value]
    return value


def write_outputs(catalog: dict[str, Any]) -> None:
    CATALOG_PATH.write_text(
        json.dumps(_normalize(catalog), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    COVERAGE_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in render_docs(catalog).items():
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated artifacts")
    args = parser.parse_args()
    catalog = build_catalog()
    if args.write:
        write_outputs(catalog)
    else:
        print(json.dumps(_normalize(catalog), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
