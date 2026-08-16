"""Presentation helpers for the local NanoJuris Studio."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, cast

from nanojuris.client import NanoJurisClient
from nanojuris.models import ProviderCapabilities
from nanojuris.source_contracts import assess_source_contract
from nanojuris.validation import validate_sources
from nanojuris.web.schemas import StudioSearchRequest, StudioValidationRequest

UNIVERSAL_FILTERS = [
    "text",
    "case_number",
    "date_range",
    "decision_type",
    "full_text",
]

FIELD_FILTERS = {
    "case_number": "case_number",
    "number": "case_number",
    "publication_date": "date_range",
    "judgment_date": "date_range",
    "decision_type": "decision_type",
    "rapporteur": "rapporteur",
    "case_class": "case_class",
    "subject": "subject",
    "judging_body": "judging_body",
    "origin_county": "origin_county",
}


def studio_sources_payload(client: NanoJurisClient) -> dict[str, Any]:
    """Return source metadata tailored to a single-screen search UI."""

    sources = []
    for capability in client.list_sources():
        contract = assess_source_contract(capability)
        item = capability.to_dict()
        item["supported_filters"] = supported_filters_for(capability)
        item["recommended_for_studio"] = _is_studio_source(capability)
        item["contract_level"] = contract.contract_level
        item["contract_label"] = contract.contract_label
        item["risk_level"] = contract.risk_level
        item["jurimetry_fit"] = contract.jurimetry_fit
        item["studio_tier"] = _studio_tier(capability, contract.risk_level, contract.contract_level)
        item["documentation_url"] = (
            "https://github.com/ndtj/nanojuris/blob/main/docs/providers/"
            f"{capability.source}/README.md"
        )
        sources.append(item)
    return {
        "total": len(sources),
        "default_sources": _default_studio_sources(sources),
        "recommended_sources": [
            str(item["source"]) for item in sources if item.get("recommended_for_studio")
        ],
        "tier_counts": dict(Counter(str(item["studio_tier"]) for item in sources)),
        "selection_policy": {
            "default": "stable",
            "jurisprudence": "recommended",
            "all": "catalog",
            "default_explanation": (
                "O modo padrao seleciona fontes estaveis para uma primeira consulta previsivel."
            ),
            "jurisprudence_explanation": (
                "O modo jurisprudencia inclui fontes recomendadas, inclusive contratos avancados "
                "e fontes com risco de acesso explicitamente sinalizado."
            ),
            "all_explanation": (
                "O modo todas consulta todo o catalogo; fontes fora do escopo podem ser puladas "
                "pelo roteador e falhas permanecem visiveis."
            ),
        },
        "sources": sources,
    }


def studio_search(client: NanoJurisClient, request: StudioSearchRequest) -> dict[str, Any]:
    """Run one unified search and normalize it for the Studio frontend."""

    sources = request.sources or studio_sources_payload(client)["default_sources"]
    payload = client.search_many(
        request.query,
        sources=sources,
        page=request.page,
        page_size=request.page_size,
        canonical=request.canonical,
        **request.search_kwargs(),
    )
    results = [_jsonable(result) for result in payload["results"]]
    routing = payload.get("routing_summary", [])
    return {
        "query": request.query,
        "page": payload["page"],
        "page_size": payload["page_size"],
        "total": payload["total_returned"],
        "sources": payload["sources"],
        "searched_sources": payload["searched_sources"],
        "skipped_sources": payload["skipped_sources"],
        "source_status": _source_status(routing, results),
        "routing_summary": routing,
        "errors": payload["errors"],
        "results": results,
    }


def studio_validate(
    client: NanoJurisClient,
    request: StudioValidationRequest,
) -> dict[str, Any]:
    """Run the same live contract validation used by CLI and MCP."""

    sources = request.sources or studio_sources_payload(client)["default_sources"]
    method = getattr(client, "validate_sources", None)
    if callable(method):
        return _jsonable(
            method(sources=sources, text=request.query, timeout=request.timeout, page_size=1)
        )
    return _jsonable(
        validate_sources(
            client,
            sources=sources,
            text=request.query,
            timeout=request.timeout,
            page_size=1,
        )
    )


def supported_filters_for(capability: ProviderCapabilities) -> list[str]:
    """Infer UI filters from declared provider capabilities."""

    filters = set(capability.supported_filters)
    filters.update(_normalize_mode(mode) for mode in capability.search_modes)
    for field in capability.extracted_fields:
        mapped = FIELD_FILTERS.get(field)
        if mapped:
            filters.add(mapped)
    if capability.supports_full_text:
        filters.add("full_text")
    filters.discard("")
    return sorted(filters)


def _source_status(
    routing_summary: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    counts: dict[str, int] = {}
    for result in results:
        source = str(result.get("source") or "")
        counts[source] = counts.get(source, 0) + 1

    status: dict[str, dict[str, Any]] = {}
    for item in routing_summary:
        source = str(item.get("source") or "")
        action = str(item.get("action") or "")
        status[source] = {
            "status": _status_from_action(action),
            "count": counts.get(source, 0),
            "reason": item.get("reason"),
            "message": item.get("message"),
        }
    for source, count in counts.items():
        status.setdefault(
            source,
            {"status": "ok", "count": count, "reason": "returned_results", "message": ""},
        )
    return status


def _status_from_action(action: str) -> str:
    if action == "searched":
        return "ok"
    if action == "skipped":
        return "skipped"
    if action == "failed":
        return "failed"
    return "unknown"


def _normalize_mode(mode: str) -> str:
    mapping = {
        "full_text": "text",
        "summary": "text",
        "case_number": "case_number",
        "date_range": "date_range",
        "page": "page",
        "catalog": "catalog",
    }
    return mapping.get(mode, mode)


def _is_studio_source(capability: ProviderCapabilities) -> bool:
    return capability.category in {
        "administrative_jurisprudence",
        "court_jurisprudence",
        "court_precedents",
        "electoral_jurisprudence",
        "jurisprudence",
        "qualified_precedents",
    }


def _studio_tier(
    capability: ProviderCapabilities,
    risk_level: str,
    contract_level: int,
) -> str:
    if not _is_studio_source(capability):
        return "context"
    if risk_level == "alto":
        return "restricted"
    if contract_level >= 5:
        return "stable"
    if contract_level >= 4:
        return "advanced"
    return "experimental"


def _default_studio_sources(sources: list[dict[str, Any]]) -> list[str]:
    stable = [
        str(item["source"])
        for item in sources
        if item.get("recommended_for_studio") and item.get("studio_tier") == "stable"
    ]
    if len(stable) >= 3:
        return stable[:8]
    advanced = [
        str(item["source"])
        for item in sources
        if item.get("recommended_for_studio") and item.get("studio_tier") == "advanced"
    ]
    defaults = stable + advanced
    return defaults[:8]


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(cast(Any, value)))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value
