"""Audit mapped providers and run discovery only over checked-in local evidence.

This tool deliberately has no HTTP client and never contacts a provider. It
cross-checks the generated catalog, canonical/legacy dossiers, runtime modules,
tests and fixture references, then applies the discovery extractors to local
HTML/JSON fixtures when they are available.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from nanojuris.discovery.extract import extract_route_candidates, suggest_selector_candidates
from nanojuris.route_probe import analyze_route_response

FIXTURE_REF = re.compile(r"tests[\\/]fixtures[\\/]([A-Za-z0-9_.-]+)")
URL_RE = re.compile(r"https?://[^\s`)>]+")
SOURCE_MODULE_RE = re.compile(r"nanojuris\.providers\.([a-z0-9_]+)")

# Inline payloads are useful deterministic evidence, but they are not
# equivalent to a reviewed, replayable fixture file. Keep both evidence types
# visible in the audit instead of silently treating either one as the other.
INLINE_ASSIGNMENT_RE = re.compile(
    r"(?im)^\s*(?P<name>[A-Za-z_]\w*(?:html|json|csv|fixture|payload|body|response))"
    r"\s*=\s*(?:[rubf]{0,3})?(?:\"\"\"|''')"
)
INLINE_RESPONSE_RE = re.compile(
    r"(?is)FakeResponse\s*\(\s*['\"](?:<html|\{\s*['\"]|\[\s*['\"]|"
    r"blocked|error|plain text)"
)
# A few binary/structured parser tests build a small payload through a helper
# (for example an in-memory XLSX) instead of assigning a triple-quoted string.
# Require the helper to be clearly fixture-oriented and to construct bytes, so
# ordinary test utilities are not reported as source evidence.
INLINE_BUILDER_RE = re.compile(
    r"(?ism)^\s*def\s+\w*(?:xlsx|inline)\w*fixture\w*\s*\([^)]*\).*?"
    r"(?:BytesIO|ZipFile|<html|FakeResponse)"
)
FIXTURE_LITERAL_RE = re.compile(
    r"(?i)(?:tests[\\/]fixtures[\\/])?([A-Za-z0-9_.-]+\.(?:html|json|csv|txt))"
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _fixture_refs(root: Path, source_id: str) -> set[str]:
    refs: set[str] = set()
    paths = (
        Path("docs/providers") / source_id / "README.md",
        Path("docs/source-contracts") / f"{source_id}.md",
    )
    for relative in paths:
        path = root / relative
        if path.is_file():
            refs.update(match.group(1) for match in FIXTURE_REF.finditer(_read(path)))
    return refs


def _test_files(root: Path, source_id: str) -> list[str]:
    matches: list[str] = []
    for path in (root / "tests").rglob("*"):
        # Fixture files are evidence inputs, not tests. Counting them here
        # made a provider appear covered even when no test exercised it.
        if not path.is_file() or path.suffix != ".py" or not path.name.startswith("test_"):
            continue
        try:
            text = _read(path)
        except OSError:
            continue
        # Prefer provider-specific test modules. Generic inventory/registry
        # tests mention every source id, but they do not exercise that
        # provider's parser or transport and would contaminate evidence.
        test_stem = path.stem.removeprefix("test_")
        if source_id in test_stem or source_id in path.name:
            matches.append(path.relative_to(root).as_posix())
            continue
        # Shared-family tests (for example state eproc adapters) can exercise
        # more than one provider without naming every source in the filename.
        # Count them only when the test imports provider code; generic catalog
        # inventory tests that merely mention source ids remain excluded.
        if source_id in text and "nanojuris.providers" in text:
            matches.append(path.relative_to(root).as_posix())
    return sorted(matches)


def _test_fixture_refs(root: Path, test_paths: list[str], source_id: str) -> set[str]:
    """Extract fixture filenames explicitly loaded by provider tests."""

    refs: set[str] = set()
    for relative in test_paths:
        text = _read(root / relative)
        for match in FIXTURE_LITERAL_RE.finditer(text):
            name = match.group(1)
            # A shared test module may exercise several adapters with
            # different response fixtures. Do not attribute a TJSP/TNU
            # response to TJRJ/TJSC merely because the same parser is reused;
            # a fixture filename must identify this source unless the test
            # module itself is provider-specific.
            provider_specific_test = source_id in Path(relative).stem
            if not provider_specific_test and source_id not in name:
                continue
            if (root / "tests" / "fixtures" / name).is_file():
                refs.add(name)
    return refs


def _inline_fixture_evidence(
    root: Path, test_paths: list[str], source_id: str
) -> list[dict[str, Any]]:
    """Return conservative evidence for responses embedded directly in tests."""

    evidence: list[dict[str, Any]] = []
    for relative in test_paths:
        # Shared-family modules can contain inline responses for another
        # adapter. Unless the filename is source-specific, avoid attributing
        # those literals to this provider.
        if source_id not in Path(relative).stem:
            continue
        text = _read(root / relative)
        names = sorted({match.group("name") for match in INLINE_ASSIGNMENT_RE.finditer(text)})
        direct_response = bool(INLINE_RESPONSE_RE.search(text))
        builder = bool(INLINE_BUILDER_RE.search(text))
        if names or direct_response or builder:
            evidence.append(
                {
                    "test": relative,
                    "named_payloads": names,
                    "direct_response_literals": direct_response,
                    "in_memory_builder": builder,
                }
            )
    return evidence


def _runtime_registered(root: Path, source_id: str) -> bool:
    module_marker = f"providers.{source_id}"
    for relative in (Path("src/nanojuris/client.py"), Path("src/nanojuris/providers/__init__.py")):
        path = root / relative
        if path.is_file() and module_marker in _read(path):
            return True
    return False


def _fixture_analysis(root: Path, source_id: str, fixture_names: set[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    dossier = root / "docs/providers" / source_id / "README.md"
    urls = URL_RE.findall(_read(dossier)) if dossier.is_file() else []
    base_url = next(
        (url.rstrip(".,") for url in urls if urlparse(url).scheme),
        "https://local.invalid/",
    )
    for name in sorted(fixture_names):
        path = root / "tests/fixtures" / name
        if not path.is_file():
            results.append(
                {"fixture": path.relative_to(root).as_posix(), "status": "missing_reference"}
            )
            continue
        body = path.read_bytes()
        content_type = "application/json" if path.suffix.lower() == ".json" else "text/html"
        probe = analyze_route_response(
            url=base_url,
            final_url=base_url,
            method="GET",
            status_code=200,
            content=body,
            content_type=content_type,
            elapsed_ms=0,
        )
        routes = extract_route_candidates(base_url, body, content_type)
        selectors = suggest_selector_candidates(
            body,
            {
                "decision_text": ("ementa", "decisão", "decisao"),
                "identifier": ("processo", "acórdão", "acordao"),
            },
        )
        results.append(
            {
                "fixture": path.relative_to(root).as_posix(),
                "status": "analyzed",
                "bytes": len(body),
                "probe_status": probe.route_status,
                "probe_access_signals": probe.access_signals,
                "routes": len(routes),
                "selectors": len(selectors),
                "route_samples": [candidate.to_dict() for candidate in routes[:8]],
                "selector_samples": [candidate.to_dict() for candidate in selectors[:8]],
            }
        )
    return results


def audit(root: Path, catalog_path: Path) -> dict[str, Any]:
    catalog = json.loads(_read(catalog_path))
    entries = catalog["entries"]
    records: list[dict[str, Any]] = []
    for entry in entries:
        source_id = str(entry["source_id"])
        implementation_status = str(entry.get("implementation_status", "unknown"))
        module_path = root / "src/nanojuris/providers" / f"{source_id}.py"
        dossier_path = root / "docs/providers" / source_id / "README.md"
        contract_path = root / "docs/source-contracts" / f"{source_id}.md"
        fixture_names = _fixture_refs(root, source_id)
        tests = _test_files(root, source_id)
        fixture_names.update(_test_fixture_refs(root, tests, source_id))
        inline_fixture_evidence = _inline_fixture_evidence(root, tests, source_id)
        needs_discovery = implementation_status in {"none", "family"}
        fixture_analysis = (
            _fixture_analysis(root, source_id, fixture_names) if needs_discovery else []
        )
        documentation = entry.get("documentation") or {}
        maturity = entry.get("maturity_score") or {}
        blockers: list[str] = []
        if implementation_status == "none" and not module_path.is_file():
            blockers.append("no_runtime_module")
        if implementation_status == "family" and not module_path.is_file():
            blockers.append("family_requires_concrete_member")
        if not fixture_names:
            blockers.append("no_checked_in_fixture_reference")
        if not tests:
            blockers.append("no_local_test_reference")
        if documentation.get("open_items", 0):
            blockers.append("open_documentation_items")
        if not dossier_path.is_file():
            blockers.append("missing_canonical_dossier")
        if not contract_path.is_file():
            blockers.append("missing_legacy_contract_copy")
        records.append(
            {
                "source_id": source_id,
                "display_name": entry.get("display_name", source_id),
                "implementation_status": implementation_status,
                "coverage_role": entry.get("coverage_role"),
                "development_priority": entry.get("development_priority"),
                "maturity_score": maturity.get("total"),
                "maturity_grade": maturity.get("grade"),
                "next_actions": list(maturity.get("next_actions") or []),
                "module": (
                    module_path.relative_to(root).as_posix() if module_path.is_file() else None
                ),
                "runtime_registered": _runtime_registered(root, source_id),
                "canonical_dossier": dossier_path.is_file(),
                "legacy_contract": contract_path.is_file(),
                "documentation_readiness": documentation.get("readiness"),
                "documentation_open_items": documentation.get("open_items", 0),
                "fixture_references": sorted(fixture_names),
                "test_references": tests,
                "inline_fixture_evidence": inline_fixture_evidence,
                "fixture_evidence_kind": (
                    "versioned_and_inline"
                    if fixture_names and inline_fixture_evidence
                    else "versioned_fixture"
                    if fixture_names
                    else "inline_test_only"
                    if inline_fixture_evidence
                    else "none"
                ),
                "blockers": blockers,
                "offline_discovery": fixture_analysis,
                "offline_evidence_status": (
                    "analyzed_local_fixtures"
                    if any(item.get("status") == "analyzed" for item in fixture_analysis)
                    else "no_local_fixture"
                ),
            }
        )

    mapped = [item for item in records if item["implementation_status"] == "none"]
    family = [item for item in records if item["implementation_status"] == "family"]
    runtime = [
        item for item in records if item["implementation_status"] in {"implemented", "runtime"}
    ]
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "offline_only",
        "network_access": "not_used",
        "catalog": catalog_path.relative_to(root).as_posix(),
        "summary": {
            "catalog_entries": len(records),
            "implementation_status": dict(
                sorted(Counter(item["implementation_status"] for item in records).items())
            ),
            "mapped_unimplemented": len(mapped),
            "family_entries": len(family),
            "mapped_without_local_fixture": sum(
                item["offline_evidence_status"] == "no_local_fixture" for item in mapped
            ),
            "local_discovery_runs": sum(len(item["offline_discovery"]) for item in records),
            "runtime_providers": len(runtime),
            "runtime_with_versioned_fixture": sum(
                bool(item["fixture_references"]) for item in runtime
            ),
            "runtime_inline_test_only": sum(
                item["fixture_evidence_kind"] == "inline_test_only" for item in runtime
            ),
            "runtime_without_fixture_evidence": sum(
                item["fixture_evidence_kind"] == "none" for item in runtime
            ),
        },
        "mapped_candidates": sorted(
            mapped,
            key=lambda item: (
                item["maturity_score"] is None,
                item["maturity_score"] or 0,
                item["source_id"],
            ),
        ),
        "family_entries": family,
        "all_entries": records,
        "interpretation": [
            "Este relatório não executa HTTP, Playwright nem consulta endpoint externo.",
            (
                "Ausência de fixture local significa ausência de evidência offline, "
                "não resultado vazio da fonte."
            ),
            (
                "Um provider só pode ser promovido após contrato de entrada/saída, "
                "fixture, parser canônico, estados de falha e testes."
            ),
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Auditoria offline de descoberta de providers",
        "",
        f"Gerado em `{report['generated_at']}`. Modo: **offline-only**; rede utilizada: **não**.",
        "",
        "## Resultado executivo",
        "",
        f"- Entradas no catálogo: **{summary['catalog_entries']}**.",
        f"- Candidates sem provider runtime: **{summary['mapped_unimplemented']}**.",
        f"- Entradas de família: **{summary['family_entries']}**.",
        f"- Candidates sem fixture local: **{summary['mapped_without_local_fixture']}**.",
        f"- Análises de fixtures executadas: **{summary['local_discovery_runs']}**.",
        f"- Providers runtime auditados: **{summary['runtime_providers']}**; "
        f"com fixture versionada: **{summary['runtime_with_versioned_fixture']}**.",
        f"- Providers runtime somente com payload inline: "
        f"**{summary['runtime_inline_test_only']}**; sem evidência de fixture: "
        f"**{summary['runtime_without_fixture_evidence']}**.",
        "",
        (
            "A ausência de fixture local não é tratada como `empty`: é uma lacuna de "
            "evidência. O catálogo e os status live foram apenas lidos; não foram "
            "revalidados contra a internet."
        ),
        "",
        "## Candidates mapeados, ainda não implementados",
        "",
        (
            "| Provider | Score | Dossiê | Contrato | Fixture local | Teste local | "
            "Bloqueadores | Próxima ação |"
        ),
        "| --- | ---: | :---: | :---: | :---: | :---: | --- | --- |",
    ]
    for item in report["mapped_candidates"]:
        blockers = ", ".join(item["blockers"]) or "—"
        next_action = "; ".join(item["next_actions"]) or "revisar dossier"
        lines.append(
            f"| `{item['source_id']}` | {item['maturity_score'] or '—'} | "
            f"{'sim' if item['canonical_dossier'] else 'não'} | "
            f"{'sim' if item['legacy_contract'] else 'não'} | "
            f"{'sim' if item['fixture_references'] else 'não'} | "
            f"{'sim' if item['test_references'] else 'não'} | {blockers} | {next_action} |"
        )
    runtime_inline = [
        item
        for item in report["all_entries"]
        if item["implementation_status"] in {"implemented", "runtime"}
        and item["fixture_evidence_kind"] == "inline_test_only"
    ]
    runtime_without_evidence = [
        item
        for item in report["all_entries"]
        if item["implementation_status"] in {"implemented", "runtime"}
        and item["fixture_evidence_kind"] == "none"
    ]
    lines += [
        "",
        "## Evidência dos providers runtime",
        "",
        (
            "A auditoria separa fixture versionada de payload embutido no teste. "
            "Payload inline não é promovido automaticamente a fixture: ele deve "
            "ser extraído somente quando o conteúdo já estiver versionado e sanitizado."
        ),
        "",
        "### Somente payload inline",
        "",
    ]
    if runtime_inline:
        lines.extend(
            f"- `{item['source_id']}`: "
            + "; ".join(evidence["test"] for evidence in item["inline_fixture_evidence"])
            for item in runtime_inline
        )
    else:
        lines.append("- Nenhum provider runtime identificado.")
    lines += ["", "### Sem fixture nem payload inline", ""]
    if runtime_without_evidence:
        lines.extend(f"- `{item['source_id']}`" for item in runtime_without_evidence)
    else:
        lines.append("- Nenhum provider runtime identificado.")
    lines += [
        "",
        "## Execução prática sobre evidência local",
        "",
        (
            "A camada de discovery foi executada sobre referências de fixture encontradas "
            "nos dossiers. A família eproc possui evidências locais; os nove candidates "
            "mapeados não possuem fixture referenciada no repositório."
        ),
        "",
    ]
    for item in report["family_entries"]:
        lines.append(f"### `{item['source_id']}`")
        if not item["offline_discovery"]:
            lines.append("- Nenhuma fixture referenciada para análise offline.")
            continue
        for run in item["offline_discovery"]:
            lines.append(
                f"- `{run['fixture']}`: {run['bytes']} bytes, classificador offline "
                f"`{run['probe_status']}`, "
                f"{run['routes']} rotas candidatas e {run['selectors']} sugestões de seletores."
            )
    lines += [
        "",
        "## Decisão de promoção",
        "",
        (
            "Nenhum candidate foi promovido automaticamente. O próximo passo de cada "
            "candidate é obter uma evidência pública reproduzível e adicioná-la como "
            "fixture/HAR sanitizado, depois fechar o contrato e implementar em mudança "
            "SDD separada."
        ),
        "",
        "## Próxima ordem de trabalho",
        "",
        (
            "1. Escolher um candidate com contrato mais detalhado no dossier e obter "
            "fixture pública revisável."
        ),
        "2. Reexecutar este relatório para confirmar a presença da evidência local.",
        (
            "3. Criar parser e provider somente após fixture de sucesso, vazio/erro e "
            "detalhe quando disponível."
        ),
        "4. Atualizar catálogo gerado somente pelos geradores oficiais.",
        "",
        "Relatório JSON correspondente: `docs/provider-discovery/offline-audit.json`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--catalog", type=Path, default=Path("docs/registry/provider-catalog.full.json")
    )
    parser.add_argument(
        "--json-output", type=Path, default=Path("docs/provider-discovery/offline-audit.json")
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("docs/provider-discovery/offline-audit.md"),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = (
        (root / args.catalog).resolve()
        if not args.catalog.is_absolute()
        else args.catalog.resolve()
    )
    report = audit(root, catalog)
    json_output = (
        (root / args.json_output).resolve()
        if not args.json_output.is_absolute()
        else args.json_output.resolve()
    )
    markdown_output = (
        (root / args.markdown_output).resolve()
        if not args.markdown_output.is_absolute()
        else args.markdown_output.resolve()
    )
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
