"""Small request contracts for the local NanoJuris Studio API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class StudioSearchRequest:
    """Normalized payload accepted by the Studio unified search endpoint."""

    query: str = ""
    sources: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    types: list[str] = field(default_factory=list)
    page: int = 1
    page_size: int = 10
    canonical: bool = True
    mode: str = "adaptive"
    ranking_version: str = "legal-live-v1"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> StudioSearchRequest:
        filters = payload.get("filters")
        if filters is None:
            filters = {}
        if not isinstance(filters, dict):
            raise ValueError("filters must be an object")
        mode = str(payload.get("mode") or "adaptive").strip().casefold()
        if mode not in {"adaptive", "selected", "all", "legacy"}:
            raise ValueError("mode must be adaptive, selected, all or legacy")
        ranking_version = str(payload.get("ranking_version") or "legal-live-v1").strip()
        if ranking_version not in {"legacy", "legal-live-v1"}:
            raise ValueError("ranking_version must be legacy or legal-live-v1")
        return cls(
            query=str(payload.get("query") or payload.get("text") or ""),
            sources=_string_list(payload.get("sources")),
            filters=filters,
            types=_string_list(payload.get("types") or filters.get("types")),
            page=max(1, int(payload.get("page") or 1)),
            page_size=max(1, min(50, int(payload.get("page_size") or payload.get("limit") or 10))),
            canonical=bool(payload.get("canonical", True)),
            mode=mode,
            ranking_version=ranking_version,
        )

    def search_kwargs(self) -> dict[str, Any]:
        kwargs = dict(self.filters)
        kwargs.pop("types", None)
        if "date_from" in kwargs and "published_from" not in kwargs:
            kwargs["published_from"] = kwargs.pop("date_from")
        if "date_to" in kwargs and "published_to" not in kwargs:
            kwargs["published_to"] = kwargs.pop("date_to")
        return kwargs


@dataclass(slots=True)
class StudioValidationRequest:
    """Bounded live validation request exposed by the Studio."""

    query: str = "responsabilidade civil"
    sources: list[str] = field(default_factory=list)
    timeout: float = 45.0

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> StudioValidationRequest:
        query = str(payload.get("query") or payload.get("text") or "responsabilidade civil").strip()
        if not query:
            raise ValueError("query must not be empty")
        if len(query) > 500:
            raise ValueError("query must contain at most 500 characters")

        raw_timeout = payload.get("timeout", 45)
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError) as exc:
            raise ValueError("timeout must be a number") from exc
        if not 1 <= timeout <= 120:
            raise ValueError("timeout must be between 1 and 120 seconds")
        return cls(query=query, sources=_string_list(payload.get("sources")), timeout=timeout)


def _string_list(value: Any) -> list[str]:
    if value in (None, "", "all"):
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list | tuple | set):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ValueError("sources must be a list or comma-separated string")
