"""Build a conservative documentation inventory for maintainers and agents."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "documentation-inventory.md"
EXCLUDED_PARTS = {".git", ".venv", "dist", "build", ".pytest_cache", "node_modules"}


def tracked_documents() -> list[Path]:
    """Return NanoJuris root and docs Markdown documents only."""

    documents = list(ROOT.glob("*.md"))
    docs_root = ROOT / "docs"
    for path in docs_root.rglob("*.md"):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative == OUTPUT.relative_to(ROOT):
            continue
        documents.append(relative)
    root_documents = [path.relative_to(ROOT) for path in documents if path.is_absolute()]
    return sorted(
        root_documents + [path for path in documents if not path.is_absolute()],
        key=lambda item: item.as_posix(),
    )


def classify(path: Path) -> tuple[str, str, str]:
    """Classify a document without guessing that historical evidence is disposable."""

    value = path.as_posix()
    name = path.name
    if value.startswith("docs/providers/") and name == "README.md":
        return "canonical", "manter", "Dossie tecnico canônico por provider."
    if value.startswith("docs/source-contracts/") and name != "README.md":
        return (
            "compatibility_copy",
            "manter",
            "Copia legada com links, catalogo e testes de paridade ativos.",
        )
    if value.startswith("docs/coverage/"):
        if value == "docs/coverage/maturity-waves.md":
            return (
                "active_guide",
                "revisar_periodicamente",
                "Plano mantido manualmente; os indicadores de cobertura sao gerados separadamente.",
            )
        return "generated", "manter", "Gerado por build_provider_coverage.py."
    if value.startswith("docs/validation/runs/"):
        return "historical_evidence", "manter", "Evidencia live estruturada e auditavel."
    if value.startswith("docs/qa/") or re.search(
        r"(?:audit|validation|mapping|research|survey)-\d{4}-\d{2}-\d{2}", value
    ):
        return "historical_evidence", "manter", "Registro de pesquisa, QA ou validacao."
    if value in {
        "README.md",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "GOVERNANCE.md",
        "MAINTAINERS.md",
        "CHANGELOG.md",
        "SPECS.md",
        "docs/README.md",
        "docs/architecture.md",
        "docs/responsible-use.md",
        "docs/provider-dossier-template.md",
        "docs/quickstart.md",
        "docs/mcp.md",
        "docs/storage.md",
        "docs/provider-development.md",
        "docs/route-mapping-playbook.md",
    }:
        return "canonical", "manter", "Entrada normativa, de produto ou de governanca."
    if value.startswith("docs/registry/"):
        return "canonical", "manter", "Catalogo, schema ou indice de integracao."
    return (
        "active_guide",
        "revisar_periodicamente",
        "Guia ativo; nao ha base automatica para remocao.",
    )


def reference_count(path: Path, corpus: dict[Path, str]) -> int:
    """Count explicit repository-path references, excluding the document itself."""

    needle = path.as_posix()
    alternatives = {needle, f"../{needle}"}
    if path.name != "README.md":
        alternatives.add(path.name)
    count = 0
    for candidate, content in corpus.items():
        if candidate == path:
            continue
        if any(value in content for value in alternatives):
            count += 1
    return count


def build_report() -> str:
    documents = tracked_documents()
    corpus_paths = list(documents)
    corpus_paths.extend(path.relative_to(ROOT) for path in (ROOT / "src").rglob("*.py"))
    corpus_paths.extend(path.relative_to(ROOT) for path in (ROOT / "tests").rglob("*.py"))
    corpus = {
        path: (ROOT / path).read_text(encoding="utf-8", errors="replace") for path in corpus_paths
    }
    rows: list[str] = []
    counts: dict[str, int] = {}
    for path in documents:
        kind, action, reason = classify(path)
        counts[kind] = counts.get(kind, 0) + 1
        references = reference_count(path, corpus)
        rows.append(f"| `{path.as_posix()}` | `{kind}` | {references} | {reason} | `{action}` |")

    summary = ", ".join(f"`{kind}`={count}" for kind, count in sorted(counts.items()))
    return "\n".join(
        [
            "# Inventario Documental",
            "",
            "Gerado por `python tools/audit_documentation_inventory.py --write`. "
            "Este inventario orienta consolidacoes sem apagar contratos, evidencias "
            "ou caminhos de compatibilidade sem uma migracao explicita.",
            "",
            f"Documentos inventariados: **{len(documents)}** ({summary}).",
            "",
            "## Regra De Limpeza",
            "",
            "Um item somente pode ser removido quando nao tiver referencias, conteudo "
            "unico, funcao canonica, funcao de compatibilidade ou valor de evidencia. "
            "Nesta rodada, nenhuma exclusao automatica e recomendada.",
            "",
            "| Arquivo | Papel | Referencias | Conteudo/justificativa | Acao |",
            "| --- | --- | ---: | --- | --- |",
            *rows,
            "",
            "## Caminhos Duplicados Intencionais",
            "",
            "`docs/providers/<source_id>/README.md` e o dossie canonico. "
            "`docs/source-contracts/<source_id>.md` continua como copia de "
            "compatibilidade enquanto catalogo, links e testes de paridade apontarem "
            "para ele. A consolidacao futura deve trocar cada copia por um apontador "
            "curto somente depois de migrar referencias e remover a regra de paridade.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write the Markdown inventory.")
    args = parser.parse_args()
    report = build_report()
    if args.write:
        OUTPUT.write_text(report, encoding="utf-8")
        print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
