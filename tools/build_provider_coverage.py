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
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(1, str(ROOT))

from nanojuris.client import NanoJurisClient  # noqa: E402
from tools.audit_provider_docs import audit as audit_provider_docs  # noqa: E402

REGISTRY_PATH = ROOT / "docs" / "registry" / "providers.json"
CATALOG_PATH = ROOT / "docs" / "registry" / "provider-catalog.full.json"
PACKAGE_CATALOG_PATH = ROOT / "src" / "nanojuris" / "data" / "provider-catalog.full.json"
COVERAGE_DIR = ROOT / "docs" / "coverage"
LATEST_LIVE_PATH = ROOT / "docs" / "live-validation-2026-08-15.md"
VALIDATION_RUNS_DIR = ROOT / "docs" / "validation" / "runs"
DEDICATED_LIVE_PATHS = (
    ROOT / "docs" / "provider-discovery" / "cjf-trf1-live-recheck-20260901-cycle8.json",
    ROOT / "docs" / "provider-discovery" / "stf-juris-live-recheck-20260901-cycle9.json",
    ROOT / "docs" / "provider-discovery" / "tjpe-live-recheck-20260901-cycle10.json",
    ROOT / "docs" / "provider-discovery" / "tjpe-cjsg-jsf-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjsp-cjsg-detail-continuation-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjsp-cjsg-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjms-cjpg-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjap-banco-sentencas-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjsp-cjsg-live-recheck-20260901-cycle11.json",
    ROOT / "docs" / "provider-discovery" / "esaj-juscraper-flow-live-recheck-20260902-cycle12.json",
    ROOT / "docs" / "provider-discovery" / "tjes-cjpg-live-20260901.json",
    ROOT / "docs" / "provider-discovery" / "tjsp-cjpg-live-20260901.json",
    ROOT / "docs" / "provider-discovery" / "tjto-cjpg-live-20260901.json",
    ROOT / "docs" / "provider-discovery" / "tjro-jurisprudencia-live-20260902-cycle14.json",
    ROOT / "docs" / "provider-discovery" / "tjro-jurisprudencia-live-20260902-cycle15.json",
    ROOT
    / "docs"
    / "provider-discovery"
    / "tjro-jurisprudencia-federated-live-20260902-cycle16.json",
    ROOT / "docs" / "provider-discovery" / "tjrn-jurisprudencia-live-20260902-cycle17.json",
    ROOT / "docs" / "provider-discovery" / "tjto-jurisprudencia-detail-live-20260902-cycle18.json",
    ROOT / "docs" / "provider-discovery" / "tjto-cjsg-live-20260906-cycle56.json",
    ROOT / "docs" / "provider-discovery" / "tjto-cjpg-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjto-cjpg-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjgo-cjpg-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjes-jurisprudencia-live-20260902-cycle19.json",
    ROOT / "docs" / "provider-discovery" / "degree-bindings-live-20260902-cycle26.json",
    ROOT / "docs" / "provider-discovery" / "tjrn-jurisprudencia-live-20260905-cycle27.json",
    ROOT / "docs" / "provider-discovery" / "tjrn-jurisprudencia-live-20260905-cycle28.json",
    ROOT / "docs" / "provider-discovery" / "tjro-tjgo-live-20260905-cycle32.json",
    ROOT / "docs" / "provider-discovery" / "tjes-turma-recursal-live-20260905-cycle34.json",
    ROOT / "docs" / "provider-discovery" / "tjgo-projudi-live-20260905-cycle36.json",
    ROOT / "docs" / "provider-discovery" / "tjgo-cjsg-live-20260906-cycle58.json",
    ROOT / "docs" / "provider-discovery" / "tjgo-projudi-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjpi-juspi-live-20260905-cycle38.json",
    ROOT / "docs" / "provider-discovery" / "tst-live-20260905-cycle46.json",
    ROOT / "docs" / "provider-discovery" / "tst-live-20260907-cycle60.json",
    ROOT / "docs" / "provider-discovery" / "cjsg-live-20260905-cycle51.json",
    ROOT / "docs" / "provider-discovery" / "tjsc-eproc-live-20260905-cycle54.json",
    ROOT / "docs" / "provider-discovery" / "tjpb-pje-live-20260905-cycle55.json",
    ROOT / "docs" / "provider-discovery" / "tjrr-live-20260905-cycle57.json",
    ROOT / "docs" / "provider-discovery" / "tjrr-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjap-banco-sentencas-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjam-cjsg-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjam-cjsg-detail-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "stm-live-20260905-cycle58.json",
    ROOT / "docs" / "provider-discovery" / "stm-live-20260907-cycle59.json",
    ROOT / "docs" / "provider-discovery" / "stm-live-20260908-cycle70.json",
    ROOT / "docs" / "provider-discovery" / "bnp-pangea-live-20260905-cycle59.json",
    ROOT / "docs" / "provider-discovery" / "tjpa-bff-live-20260905-cycle60.json",
    ROOT / "docs" / "provider-discovery" / "trf4-live-20260905-cycle61.json",
    ROOT / "docs" / "provider-discovery" / "trf4-live-20260907-cycle62.json",
    ROOT / "docs" / "provider-discovery" / "trf4-live-20260908-cycle71.json",
    ROOT / "docs" / "provider-discovery" / "trf5-live-20260907-cycle45.json",
    ROOT / "docs" / "provider-discovery" / "trf5-live-20260908-cycle72.json",
    ROOT / "docs" / "provider-discovery" / "eproc-detail-live-20260908-cycle73.json",
    ROOT / "docs" / "provider-discovery" / "stj-live-20260908-cycle74.json",
    ROOT / "docs" / "provider-discovery" / "eproc-detail-live-20260908-cycle75.json",
    ROOT / "docs" / "provider-discovery" / "federal-eproc-detail-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "document-qa-cycle-20260907-batch09.json",
    ROOT / "docs" / "provider-discovery" / "document-qa-cycle-20260907-batch10.json",
    ROOT / "docs" / "provider-discovery" / "tjsp-eproc-live-20260905-cycle63.json",
    ROOT / "docs" / "provider-discovery" / "tjal-turma-recursal-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjal-esmal-banco-sentencas-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjal-esmal-banco-sentencas-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tjmg-ejef-boletim-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjrj-ejuris-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjrj-ejuris-pagination-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "tjse-jurisprudencia-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "cnj-live-20260905-cycle64.json",
    ROOT / "docs" / "provider-discovery" / "tjro-liame-live-20260905-cycle66.json",
    ROOT / "docs" / "provider-discovery" / "tjrn-cjsg-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjrr-cjsg-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjro-cjsg-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tce-sp-document-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "stj-informativo-cnot-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "stj-open-data-catalog-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "stj-open-data-zip-contract-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "justica-eleitoral-sjur-catalog-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "inline-document-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "cjsg-live-recheck-20260906.json",
    ROOT / "docs" / "provider-discovery" / "cjsg-live-20260908-cycle67.json",
    ROOT / "docs" / "provider-discovery" / "state-cjsg-live-20260908-cycle68.json",
    ROOT / "docs" / "provider-discovery" / "federated-promotion-live-20260906-current.json",
    ROOT / "docs" / "provider-discovery" / "juscraper-captcha-boundary-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjma-jurisprudencia-captcha-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjse-boletim-jurisprudencia-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "tjse-boletim-jurisprudencia-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjmg-dspace-jurisprudencia-live-20260906.json",
    ROOT / "docs" / "provider-discovery" / "cjsg-live-legitimate-recheck-20260906.json",
    ROOT
    / "docs"
    / "provider-discovery"
    / "federated-promotion-live-20260906-legitimate-recheck.json",
    ROOT / "docs" / "provider-discovery" / "falcao-api-search-live-20260911.json",
    ROOT / "docs" / "provider-discovery" / "state-eproc-degree-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "state-eproc-degree-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "state-cjsg-blocked-recheck-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjmg-modern-api-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "tjmg-modern-api-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjmg-modern-api-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjmg-modern-api-document-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjce-cjsg-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tjce-cjsg-detail-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "trt2-ementario-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjma-informativos-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjsp-nugepnac-catalog-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "trt2-basis-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "trf3-jurisprudencia-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "trt2-ementario-live-20260907.json",
    ROOT / "docs" / "provider-discovery" / "state-b1-live-20260908-cycle69.json",
    ROOT / "docs" / "provider-discovery" / "state-b1-live-20260908-cycle70.json",
    ROOT / "docs" / "provider-discovery" / "tjrj-banco-sentencas-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "trf3-exact-process-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjac-ementario-live-20260908.json",
    ROOT / "docs" / "provider-discovery" / "tjac-banco-sentencas-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "bnp-pangea-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "trf3-jurisprudencia-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tse-sjur-search-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tse-sjur-empty-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tse-sjur-pagination-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tse-sjur-document-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "gold-document-probe-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tjms-cjpg-transport-detail-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tjes-cjpg-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "trt8-pje-jurisprudencia-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tjmrs-jurisprudencia-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tjm-mg-jurisprudencia-api-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tjm-mg-jurisprudencia-api-live-20260911.json",
    ROOT / "docs" / "provider-discovery" / "tjmsp-jurisprudencia-live-recheck-20260910.json",
    ROOT / "docs" / "provider-discovery" / "trf3-jurisprudencia-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "trt6-jurisprudencia-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "trt6-legacy-search-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "trt2-pje-jurisprudencia-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "trt3-ementario-live-20260909.json",
    ROOT / "docs" / "provider-discovery" / "tre-sp-sjur-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "trt9-nugepnac-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "trt4-sumulas-live-20260910.json",
    ROOT / "docs" / "provider-discovery" / "tjce-sjuris-live-20260910-continue.json",
    ROOT / "docs" / "provider-discovery" / "tjgo-projudi-live-20260910-continue.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-type-filter-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-large-window-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-pagination-recheck-20260912.json",
    ROOT
    / "docs"
    / "provider-discovery"
    / "tre-sjur-pagination-parameter-recheck-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-pagination-recheck-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tre-sp-sjur-document-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-sp-sjur-date-partition-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-sp-sjur-date-partition-year-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-date-partition-uf-sweep-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-date-partition-uf-sweep-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-document-uf-sweep-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tre-sjur-first-degree-sweep-live-20260913.json",
    ROOT / "docs" / "provider-discovery" / "tre-mg-first-degree-live-20260913.json",
    ROOT
    / "docs"
    / "provider-discovery"
    / "tre-sjur-first-degree-date-partition-uf-sweep-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tre-mg-first-degree-date-partition-live-20260912.json",
    ROOT / "docs" / "provider-discovery" / "tse-sjur-scope-contract-live-20260912.json",
)

# Candidate/family entries do not have a runtime capability object, but their
# official landing routes are still known from the source dossiers.  Keeping
# these URLs in the catalog makes discovery actionable without implying that a
# contract or live result has been proven.
CANDIDATE_SOURCE_URLS: dict[str, tuple[str, ...]] = {
    "eproc_jurisprudencia_federal": (
        "https://eproctnu.cjf.jus.br/eproc/externo_controlador.php?acao="
        "jurisprudencia@jurisprudencia/pesquisar",
        "https://eproc.trf2.jus.br/eproc/externo_controlador.php?acao="
        "jurisprudencia@jurisprudencia/pesquisar",
        "https://eproc-jur.trf6.jus.br/eproc/externo_controlador.php?acao="
        "jurisprudencia@jurisprudencia/pesquisar",
    ),
    "falcao_jt": ("https://jurisprudencia.jt.jus.br/",),
    "trt2_pje_jurisprudencia": ("https://pje.trt2.jus.br/jurisprudencia/",),
    "trt6_jurisprudencia": (
        "https://pje.trt6.jus.br/jurisprudencia/",
        "https://apps.trt6.jus.br/acordaos/",
    ),
    "tre_sjur_jurisprudencia": ("https://jurisprudencia-tres.tse.jus.br/",),
    "tre_sjur_first_degree": ("https://jurisprudencia-tres.tse.jus.br/",),
    "trt8_pje_jurisprudencia": ("https://pje.trt8.jus.br/jurisprudencia/",),
}

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
        "degree",
        "instance",
        "branch",
        "legal_area",
        "authority",
        "collection",
        "document_type",
    },
    "actors": {
        "rapporteur",
        "judging_body",
        "origin_county",
        "authority",
        "party",
        "parties",
        "lawyer",
    },
    "dates": {
        "judgment_date",
        "publication_date",
        "published_at",
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

# Electoral courts exposed by the official TSE SJUR family.  Keep this list
# local to the catalog builder so generated metadata remains deterministic and
# does not depend on importing the network-facing provider module.
TRE_UFS = (
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
)


def build_catalog() -> dict[str, Any]:
    """Return the consolidated provider coverage catalog."""

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    client = NanoJurisClient()
    # Keep the default runtime count authoritative, but expose capabilities
    # for candidates that have an explicit, safe opt-in constructor path.
    # Otherwise the catalog would report a real candidate adapter as if it had
    # no interface at all, creating a runtime/catalog divergence.
    candidate_client = NanoJurisClient(include_candidate_providers=True)
    capabilities = {item.source: item for item in client.list_sources()}
    capabilities.update({item.source: item for item in candidate_client.list_sources()})
    contracts = {item.source: item for item in client.list_source_contracts()}
    contracts.update({item.source: item for item in candidate_client.list_source_contracts()})
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
            # A candidate may already have a safe opt-in adapter.  Keep this
            # orthogonal to lifecycle so the catalog does not claim default
            # federation merely because a diagnostic binding exists.
            "runtime_binding": capability is not None,
            "runtime_binding_status": (
                "available_default"
                if lifecycle == "implemented" and capability is not None
                else "available_opt_in"
                if lifecycle == "candidate" and capability is not None
                else "none"
            ),
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
            # Keep transport/access health separate from corpus completeness.
            # A public bounded window can be useful while still lacking a
            # trustworthy remote pagination contract (notably SJUR/TRE).
            "live_dimensions": _live_dimensions(live_status),
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
        entry.update(_surface_metadata(source_id, capability, contract, entry, live_status))
        entries.append(entry)

    return {
        "schema_version": "1.0",
        "generated_at": _snapshot_date(),
        "quality_evaluation": {
            "schema": "docs/schemas/provider-quality.schema.json",
            "report": "docs/quality/provider-quality.json",
            "command": "python tools/build_provider_quality.py --write",
            "network_required": False,
        },
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
        "runtime_bindings": sum(1 for entry in entries if entry["runtime_binding"]),
        "opt_in_runtime_bindings": sum(
            1 for entry in entries if entry["runtime_binding_status"] == "available_opt_in"
        ),
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
    live_state = str(live_status.get("status") or "").casefold()
    access_blocked_states = {
        "access_control_required",
        "access_controlled",
        "blocked",
        "blocked_access_control_no_reproducible_result",
        "login_required",
        "rate_limited",
    }
    # Candidate adapters may already have a parser, fixtures and a safe
    # diagnostic entry point.  When the authoritative route is challenge- or
    # access-gated, asking the next engineer to "reproduce the HTTP contract"
    # is misleading and encourages repeated probes.  Keep the remaining work
    # explicitly external until the source publishes an approved route or an
    # operator supplies a legitimate, bounded authorization flow.
    if entry["lifecycle"] != "implemented":
        if live_state in access_blocked_states:
            actions.append(
                "aguardar rota publica/alternativa oficial ou autorizacao humana bounded; "
                "nao repetir nem contornar o bloqueio"
            )
        else:
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


def _surface_metadata(
    source_id: str,
    capability: Any | None,
    contract: Any | None,
    entry: dict[str, Any],
    live_status: dict[str, Any],
) -> dict[str, Any]:
    """Attach the auditable identity and ownership fields for one provider.

    These values intentionally distinguish what is known from what is not.  A
    provider name such as ``tjxx_jurisprudencia`` is not enough to assert a
    degree or collection, so the corresponding dimensions remain ``unknown``
    unless the provider identity contains an explicit, stable marker.
    """

    authority = _surface_authority(source_id)
    branch = _surface_branch(source_id)
    degree, instance, collection = _surface_scope(source_id, capability, contract)
    document_scope = str(getattr(capability, "category", "provider"))
    surface_id = "/".join(
        (authority, branch, degree, instance, collection, document_scope, source_id)
    )
    evidence_ids = _surface_evidence_ids(source_id, entry, live_status)
    live_is_fresh = live_status.get("status") in {"valid", "empty"}
    metadata = {
        "surface_id": surface_id,
        "owner": "team:provider-engineering",
        "next_action": entry["maturity_score"]["next_actions"][0],
        "evidence_ids": evidence_ids,
        "evidence_ttl": 30 if live_is_fresh else 7,
        "evidence_ttl_days": 30 if live_is_fresh else 7,
        "surface_identity": {
            "authority": authority,
            "branch": branch,
            "degree": degree,
            "instance": instance,
            "collection": collection,
            "document_scope": document_scope,
        },
    }
    # The TSE SJUR adapter is one official family whose runtime constructor
    # materializes one scoped binding per state electoral court.  Those
    # ``tre_<uf>_sjur_*`` names are operational instances, not independent
    # catalog providers; recording the expansion here keeps the canonical
    # provider count stable while making the runtime/catalog relationship
    # auditable to tooling and operators.
    if source_id in {"tre_sjur_jurisprudencia", "tre_sjur_first_degree"}:
        suffix = "jurisprudencia" if source_id.endswith("jurisprudencia") else "first_degree"
        metadata["runtime_expansion"] = {
            "kind": "scoped_family_instances",
            "factory": "nanojuris.providers.tre_sjur_jurisprudencia",
            "instance_pattern": f"tre_<uf>_sjur_{suffix}",
            "authorities": [f"TRE-{uf}" for uf in TRE_UFS],
            "instance_count": len(TRE_UFS),
            "catalog_identity": source_id,
            "federation_default": False,
            "reason": (
                "instancias por UF permanecem diagnosticas ate que cada rota "
                "feche paginacao, documentos e fixtures"
            ),
        }
    return metadata


def _surface_authority(source_id: str) -> str:
    # The CJF-hosted adapter is specifically the TRF1 jurisprudence surface,
    # not an implementation of the aggregate CJF search.  Keep the provider
    # name for compatibility while exposing the canonical judicial authority
    # used by the national coverage matrix.
    if source_id == "cjf_jurisprudencia":
        return "TRF1"
    if source_id.startswith("justica_eleitoral"):
        return "JUSTICA-ELEITORAL"
    if source_id == "eproc_jurisprudencia_federal":
        return "EPROC-FEDERAL"
    if source_id == "falcao_jt":
        return "FALCAO-JT"
    if source_id == "tre_sp_temas":
        return "TRE-SP"
    if source_id.startswith("tce_"):
        parts = source_id.split("_")
        return "-".join(parts[:2]).upper()
    return source_id.split("_")[0].upper()


def _surface_branch(source_id: str) -> str:
    if source_id.startswith("tce_"):
        return "control"
    if source_id in {
        "tjmmg_jurisprudencia_api",
        "tjmmg_jurisprudencia",
        "tjmrs_jurisprudencia",
        "tjmsp_jurisprudencia",
    }:
        return "military"
    if source_id.startswith("tj"):
        return "state"
    if source_id.startswith(("trf", "cjf", "eproc_")):
        return "federal"
    if source_id.startswith(("trt", "tst")) or source_id == "falcao_jt":
        return "labor"
    if source_id.startswith(("tre_", "tse_")) or source_id.startswith("justica_eleitoral"):
        return "electoral"
    if source_id == "tcu_jurisprudencia":
        return "accounts"
    if source_id in {
        "stf_juris",
        "stf_informativo",
        "stj_scon",
        "stj_informativo",
        "stm_jurisprudencia",
    }:
        return "superior"
    if source_id in {"cnj_jurisprudencia", "bnp_pangea"}:
        return "national"
    return "unknown"


def _surface_scope(
    source_id: str,
    capability: Any | None,
    contract: Any | None,
) -> tuple[str, str, str]:
    del contract
    # Some providers expose a collection-specific surface without encoding
    # the collection name in their source id.  Keep this mapping explicit so
    # the catalog cannot erase a proven degree/instance contract merely
    # because the provider uses a descriptive name.
    if source_id == "tjap_banco_sentencas":
        return "first", "first", "CJPG"
    if source_id == "tjac_banco_sentencas":
        return "first", "first", "CJPG"
    if source_id == "cjf_jurisprudencia":
        return "second", "second", "JURISPRUDENCIA"
    if source_id == "tjac_ementario_jurisprudencia":
        return "second", "second", "TJAC_EMENTARIO"
    if source_id == "tjal_esmal_banco_sentencas":
        return "first", "first", "TJAL_ESMAL_CJPG"
    if source_id == "tjal_turma_recursal_ementario":
        return "recursal", "turma_recursal", "TJAL_TURMAS_RECURSAIS"
    if source_id == "tjrj_banco_sentencas":
        return "first", "first", "TJRJ_BANCO_SENTENCAS"
    if source_id == "tjmrs_jurisprudencia":
        return "second", "second", "TJMRS_JURISPRUDENCIA"
    if source_id == "tjma_jurisconsult":
        # JurisConsult exposes the official TJMA appellate result routes
        # (including ``pesquisa_acordaos_tr``), but automated execution is
        # gated by the court's human CAPTCHA flow.  Record the scope that the
        # authorized parser already enforces so diagnostics do not lose the
        # CJSG identity merely because the provider is catalog-oriented.
        # This does not promote the source: ``supports_unified_search`` stays
        # false and the live status remains access-controlled.
        return "second", "second", "CJSG"
    if source_id in {"tjmmg_jurisprudencia_api", "tjmsp_jurisprudencia"}:
        return "second", "second", "PORTAL"
    if source_id in {"tjrj_ejuris", "tjrn_jurisprudencia", "tjse_jurisprudencia"}:
        return "second", "second", "CJSG"
    if source_id == "trt2_ementario_jurisprudencia":
        return "second", "second", "TRT2_EMENTARIO"
    if source_id == "trt2_basis_jurisprudencia":
        return "second", "second", "CJSG_CURATED_BULLETIN"
    if source_id == "tjmg_dspace_jurisprudencia":
        return "second", "second", "CJSG_DSPACE"
    if source_id in {"tjse_boletim_jurisprudencia", "tjce_sjuris"}:
        collection = "INFORMATIVO" if source_id.startswith("tjse_") else "SJUR"
        return "second", "second", collection
    if source_id == "tre_sjur_first_degree":
        return "first", "first", "SJUR"
    if source_id == "tre_sjur_jurisprudencia":
        # The TRE family binding is explicitly restricted to appellate
        # decision labels (acórdão, decisão monocrática, resolução and the
        # equivalent).  Keep that proven second-degree scope in the catalog;
        # pagination/completeness remain separate promotion gates.
        return "second", "second", "SJUR"
    if source_id == "tse_sjur_jurisprudencia":
        # The public TSE route is permanently scoped to the superior electoral
        # court.  Keep that scope in the generated catalog instead of leaving
        # it as unknown merely because the provider name does not contain
        # ``cjsg`` or ``eproc``.
        return "superior", "superior", "SJUR"
    if "cjpg" in source_id:
        return "first", "first", "CJPG"
    if "cjsg" in source_id:
        return "second", "second", "CJSG"
    if "sjur" in source_id:
        return "unknown", "unknown", "SJUR"
    if "eproc" in source_id:
        collection = "EPROC"
    elif "informativo" in source_id or "boletim" in source_id:
        collection = "INFORMATIVO"
    elif "nugepnac" in source_id:
        collection = "NUGEP"
    elif "scon" in source_id:
        collection = "SCON"
    elif "pangea" in source_id:
        collection = "PANGEA"
    else:
        collection = str(getattr(capability, "category", "provider")).upper()
    return "unknown", "unknown", collection


def _surface_evidence_ids(
    source_id: str,
    entry: dict[str, Any],
    live_status: dict[str, Any],
) -> list[str]:
    candidates = [
        f"docs/providers/{source_id}/README.md",
        f"docs/source-contracts/{source_id}.md",
    ]
    evidence = live_status.get("evidence") or live_status.get("evidence_id")
    if evidence:
        candidates.insert(0, str(evidence))
    return [item for item in candidates if (ROOT / item).is_file()]


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
        "| Qual e o estado de fechamento das ondas tecnicas? | "
        "[../operations/"
        "wave-implementation-20260902.md](../operations/wave-implementation-20260902.md) |",
        "| Qual e o roadmap executavel para CJPG/CJSG? | "
        "[degree-coverage-roadmap-20260902.md](degree-coverage-roadmap-20260902.md) |",
        "| Qual e o mapa completo de lacunas por superficie, incluindo fontes "
        "com pouca informacao? | "
        "[national-coverage-gap-map-20260908.md](national-coverage-gap-map-20260908.md) e "
        "[national-coverage-gap-map-20260908.json](national-coverage-gap-map-20260908.json) |",
        "| Quais tecnicas de acesso publico sao permitidas e quais sao proibidas? | "
        "[public-access-boundary-playbook-20260908.md]("
        "public-access-boundary-playbook-20260908.md) e "
        "[public-access-boundary-playbook-20260908.json]("
        "public-access-boundary-playbook-20260908.json) |",
        "| Qual catalogo uma IA deve ler? | "
        "[../registry/provider-catalog.full.json](../registry/provider-catalog.full.json) |",
        "| Qual pacote autonomo deve ser seguido para fechar a cobertura nacional? | "
        "[national-coverage-gold-handoff-20260908.md]("
        "national-coverage-gold-handoff-20260908.md) e "
        "[SDD 0091](../../specs/changes/0091-national-coverage-gold-handoff/) |",
        "| Qual é o inventário atual de tarefas e decisões de baixo risco? | "
        "[low-risk-decision-register-20260909.md](low-risk-decision-register-20260909.md) "
        "e [open-task-audit-current.json](open-task-audit-current.json) |",
        "| Qual foi o último ciclo de reconciliação técnica? | "
        "[reconciliation-cycle-20260909.md](reconciliation-cycle-20260909.md) |",
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
        "Busca Unificada | Opt-in | Inteiro Teor | Doc |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |",
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
            f"| {_yes(entry['interfaces']['opt_in_unified_search'])} "
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
    rows = dict(structured)
    if not rows and LATEST_LIVE_PATH.is_file():
        text = LATEST_LIVE_PATH.read_text(encoding="utf-8")
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
    for path in DEDICATED_LIVE_PATHS:
        _merge_dedicated_live(rows, path)
    # The marker is only used while merging append-only evidence and is not a
    # public catalog field.
    for row in rows.values():
        row.pop("_dedicated_evidence_date", None)
    return rows


def _merge_dedicated_live(rows: dict[str, dict[str, Any]], path: Path) -> None:
    """Join a provider-specific bounded check without retaining its body."""

    if not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    # The TRE type-filter probe is intentionally an aggregate artifact: one
    # bounded, redacted report per UF, with no provider-shaped ``source_id``
    # in each child row.  Reconcile it once at the family level so the live
    # ledger reflects the observed first-degree route without pretending that
    # every UF has a non-empty corpus or that pagination is complete.
    if path.name == "tre-sjur-type-filter-live-20260912.json":
        _merge_tre_type_filter_probe(rows, payload, path)
        return
    if path.name == "tre-sjur-large-window-live-20260912.json":
        _merge_tre_large_window_probe(rows, payload, path)
        return
    if path.name == "tre-sjur-pagination-recheck-20260912.json":
        _merge_tre_pagination_recheck(rows, payload, path)
        return
    if path.name == "tre-sjur-pagination-parameter-recheck-live-20260912.json":
        _merge_tre_pagination_recheck(rows, payload, path)
        return
    if path.name.startswith("tre-sjur-pagination-recheck-live-"):
        _merge_tre_pagination_recheck(rows, payload, path)
        return
    if path.name == "tre-sp-sjur-document-live-20260912.json":
        _merge_tre_document_probe(rows, payload, path)
        return
    if path.name in {
        "tre-sp-sjur-date-partition-live-20260912.json",
        "tre-sp-sjur-date-partition-year-live-20260912.json",
    }:
        _merge_tre_date_partition_probe(rows, payload, path)
        return
    if path.name.startswith("tre-sjur-date-partition-uf-sweep-live-"):
        _merge_tre_uf_sweep_probe(rows, payload, path)
        return
    if path.name.startswith("tre-sjur-document-uf-sweep-live-"):
        _merge_tre_document_uf_sweep(rows, payload, path)
        return
    if path.name == "tre-sjur-first-degree-sweep-live-20260913.json":
        _merge_tre_first_degree_text_sweep(rows, payload, path)
        return
    if path.name == "tre-mg-first-degree-live-20260913.json":
        _merge_tre_first_degree_sample(rows, payload, path)
        return
    if path.name == "tjam-cjsg-detail-live-20260913.json":
        _merge_tjam_detail_probe(rows, payload, path)
        return
    if path.name == "tjce-cjsg-detail-live-20260913.json":
        _merge_tjce_detail_probe(rows, payload, path)
        return
    if path.name in {
        "tre-sjur-first-degree-date-partition-uf-sweep-live-20260912.json",
        "tre-mg-first-degree-date-partition-live-20260912.json",
    }:
        _merge_tre_first_degree_partition_probe(rows, payload, path)
        return
    reports = payload.get("results", [])
    if not isinstance(reports, list):
        reports = []
    # Provider-specific smoke tools may emit one standalone report instead of
    # the multi-surface ``results`` envelope.  Accept both shapes so a valid
    # live check cannot be lost merely because it covers one source.
    if not reports and (
        payload.get("source") or payload.get("source_id") or payload.get("provider")
    ):
        reports = [payload]
    # Newer bounded probes keep the redacted transport facts in a nested
    # ``search`` object (and optionally a separate ``detail`` object).  Flatten
    # that envelope here so evidence remains consumable by the append-only
    # catalog merger without persisting request bodies or document contents.
    # A nested search is the provider health signal; detail metadata can enrich
    # extraction status but must never replace the primary search surface.
    if (
        len(reports) == 1
        and isinstance(reports[0], dict)
        and isinstance(reports[0].get("search"), dict)
    ):
        report = reports[0]
        search = report["search"]
        detail = report.get("detail")
        detail = detail if isinstance(detail, dict) else {}
        http_status = search.get("http_status")
        returned = search.get("record_count_observed")
        if returned is None:
            returned = search.get("result_count")
        total = search.get("reported_total")
        classification = str(report.get("classification") or "")
        if not classification:
            if isinstance(http_status, int) and http_status in {401, 403}:
                classification = "access_control_required"
            elif isinstance(http_status, int) and http_status == 429:
                classification = "rate_limited"
            elif isinstance(http_status, int) and http_status >= 500:
                classification = "source_unavailable"
            elif http_status == 200 and isinstance(returned, int) and returned > 0:
                classification = "success_with_results"
            elif http_status == 200 and search.get("total_known") is True and total == 0:
                classification = "reachable_empty_data"
            elif http_status == 200:
                classification = "unconfirmed_empty"
            else:
                classification = "source_unavailable"
        reports = [
            {
                "source_id": report.get("source_id") or report.get("provider"),
                "surface": report.get("surface") or search.get("surface") or "jurisprudencia",
                "classification": classification,
                "record_count_observed": returned,
                "reported_total": total,
                "http_status": http_status,
                "latency_ms": search.get("latency_ms") or search.get("elapsed_ms"),
                "content_type": search.get("content_type"),
                "content_sha256": search.get("content_sha256"),
                "response_bytes": search.get("response_bytes"),
                "access_status": search.get("access_status"),
                "full_text_status": (
                    "valid"
                    if detail.get("http_status") == 200 and detail.get("text_characters", 0) > 0
                    else None
                ),
                "extraction_status": (
                    "valid"
                    if detail.get("http_status") == 200 and detail.get("text_characters", 0) > 0
                    else None
                ),
                "pagination_mode": report.get("pagination_mode") or "page",
            }
        ]
        # Preserve bounded document evidence separately from the search
        # response.  A detail probe must not replace the search hash/size,
        # but its own hash, MIME and byte count are valuable for the full-text
        # gate and remain body-free metadata.
        if isinstance(detail, dict):
            reports[0].update(
                {
                    "document_content_sha256": detail.get("content_sha256") or detail.get("sha256"),
                    "document_response_bytes": detail.get("response_bytes")
                    or detail.get("byte_size"),
                    "document_content_type": detail.get("content_type"),
                    "document_text_characters": detail.get("text_characters"),
                    "document_access_status": detail.get("access_status"),
                }
            )
    # The document QA tool emits a redacted ``sources`` envelope.  Promote
    # only the outcome facts needed by the coverage ledger; bodies and query
    # content are intentionally never copied into the catalog.  A document
    # surface has lower precedence than a primary search surface, so this
    # evidence can enrich a provider without falsely replacing its search
    # health.
    if not reports and isinstance(payload.get("sources"), list):
        for source_report in payload["sources"]:
            if not isinstance(source_report, dict):
                continue
            search = source_report.get("search")
            if not isinstance(search, dict):
                search = {}
            public_url = source_report.get("public_url")
            if not isinstance(public_url, dict):
                public_url = {}
            provider_document = source_report.get("provider_document")
            if not isinstance(provider_document, dict):
                provider_document = {}
            status = str(source_report.get("status") or "unknown")
            if status == "checked":
                classification = "reachable_valid_data"
            elif status == "empty":
                classification = "reachable_empty_data"
            elif status == "partial":
                classification = "partial"
            elif status == "error":
                error_type = str(source_report.get("error_type") or "")
                classification = (
                    "access_control_required"
                    if error_type == "AccessControlRequiredError"
                    else "source_unavailable"
                )
            else:
                classification = status
            reports.append(
                {
                    "source_id": source_report.get("source"),
                    "surface": "public_full_text",
                    "classification": classification,
                    "record_count_observed": search.get("returned"),
                    "reported_total": search.get("reported_total"),
                    "http_status": public_url.get("http_status"),
                    "content_type": public_url.get("content_type")
                    or provider_document.get("content_type"),
                    "content_sha256": public_url.get("sha256"),
                    "response_bytes": public_url.get("response_bytes"),
                    "full_text_status": provider_document.get("status"),
                    "access_status": (source_report.get("result") or {}).get("access_status")
                    if isinstance(source_report.get("result"), dict)
                    else None,
                    "extraction_status": (source_report.get("result") or {}).get(
                        "extraction_status"
                    )
                    if isinstance(source_report.get("result"), dict)
                    else None,
                }
            )
    # The federal eproc detail smoke groups one redacted search/detail report
    # under ``providers``.  Treat the search result as the provider health
    # signal and retain only bounded detail metadata; never copy response
    # bodies or promote the family dispatcher as an aggregate source.
    if not reports and isinstance(payload.get("providers"), list):
        for provider_report in payload["providers"]:
            if not isinstance(provider_report, dict):
                continue
            source_id = provider_report.get("source") or provider_report.get("source_id")
            search = provider_report.get("search")
            detail = provider_report.get("detail")
            if not source_id or not isinstance(search, dict):
                continue
            http_status = search.get("http_status")
            returned = search.get("returned")
            total = search.get("total")
            detail_valid = isinstance(detail, dict) and detail.get("status") == "valid"
            if isinstance(http_status, int) and http_status in {401, 403}:
                classification = "access_control_required"
            elif isinstance(http_status, int) and http_status == 429:
                classification = "rate_limited"
            elif isinstance(http_status, int) and http_status >= 500:
                classification = "source_unavailable"
            elif http_status == 200 and isinstance(returned, int) and returned > 0:
                classification = (
                    "success_with_results_and_document" if detail_valid else "success_with_results"
                )
            elif http_status == 200 and search.get("total_known") is True and total == 0:
                classification = "reachable_empty_data"
            elif http_status == 200:
                classification = "unconfirmed_empty"
            else:
                classification = "source_unavailable"
            reports.append(
                {
                    "source_id": source_id,
                    "surface": "federal_eproc",
                    "classification": classification,
                    "record_count_observed": returned,
                    "reported_total": total,
                    "http_status": http_status,
                    "full_text_status": detail.get("status") if isinstance(detail, dict) else None,
                    "access_status": detail.get("access_status")
                    if isinstance(detail, dict)
                    else None,
                    "extraction_status": detail.get("extraction_status")
                    if isinstance(detail, dict)
                    else None,
                    "content_type": detail.get("content_type")
                    if isinstance(detail, dict)
                    else None,
                    "content_sha256": detail.get("sha256") if isinstance(detail, dict) else None,
                    "response_bytes": detail.get("byte_size") if isinstance(detail, dict) else None,
                    "pagination_mode": "page",
                }
            )
    # The federated promotion smoke emits one redacted envelope containing a
    # completeness row per source rather than a ``results`` list.  Treat only
    # explicitly public sources with at least one returned record as valid;
    # missing access status remains unknown and is never inferred as empty.
    if not reports and isinstance(payload.get("source_completeness"), dict):
        access_by_source = payload.get("source_access_status", {})
        if not isinstance(access_by_source, dict):
            access_by_source = {}
        for source_id, completeness in payload["source_completeness"].items():
            if not isinstance(completeness, dict):
                continue
            if access_by_source.get(source_id) != "public":
                continue
            returned = completeness.get("returned")
            if not isinstance(returned, int) or returned <= 0:
                continue
            reports.append(
                {
                    "source_id": source_id,
                    "surface": "federated_search",
                    "classification": "valid",
                    "record_count_observed": returned,
                    "reported_total": completeness.get("reported_total"),
                    "pagination_mode": completeness.get("pagination_mode"),
                }
            )
    # The state CJSG batch smoke keeps page 1 and page 2 nested so pagination
    # can be audited without duplicating provider metadata.  Flatten only the
    # primary page for the provider-level health row; page 2 remains available
    # in the evidence artifact and never overrides page-1 status.
    normalized_reports: list[dict[str, Any]] = []
    for report in reports:
        if not isinstance(report, dict):
            continue
        first_page = report.get("first_page")
        # The B1 batch names its nested pages explicitly instead of exposing
        # a separate first_page key.  Treat page 1 as the provider health
        # observation while retaining the complete pagination evidence in the
        # dedicated artifact.
        if not isinstance(first_page, dict):
            pages = report.get("pages")
            if isinstance(pages, list) and pages and isinstance(pages[0], dict):
                first_page = pages[0]
        if isinstance(first_page, dict):
            trace = first_page.get("trace")
            trace = trace if isinstance(trace, dict) else {}
            normalized_reports.append(
                {
                    "source_id": report.get("source_id"),
                    "surface": report.get("surface") or "cjsg",
                    # Some bounded probes classify the whole paginated
                    # envelope instead of repeating the classification on
                    # page 1. Preserve that outer value as a fallback so a
                    # valid search cannot regress to ``unknown`` merely
                    # because the evidence is compact.
                    "classification": first_page.get("classification")
                    or report.get("classification")
                    or report.get("status"),
                    "record_count_observed": first_page.get("returned")
                    if first_page.get("returned") is not None
                    else report.get("record_count_observed"),
                    "reported_total": first_page.get("reported_total")
                    if first_page.get("reported_total") is not None
                    else report.get("reported_total"),
                    "http_status": trace.get("http_status") or report.get("http_status"),
                    "content_type": trace.get("content_type") or report.get("content_type"),
                    "content_sha256": trace.get("content_sha256") or report.get("content_sha256"),
                    "response_bytes": trace.get("response_bytes") or report.get("response_bytes"),
                    "pagination_mode": "page",
                }
            )
        else:
            normalized_reports.append(report)
    reports = normalized_reports
    for report in reports:
        if not isinstance(report, dict):
            continue
        # Standalone evidence packages may keep the HTTP classification under
        # a redacted ``response`` object.  Promote that outcome without
        # copying response bodies into the catalog; otherwise a bounded 403
        # would regress to the misleading ``unknown``/not-checked state.
        nested_response = report.get("response")
        if not isinstance(nested_response, dict):
            nested_response = {}
        source_value = report.get("source_id") or report.get("source") or report.get("provider")
        if not source_value:
            continue
        source_id = str(source_value)
        # Standalone provider probes historically omitted ``surface`` even
        # though they represented the primary search. Treat that shape as a
        # jurisprudence search; explicit detail/facet surfaces still retain
        # their lower precedence below.
        surface = str(report.get("surface") or "jurisprudencia")
        # A provider may emit one artifact for several bounded surfaces (for
        # example search, facets and related documents).  Coverage status must
        # represent the primary search contract, not be overwritten by a
        # metadata/detail call that happens to appear later in the artifact.
        current = rows.get(source_id)
        if current is not None and _dedicated_surface_rank(surface) > _dedicated_surface_rank(
            str(current.get("scope") or "")
        ):
            continue
        classification = str(
            report.get("classification")
            or report.get("status")
            or nested_response.get("classification")
            or "unknown"
        )
        if classification in {
            "valid",
            "public_textual_second_degree",
            "valid_second_degree",
            "success_with_results",
            "success_with_results_and_document",
            "success_with_results_and_public_full_text",
            "success_with_document",
            "success_with_results_pagination_validated",
            "bounded_result_schema_stable",
        }:
            classification = "reachable_valid_data"
        # A single evidence file may deliberately contain both successful
        # probes and an explicit empty probe (for example a valid text search
        # followed by an impossible process number).  The provider-level
        # health must remain ``valid`` when a successful primary search was
        # observed; an empty query is evidence about that query, not proof
        # that the source as a whole is unavailable.
        if (
            current is not None
            and current.get("status") == "valid"
            and classification == "reachable_empty_data"
            and _dedicated_surface_rank(surface)
            <= _dedicated_surface_rank(str(current.get("scope") or ""))
        ):
            continue
        # DEDICATED_LIVE_PATHS is intentionally append-only and may contain
        # older rechecks for the same provider.  Never let an older artifact
        # overwrite newer evidence merely because it appears later in the
        # tuple; stale evidence can otherwise hide a legitimate transport
        # fallback that was validated afterward.
        candidate_date = str(payload.get("observed_at") or payload.get("generated_at") or "")[:10]
        if (
            current is not None
            and candidate_date
            and str(current.get("_dedicated_evidence_date") or "")
            and candidate_date < str(current.get("_dedicated_evidence_date"))
        ):
            continue
        # A transient bounded recheck must not erase a previously validated
        # public route.  Timeouts, transport failures and upstream 5xx/403
        # responses describe this observation, not the provider's permanent
        # availability.  Keep the successful primary status for promotion
        # while retaining the latest failure as an auditable health note.
        if (
            current is not None
            and current.get("status") == "valid"
            and classification
            in {
                "source_unavailable",
                "timeout",
                "transport_error",
            }
        ):
            current["last_recheck"] = {
                "date": candidate_date or None,
                "status": classification,
                "evidence": _evidence_path(path),
                "http_status": report.get("http_status") or nested_response.get("http_status"),
            }
            continue
        rows[source_id] = {
            "status": "valid" if classification == "reachable_valid_data" else classification,
            "scope": surface or None,
            # Dedicated smokes historically used ``generated_at`` while newer
            # ones emit ``observed_at``. Both are evidence timestamps; prefer
            # the observation time and fall back to generation time so a valid
            # bounded check is not incorrectly treated as stale/missing.
            "date": candidate_date or None,
            "returned": report.get("record_count_observed"),
            "reported_total": report.get("reported_total"),
            "pagination_mode": report.get("pagination_mode")
            or ("page" if report.get("surface") == "cjpg" else "offset"),
            "latency": report.get("latency") or report.get("latency_ms"),
            "http_status": report.get("http_status") or nested_response.get("http_status"),
            "content_type": report.get("content_type") or nested_response.get("content_type"),
            "content_sha256": report.get("content_sha256"),
            "response_bytes": report.get("response_bytes"),
            "full_text_status": report.get("full_text_status"),
            "access_status": report.get("access_status"),
            "extraction_status": report.get("extraction_status"),
            "sha256": report.get("sha256") or report.get("content_sha256"),
            "note": "bounded dedicated provider check",
            "evidence": _evidence_path(path),
            "_dedicated_evidence_date": candidate_date or None,
        }
        for key in (
            "document_content_sha256",
            "document_response_bytes",
            "document_content_type",
            "document_text_characters",
            "document_access_status",
        ):
            if key in report and report[key] is not None:
                rows[source_id][key] = report[key]


def _merge_tre_type_filter_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Merge the first-degree TRE filter probe as family-level evidence."""

    degree_scope = str(payload.get("degree_scope") or "").casefold()
    if degree_scope not in {"first", "second"}:
        return
    reports = payload.get("results")
    if not isinstance(reports, list) or not reports:
        return
    successes = 0
    empties = 0
    failures = 0
    returned = 0
    reported_total = 0
    statuses: list[int] = []
    for report in reports:
        if not isinstance(report, dict):
            continue
        classification = str(report.get("classification") or "")
        if classification == "success_filtered_window":
            successes += 1
        elif classification == "authoritative_empty":
            empties += 1
        else:
            failures += 1
        value = report.get("returned")
        if isinstance(value, int):
            returned += value
        value = report.get("reported_total")
        if isinstance(value, int):
            reported_total += value
        status = report.get("http_status")
        if isinstance(status, int):
            statuses.append(status)
    if successes and failures:
        status = "partial"
    elif successes:
        status = "valid"
    elif empties == len(reports):
        status = "empty"
    else:
        status = "source_unavailable"
    observed_at = str(payload.get("observed_at") or payload.get("generated_at") or "")
    date_value = observed_at[:10] or None
    source_id = "tre_sjur_first_degree" if degree_scope == "first" else "tre_sjur_jurisprudencia"
    current = rows.get(source_id)
    if current is not None and date_value and str(current.get("date") or "") > date_value:
        return
    rows[source_id] = {
        "status": status,
        "scope": f"SJUR/TRE/{degree_scope}/decision_type_filter",
        "date": date_value,
        "returned": returned,
        "reported_total": reported_total,
        "pagination_mode": "none",
        "latency": None,
        "http_status": 200 if statuses and all(value == 200 for value in statuses) else None,
        "content_type": "application/json",
        "content_sha256": None,
        "response_bytes": None,
        "full_text_status": None,
        "access_status": "public" if statuses and all(value == 200 for value in statuses) else None,
        "extraction_status": "complete" if successes else "empty" if not failures else None,
        "sha256": None,
        "note": (
            f"filtro remoto de tipo de decisao observado em {len(reports)} TREs; "
            f"{successes} janela(s) com registros, {empties} vazio(s) autoritativo(s), "
            f"{failures} resposta(s) nao classificadas; paginacao e inteiro teor pendentes"
        ),
        "evidence": _evidence_path(path),
        "_dedicated_evidence_date": date_value,
    }


def _merge_tre_first_degree_text_sweep(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Record when an unrestricted text probe returns only appellate labels.

    The probe deliberately does not claim that first-degree records do not
    exist: it only demonstrates that searching for the word ``sentenca`` is
    not a valid substitute for the official decision-type filter.  Preserve
    the previously observed filter evidence and expose the mismatch as a
    partial diagnostic so callers cannot mistake it for an empty corpus.
    """

    reports = payload.get("results")
    if not isinstance(reports, list) or not reports:
        return
    current = rows.get("tre_sjur_first_degree")
    if current is None:
        return
    observed = str(payload.get("observed_at") or payload.get("generated_at") or "")
    current_date = str(current.get("date") or "")
    if observed and current_date and observed[:10] < current_date[:10]:
        return
    second_only = 0
    unknown = 0
    checked = 0
    for report in reports:
        if not isinstance(report, dict):
            continue
        checked += 1
        degree_labels = report.get("degree_labels")
        if isinstance(degree_labels, dict) and degree_labels.get("second"):
            second_only += 1
        else:
            unknown += 1
    enriched = dict(current)
    enriched.update(
        {
            "first_degree_text_probe_status": "second_degree_only_window",
            "first_degree_text_probe_checked": checked,
            "first_degree_text_probe_second_only": second_only,
            "first_degree_text_probe_unknown": unknown,
            "first_degree_text_probe_evidence": _evidence_path(path),
            "first_degree_text_probe_observed_at": observed,
            "note": (
                str(current.get("note") or "").rstrip("; ")
                + "; busca textual sem filtro retornou somente segundo grau; "
                "filtro de tipo permanece obrigatório"
            ),
        }
    )
    rows["tre_sjur_first_degree"] = enriched


def _merge_tre_first_degree_sample(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Attach a current first-degree sample without replacing family evidence."""

    if payload.get("source_id") != "tre_sjur_first_degree":
        return
    observations = payload.get("observations")
    if not isinstance(observations, dict) or observations.get("degree") != "first":
        return
    current = rows.get("tre_sjur_first_degree")
    if current is None:
        return
    observed = str(payload.get("checked_at") or payload.get("generated_at") or "")
    current_date = str(current.get("date") or "")
    if observed and current_date and observed[:10] < current_date[:10]:
        return
    enriched = dict(current)
    enriched.update(
        {
            "first_degree_sample_authority": payload.get("authority"),
            "first_degree_sample_status": "valid",
            "first_degree_sample_returned": observations.get("returned"),
            "first_degree_sample_total": observations.get("reported_total"),
            "first_degree_sample_id": observations.get("source_id"),
            "first_degree_sample_evidence": _evidence_path(path),
            "first_degree_sample_response_bytes": observations.get("response_bytes"),
            "first_degree_sample_content_sha256": observations.get("content_sha256"),
            "first_degree_sample_observed_at": observed,
        }
    )
    rows["tre_sjur_first_degree"] = enriched


def _merge_tre_large_window_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Enrich the second-degree family with targeted large-window retries."""

    reports = payload.get("results")
    if not isinstance(reports, list) or not reports:
        return
    successes = [
        report
        for report in reports
        if isinstance(report, dict)
        and str(report.get("classification") or "") == "success_with_results"
    ]
    if not successes:
        return
    observed_at = str(payload.get("observed_at") or payload.get("generated_at") or "")
    date_value = observed_at[:10] or None
    current = rows.get("tre_sjur_jurisprudencia")
    if current is not None and date_value and str(current.get("date") or "") > date_value:
        return
    response_sizes = [
        int(report["response_bytes"])
        for report in successes
        if isinstance(report.get("response_bytes"), int)
    ]
    latencies = [
        float(report["elapsed_ms"])
        for report in successes
        if isinstance(report.get("elapsed_ms"), (int, float))
    ]
    rows["tre_sjur_jurisprudencia"] = {
        **(current or {}),
        "status": "partial",
        "scope": "SJUR/TRE/second/document_type_targeted",
        "date": date_value or (current or {}).get("date"),
        "returned": sum(int(report.get("result_count") or 0) for report in successes),
        "reported_total": sum(int(report.get("total") or 0) for report in successes),
        "pagination_mode": "none",
        "latency": max(latencies) if latencies else None,
        "http_status": 200,
        "content_type": "application/json",
        "content_sha256": None,
        "sha256": None,
        "response_bytes": max(response_sizes) if response_sizes else None,
        "access_status": "public",
        "extraction_status": "complete",
        "note": (
            "sonda direcionada confirmou janela de acordao em "
            f"{len(successes)} TREs; paginacao remota e completude permanecem pendentes"
        ),
        "evidence": _evidence_path(path),
        "_dedicated_evidence_date": date_value,
    }


def _merge_tre_pagination_recheck(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Keep a repeated official page explicit in the TRE family ledger."""

    if payload.get("pagination_classification") != "remote_page_ignored_duplicate_window":
        return
    current = rows.get("tre_sjur_jurisprudencia")
    if current is None:
        return
    observed_at = str(payload.get("observed_at") or payload.get("generated_at") or "")
    date_value = observed_at[:10] or None
    if date_value and str(current.get("date") or "") > date_value:
        return
    reports = payload.get("results")
    if not isinstance(reports, list):
        reports = []
    returned = [
        int(item["returned"])
        for item in reports
        if isinstance(item, dict) and isinstance(item.get("returned"), int)
    ]
    totals = [
        int(item["reported_total"])
        for item in reports
        if isinstance(item, dict) and isinstance(item.get("reported_total"), int)
    ]
    latencies = [
        float(item["elapsed_ms"])
        for item in reports
        if isinstance(item, dict) and isinstance(item.get("elapsed_ms"), (int, float))
    ]
    response_sizes = [
        int(item["response_bytes"])
        for item in reports
        if isinstance(item, dict) and isinstance(item.get("response_bytes"), int)
    ]
    rows["tre_sjur_jurisprudencia"] = {
        **current,
        "status": "partial",
        "scope": "SJUR/TRE/second/pagination_recheck",
        "pagination_mode": "none",
        "total_known": False,
        "returned": max(returned) if returned else current.get("returned"),
        "reported_total": max(totals) if totals else current.get("reported_total"),
        "latency": max(latencies) if latencies else current.get("latency"),
        "response_bytes": max(response_sizes) if response_sizes else current.get("response_bytes"),
        "http_status": 200,
        "content_type": "application/json",
        "note": (
            "sonda oficial comparou pagina 0 e 1 e recebeu a mesma janela; "
            "paginaÃ§ao remota permanece nao comprovada"
        ),
        "evidence": _evidence_path(path),
        "_dedicated_evidence_date": date_value or current.get("date"),
    }


def _merge_tre_document_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Attach a valid observed PDF without replacing search health.

    Document probes have lower precedence than the primary search contract.
    They therefore enrich the existing TRE family row instead of changing its
    pagination status or replacing its search evidence.
    """

    source_id = str(payload.get("source_id") or "")
    if source_id != "tre_sp_sjur_jurisprudencia":
        return
    document = payload.get("document")
    if not isinstance(document, dict) or document.get("status") != "valid":
        return
    # The live probe targets one scoped UF binding, while the canonical
    # catalog row represents the shared family.  Enrich that family row
    # without turning the scoped observation into national completeness.
    family_source_id = "tre_sjur_jurisprudencia"
    current = rows.get(family_source_id)
    if current is None:
        return
    observed = str(payload.get("observed_at") or payload.get("generated_at") or "")
    date_value = observed[:10] or None
    current_date = str(current.get("date") or "")
    if date_value and current_date and date_value < current_date:
        return
    enriched = dict(current)
    enriched.update(
        {
            "full_text_status": "valid",
            "document_access_status": document.get("access_status"),
            "document_extraction_status": document.get("extraction_status"),
            "document_content_type": document.get("content_type"),
            "document_bytes": document.get("bytes"),
            "document_sha256": document.get("sha256"),
            "document_evidence": _evidence_path(path),
            "note": (
                str(current.get("note") or "").rstrip("; ")
                + "; PDF publico validado para um registro observado"
            ),
        }
    )
    rows[family_source_id] = enriched


def _merge_tre_date_partition_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Record bounded date-partition completeness without claiming pagination."""

    if payload.get("provider") != "tre_sp_sjur_jurisprudencia":
        return
    if payload.get("classification") != "bounded_date_partition_complete":
        return
    current = rows.get("tre_sjur_jurisprudencia")
    if current is None:
        return
    observed = str(payload.get("checked_at") or "")
    current_date = str(current.get("date") or "")
    if observed and current_date and observed < current_date:
        return
    enriched = dict(current)
    note = str(current.get("note") or "").rstrip("; ")
    partition_note = "particao mensal de data validada em intervalo bounded"
    enriched.update(
        {
            "date_partition_status": "valid",
            "date_partition_total": payload.get("totalRegistros", payload.get("total")),
            "date_partition_returned": payload.get("returned"),
            "date_partition_evidence": _evidence_path(path),
            "note": (note if partition_note in note else f"{note}; {partition_note}".lstrip("; ")),
        }
    )
    rows["tre_sjur_jurisprudencia"] = enriched


def _merge_tre_uf_sweep_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Attach the 27-UF bounded sweep without claiming historical coverage."""

    # Accept both the historical family label and the probe's generic
    # bounded-partition label.  The latter is emitted by current probes and
    # still carries the same 27-UF, second-degree semantics.
    if payload.get("classification") not in {
        "family_date_partition_live_validated",
        "bounded_date_partition_complete",
    }:
        return
    current = rows.get("tre_sjur_jurisprudencia")
    if current is None:
        return
    observed = str(payload.get("checked_at") or "")
    current_date = str(current.get("date") or "")
    if observed and current_date and observed < current_date:
        return
    enriched = dict(current)
    enriched.update(
        {
            "uf_sweep_status": "valid",
            "uf_sweep_checked": payload.get("checked"),
            "uf_sweep_complete": payload.get("complete"),
            "uf_sweep_evidence": _evidence_path(path),
        }
    )
    rows["tre_sjur_jurisprudencia"] = enriched


def _merge_tre_document_uf_sweep(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Attach the bounded 27-TRE document extraction sweep.

    This evidence enriches document capability only; it must not replace the
    primary search or pagination health signal.  The probe stores hashes and
    status metadata, so no response body is copied into the catalog.
    """

    current = rows.get("tre_sjur_jurisprudencia")
    reports = payload.get("results")
    if current is None or not isinstance(reports, list):
        return
    valid = [
        report
        for report in reports
        if isinstance(report, dict)
        and report.get("classification") == "success_with_document"
        and report.get("degree") == "second"
        and report.get("collection") == "SJUR"
        and report.get("document_access_status") == "public"
        and report.get("document_extraction_status") == "complete"
        and report.get("document_has_text") is True
    ]
    failures = [
        {
            "authority": report.get("authority"),
            "classification": report.get("classification"),
        }
        for report in reports
        if isinstance(report, dict) and report not in valid
    ]
    checked = len(reports)
    if not checked:
        return
    enriched = dict(current)
    enriched.update(
        {
            "document_uf_sweep_status": "complete" if len(valid) == checked else "partial",
            "document_uf_sweep_checked": checked,
            "document_uf_sweep_valid": len(valid),
            "document_uf_sweep_failures": failures,
            "document_uf_sweep_evidence": _evidence_path(path),
            "document_uf_sweep_observed_at": payload.get("observed_at"),
        }
    )
    rows["tre_sjur_jurisprudencia"] = enriched


def _merge_tjam_detail_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Enrich TJAM search health with an explicit blocked detail observation.

    The CJSG search route is public and independently useful when the detail
    endpoint presents a CAPTCHA.  Keep the provider search status valid while
    exposing the document access/extraction state instead of treating the
    blocked detail as an empty or unavailable search.
    """

    if payload.get("source_id") != "tjam_cjsg":
        return
    response = payload.get("response")
    if not isinstance(response, dict):
        return
    if response.get("access_status") != "access_control_required":
        return
    current = rows.get("tjam_cjsg")
    if current is None:
        return
    observed = str(payload.get("checked_at") or payload.get("generated_at") or "")
    current_date = str(current.get("date") or "")
    if observed and current_date and observed[:10] < current_date[:10]:
        return
    enriched = dict(current)
    enriched.update(
        {
            "document_access_status": "access_control_required",
            "document_extraction_status": "blocked",
            "document_http_status": response.get("http_status"),
            "document_content_type": response.get("content_type"),
            "document_response_bytes": response.get("response_bytes"),
            "document_content_sha256": response.get("content_sha256"),
            "document_evidence": _evidence_path(path),
            "note": (
                str(current.get("note") or "").rstrip("; ")
                + "; detalhe oficial bloqueado por CAPTCHA, busca permanece valida"
            ),
        }
    )
    rows["tjam_cjsg"] = enriched


def _merge_tjce_detail_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Attach bounded TJCE/CJSG document extraction evidence to the provider row."""

    if payload.get("source_id") != "tjce_cjsg":
        return
    response = payload.get("response")
    if not isinstance(response, dict):
        return
    current = rows.get("tjce_cjsg")
    if current is None:
        return
    observed = str(payload.get("checked_at") or payload.get("generated_at") or "")
    current_date = str(current.get("date") or "")
    if observed and current_date and observed[:10] < current_date[:10]:
        return
    if response.get("access_status") != "public" or response.get("extraction_status") != "complete":
        return
    enriched = dict(current)
    enriched.update(
        {
            "full_text_status": "valid",
            "extraction_status": "complete",
            "document_access_status": response.get("access_status"),
            "document_extraction_status": response.get("extraction_status"),
            "document_http_status": response.get("http_status"),
            "document_content_type": response.get("content_type"),
            "document_response_bytes": response.get("response_bytes"),
            "document_content_sha256": response.get("content_sha256"),
            "document_detected_content_type": response.get("detected_content_type"),
            "document_text_characters": response.get("text_characters"),
            "document_page_count": response.get("page_count"),
            "document_evidence": _evidence_path(path),
            "note": (
                str(current.get("note") or "").rstrip("; ")
                + "; inteiro teor PDF validado em chamada bounded"
            ),
        }
    )
    rows["tjce_cjsg"] = enriched


def _merge_tre_first_degree_partition_probe(
    rows: dict[str, dict[str, Any]], payload: dict[str, Any], path: Path
) -> None:
    """Attach first-degree date evidence while keeping the family opt-in."""

    if payload.get("provider") not in {"tre_sjur_first_degree", "tre_mg_sjur_first_degree"}:
        return
    current = rows.get("tre_sjur_first_degree")
    if current is None:
        return
    observed = str(payload.get("checked_at") or "")
    current_date = str(current.get("date") or "")
    if observed and current_date and observed < current_date:
        return
    enriched = dict(current)
    classification = payload.get("classification")
    if classification == "bounded_date_partition_authoritative_empty":
        enriched.update(
            {
                "date_partition_uf_sweep_status": "valid_empty_window",
                "date_partition_uf_sweep_checked": payload.get("checked"),
                "date_partition_uf_sweep_evidence": _evidence_path(path),
            }
        )
    elif classification == "bounded_date_partition_complete":
        enriched.update(
            {
                "date_partition_status": "valid",
                "date_partition_total": payload.get("totalRegistros", payload.get("total")),
                "date_partition_returned": payload.get("returned"),
                "date_partition_evidence": _evidence_path(path),
            }
        )
    else:
        return
    rows["tre_sjur_first_degree"] = enriched


def _dedicated_surface_rank(surface: str) -> int:
    """Order dedicated evidence so primary search wins over detail metadata."""

    normalized = surface.casefold().strip()
    if normalized in {"jurisprudencia", "cjpg", "cjsg", "search"}:
        return 0
    if normalized in {"public_full_text", "public_full_text_download", "document"}:
        return 1
    return 2


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


def _live_dimensions(live_status: dict[str, Any]) -> dict[str, Any]:
    """Expose orthogonal health dimensions without changing legacy status.

    ``live_status`` remains the conservative promotion gate used by the
    existing catalog and coverage matrix.  The dimensions below answer three
    different questions explicitly:

    * availability: could the official route be reached and parsed?
    * completeness: did the observation prove the requested corpus/window?
    * pagination: is remote pagination an established contract?

    This is intentionally additive.  In particular, a public HTTP 200 with a
    repeated window is not promoted to a complete or federated source.
    """

    status = str(live_status.get("status") or "unknown")
    access = str(live_status.get("access_status") or "")
    extraction = str(live_status.get("extraction_status") or "")
    http_status = live_status.get("http_status")

    if status in {"valid", "empty"}:
        availability = "valid"
    elif (
        status == "partial"
        and access == "public"
        and extraction in {"complete", "partial"}
        and http_status == 200
    ):
        availability = "valid_partial"
    elif status in {"blocked", "blocked_access", "access_controlled", "access_control_required"}:
        availability = "blocked"
    elif status in {"blocked_transport", "transport_blocked", "timeout", "source_unavailable"}:
        availability = "unavailable"
    else:
        availability = "unknown"

    if live_status.get("date_partition_status") == "valid":
        completeness = "bounded_partition"
    elif status == "empty":
        completeness = "authoritative_empty"
    elif status == "valid" and live_status.get("total_known") is True:
        completeness = "complete"
    elif status in {"valid", "partial"}:
        completeness = "partial"
    else:
        completeness = "unknown"

    pagination_mode = str(live_status.get("pagination_mode") or "unknown")
    if pagination_mode in {"cursor", "offset", "page", "date_partition"}:
        pagination = "validated"
    elif pagination_mode in {"none", "unknown"}:
        pagination = "unverified" if status in {"partial", "valid"} else "not_observed"
    else:
        pagination = "unverified"

    return {
        "availability": availability,
        "completeness": completeness,
        "pagination": pagination,
        "access_status": access or None,
        "legacy_live_status": status,
    }


def _identity(source_id: str, capability: Any | None) -> dict[str, Any]:
    declared_urls = CANDIDATE_SOURCE_URLS.get(source_id, ())
    capability_url = getattr(capability, "source_url", None)
    source_url = capability_url or (declared_urls[0] if declared_urls else None)
    return {
        "source_id": source_id,
        "display_name": getattr(capability, "display_name", _display_name(source_id)),
        "source_url": source_url,
        "category": getattr(capability, "category", "research_candidate"),
        **({"source_urls": list(declared_urls)} if declared_urls else {}),
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
    """Return a stable date that is at least as new as available evidence.

    The catalog is regenerated after dedicated live checks, so retaining an
    older ``generated_at`` from the previous catalog can make the documentation
    look stale even when newer evidence is already checked in.  We therefore
    keep the existing snapshot as a floor and advance it to the newest
    timestamp found in structured validation artifacts.  No network is used.
    """

    existing_date: str | None = None
    if CATALOG_PATH.is_file():
        try:
            existing = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
        generated_at = existing.get("generated_at")
        if isinstance(generated_at, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", generated_at):
            existing_date = generated_at

    evidence_dates: list[str] = []
    for path in DEDICATED_LIVE_PATHS:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for key in ("observed_at", "checked_at", "generated_at", "date"):
            value = payload.get(key)
            if isinstance(value, str):
                match = re.match(r"(\d{4}-\d{2}-\d{2})", value)
                if match:
                    evidence_dates.append(match.group(1))
                    break
    if VALIDATION_RUNS_DIR.is_dir():
        for path in VALIDATION_RUNS_DIR.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for key in ("generated_at", "checked_at", "observed_at", "date"):
                value = payload.get(key)
                if isinstance(value, str):
                    match = re.match(r"(\d{4}-\d{2}-\d{2})", value)
                    if match:
                        evidence_dates.append(match.group(1))
                        break

    candidates = [value for value in [existing_date, *evidence_dates] if value]
    return max(candidates, default=date.today().isoformat())


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
            "opt_in_unified_search": False,
            "mcp": False,
            "studio": False,
            "live_tests": False,
        }
    return {
        "cli": capability.supports_cli,
        "unified_search": capability.supports_unified_search,
        "opt_in_unified_search": capability.opt_in_unified_search,
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
        "blocked_access",
        "access_controlled",
        "access_controlled_or_inconclusive",
        "blocked_transport",
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
    if is_dataclass(value) and not isinstance(value, type):
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
        # Keep the preview command portable on Windows consoles that still use
        # cp1252; generated files remain UTF-8 while stdout is ASCII-safe.
        print(json.dumps(_normalize(catalog), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
