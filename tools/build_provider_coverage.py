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
PACKAGE_CATALOG_PATH = ROOT / "src" / "nanojuris" / "data" / "provider-catalog.full.json"
COVERAGE_DIR = ROOT / "docs" / "coverage"
LATEST_LIVE_PATH = ROOT / "docs" / "live-validation-2026-08-15.md"
VALIDATION_RUNS_DIR = ROOT / "docs" / "validation" / "runs"

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
        source_contract = _normalize(asdict(contract)) if contract else None
        entry = {
            "source_id": source_id,
            "lifecycle": lifecycle,
            "display_name": getattr(capability, "display_name", _display_name(source_id)),
            "category": getattr(capability, "category", "research_candidate"),
            "identity": _identity(source_id, capability),
            "implementation_status": _implementation_status(lifecycle),
            "offline_status": _offline_status(lifecycle, doc),
            "live_status": live_status["status"],
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
            "live_evidence": live_status,
            "input_contract": _input_contract(capability),
            "output_contract": _output_contract(capability),
            "search_contract": _input_contract(capability),
            "document_contract": _document_contract(capability),
            "pagination_contract": _pagination_contract(capability),
            "error_contract": _error_contract(capability, contract),
            "quality_contract": _quality_contract(doc, live_status),
            "interfaces": _interfaces(capability),
            "jurimetry": _jurimetry_contract(capability, contract),
            "ai_usage": _ai_usage(capability, contract, lifecycle),
            "source_contract": source_contract,
        }
        entry["known_defects"] = _known_defects(entry, doc, contract, live_status)
        entry["recommended_for"] = _recommended_for(entry, contract)
        entry["not_recommended_for"] = _not_recommended_for(entry, live_status)
        entry["mcp"] = _interface_contract(entry, "mcp")
        entry["studio"] = _interface_contract(entry, "studio")
        entry["maturity_score"] = _maturity_score(entry, capability, contract, doc, live_status)
        entries.append(entry)

    return {
        "schema_version": "1.0",
        "generated_at": _snapshot_date(),
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
        COVERAGE_DIR / "maturity-score.md": _render_maturity_score(entries),
        COVERAGE_DIR / "improvement-queue.md": _render_improvement_queue(entries),
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
        entry for entry in unified if entry["coverage_role"] == "primary_textual_jurisprudence"
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
        "score": _score_summary(entries),
    }


def _score_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    implemented = [entry for entry in entries if entry["lifecycle"] == "implemented"]
    scored = [entry for entry in implemented if "maturity_score" in entry]
    if not scored:
        return {"average": 0, "top": [], "needs_attention": []}
    average = round(sum(entry["maturity_score"]["total"] for entry in scored) / len(scored), 1)
    top = sorted(scored, key=lambda item: (-item["maturity_score"]["total"], item["source_id"]))[:5]
    needs_attention = sorted(
        [
            entry
            for entry in scored
            if entry["development_priority"] == "P0_harden_for_unified_search"
        ],
        key=lambda item: (item["maturity_score"]["total"], item["source_id"]),
    )[:10]
    return {
        "average": average,
        "top": [entry["source_id"] for entry in top],
        "needs_attention": [entry["source_id"] for entry in needs_attention],
    }


def _maturity_score(
    entry: dict[str, Any],
    capability: Any | None,
    contract: Any | None,
    doc: dict[str, Any],
    live_status: dict[str, Any],
) -> dict[str, Any]:
    dimensions = {
        "input": _score_input(entry),
        "output": _score_output(entry),
        "reliability": _score_reliability(capability, contract, live_status),
        "documentation": _score_documentation(doc),
        "product": _score_product(entry),
    }
    total = min(100, sum(dimensions.values()))
    blockers = _score_blockers(entry, capability, contract, doc, live_status)
    next_actions = _score_next_actions(entry, blockers, doc, live_status)
    return {
        "total": total,
        "grade": _score_grade(total),
        "dimensions": dimensions,
        "blockers": blockers,
        "next_actions": next_actions,
    }


def _score_input(entry: dict[str, Any]) -> int:
    input_contract = entry["input_contract"]
    score = 0
    if input_contract["text_query"]:
        score += 8
    if input_contract["supported_filters"]:
        score += min(5, len(input_contract["supported_filters"]) // 2 + 1)
    if input_contract["pagination_mode"] != "unknown":
        score += 4
    if input_contract["supports_catalog"]:
        score += 2
    if input_contract["supports_suggestions"]:
        score += 1
    return min(20, score)


def _score_output(entry: dict[str, Any]) -> int:
    output = entry["output_contract"]
    fields = set(output["extracted_fields"])
    score = 0
    if "CanonicalDecision" in output["canonical_records"]:
        score += 6
    elif output["canonical_records"]:
        score += 3
    if fields & FIELD_GROUPS["identity"]:
        score += 4
    if fields & FIELD_GROUPS["legal_content"]:
        score += 5
    if fields & FIELD_GROUPS["dates"]:
        score += 4
    if output["supports_full_text"]:
        score += 3
    if output["trace_expected"]:
        score += 3
    return min(25, score)


def _score_reliability(
    capability: Any | None,
    contract: Any | None,
    live_status: dict[str, Any],
) -> int:
    if capability is None:
        return 2
    level = int(getattr(contract, "contract_level", 1))
    risk = str(getattr(contract, "risk_level", "alto"))
    score = min(12, level * 2)
    score += {"baixo": 5, "medio": 3, "alto": 1, "critico": 0}.get(risk, 1)
    score += {
        "valid": 3,
        "empty": 2,
        "not_checked_in_latest_focused_run": 1,
        "source_unavailable": 0,
        "blocked": 0,
    }.get(live_status["status"], 1)
    return min(20, score)


def _score_documentation(doc: dict[str, Any]) -> int:
    score = 0
    readiness = doc.get("readiness", "missing")
    if readiness == "implementation_ready":
        score += 7
    elif readiness in {"needs_deepening", "research_ready", "family_spec"}:
        score += 4
    if not doc.get("missing_sections"):
        score += 5
    open_items = int(doc.get("unchecked", 0))
    score += max(0, 4 - min(4, open_items))
    score += min(4, int(len(doc.get("fixture_references", []))))
    return min(20, score)


def _score_product(entry: dict[str, Any]) -> int:
    interfaces = entry["interfaces"]
    jurimetry = entry["jurimetry"]
    ai_usage = entry["ai_usage"]
    score = 0
    if interfaces["unified_search"]:
        score += 4
    if interfaces["mcp"]:
        score += 2
    if interfaces["studio"]:
        score += 2
    if interfaces["cli"]:
        score += 2
    if jurimetry["dataset_ready"]:
        score += 3
    if ai_usage["safe_to_route"]:
        score += 2
    return min(15, score)


def _score_blockers(
    entry: dict[str, Any],
    capability: Any | None,
    contract: Any | None,
    doc: dict[str, Any],
    live_status: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if entry["lifecycle"] != "implemented":
        blockers.append("sem provider runtime")
    if capability is not None and not entry["interfaces"]["unified_search"]:
        blockers.append("fora da busca unificada")
    if getattr(contract, "risk_level", "") == "alto":
        blockers.append("risco operacional alto")
    if live_status["status"] in {"blocked", "source_unavailable"}:
        blockers.append(f"live status: {live_status['status']}")
    if doc.get("missing_sections"):
        blockers.append("dossie com secoes faltantes")
    if int(doc.get("unchecked", 0)) > 0:
        blockers.append("dossie com pendencias abertas")
    return blockers


def _score_next_actions(
    entry: dict[str, Any],
    blockers: list[str],
    doc: dict[str, Any],
    live_status: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    if entry["lifecycle"] != "implemented":
        actions.append("reproduzir contrato HTTP publico e criar fixture minima")
    if doc.get("missing_sections"):
        actions.append("completar secoes faltantes do dossie")
    if int(doc.get("unchecked", 0)) > 0:
        actions.append("fechar checklist objetivo do dossie")
    if entry["output_contract"]["supports_full_text"]:
        actions.append("validar inteiro teor com hash, tamanho e access_status")
    if live_status["status"] == "not_checked_in_latest_focused_run":
        actions.append("rodar validacao live pequena com termo juridico padrao")
    if "risco operacional alto" in blockers:
        actions.append("classificar WAF, captcha, timeout e mudanca de contrato separadamente")
    if not actions:
        actions.append("manter monitoramento e ampliar fixtures por variacao juridica")
    return actions[:4]


def _score_grade(total: int) -> str:
    if total >= 85:
        return "A"
    if total >= 70:
        return "B"
    if total >= 50:
        return "C"
    return "D"


def _priority_rank(priority: str) -> int:
    order = {
        "P0_harden_for_unified_search": 0,
        "P0_reference_provider": 1,
        "P1_candidate_contract": 2,
        "P1_access_diagnostics": 3,
        "P1_contextual_value": 4,
        "P1_family_reuse": 5,
        "P2_maintain": 6,
    }
    return order.get(priority, 99)


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
        "| Como o score de maturidade e calculado? | [maturity-score.md](maturity-score.md) |",
        "| Quais providers devemos amadurecer primeiro? | "
        "[improvement-queue.md](improvement-queue.md) |",
        "| Qual e o plano de ondas para maturidade dos providers? | "
        "[maturity-waves.md](maturity-waves.md) |",
        "| Qual artefato e a fonte de verdade para cada pergunta? | "
        "[source-of-truth.md](source-of-truth.md) |",
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
        "| Fonte | Ciclo | Papel | Score | Maturidade | Prioridade | Live | "
        "Busca Unificada | Inteiro Teor | Doc |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for entry in catalog["entries"]:
        doc = entry["documentation"]
        lines.append(
            f"| [`{entry['source_id']}`](../providers/{entry['source_id']}/README.md) "
            f"| {entry['lifecycle']} | `{entry['coverage_role']}` | "
            f"{entry['maturity_score']['total']} | "
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
        "contrato forte, baixo/medio risco, busca unificada, offline completo e "
        "documentacao estrutural completa |",
        "| `silver` | uso produtivo com cautela | contrato nivel 4+, busca unificada "
        "e evidencia offline; lacunas avancadas permanecem visiveis |",
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
            "## Como Ler O Gate Prata",
            "",
            "Itens de checklist ainda abertos aparecem no dossie e no score, mas nao "
            "bloqueiam automaticamente a camada `silver` quando nao representam "
            "uma omissao estrutural. Isso separa backlog de aprofundamento da "
            "ausencia de contrato minimo.",
            "Risco operacional alto, WAF, TLS, CAPTCHA, timeout e mudanca de "
            "contrato nunca viram resultado vazio e podem manter a fonte em `blocked`.",
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


def _render_maturity_score(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Maturity Score",
        "",
        GENERATED_NOTE,
        "",
        "O score traduz a maturidade tecnica de cada fonte em uma escala de 0 a 100.",
        "Ele nao substitui revisao humana, mas cria uma fila objetiva para engenharia,",
        "documentacao, QA, Studio, MCP e jurimetria.",
        "",
        "## Dimensoes",
        "",
        "| Dimensao | Peso | O que mede |",
        "| --- | ---: | --- |",
        "| Entrada | 20 | texto, filtros, paginacao e catalogos |",
        "| Saida | 25 | registros canonicos, campos juridicos, datas, trace e inteiro teor |",
        "| Confiabilidade | 20 | nivel de contrato, risco, live validation e bloqueios |",
        "| Documentacao | 20 | dossie, lacunas, pendencias e fixtures |",
        "| Produto/Jurimetria | 15 | busca unificada, MCP, Studio, CLI e dataset-ready |",
        "",
        "## Matriz",
        "",
        "| Fonte | Total | Entrada | Saida | Confiabilidade | Docs | Produto | Grau |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for entry in sorted(
        entries, key=lambda item: (-item["maturity_score"]["total"], item["source_id"])
    ):
        score = entry["maturity_score"]
        dims = score["dimensions"]
        lines.append(
            f"| `{entry['source_id']}` | {score['total']} | {dims['input']} | "
            f"{dims['output']} | {dims['reliability']} | {dims['documentation']} | "
            f"{dims['product']} | `{score['grade']}` |"
        )
    lines.extend(
        [
            "",
            "## Como Interpretar",
            "",
            "- `A`: referencia para demonstracao, Studio, MCP e coletas iniciais.",
            "- `B`: util, mas ainda precisa fechar lacunas antes de virar referencia nacional.",
            "- `C`: provider promissor, adequado para hardening e testes de contrato.",
            "- `D`: fonte mapeada ou contextual; nao deve liderar jurimetria ampla.",
            "",
            "Uma fonte de alto valor juridico pode ter score baixo se o acesso live, a",
            "paginacao, os filtros ou a documentacao ainda nao estiverem maduros.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_improvement_queue(entries: list[dict[str, Any]]) -> str:
    queue = sorted(
        entries,
        key=lambda item: (
            _priority_rank(item["development_priority"]),
            item["maturity_score"]["total"],
            item["source_id"],
        ),
    )
    lines = [
        "# Improvement Queue",
        "",
        GENERATED_NOTE,
        "",
        "Esta fila usa o catalogo consolidado para orientar a proxima rodada de",
        "amadurecimento dos providers. Ela privilegia fontes de jurisprudencia textual",
        "que ja participam da busca unificada, mas ainda possuem lacunas objetivas.",
        "",
        "| Ordem | Fonte | Prioridade | Score | Papel | Proxima acao |",
        "| ---: | --- | --- | ---: | --- | --- |",
    ]
    position = 1
    for entry in queue:
        if entry["development_priority"] == "P2_maintain":
            continue
        actions = entry["maturity_score"]["next_actions"]
        first_action = actions[0] if actions else "manter monitoramento"
        lines.append(
            f"| {position} | `{entry['source_id']}` | `{entry['development_priority']}` | "
            f"{entry['maturity_score']['total']} | `{entry['coverage_role']}` | {first_action} |"
        )
        position += 1
    lines.extend(
        [
            "",
            "## Regra De Execucao",
            "",
            "Para subir um provider na fila, feche primeiro o item mais objetivo: fixture,",
            "erro classificado, paginacao, campo canonico ou documentacao faltante. Depois",
            "regenere o catalogo e deixe o score mostrar a evolucao.",
        ]
    )
    return "\n".join(lines) + "\n"


def _parse_latest_live_validation() -> dict[str, dict[str, Any]]:
    structured = _parse_validation_runs()
    if structured:
        return structured
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


def _parse_validation_runs() -> dict[str, dict[str, Any]]:
    """Read the latest structured evidence for each provider from validation runs."""

    if not VALIDATION_RUNS_DIR.is_dir():
        return {}
    latest: dict[str, tuple[str, dict[str, Any]]] = {}
    for path in sorted(VALIDATION_RUNS_DIR.glob("*.json")):
        try:
            artifact = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        generated_at = str(artifact.get("generated_at") or artifact.get("checked_at") or "")
        reports = artifact.get("reports")
        if reports is None:
            # Live probes historically used `sources` for the same envelope
            # shape. Accept both spellings so valid evidence is not lost.
            reports = artifact.get("sources")
        if isinstance(reports, list):
            report_items = reports
        elif artifact.get("source"):
            # Document and provider-specific evidence may be stored as one
            # standalone report instead of a multi-source validation envelope.
            report_items = [artifact]
        else:
            report_items = []
        for report in report_items:
            if not isinstance(report, dict):
                continue
            checked_at = str(report.get("checked_at") or generated_at)
            source_value = report.get("source") or report.get("source_id")
            if not source_value:
                continue
            source_id = str(source_value)
            previous = latest.get(source_id)
            if previous is None or checked_at >= previous[0]:
                latest[source_id] = (checked_at, {**report, "_path": path})
    rows: dict[str, dict[str, Any]] = {}
    for source_id, (checked_at, report) in latest.items():
        path = report.pop("_path")
        rows[source_id] = {
            "status": report.get("status") or _status_from_evidence(report),
            "scope": report.get("scope"),
            "date": checked_at[:10] or None,
            "checked_at": checked_at or None,
            "document_id": report.get("document_id"),
            "url": report.get("url"),
            "returned": report.get("returned"),
            "reported_total": report.get("reported_total"),
            "pagination_mode": report.get("pagination_mode"),
            "requested_page_size": report.get("requested_page_size"),
            "effective_page_size": report.get("effective_page_size"),
            "latency": report.get("elapsed_ms"),
            "http_status": report.get("http_status"),
            "access_status": report.get("access_status"),
            "retrieval_status": report.get("retrieval_status"),
            "extraction_status": report.get("extraction_status"),
            "full_text_status": report.get("full_text_status"),
            "content_type": report.get("content_type"),
            "content_sha256": report.get("content_sha256"),
            "sha256": report.get("sha256") or report.get("content_sha256"),
            "response_bytes": report.get("response_bytes"),
            "parser": report.get("parser"),
            "parser_version": report.get("parser_version"),
            "note": report.get("message") or report.get("completeness_reason") or "",
            "error_type": report.get("error_type"),
            "evidence": _evidence_path(path),
        }
    return rows


def _status_from_evidence(report: dict[str, Any]) -> str:
    """Classify standalone evidence when its producer omitted a summary status."""

    access_status = str(report.get("access_status") or "")
    retrieval_status = str(report.get("retrieval_status") or "")
    extraction_status = str(report.get("extraction_status") or "")
    if access_status in {"access_control_required", "login_required", "rate_limited"}:
        return access_status
    if retrieval_status in {"source_unavailable", "timeout", "error"}:
        return "source_unavailable"
    if retrieval_status == "ok" and extraction_status in {"complete", "partial"}:
        return "valid"
    return "unknown"


def _evidence_path(path: Path) -> str:
    """Return a stable repository path, or an absolute path for test fixtures."""

    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


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


def _identity(source_id: str, capability: Any | None) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "display_name": getattr(capability, "display_name", _display_name(source_id)),
        "source_url": getattr(capability, "source_url", None),
        "category": getattr(capability, "category", "research_candidate"),
    }


def _implementation_status(lifecycle: str) -> str:
    return {"implemented": "runtime", "candidate": "none", "family": "family"}.get(
        lifecycle, "unknown"
    )


def _offline_status(lifecycle: str, doc: dict[str, Any]) -> str:
    if lifecycle != "implemented":
        return "not_applicable"
    fixture_count = len(doc.get("fixture_references", []))
    if fixture_count >= 3 and not doc.get("missing_sections"):
        return "complete"
    if fixture_count:
        return "partial"
    return "missing"


def _document_contract(capability: Any | None) -> dict[str, Any]:
    output = _output_contract(capability)
    return {
        "supports_full_text": output["supports_full_text"],
        "document_types": output["document_types"],
        "content_formats": output["content_formats"],
        "trace_expected": output["trace_expected"],
        "full_text_access": getattr(capability, "full_text_access", "unknown"),
    }


def _pagination_contract(capability: Any | None) -> dict[str, Any]:
    return {
        "mode": getattr(capability, "pagination_mode", "unknown"),
        "declared": getattr(capability, "pagination_mode", "unknown") != "unknown",
        "max_remote_page": getattr(capability, "max_remote_page", None),
        "max_remote_page_size": getattr(capability, "max_remote_page_size", None),
    }


def _error_contract(capability: Any | None, contract: Any | None) -> dict[str, Any]:
    return {
        "access_statuses": [
            getattr(status, "value", status)
            for status in getattr(capability, "access_statuses", [])
        ],
        "risk_level": getattr(contract, "risk_level", "research"),
        "limitations": list(getattr(capability, "limitations", [])),
    }


def _quality_contract(doc: dict[str, Any], live_status: dict[str, Any]) -> dict[str, Any]:
    return {
        "documentation_readiness": doc.get("readiness", "missing"),
        "fixture_references": len(doc.get("fixture_references", [])),
        "latest_live_status": live_status["status"],
        "quality_flags": [
            item
            for item in [
                "documentation_incomplete" if doc.get("missing_sections") else "",
                "open_documentation_items" if doc.get("unchecked", 0) else "",
                "live_not_recently_checked"
                if live_status["status"] == "not_checked_in_latest_focused_run"
                else "",
            ]
            if item
        ],
    }


def _known_defects(
    entry: dict[str, Any], doc: dict[str, Any], contract: Any | None, live_status: dict[str, Any]
) -> list[str]:
    defects = list(doc.get("missing_sections", []))
    if doc.get("unchecked", 0):
        defects.append("documentacao_com_pendencias_abertas")
    if live_status["status"] not in {"valid", "empty"}:
        defects.append(f"live:{live_status['status']}")
    if contract is not None:
        defects.extend(f"gap:{gap}" for gap in getattr(contract, "gaps", [])[:3])
    return defects


def _recommended_for(entry: dict[str, Any], contract: Any | None) -> list[str]:
    role = entry["coverage_role"]
    recommendation = getattr(contract, "jurimetry_fit", "")
    values = ["agent_assisted_research"] if entry["interfaces"]["mcp"] else []
    if role == "primary_textual_jurisprudence":
        values.extend(["textual_legal_research", "jurimetry"])
    elif role in {"precedent_context", "curated_context"}:
        values.append("contextual_legal_research")
    if "alto" in recommendation:
        values.append("structured_data_analysis")
    return values


def _not_recommended_for(entry: dict[str, Any], live_status: dict[str, Any]) -> list[str]:
    values: list[str] = []
    if entry["coverage_role"] != "primary_textual_jurisprudence":
        values.append("broad_textual_jurimetry")
    if live_status["status"] in {"blocked", "source_unavailable", "source_changed"}:
        values.append("unattended_live_collection")
    if not entry["document_contract"]["supports_full_text"]:
        values.append("full_text_only_research")
    return values


def _interface_contract(entry: dict[str, Any], name: str) -> dict[str, Any]:
    enabled = bool(entry["interfaces"][name])
    return {
        "enabled": enabled,
        "status": "declared" if enabled else "not_exposed",
        "limitations": entry["error_contract"]["limitations"],
    }


def _snapshot_date() -> str:
    """Return a stable coverage snapshot date for generated docs."""

    if CATALOG_PATH.is_file():
        try:
            existing = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        generated_at = existing.get("generated_at")
        if isinstance(generated_at, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", generated_at):
            return generated_at
    return date.today().isoformat()


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
        "text_query": bool(set(capability.search_modes) & TEXTUAL_SEARCH_MODES),
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
    # Open checklist items are an improvement backlog, not automatically a
    # contract failure. Structural omissions remain a hard documentation gate.
    has_structural_doc_gap = bool(doc.get("missing_sections"))
    live = live_status["status"]
    if live in {
        "blocked",
        "source_unavailable",
        "access_control_required",
        "captcha_detected",
        "waf_detected",
        "tls_verification_failed",
    }:
        return "blocked"
    if capability.category not in {"court_jurisprudence", "administrative_jurisprudence"}:
        return "context"
    if (
        level >= 5
        and risk in {"baixo", "medio"}
        and capability.supports_unified_search
        and _offline_status(lifecycle, doc) == "complete"
    ):
        return "silver" if has_structural_doc_gap else "gold"
    if (
        level >= 4
        and capability.supports_unified_search
        and _offline_status(lifecycle, doc) in {"partial", "complete"}
    ):
        return "silver"
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
    serialized = (
        json.dumps(_normalize(catalog), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    CATALOG_PATH.write_text(serialized, encoding="utf-8")
    PACKAGE_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    PACKAGE_CATALOG_PATH.write_text(serialized, encoding="utf-8")
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
