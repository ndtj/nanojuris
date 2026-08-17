"""Deterministic FastAPI app used by Studio browser tests."""

from __future__ import annotations

import os
from typing import Any

from nanojuris.models import CanonicalDocument, ProviderCapabilities
from nanojuris.source_contracts import assess_source_contract
from nanojuris.web.app import create_app


class FakeStudioClient:
    """Small in-memory client that exercises the production Studio routes."""

    def __init__(self) -> None:
        self._capabilities = [
            _capability("tjdf_juris", "TJDFT - Jurisprudencia", risk="baixo"),
            _capability("tst_jurisprudencia", "TST - Jurisprudencia", risk="medio"),
            _capability("stf_informativo", "STF - Informativos", risk="baixo"),
            _capability("provider_empty", "Fonte sem resultados", risk="baixo", level=5),
            _capability("provider_failed", "Fonte indisponivel", risk="alto", level=3),
            _capability(
                "provider_restricted",
                "Fonte com controle de acesso",
                risk="alto",
                level=3,
            ),
        ]
        self.providers = {item.source: object() for item in self._capabilities}

    def list_sources(self) -> list[ProviderCapabilities]:
        return list(self._capabilities)

    def get_capabilities(self, *, source: str) -> ProviderCapabilities:
        for capability in self._capabilities:
            if capability.source == source:
                return capability
        raise KeyError(source)

    def get_source_contract(self, *, source: str) -> Any:
        return assess_source_contract(self.get_capabilities(source=source))

    def get_document(self, document_id: str, *, source: str) -> CanonicalDocument:
        return CanonicalDocument(
            id=document_id,
            source=source,
            document_type="acordao",
            content_type="text/plain",
            title="Inteiro teor de demonstracao",
            text="Inteiro teor publico de demonstracao para o Studio.",
            url="https://example.org/documento-publico",
            sha256="a" * 64,
            byte_size=51,
            raw_bytes=b"Inteiro teor publico de demonstracao para o Studio.",
        )

    def search_many(
        self,
        query: str,
        *,
        sources: list[str],
        page: int,
        page_size: int,
        canonical: bool,
        **filters: Any,
    ) -> dict[str, Any]:
        del canonical, filters
        results: list[dict[str, Any]] = []
        routing: list[dict[str, Any]] = []
        searched: list[str] = []
        skipped: list[str] = []

        for source in sources:
            if source == "provider_failed":
                routing.append(
                    {
                        "source": source,
                        "action": "failed",
                        "reason": "source_unavailable",
                        "message": "A fonte simulada esta indisponivel.",
                    }
                )
                continue
            if source == "provider_restricted":
                routing.append(
                    {
                        "source": source,
                        "action": "skipped",
                        "reason": "access_control_required",
                        "message": "A fonte exige validacao externa.",
                    }
                )
                skipped.append(source)
                continue

            searched.append(source)
            routing.append({"source": source, "action": "searched", "reason": "eligible"})
            if query.strip().lower() == "vazio" or source == "provider_empty":
                continue
            if source not in {"tjdf_juris", "tst_jurisprudencia", "stf_informativo"}:
                continue

            results.append(
                {
                    "id": f"{source}-demo-001",
                    "source": source,
                    "court": "TJDFT" if source == "tjdf_juris" else source.upper(),
                    "case_number": "0700000-00.2024.8.07.0001",
                    "case_class": "Apelacao Civel",
                    "rapporteur": "Des. Relator de Demonstracao",
                    "judging_body": "Turma de Demonstracao",
                    "judgment_date": "2024-05-10",
                    "publication_date": "2024-05-20",
                    "decision_type": "acordao",
                    "title": "Responsabilidade civil e reparacao de danos",
                    "summary": f"Resultado sintetico da fonte {source} para a consulta {query}.",
                    "document_url": "https://example.org/documento-publico"
                    if source == "stf_informativo"
                    else None,
                }
            )

        has_more = page == 1 and bool(results)
        if page > 1 and results:
            continuation = dict(results[0])
            continuation["id"] = f"{continuation['source']}-demo-002"
            continuation["title"] = "Segunda pagina de demonstracao"
            results = [continuation]

        return {
            "query": query,
            "page": page,
            "page_size": page_size,
            "total_available": len(results) + 1 if has_more else len(results),
            "total_returned": len(results),
            "deduplicated_total": len(results) + 1 if has_more else len(results),
            "observed_total_pages": 2 if has_more else page,
            "has_more": has_more,
            "next_page": page + 1 if has_more else None,
            "previous_page": page - 1 if page > 1 else None,
            "pagination_complete": not has_more,
            "collection_complete": not has_more,
            "completeness_reason": "janela de demonstracao parcial" if has_more else "completa",
            "sources": sources,
            "searched_sources": searched,
            "skipped_sources": skipped,
            "routing_summary": routing,
            "errors": [
                {
                    "source": "provider_failed",
                    "error": "A fonte simulada esta indisponivel.",
                }
            ]
            if "provider_failed" in sources
            else [],
            "results": results,
        }

    def validate_sources(self, *, sources, text, page_size, timeout):
        """Return deterministic validation states for the browser workflow."""

        del timeout
        reports = []
        for source in sources:
            if source == "provider_failed":
                status = "source_unavailable"
                message = "A fonte simulada esta indisponivel."
                returned = 0
            elif source == "provider_restricted":
                status = "blocked"
                message = "A fonte exige validacao externa."
                returned = 0
            elif source in {"stf_informativo", "provider_empty"}:
                status = "empty"
                message = None
                returned = 0
            else:
                status = "valid"
                message = None
                returned = 1
            reports.append(
                {
                    "source": source,
                    "status": status,
                    "checked_at": "2026-08-15T12:00:00+00:00",
                    "query_text": text,
                    "returned": returned,
                    "reported_total": returned,
                    "elapsed_ms": 12.0,
                    "checks": {},
                    "failed_checks": [],
                    "message": message,
                    "passed": status in {"valid", "empty"},
                }
            )
        summary = {}
        for report in reports:
            summary[report["status"]] = summary.get(report["status"], 0) + 1
        return {
            "query": {"text": text, "page_size": page_size},
            "checked_sources": list(sources),
            "reports": reports,
            "summary": summary,
            "complete": True,
            "passed": all(report["passed"] for report in reports),
        }


def _capability(
    source: str,
    display_name: str,
    *,
    risk: str,
    level: int | None = None,
) -> ProviderCapabilities:
    del level
    return ProviderCapabilities(
        source=source,
        display_name=display_name,
        source_url="https://example.org/fonte",
        category="court_jurisprudence",
        search_modes=["full_text", "case_number", "date_range"],
        document_types=["decision"],
        content_formats=["json"],
        canonical_records=["CanonicalDecision"],
        extracted_fields=[
            "case_number",
            "publication_date",
            "judgment_date",
            "rapporteur",
            "case_class",
            "judging_body",
        ],
        supports_full_text=True,
        supports_unified_search=True,
        supports_studio=True,
        pagination_mode="page",
        completeness_contract="fixture_complete",
        supported_filters=["text", "case_number", "date_range"],
        limitations=[f"Fonte de teste com risco {risk}."],
    )


# The compatibility suite must exercise the legacy entrypoint explicitly even
# when production defaults to Workbench at the root.
os.environ["NANOJURIS_WORKBENCH_DEFAULT"] = "0"
app = create_app(client=FakeStudioClient())
