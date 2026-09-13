"""Canonical mapping helpers for extracted jurisprudence data."""

from __future__ import annotations

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
from nanojuris.normalization import normalize_date_value

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
    extraction_status = _effective_extraction_status(result)
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
        case_class=_optional_str(result.case_class or raw.get("classe") or raw.get("case_class")),
        subject=_optional_str(raw.get("assunto") or raw.get("subject")),
        rapporteur=result.rapporteur,
        judging_body=_optional_str(
            result.judging_body or raw.get("orgao_julgador") or raw.get("judging_body")
        ),
        origin_county=_optional_str(raw.get("comarca") or raw.get("origin_county")),
        judgment_date=normalize_date(judgment_raw),
        publication_date=normalize_date(publication_raw),
        judgment_date_raw=judgment_raw,
        publication_date_raw=publication_raw,
        source_updated_at=normalize_date(source_updated_raw),
        source_updated_at_raw=source_updated_raw,
        retrieved_at=retrieved_at,
        access_status=_effective_access_status(result),
        extraction_status=extraction_status,
        summary=result.summary,
        full_text=result.full_text or _optional_str(raw.get("full_text")),
        document_url=_optional_str(
            result.document_url or raw.get("full_text_url") or raw.get("document_url")
        ),
        degree=_optional_str(result.degree or raw.get("degree") or raw.get("grau")),
        instance=_optional_str(result.instance or raw.get("instance") or raw.get("instancia")),
        branch=_optional_str(result.branch or raw.get("branch") or raw.get("ramo")),
        legal_area=_optional_str(
            result.legal_area or raw.get("legal_area") or raw.get("area_juridica")
        ),
        authority=_optional_str(result.authority or raw.get("authority") or raw.get("autoridade")),
        collection=_optional_str(result.collection or raw.get("collection") or raw.get("colecao")),
        document_type=_optional_str(
            result.document_type or raw.get("document_type") or raw.get("tipo_documento")
        ),
        source_origin=_optional_str(
            result.source_origin or raw.get("source_origin") or raw.get("origem")
        ),
        field_provenance=_field_provenance(result),
        source_trace=result.source_trace,
        extraction_trace=_build_trace(result, parser_version=parser_version),
        raw=raw,
        native_rank=result.native_rank,
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
    updated_raw = result.updated_at
    source_updated_raw = result.source_updated_at
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
        updated_at=normalize_date(updated_raw),
        updated_at_raw=updated_raw,
        source_updated_at=normalize_date(source_updated_raw),
        source_updated_at_raw=source_updated_raw,
        retrieved_at=retrieved_at,
        access_status=_effective_access_status(result),
        extraction_status=_effective_extraction_status(result),
        degree=_optional_str(result.degree or raw.get("degree") or raw.get("grau")),
        instance=_optional_str(result.instance or raw.get("instance") or raw.get("instancia")),
        branch=_optional_str(result.branch or raw.get("branch") or raw.get("ramo")),
        legal_area=_optional_str(
            result.legal_area or raw.get("legal_area") or raw.get("area_juridica")
        ),
        authority=_optional_str(result.authority or raw.get("authority") or raw.get("autoridade")),
        collection=_optional_str(result.collection or raw.get("collection") or raw.get("colecao")),
        document_type=_optional_str(
            result.document_type or raw.get("document_type") or raw.get("tipo_documento")
        ),
        source_origin=_optional_str(
            result.source_origin or raw.get("source_origin") or raw.get("origem")
        ),
        field_provenance=_field_provenance(result),
        source_trace=result.source_trace,
        extraction_trace=_build_trace(result, parser_version=parser_version),
        raw=raw,
        native_rank=result.native_rank,
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
    return normalize_date_value(value)


def _build_trace(result: JurisprudenceResult, *, parser_version: str) -> ExtractionTrace:
    status = _effective_extraction_status(result)
    transformations = ["canonical_mapping"]
    if result.access_status is None:
        transformations.append("access_status_defaulted_to_partial")
    if result.retrieved_at is None and result.source_trace is not None:
        transformations.append("retrieved_at_inherited_from_source_trace")
    if result.source_updated_at is None and result.updated_at:
        transformations.append("source_updated_at_inherited_from_updated_at")
    if result.full_text is None and (result.raw or {}).get("full_text"):
        transformations.append("full_text_inherited_from_raw")
    if status != result.extraction_status:
        transformations.append("extraction_status_downgraded_to_partial")
    for field_name, raw_value in (
        ("judgment_date", result.judgment_date or (result.raw or {}).get("data_julgamento")),
        ("publication_date", result.publication_date or (result.raw or {}).get("data_publicacao")),
        ("source_updated_at", result.source_updated_at or result.updated_at),
    ):
        normalized_value = normalize_date(raw_value)
        if raw_value and normalized_value and normalized_value != _optional_str(raw_value):
            transformations.append(f"{field_name}_normalized_to_iso")
    return ExtractionTrace(
        parser=f"{result.source}.canonical_result_mapper",
        parser_version=parser_version,
        status=status,
        access_status=_effective_access_status(result),
        transformations=transformations,
        metadata={
            "result_id": result.id,
            "result_type": result.type,
            "field_provenance": _field_provenance(result),
        },
    )


def _field_provenance(result: JurisprudenceResult) -> dict[str, dict[str, object]]:
    """Describe where populated canonical fields came from without copying values."""

    raw = result.raw or {}
    retrieved_at = result.retrieved_at or (
        result.source_trace.retrieved_at if result.source_trace is not None else None
    )
    aliases = {
        "case_class": ("classe", "case_class"),
        "judging_body": ("orgao_julgador", "judging_body"),
        "degree": ("degree", "grau"),
        "instance": ("instance", "instancia"),
        "branch": ("branch", "ramo"),
        "legal_area": ("legal_area", "area_juridica"),
        "authority": ("authority", "autoridade"),
        "collection": ("collection", "colecao"),
        "document_type": ("document_type", "tipo_documento"),
        "source_origin": ("source_origin", "origem"),
        "judgment_date": ("data_julgamento", "judgment_date"),
        "publication_date": ("data_publicacao", "publication_date"),
        "source_updated_at": ("source_updated_at",),
        "document_url": ("full_text_url", "document_url"),
    }
    provenance: dict[str, dict[str, object]] = {}
    for field_name, raw_names in aliases.items():
        value = getattr(result, field_name, None)
        if value is not None and str(value).strip():
            path = f"result.{field_name}"
        else:
            raw_name = next((name for name in raw_names if raw.get(name) is not None), None)
            if raw_name is None:
                continue
            path = f"raw.{raw_name}"
        provenance[field_name] = {
            "source": result.source,
            "path": path,
            "retrieved_at": retrieved_at,
        }
    return provenance


def _effective_access_status(result: JurisprudenceResult) -> AccessStatus:
    """Never claim public access without explicit evidence from the provider."""

    return result.access_status or AccessStatus.PARTIAL


def _effective_extraction_status(result: JurisprudenceResult) -> ExtractionStatus:
    """Downgrade incomplete normalized results instead of claiming completeness."""

    if result.extraction_status == ExtractionStatus.COMPLETE and not _has_primary_text(result):
        return ExtractionStatus.PARTIAL
    return result.extraction_status


_PRECEDENT_TYPE_MARKERS = (
    "sumula",
    "súmula",
    "tema",
    "repercus",
    "repetitiv",
    "enunciado",
    "precedente",
    "verbete",
    "orientacao",
    "orientação",
    "paradigma",
    "incidente de",
)
_PRECEDENT_TYPE_CODES = {"rr", "rg", "irdr", "iac", "iuj", "puil", "qo"}
_DECISION_TYPE_MARKERS = (
    "decisao",
    "decisão",
    "despacho",
    "sentenca",
    "sentença",
    "acordao",
    "acórdão",
    "monocrat",
    "informativo",
    "jurisprud",
    "merito",
    "mérito",
    "recurso inominado",
    "apelacao",
    "apelação",
    "agravo",
    "habeas",
)


def _looks_like_decision(result: JurisprudenceResult) -> bool:
    """A jurisprudence result is a decision unless it carries a precedent thesis.

    Qualified precedents (súmulas, temas repetitivos, repercussão geral) expose
    a ``thesis``/``question`` and a precedent-shaped ``type``; everything else is
    an individual decision whose ementa must be preserved on ``summary``.
    """

    normalized_type = (result.type or "").strip().lower()
    if result.thesis or result.question:
        return False
    if normalized_type in _PRECEDENT_TYPE_CODES:
        return False
    if any(marker in normalized_type for marker in _PRECEDENT_TYPE_MARKERS):
        return False
    if any(marker in normalized_type for marker in _DECISION_TYPE_MARKERS):
        return True
    # No explicit signal: a result carrying an ementa or full text is a
    # decision; an empty, unlabelled record stays a precedent (conservative).
    return bool(result.summary or result.full_text)


def _has_primary_text(result: JurisprudenceResult) -> bool:
    return bool(result.summary or result.thesis or result.question or result.full_text)


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
