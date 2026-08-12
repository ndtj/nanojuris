"""Canonical mapping helpers for extracted jurisprudence data."""

from __future__ import annotations

import re
from datetime import date, datetime

from nanojuris.models import (
    AccessStatus,
    CanonicalDecision,
    CanonicalPrecedent,
    ExtractionStatus,
    ExtractionTrace,
    JurisprudenceResult,
    ParadigmCase,
    SearchPage,
)

DEFAULT_CANONICAL_PARSER_VERSION = "1"


def result_to_canonical_decision(
    result: JurisprudenceResult,
    *,
    parser_version: str = DEFAULT_CANONICAL_PARSER_VERSION,
) -> CanonicalDecision:
    """Map an extracted jurisprudence result to a canonical decision."""

    raw = result.raw or {}
    judgment_raw = _first_value(
        result.judgment_date,
        raw.get("data_julgamento"),
        raw.get("judgment_date"),
    )
    publication_raw = _first_value(
        result.publication_date,
        raw.get("data_publicacao"),
        raw.get("publication_date"),
    )
    source_updated_raw = _first_value(
        result.source_updated_at,
        raw.get("source_updated_at"),
        result.updated_at,
    )
    retrieved_at = result.retrieved_at or (
        result.source_trace.retrieved_at if result.source_trace is not None else None
    )
    return CanonicalDecision(
        id=result.id,
        source=result.source,
        court=result.court,
        case_number=str(result.number) if result.number is not None else None,
        registry_number=_optional_str(raw.get("nu_registro") or raw.get("registry_number")),
        decision_type=result.type or None,
        case_class=_optional_str(raw.get("classe") or raw.get("case_class")),
        subject=_optional_str(raw.get("assunto") or raw.get("subject")),
        rapporteur=result.rapporteur,
        judging_body=_optional_str(raw.get("orgao_julgador") or raw.get("judging_body")),
        origin_county=_optional_str(raw.get("comarca") or raw.get("origin_county")),
        judgment_date=normalize_date(judgment_raw),
        publication_date=normalize_date(publication_raw),
        judgment_date_raw=judgment_raw,
        publication_date_raw=publication_raw,
        source_updated_at=normalize_date(source_updated_raw),
        retrieved_at=retrieved_at,
        access_status=_effective_access_status(result),
        summary=result.summary,
        full_text=result.full_text or _optional_str(raw.get("full_text")),
        document_url=_optional_str(raw.get("full_text_url") or raw.get("document_url")),
        source_trace=result.source_trace,
        extraction_trace=_build_trace(result, parser_version=parser_version),
        raw=raw,
    )


def result_to_canonical_precedent(
    result: JurisprudenceResult,
    *,
    parser_version: str = DEFAULT_CANONICAL_PARSER_VERSION,
) -> CanonicalPrecedent:
    """Map an extracted jurisprudence result to a canonical precedent."""

    raw = result.raw or {}
    retrieved_at = result.retrieved_at or (
        result.source_trace.retrieved_at if result.source_trace is not None else None
    )
    return CanonicalPrecedent(
        id=result.id,
        source=result.source,
        court=result.court,
        precedent_type=result.type,
        number=result.number,
        status=result.status,
        question=result.question,
        thesis=result.thesis,
        affected_cases=_map_cases(raw.get("affected_cases") or raw.get("processosAfetados")),
        paradigm_cases=result.paradigm_cases,
        updated_at=normalize_date(result.updated_at),
        source_updated_at=normalize_date(result.source_updated_at),
        retrieved_at=retrieved_at,
        access_status=_effective_access_status(result),
        source_trace=result.source_trace,
        extraction_trace=_build_trace(result, parser_version=parser_version),
        raw=raw,
    )


def search_page_to_canonical(
    page: SearchPage,
    *,
    parser_version: str = DEFAULT_CANONICAL_PARSER_VERSION,
) -> list[CanonicalDecision | CanonicalPrecedent]:
    """Map a search page to canonical extraction records."""

    return [
        result_to_canonical_decision(result, parser_version=parser_version)
        if _looks_like_decision(result)
        else result_to_canonical_precedent(result, parser_version=parser_version)
        for result in page.results
    ]


def normalize_date(value: object) -> str | None:
    """Normalize known source date formats to ISO date, preserving unknown raw values elsewhere."""

    text = _optional_str(value)
    if not text:
        return None
    for parser in (
        lambda item: datetime.fromisoformat(item.replace("Z", "+00:00")).date(),
        lambda item: datetime.strptime(item, "%d/%m/%Y").date(),
        lambda item: datetime.strptime(item, "%d-%m-%Y").date(),
        lambda item: date.fromisoformat(item[:10]),
    ):
        try:
            return parser(text).isoformat()
        except (TypeError, ValueError):
            continue
    match = re.fullmatch(r"(\d{4})/(\d{2})/(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def _build_trace(result: JurisprudenceResult, *, parser_version: str) -> ExtractionTrace:
    status = result.extraction_status
    if status == ExtractionStatus.COMPLETE and not _has_primary_text(result):
        status = ExtractionStatus.PARTIAL
    return ExtractionTrace(
        parser=f"{result.source}.canonical_result_mapper",
        parser_version=parser_version,
        status=status,
        access_status=_effective_access_status(result),
        metadata={"result_id": result.id, "result_type": result.type},
    )


def _effective_access_status(result: JurisprudenceResult) -> AccessStatus:
    """Never claim public access without explicit evidence from the provider."""

    return result.access_status or AccessStatus.PARTIAL


def _looks_like_decision(result: JurisprudenceResult) -> bool:
    normalized_type = result.type.strip().lower()
    decision_markers = {
        "decisao",
        "decisão",
        "despacho",
        "sentenca",
        "sentença",
    }
    if any(marker in normalized_type for marker in decision_markers):
        return True
    return normalized_type in {
        "acordao",
        "acórdão",
        "monocratica",
        "monocrática",
        "comunicacao",
        "comunicação",
        "processo",
        "sentenca",
        "sentença",
    }


def _has_primary_text(result: JurisprudenceResult) -> bool:
    return bool(result.summary or result.thesis or result.question)


def _first_value(*values: object) -> str | None:
    for value in values:
        normalized = _optional_str(value)
        if normalized:
            return normalized
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _map_cases(items: object) -> list[ParadigmCase]:
    if not isinstance(items, list):
        return []
    cases: list[ParadigmCase] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        number = _optional_str(item.get("numero") or item.get("number"))
        if not number:
            continue
        cases.append(
            ParadigmCase(
                number=number,
                case_class=item.get("classe") or item.get("case_class"),
                url=_optional_str(item.get("link") or item.get("url")),
            )
        )
    return cases
