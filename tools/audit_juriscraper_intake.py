"""Create an auditable, static intake record for jtrecenti/juscraper.

This tool reads a checked-out tree only. It never imports or executes the
upstream package, makes network calls, copies files, or infers live health.
The output is evidence for an adapter decision, not a runtime registry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None  # type: ignore[assignment]


UPSTREAM_URL = "https://github.com/jtrecenti/juscraper"
COURT_ID = re.compile(r"^tj[a-z0-9]+$")
METHOD = re.compile(
    r"(?m)^\s+(?:async\s+)?def\s+"
    r"(cjsg|cjpg|cjsg_parse|cjpg_parse|cjsg_download|cjpg_download|cjsg_ementa|cpopg|cposg)\b"
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _git(source: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(source), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _project_metadata(source: Path) -> dict[str, str]:
    path = source / "pyproject.toml"
    if tomllib is None or not path.is_file():
        return {}
    data = tomllib.loads(_read(path))
    project = data.get("project", {})
    metadata: dict[str, str] = {}
    for key in ("name", "version", "description"):
        if key in project:
            metadata[key] = str(project[key]).strip()
    license_value = project.get("license")
    if isinstance(license_value, dict) and "file" in license_value:
        metadata["license"] = str(license_value["file"]).strip()
    elif license_value is not None:
        metadata["license"] = str(license_value).strip()
    return metadata


def _methods(court_dir: Path) -> list[str]:
    values: set[str] = set()
    for path in court_dir.rglob("*.py"):
        values.update(match.group(1) for match in METHOD.finditer(_read(path)))
    return sorted(values)


def _client_class(court_dir: Path) -> str | None:
    path = court_dir / "client.py"
    if not path.is_file():
        return None
    match = re.search(r"^class\s+(\w+Scraper)\b", _read(path), re.MULTILINE)
    return match.group(1) if match else None


def build_record(source: Path, generated_at: str | None = None) -> dict[str, Any]:
    source = source.resolve()
    package = source / "src" / "juscraper"
    courts_root = package / "courts"
    court_dirs = (
        sorted(
            path for path in courts_root.iterdir() if path.is_dir() and COURT_ID.match(path.name)
        )
        if courts_root.is_dir()
        else []
    )
    trf_dirs = (
        sorted(
            path
            for path in courts_root.iterdir()
            if path.is_dir() and re.match(r"^trf\d+$", path.name)
        )
        if courts_root.is_dir()
        else []
    )
    aggregators_root = package / "aggregators"
    aggregator_dirs = (
        sorted(path.name for path in aggregators_root.iterdir() if path.is_dir())
        if aggregators_root.is_dir()
        else []
    )
    metadata = _project_metadata(source)
    license_path = source / "LICENSE"
    courts = [
        {
            "source_id": path.name,
            "client_class": _client_class(path),
            "declared_methods": _methods(path),
            "classification": "candidate",
        }
        for path in court_dirs
    ]
    return {
        "schema_version": 2,
        "generated_at": generated_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "audit_mode": "static_source_only",
        "live_availability_claim": False,
        "upstream": {
            "repository": UPSTREAM_URL,
            "commit": _git(source, "rev-parse", "HEAD"),
            "commit_timestamp": _git(source, "show", "-s", "--format=%cI", "HEAD"),
            "version": metadata.get("version"),
            "license_declared": "MIT"
            if metadata.get("license") == "LICENSE"
            else metadata.get("license"),
            "license_file_sha256": (
                hashlib.sha256(license_path.read_bytes()).hexdigest()
                if license_path.is_file()
                else None
            ),
        },
        "observed_scope": {
            "description": metadata.get("description"),
            "brazilian_court_packages": len(court_dirs),
            "brazilian_source_ids": [path.name for path in court_dirs],
            "trf_packages": len(trf_dirs),
            "trf_source_ids": [path.name for path in trf_dirs],
            "aggregator_packages": aggregator_dirs,
            "court_packages": courts,
            "shared_surfaces": ["cjsg", "cjpg", "tjto.cjsg_ementa"],
            "process_surfaces": ["cpopg", "cposg"],
        },
        "nanojuris_surface_decisions": {
            "cjsg": {
                "count": 25,
                "classification": "candidate",
                "decision": "cross_reference_each_source_contract_and_fixture",
            },
            "cjpg": {
                "source_ids": ["tjes", "tjsp", "tjto"],
                "count": 3,
                "classification": "candidate",
                "decision": "keep_first_instance_separate_from_cjsg",
            },
            "tjto_cjsg_ementa": {
                "count": 1,
                "classification": "candidate",
                "decision": "lazy_detail_only_after_base_identity_gate",
            },
            "cpopg_cposg": {
                "classification": "out_of_scope",
                "decision": "do_not_register_as_textual_jurisprudence",
            },
            "aggregators": {
                "source_ids": aggregator_dirs,
                "classification": "out_of_scope_or_separate_domain",
                "decision": "do_not_promote_to_nanojuris_jurisprudence_runtime",
            },
        },
        "nanojuris_action": {
            "runtime_change": "none",
            "copied_upstream_code": False,
            "required_before_adapter": [
                "official source contract with method, payload, filters and pagination",
                "sanitized success, empty, error and schema-drift fixtures",
                "canonical output and legal identity mapping",
                "bounded live evidence from the official court surface",
                "license and terms review",
            ],
            "next_step": (
                "use the 25 TJ packages as candidates for differential review; "
                "promote only a source with independent NanoJuris evidence"
            ),
        },
    }


def _markdown(record: dict[str, Any]) -> str:
    upstream = record["upstream"]
    scope = record["observed_scope"]
    return f"""# Intake estático do Juscraper — 2026-09-01

Este registro audita o repositório correto (`jtrecenti/juscraper`) a partir de
uma árvore local fixada. Não executa código upstream, não copia arquivos, não
faz chamadas live e não altera o catálogo runtime.

## Proveniência

- Repositório: {upstream["repository"]}
- Commit: `{upstream["commit"]}` ({upstream["commit_timestamp"]})
- Versão: `{upstream["version"]}`
- Licença: `{upstream["license_declared"]}`
- SHA-256 de `LICENSE`: `{upstream["license_file_sha256"]}`

## Superfícies encontradas

O projeto declara {scope["brazilian_court_packages"]} pacotes de tribunais
estaduais brasileiros e {scope["trf_packages"]} pacotes TRF. A superfície
jurisprudencial útil para este intake é de 25 `cjsg`, três `cjpg` (TJES, TJSP e
TJTO) e um detalhe `tjto.cjsg_ementa`. `cpopg`/`cposg` são consultas
processuais e os agregadores (`{", ".join(scope["aggregator_packages"])}`) ficam
fora do runtime textual da NanoJuris.

## Decisão

Todas as superfícies upstream são `candidate`, não `implemented`: código e
fixtures ainda precisam de adaptação independente, contrato NanoJuris,
identidade jurídica, testes negativos e evidência live limitada por fonte.
Nenhum provider novo foi registrado ou promovido nesta auditoria.

O sweep live dos providers NanoJuris permanece separado em
`all-provider-sweep-20260901.json`. Evidência estática do Juscraper não prova
que uma rota de tribunal esteja disponível agora.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--generated-at")
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
