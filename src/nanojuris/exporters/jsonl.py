"""JSON Lines exporter."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from nanojuris.canonical import search_page_to_canonical
from nanojuris.models import (
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    JurisprudenceResult,
    SearchPage,
)

CanonicalExportRecord = CanonicalDecision | CanonicalDocument | CanonicalPrecedent


def to_jsonl(page_or_results: SearchPage | list[JurisprudenceResult]) -> str:
    """Serialize a search page or result list as JSON Lines."""

    results = (
        page_or_results.results if isinstance(page_or_results, SearchPage) else page_or_results
    )
    return "\n".join(
        json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True) for result in results
    )


def to_canonical_jsonl(
    page_or_records: SearchPage | list[CanonicalExportRecord],
) -> str:
    """Serialize canonical extraction records as JSON Lines."""

    records = (
        search_page_to_canonical(page_or_records)
        if isinstance(page_or_records, SearchPage)
        else page_or_records
    )
    return "\n".join(
        json.dumps(_to_jsonable(record), ensure_ascii=False, sort_keys=True) for record in records
    )


def _to_jsonable(value: object) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _to_jsonable(value.to_dict())
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value
