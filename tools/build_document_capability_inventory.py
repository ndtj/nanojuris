"""Build an offline inventory of document/full-text capabilities by provider.

The inventory is deliberately descriptive: it reads declared capabilities and
the registry, never calls a source and never promotes a provider.  Candidate
providers are included as ``candidate_opt_in`` so missing capabilities remain
visible without entering the default federation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = str(ROOT / "src")
# Always put the checkout first.  A globally installed NanoJuris (or another
# checkout injected by a workspace launcher) may already have added ``src``
# later in ``sys.path``; merely checking membership would then make this
# offline generator read the wrong provider declarations.
if SOURCE_ROOT in sys.path:
    sys.path.remove(SOURCE_ROOT)
sys.path.insert(0, SOURCE_ROOT)

from nanojuris.client import NanoJurisClient  # noqa: E402

REGISTRY = ROOT / "docs" / "registry" / "providers.json"
DEFAULT_JSON = ROOT / "docs" / "coverage" / "document-capability-inventory.json"
DEFAULT_MD = ROOT / "docs" / "coverage" / "document-capability-inventory.md"


def build() -> dict[str, Any]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    implemented = set(registry.get("implemented", []))
    candidates = set(registry.get("candidates", []))
    client = NanoJurisClient(include_candidate_providers=True)
    capabilities = {cap.source: cap for cap in client.list_sources()}
    source_ids = sorted(implemented | candidates | set(registry.get("families", [])))
    rows: list[dict[str, Any]] = []
    for source_id in source_ids:
        cap = capabilities.get(source_id)
        if cap is None:
            rows.append(
                {
                    "source_id": source_id,
                    "lifecycle": "candidate" if source_id in candidates else "family",
                    "runtime": False,
                    "opt_in_runtime": False,
                    "document_types": [],
                    "content_formats": [],
                    "supports_full_text": False,
                    "full_text_access": "unknown",
                    "detail_modes": [],
                    "document_endpoints": [],
                    "pipeline_policy": _pipeline_policy([]),
                    "extracted_fields": [],
                    "status": "not_declared",
                }
            )
            continue
        rows.append(
            {
                "source_id": source_id,
                "lifecycle": "implemented" if source_id in implemented else "candidate",
                "runtime": source_id in implemented,
                "opt_in_runtime": source_id in client.providers and source_id not in implemented,
                "document_types": list(cap.document_types),
                "content_formats": list(cap.content_formats),
                "supports_full_text": bool(cap.supports_full_text),
                "full_text_access": cap.full_text_access,
                "detail_modes": list(cap.detail_modes),
                "document_endpoints": list(cap.endpoints),
                "pipeline_policy": _pipeline_policy(cap.content_formats),
                "extracted_fields": list(cap.extracted_fields),
                "status": "declared",
            }
        )
    return {
        "schema_version": "1.0",
        "generated_by": "python tools/build_document_capability_inventory.py --write",
        "network_access": "not_used",
        "scope": "declared runtime and opt-in candidate capabilities; not live availability",
        "summary": {
            "sources": len(rows),
            "runtime": sum(1 for row in rows if row["runtime"]),
            "runtime_with_full_text": sum(
                1 for row in rows if row["runtime"] and row["supports_full_text"]
            ),
            "candidates": sum(1 for row in rows if row["lifecycle"] == "candidate"),
            "opt_in_runtime": sum(1 for row in rows if row["opt_in_runtime"]),
            "declared_document_routes": sum(1 for row in rows if row["document_endpoints"]),
        },
        "providers": rows,
    }


def _pipeline_policy(content_formats: list[str]) -> dict[str, Any]:
    """Expose the shared safety contract alongside source declarations."""

    formats = {str(value).casefold() for value in content_formats}
    extractors = []
    if "pdf" in formats or "application/pdf" in formats:
        extractors.append("pypdf")
        # OCR is available through the shared, bounded helper but remains an
        # explicit per-request opt-in; declaring it here must not promote a
        # provider or imply that every PDF is scanned.
        extractors.append("ocr_optional")
    if formats & {"html", "text/html", "xhtml"}:
        extractors.append("html_visible_text")
    if formats & {"json", "application/json"}:
        extractors.append("json_utf8")
    if formats & {"text", "plain", "text/plain"}:
        extractors.append("utf8_text")
    return {
        "max_bytes": 4_000_000,
        "redirect_policy": "https_allowlisted",
        "mime_policy": "declared_header_plus_magic_validation",
        "text_extractors": extractors,
        "pdf_page_count": "structural_when_pdf",
        "ocr_policy": "opt_in_with_page_time_budget",
        "hash": "sha256",
    }


def render(payload: dict[str, Any]) -> str:
    lines = [
        "# Inventário de capacidades documentais",
        "",
        "Gerado offline por `python tools/build_document_capability_inventory.py --write`.",
        "As declarações não significam disponibilidade live, autorização de reuso ou promoção.",
        "",
        f"Fontes: **{payload['summary']['sources']}**; "
        f"runtime: **{payload['summary']['runtime']}**; "
        f"runtime com inteiro teor: **{payload['summary']['runtime_with_full_text']}**; "
        f"candidatas: **{payload['summary']['candidates']}**; "
        f"runtime opt-in: **{payload['summary']['opt_in_runtime']}**.",
        "",
        "| Provider | Ciclo de vida | Runtime | Inteiro teor | Formatos | "
        "Rotas documentais | Acesso |",
        "| --- | --- | :---: | :---: | --- | ---: | --- |",
    ]
    for row in payload["providers"]:
        formats = ", ".join(row["content_formats"]) or "-"
        access = row["full_text_access"] or "unknown"
        lines.append(
            f"| `{row['source_id']}` | `{row['lifecycle']}` | "
            f"{'sim' if row['runtime'] else ('opt-in' if row['opt_in_runtime'] else 'não')} | "
            f"{'sim' if row['supports_full_text'] else 'não'} | {formats} | "
            f"{len(row['document_endpoints'])} | `{access}` |"
        )
    lines.extend(
        [
            "",
            "## Política",
            "",
            "Busca não baixa documentos automaticamente. O carregamento de inteiro teor exige",
            "rota HTTPS allowlisted, limite de bytes, hash, `SourceTrace` e "
            "classificação explícita",
            "de acesso. Providers candidatos ficam fora da federação até contrato e revisão legal.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write JSON and Markdown artifacts")
    args = parser.parse_args()
    payload = build()
    if args.write:
        DEFAULT_JSON.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        DEFAULT_MD.write_text(render(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
