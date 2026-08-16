"""Audit provider dossiers and generate a human/AI-readable maturity report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

REGISTRY_PATH = ROOT / "docs" / "registry" / "providers.json"
PROVIDERS_DIR = ROOT / "docs" / "providers"
LEGACY_DIR = ROOT / "docs" / "source-contracts"
REPORT_PATH = ROOT / "docs" / "provider-documentation-audit.md"

SECTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "identity": (r"^##\s+Identidade", r"^##\s+Identity", r"^# .*Pesquisa De"),
    "contract": (
        r"^##\s+Contrato",
        r"^##\s+Contract",
        r"^##\s+Rotas",
        r"^##\s+Superficies",
        r"^##\s+Canal",
        r"^##\s+Contrato pendente",
        r"^##\s+Evidencia institucional",
    ),
    "data": (
        r"^##\s+Dados",
        r"^##\s+Evidencia De Dados",
        r"^##\s+Campos canonicos",
        r"^##\s+Dados canonicos",
        r"^##\s+Campos extraidos",
        r"^##\s+Mapeamento Canonico",
        r"^##\s+Dados Retornados",
        r"^##\s+Evidencia De Resultado",
    ),
    "states": (
        r"^##\s+Comportamento",
        r"^##\s+Estados",
        r"^##\s+Diagnostico",
        r"^##\s+Limites",
        r"^##\s+Evidencia live",
        r"^##\s+Validacao live",
        r"^##\s+Evidencia",
        r"^##\s+Revalidacao",
    ),
    "fixtures": (
        r"^##\s+Fixtures",
        r"^##\s+Escopo De Fixture",
        r"^##\s+Criterio de promocao",
        r"^##\s+Promocao",
        r"^##\s+Fixtures necessarias",
        r"^##\s+Decisao",
    ),
    "mcp": (
        r"^##\s+MCP",
        r"^##\s+Uso Via MCP",
        r"^##\s+Uso via MCP",
        r"^##\s+Uso pelo MCP",
    ),
    "next_steps": (
        r"^##\s+Proximos passos",
        r"^##\s+Próximos passos",
        r"^##\s+Promocao Futura",
        r"^##\s+Decisao De Mapeamento",
        r"^##\s+Decisao Tecnica",
        r"^##\s+Criterio de promocao",
        r"^##\s+Promocao Para Provider",
    ),
}


def _has_section(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.MULTILINE | re.IGNORECASE) for pattern in patterns)


def _status(registry: dict[str, Any], source_id: str) -> str:
    for key, status in (
        ("implemented", "implemented"),
        ("candidates", "candidate"),
        ("families", "family"),
    ):
        if source_id in registry.get(key, []):
            return status
    return "unregistered"


def _assessment_map() -> dict[str, Any]:
    try:
        from nanojuris.client import NanoJurisClient

        return {item.source: item for item in NanoJurisClient().list_source_contracts()}
    except (ImportError, AttributeError):
        return {}


def audit() -> list[dict[str, Any]]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assessments = _assessment_map()
    source_ids = sorted(
        set(registry["implemented"]) | set(registry["candidates"]) | set(registry["families"])
    )
    rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        path = PROVIDERS_DIR / source_id / "README.md"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        status = _status(registry, source_id)
        assessment = assessments.get(source_id)
        sections = {
            name: _has_section(text, patterns) for name, patterns in SECTION_PATTERNS.items()
        }
        missing = [name for name, present in sections.items() if not present]
        unchecked = len(re.findall(r"(?m)^- \[ \]", text))
        checked = len(re.findall(r"(?m)^- \[[xX]\]", text))
        fixture_refs = sorted(set(re.findall(r"tests/fixtures/[A-Za-z0-9_./-]+", text)))
        if status == "family":
            readiness = "family_spec"
        elif status == "candidate":
            readiness = "research_ready" if not missing else "research_incomplete"
        elif missing or unchecked:
            readiness = "needs_deepening"
        else:
            readiness = "implementation_ready"
        legacy = LEGACY_DIR / f"{source_id}.md"
        rows.append(
            {
                "source_id": source_id,
                "status": status,
                "readiness": readiness,
                "contract_level": assessment.contract_level if assessment else None,
                "risk": assessment.risk_level if assessment else "research",
                "missing_sections": missing,
                "unchecked": unchecked,
                "checked": checked,
                "fixture_references": fixture_refs,
                "canonical_path": f"docs/providers/{source_id}/README.md",
                "legacy_path": f"docs/source-contracts/{source_id}.md",
                "parity": path.is_file()
                and legacy.is_file()
                and path.read_bytes() == legacy.read_bytes(),
            }
        )
    return rows


def render(rows: list[dict[str, Any]]) -> str:
    today = _snapshot_date()
    readiness = Counter(row["readiness"] for row in rows)
    statuses = Counter(row["status"] for row in rows)
    structurally_complete = sum(not row["missing_sections"] for row in rows)
    parity_ok = sum(row["parity"] for row in rows)
    readiness_summary = ", ".join(f"`{key}`={value}" for key, value in sorted(readiness.items()))
    lines = [
        "# Provider Documentation Audit",
        "",
        f"Snapshot local: `{today}`. Este relatorio e uma fotografia reproduzivel "
        "do estado documental;",
        "nao afirma que uma rota nao observada exista nem que um provider esteja "
        "disponivel em qualquer rede.",
        "",
        "## Como Ler",
        "",
        "- `implemented`: existe no runtime; o nivel e risco vem de `source_contracts`.",
        "- `candidate`: existe pesquisa documental, mas nao existe provider runtime.",
        "- `family`: contrato compartilhado de implementacao, nao uma fonte executavel isolada.",
        "- `needs_deepening`: provider implementado com lacunas documentais ou checklist aberto.",
        "- `research_incomplete`: candidato ainda sem alguma secao obrigatoria.",
        "- `research_ready`: candidato documentado para a proxima fase, ainda sem "
        "autorizacao para codigo.",
        "",
        "## Resumo",
        "",
        f"- Dossies auditados: **{len(rows)}** ({statuses['implemented']} "
        f"implemented, {statuses['candidate']} candidates, {statuses['family']} family).",
        f"- Dossies com secoes estruturais: **{structurally_complete}/{len(rows)}**.",
        f"- Canonical/legacy em paridade: **{parity_ok}/{len(rows)}**.",
        f"- Prontidao: {readiness_summary}.",
        "",
        "A paridade confirma preservacao de informacao durante a migracao. Ela nao "
        "substitui a revisao",
        "do contrato: itens `[ ]`, estados `pendente` e rotas apenas observadas "
        "continuam sendo bloqueios reais.",
        "",
        "A evidencia live mais recente esta em "
        "[live-validation-latest.md](live-validation-latest.md).",
        "A evidencia historica das 28 fontes candidatas esta em "
        "[candidate-live-validation-2026-08-11.md](candidate-live-validation-2026-08-11.md).",
        "",
        "## Matriz Por Provider",
        "",
        "| Provider | Ciclo | Prontidao | Nivel | Risco | Secoes faltantes | "
        "Pendencias | Fixtures referenciadas |",
        "| --- | --- | --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        missing = ", ".join(row["missing_sections"]) or "-"
        level = str(row["contract_level"]) if row["contract_level"] is not None else "-"
        lines.append(
            f"| [`{row['source_id']}`]({row['canonical_path']}) | {row['status']} | `"
            f"{row['readiness']}` | {level} | {row['risk']} | {missing} | "
            f"{row['unchecked']} | {len(row['fixture_references'])} |"
        )
    lines.extend(
        [
            "",
            "## Gate De Desenvolvimento",
            "",
            "Antes de implementar um candidato, o mantenedor deve fechar, no dossie "
            "e em fixture, os itens abaixo:",
            "",
            "1. rota e metodo reproduzidos com sessao publica limpa;",
            "2. payload, filtros, paginacao, ordenacao e limites confirmados;",
            "3. sucesso, vazio, erro, controle de acesso e timeout classificados;",
            "4. campos canonicos e campos ausentes/variaveis mapeados;",
            "5. fixture pequena, teste offline e teste de contrato;",
            "6. decisao explicita para documento, MCP, rate limit e uso responsavel.",
            "",
            "O proximo passo de cada fonte esta no proprio dossie. Para atualizar este relatorio:",
            "",
            "```bash",
            "python tools/audit_provider_docs.py --write",
            "```",
            "",
            "A especificacao completa esta em "
            "[provider-dossier-template.md](provider-dossier-template.md).",
        ]
    )
    return "\n".join(lines) + "\n"


def _snapshot_date() -> str:
    """Return a stable generated-doc snapshot date.

    Generated documentation must be reproducible in CI even when the runner is
    already in a different UTC date than the local machine that wrote the file.
    Reuse the committed report date when present; new reports fall back to the
    current local date.
    """

    if REPORT_PATH.is_file():
        match = re.search(
            r"Snapshot local:\s+`(?P<date>\d{4}-\d{2}-\d{2})`",
            REPORT_PATH.read_text(encoding="utf-8"),
        )
        if match:
            return match.group("date")
    return date.today().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the generated report")
    args = parser.parse_args()
    report = render(audit())
    if args.write:
        REPORT_PATH.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
