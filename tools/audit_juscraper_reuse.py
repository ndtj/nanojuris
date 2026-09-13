"""Audit the Juscraper reuse boundary without importing or executing upstream.

This is a security/provenance preflight.  It verifies the fixed upstream
license snapshot and scans NanoJuris runtime sources for accidental imports or
path references.  It cannot decide whether court data may be redistributed;
that remains an explicit human/legal gate.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPSTREAM = ROOT.parent.parent / ".artifacts" / "juscraper-upstream-20260901"
DEFAULT_INTAKE = ROOT / "docs" / "provider-discovery" / "juscraper-intake-20260901.json"
DEFAULT_BOARD = ROOT / "docs" / "provider-discovery" / "adapter-wave-board-20260901.json"
DEFAULT_OUTPUT = ROOT / "docs" / "provider-discovery" / "juscraper-reuse-audit-20260901.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "provider-discovery" / "juscraper-reuse-audit-20260901.md"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _runtime_import_violations(runtime_root: Path) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    if not runtime_root.is_dir():
        return [{"kind": "runtime_root_missing", "path": str(runtime_root)}]
    for path in sorted(runtime_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError) as exc:
            violations.append({"kind": "runtime_parse_error", "path": str(path), "error": str(exc)})
            continue
        for node in ast.walk(tree):
            module = ""
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name
                    if module == "juscraper" or module.startswith("juscraper."):
                        violations.append(
                            {
                                "kind": "upstream_import",
                                "path": str(path),
                                "line": node.lineno,
                                "module": module,
                            }
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module == "juscraper" or module.startswith("juscraper."):
                    violations.append(
                        {
                            "kind": "upstream_import",
                            "path": str(path),
                            "line": node.lineno,
                            "module": module,
                        }
                    )
    return violations


def _runtime_path_references(runtime_root: Path) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    if not runtime_root.is_dir():
        return references
    needles = ("juscraper-upstream", "juscraper.courts", "from juscraper", "import juscraper")
    for path in sorted(runtime_root.rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if any(needle in line.lower() for needle in needles):
                references.append({"path": str(path), "line": line_number})
    return references


def _check(name: str, status: str, evidence: dict[str, Any], note: str) -> dict[str, Any]:
    return {"name": name, "status": status, "evidence": evidence, "note": note}


def audit(
    *,
    upstream_root: Path = DEFAULT_UPSTREAM,
    intake_path: Path = DEFAULT_INTAKE,
    board_path: Path = DEFAULT_BOARD,
    runtime_root: Path = ROOT / "src" / "nanojuris",
    generated_at: str | None = None,
) -> dict[str, Any]:
    try:
        intake = json.loads(intake_path.read_text(encoding="utf-8"))
        board = json.loads(board_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("intake ou board invalido") from exc
    license_path = upstream_root / "LICENSE"
    expected_hash = str(intake.get("upstream", {}).get("license_file_sha256", ""))
    actual_hash = _sha256(license_path) if license_path.is_file() else None
    import_violations = _runtime_import_violations(runtime_root)
    path_references = _runtime_path_references(runtime_root)
    board_items = board.get("items", [])
    promotion_guard = bool(board.get("no_runtime_promotion")) and all(
        row.get("runtime_promotion") == "forbidden_until_0031_0034_and_human_review"
        for row in board_items
    )
    checks = [
        _check(
            "upstream_license_snapshot",
            "pass" if actual_hash and actual_hash == expected_hash else "fail",
            {
                "path": str(license_path),
                "expected_sha256": expected_hash,
                "actual_sha256": actual_hash,
            },
            "Confirma apenas a identidade do arquivo LICENSE do snapshot fixado.",
        ),
        _check(
            "runtime_import_boundary",
            "pass" if not import_violations else "fail",
            {"violations": import_violations},
            "O runtime nao pode importar Juscraper nem suas classes.",
        ),
        _check(
            "runtime_path_boundary",
            "pass" if not path_references else "fail",
            {"references": path_references},
            "O runtime nao pode depender do checkout upstream por caminho ou texto de import.",
        ),
        _check(
            "candidate_promotion_guard",
            "pass" if promotion_guard else "fail",
            {"board": str(board_path), "items": len(board_items)},
            "Toda unidade da onda permanece bloqueada ate os gates de release e revisao humana.",
        ),
        _check(
            "data_redistribution_review",
            "pending_human_review",
            {
                "upstream_commit": intake.get("upstream", {}).get("commit"),
                "license": intake.get("upstream", {}).get("license_declared"),
            },
            "MIT do codigo nao decide a permissao de redistribuir dados judiciais; "
            "requer parecer proprio.",
        ),
    ]
    generated = generated_at or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "generated_at": generated,
        "audit_mode": "offline_reuse_security_preflight",
        "upstream": {
            "repository": intake.get("upstream", {}).get("repository"),
            "commit": intake.get("upstream", {}).get("commit"),
            "license_declared": intake.get("upstream", {}).get("license_declared"),
        },
        "runtime_root": str(runtime_root),
        "checks": checks,
        "overall": "preflight_pass_human_review_pending"
        if all(check["status"] == "pass" for check in checks[:4])
        else "preflight_failed",
        "no_runtime_promotion": True,
        "limitations": [
            "A auditoria nao e parecer juridico e nao autoriza redistribuicao de acervo.",
            "A auditoria nao importa, executa ou copia o Juscraper.",
            "A ausencia de import nao prova equivalencia semantica dos adapters.",
        ],
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Auditoria de reuso Juscraper (2026-09-01)",
        "",
        "Preflight offline de seguranca e provenance; nao e parecer juridico e nao "
        "promove adapters.",
        "",
        f"- Commit upstream: `{report['upstream'].get('commit')}`",
        f"- Resultado: **{report['overall']}**",
        "",
        "| Check | Estado | Nota |",
        "| --- | --- | --- |",
    ]
    for check in report["checks"]:
        lines.append(f"| `{check['name']}` | `{check['status']}` | {check['note']} |")
    lines.extend(["", "## Limites", ""])
    lines.extend(f"- {value}" for value in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    parser.add_argument("--intake", type=Path, default=DEFAULT_INTAKE)
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    report = audit(
        upstream_root=args.upstream,
        intake_path=args.intake,
        board_path=args.board,
        generated_at=args.generated_at,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(to_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "overall": report["overall"],
                "checks": [check["status"] for check in report["checks"]],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
