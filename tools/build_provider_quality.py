"""Build an offline, evidence-backed provider quality scorecard.

This report is intentionally separate from the catalog maturity score and
from live health. It evaluates only checked-in contracts, documentation,
fixtures and explicit provenance declarations, so CI can run it without
contacting a tribunal or pretending that a blocked request is an empty result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from functools import cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(1, str(ROOT))

from tools.audit_provider_discovery_offline import (  # noqa: E402
    _fixture_refs,
    _test_files,
    _test_fixture_refs,
)

CATALOG_PATH = ROOT / "docs" / "registry" / "provider-catalog.full.json"
SCENARIOS_PATH = ROOT / "tests" / "fixtures" / "provider_quality_scenarios.json"
QUALITY_DIR = ROOT / "docs" / "quality"
REPORT_PATH = QUALITY_DIR / "provider-quality.json"
MARKDOWN_PATH = QUALITY_DIR / "provider-quality.md"
SCHEMA_PATH = ROOT / "docs" / "schemas" / "provider-quality.schema.json"

DIMENSIONS: tuple[tuple[str, int], ...] = (
    ("authority_scope", 10),
    ("contract_errors", 15),
    ("identity", 15),
    ("textual_content", 15),
    ("dates_temporality", 10),
    ("provenance_trace", 15),
    ("pagination_completeness", 10),
    ("tests_fixtures", 5),
    ("documentation_operations", 5),
)
IDENTITY_FIELDS = {
    "case_number",
    "registry_number",
    "public_id",
    "source_record_id",
    "id",
    "number",
    "edition_number",
    "informativo",
    "theme",
    "dataset_id",
    "resource_id",
    "uuid",
    "cd_acordao",
    "summary_number",
}
CONTENT_FIELDS = {
    "summary",
    "full_text",
    "question",
    "thesis",
    "title",
    "text",
    # Curated jurisprudence and bulletin providers use these canonical
    # names for the operative legal text.  They are content fields, not
    # metadata, and must contribute to the same quality gate as summary/text.
    "statement",
    "holding",
    "rationale",
    "grounds",
}
DATE_FIELDS = {
    "judgment_date",
    "publication_date",
    "updated_at",
    "source_updated_at",
    "retrieved_at",
    # Precedent catalogs expose milestone dates rather than a single
    # judgment/publication pair.  They are still first-class temporal data.
    "admission_date",
    "admissibility_publication_date",
    "merit_judgment_date",
    "merit_publication_date",
}


def build_report() -> dict[str, Any]:
    """Return the deterministic quality report for the checked-in catalog."""

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    entries = [
        _evaluate_entry(entry)
        for entry in sorted(catalog.get("entries", []), key=lambda item: item["source_id"])
    ]
    runtime = [entry for entry in entries if entry["lifecycle"] == "implemented"]
    critical = [entry for entry in entries if entry["critical_gaps"]]
    operational_blocked = [entry for entry in entries if entry["operational_gaps"]]
    return {
        "schema_version": "1.0",
        "generated_at": catalog.get("generated_at"),
        "source_catalog": "docs/registry/provider-catalog.full.json",
        "catalog_sha256": _sha256(CATALOG_PATH),
        "scope": {
            "network": False,
            "runtime_scorecards": len(runtime),
            "all_catalog_entries": len(entries),
            "live_health_is_separate": True,
            "gold_requires_zero_critical_gaps": True,
        },
        "dimensions": [{"id": name, "weight": weight} for name, weight in DIMENSIONS],
        "golden_set": {
            "path": "tests/fixtures/provider_quality_scenarios.json",
            "sha256": _sha256(SCENARIOS_PATH),
            "schema_version": scenarios.get("schema_version"),
            "scenarios": [item["id"] for item in scenarios.get("scenarios", [])],
        },
        "summary": {
            "providers": len(entries),
            "runtime": len(runtime),
            "candidates_and_families": len(entries) - len(runtime),
            "critical_gap_providers": len(critical),
            # Structural critical gaps and point-in-time operational blocks are
            # intentionally separate. A provider can have a complete parser
            # contract while being unavailable today; that state must still
            # block release promotion without falsifying the quality score.
            "operational_blocked_providers": len(operational_blocked),
            "by_quality_tier": dict(
                sorted(Counter(entry["quality_tier"] for entry in entries).items())
            ),
            "by_live_status": dict(
                sorted(Counter(entry["live_status"] for entry in entries).items())
            ),
        },
        "entries": entries,
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a concise human report from the machine-readable scorecard."""

    summary = report["summary"]
    lines = [
        "# Provider quality scorecard",
        "",
        "Gerado por o build_provider_quality.py --write; nao edite manualmente.",
        "",
        "Este scorecard e offline e independente da saude live. Um bloqueio de rede, WAF,",
        "CAPTCHA ou timeout permanece explicito em live_status e nunca e convertido em vazio.",
        "",
        f"- Catalogo avaliado: {report['source_catalog']} ({report['catalog_sha256'][:12]}...).",
        f"- Providers runtime avaliados: **{summary['runtime']}** de "
        f"**{summary['providers']}** entradas.",
        f"- Providers com lacuna critica: **{summary['critical_gap_providers']}**.",
        "- Providers bloqueados ou sem live recente: "
        f"**{summary['operational_blocked_providers']}**.",
        f"- Golden set: **{len(report['golden_set']['scenarios'])}** cenarios sanitizados.",
        "",
        "## Dimensoes",
        "",
        "| Dimensao | Peso |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {item['id']} | {item['weight']} |" for item in report["dimensions"])
    lines.extend(
        [
            "",
            "## Matriz",
            "",
            "| Provider | Score | Tier | Criticos | Live | Evidencia |",
            "| --- | ---: | --- | ---: | --- | --- |",
        ]
    )
    for entry in report["entries"]:
        evidence = ", ".join(entry["evidence_summary"][:2]) or "sem evidencia local"
        lines.append(
            f"| {entry['source_id']} | {entry['score']} | {entry['quality_tier']} | "
            f"{len(entry['critical_gaps'])} | {entry['live_status']} | {evidence} |"
        )
    lines.extend(
        [
            "",
            "## Regras de promocao",
            "",
            "- gold: score >= 85 e nenhuma lacuna critica; ainda requer aceite humano "
            "para release.",
            "- silver: score >= 70 e nenhuma lacuna critica.",
            "- bronze: score >= 50 e nenhuma lacuna critica.",
            "- blocked: existe lacuna critica; nao promover para coleta automatica.",
            "- mapped: contrato insuficiente para uma avaliacao operacional.",
            "",
            "Saude live, licenca de reutilizacao, termos do tribunal e aprovacao de release",
            "continuam gates independentes e nao sao inferidos por este relatorio.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report() -> None:
    report = build_report()
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_PATH.write_text(render_markdown(report), encoding="utf-8")


def check_report() -> bool:
    report = build_report()
    expected_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    return REPORT_PATH.read_text(encoding="utf-8") == expected_json and MARKDOWN_PATH.read_text(
        encoding="utf-8"
    ) == render_markdown(report)


def validate_report(report: dict[str, Any]) -> list[str]:
    """Validate scorecard invariants without an optional JSON-schema package."""

    errors: list[str] = []
    if report.get("schema_version") != "1.0":
        errors.append("schema_version")
    if report.get("scope", {}).get("network") is not False:
        errors.append("network_must_be_false")
    dimensions = report.get("dimensions", [])
    dimension_ids = {item.get("id") for item in dimensions}
    if sum(int(item.get("weight", 0)) for item in dimensions) != 100:
        errors.append("dimension_weights")
    if len(dimension_ids) != len(dimensions):
        errors.append("duplicate_dimensions")
    entries = report.get("entries", [])
    source_ids = [entry.get("source_id") for entry in entries]
    if len(set(source_ids)) != len(source_ids):
        errors.append("duplicate_sources")
    for entry in entries:
        score = entry.get("score")
        if not isinstance(score, int) or not 0 <= score <= 100:
            errors.append(f"score:{entry.get('source_id')}")
        if set(entry.get("dimensions", {})) != dimension_ids:
            errors.append(f"dimensions:{entry.get('source_id')}")
        for name, dimension in entry.get("dimensions", {}).items():
            if not 0 <= dimension.get("score", -1) <= dimension.get("max", -1):
                errors.append(f"dimension_score:{entry.get('source_id')}:{name}")
        if entry.get("quality_tier") == "gold" and entry.get("critical_gaps"):
            errors.append(f"gold_has_critical:{entry.get('source_id')}")
    summary = report.get("summary", {})
    if summary.get("providers") != len(entries):
        errors.append("summary.providers")
    if summary.get("runtime") != sum(entry.get("lifecycle") == "implemented" for entry in entries):
        errors.append("summary.runtime")
    return sorted(set(errors))


def _evaluate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    source_id = str(entry["source_id"])
    dimensions = {name: _dimension(name, weight, entry, source_id) for name, weight in DIMENSIONS}
    critical_gaps = _critical_gaps(entry, source_id)
    score = sum(item["score"] for item in dimensions.values())
    if critical_gaps:
        tier = "blocked"
    elif score >= 85:
        tier = "gold"
    elif score >= 70:
        tier = "silver"
    elif score >= 50:
        tier = "bronze"
    else:
        tier = "mapped"
    evidence_summary = sorted(
        {evidence for item in dimensions.values() for evidence in item["evidence"]}
    )
    return {
        "source_id": source_id,
        "lifecycle": entry.get("lifecycle"),
        "quality_tier": tier,
        "score": score,
        "critical_gaps": critical_gaps,
        "operational_gaps": _operational_gaps(entry),
        "live_status": entry.get("live_validation", {}).get("status", "unknown"),
        "dimensions": dimensions,
        "evidence_summary": evidence_summary,
    }


def _dimension(name: str, weight: int, entry: dict[str, Any], source_id: str) -> dict[str, Any]:
    contract = entry.get("source_contract") or {}
    evidence = contract.get("evidence") or {}
    fields = set(entry.get("output_contract", {}).get("extracted_fields", []))
    source_url = str(entry.get("identity", {}).get("source_url") or "")
    docs = entry.get("documentation", {})
    fixture_refs = _fixture_evidence(source_id)
    tests = _tests_for(source_id)
    if name == "authority_scope":
        parsed = urlparse(source_url)
        official = bool(parsed.hostname) and (
            parsed.hostname.endswith((".jus.br", ".gov.br", ".leg.br"))
        )
        score = (5 if source_url else 0) + (5 if official else 0)
        details = ["source_url_declarada"] if source_url else []
        if official:
            details.append("dominio_oficial_heuristico")
    elif name == "contract_errors":
        score = (
            (5 if contract else 0)
            + min(4, len(evidence.get("endpoints", [])))
            + (3 if entry.get("error_contract", {}).get("access_statuses") else 0)
            + (3 if evidence.get("limitations") is not None else 0)
        )
        details = []
        if contract:
            details.append("source_contract")
        if evidence.get("endpoints"):
            details.append("endpoints")
        if entry.get("error_contract", {}).get("access_statuses"):
            details.append("access_statuses")
    elif name == "identity":
        identity = fields & IDENTITY_FIELDS
        strong_identity = identity & {
            "id",
            "number",
            "registry_number",
            "public_id",
            "source_record_id",
            "resource_id",
            "dataset_id",
        }
        score = (7 if identity else 0) + (5 if strong_identity else 0)
        score += 3 if entry.get("output_contract", {}).get("canonical_records") else 0
        details = ["identity_fields"] if identity else []
        if evidence.get("extracted_fields"):
            details.append("extracted_fields")
    elif name == "textual_content":
        content = fields & CONTENT_FIELDS
        score = (8 if content else 0) + (
            4 if entry.get("output_contract", {}).get("supports_full_text") else 0
        )
        score += 3 if entry.get("output_contract", {}).get("document_types") else 0
        details = ["content_fields"] if content else []
        if entry.get("output_contract", {}).get("supports_full_text"):
            details.append("full_text_capability")
    elif name == "dates_temporality":
        dates = fields & DATE_FIELDS
        score = (6 if dates else 0) + (2 if any(item.endswith("_raw") for item in fields) else 0)
        score += 2 if "updated_at" in fields or "source_updated_at" in fields else 0
        details = ["date_fields"] if dates else []
    elif name == "provenance_trace":
        trace = bool(entry.get("output_contract", {}).get("trace_expected"))
        score = 8 if trace else 0
        score += 4 if "document_url" in fields or "url" in fields else 0
        score += 3 if evidence.get("endpoints") else 0
        details = ["trace_expected"] if trace else []
        if "source_trace" in fields:
            details.append("source_trace_field")
    elif name == "pagination_completeness":
        pagination = entry.get("pagination_contract", {})
        mode = pagination.get("mode")
        completeness = evidence.get("completeness_contract")
        score = (4 if mode and mode != "unknown" else 0) + (
            4 if completeness and completeness != "unknown" else 0
        )
        score += (
            2 if pagination.get("max_remote_page") or pagination.get("max_remote_page_size") else 0
        )
        details = ["pagination_mode"] if mode and mode != "unknown" else []
        if completeness and completeness != "unknown":
            details.append("completeness_contract")
    elif name == "tests_fixtures":
        score = (3 if tests else 0) + (2 if fixture_refs else 0)
        details = ["provider_test"] if tests else []
        if fixture_refs:
            details.append("replayable_fixture")
    elif name == "documentation_operations":
        human_doc = bool(docs.get("human_doc") and (ROOT / docs["human_doc"]).is_file())
        parity = bool(docs.get("canonical_legacy_parity"))
        score = (
            (2 if human_doc else 0)
            + (2 if parity else 0)
            + (1 if not docs.get("missing_sections") and not docs.get("open_items") else 0)
        )
        details = ["human_doc"] if human_doc else []
        if parity:
            details.append("legacy_parity")
    else:  # pragma: no cover - dimensions are a closed constant
        score, details = 0, []
    return {
        "score": min(weight, score),
        "max": weight,
        "evidence": sorted(details),
    }


def _critical_gaps(entry: dict[str, Any], source_id: str) -> list[str]:
    if entry.get("lifecycle") != "implemented":
        return []
    gaps: list[str] = []
    contract = entry.get("source_contract") or {}
    output = entry.get("output_contract") or {}
    evidence = contract.get("evidence") or {}
    fields = set(output.get("extracted_fields", []))
    if not entry.get("identity", {}).get("source_url"):
        gaps.append("missing_official_source_url")
    if not contract:
        gaps.append("missing_source_contract")
    if not evidence.get("endpoints"):
        gaps.append("missing_endpoint_contract")
    if not output.get("canonical_records"):
        gaps.append("missing_canonical_record_contract")
    role = entry.get("coverage_role")
    if role in {"primary_textual_jurisprudence", "precedent_context"}:
        if not fields & IDENTITY_FIELDS:
            gaps.append("missing_identity_field")
        if not fields & CONTENT_FIELDS:
            gaps.append("missing_legal_content_field")
    # SourceTrace is a canonical envelope field and is therefore not repeated
    # in the provider's extracted-field list. The contract flag is the
    # authoritative declaration here.
    if output.get("trace_expected") is False:
        gaps.append("missing_source_trace_contract")
    if not _fixture_evidence(source_id) or not _tests_for(source_id):
        gaps.append("missing_replayable_test_evidence")
    return sorted(set(gaps))


def _operational_gaps(entry: dict[str, Any]) -> list[str]:
    """Return live/release blockers without mutating offline quality tiers."""

    status = str(entry.get("live_validation", {}).get("status") or "unknown")
    blocked = {
        "blocked",
        "blocked_access",
        "blocked_transport",
        "access_controlled",
        "source_unavailable",
        "tls_error",
        "timeout",
        "source_pagination_not_validated",
    }
    if status in blocked:
        return [f"live_status:{status}"]
    if status == "not_checked_in_latest_focused_run":
        return ["live_status:not_recently_checked"]
    return []


@cache
def _tests_for(source_id: str) -> tuple[str, ...]:
    return tuple(_test_files(ROOT, source_id))


@cache
def _fixture_evidence(source_id: str) -> frozenset[str]:
    refs = _fixture_refs(ROOT, source_id)
    tests = _tests_for(source_id)
    refs.update(_test_fixture_refs(ROOT, tests, source_id))
    return frozenset(refs)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="grava o relatorio gerado")
    mode.add_argument("--check", action="store_true", help="falha se o relatorio estiver stale")
    args = parser.parse_args()
    if args.write:
        write_report()
        return 0
    if args.check:
        if (
            not REPORT_PATH.is_file()
            or not MARKDOWN_PATH.is_file()
            or not SCHEMA_PATH.is_file()
            or validate_report(build_report())
            or not check_report()
        ):
            print("provider quality report is stale; run --write", file=sys.stderr)
            return 1
        return 0
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
