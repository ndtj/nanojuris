"""CSV exporter for objective jurisprudence extraction fields."""

from __future__ import annotations

import csv
import io

from nanojuris.canonical import search_page_to_canonical
from nanojuris.identity import canonical_record_identity
from nanojuris.models import CanonicalDecision, CanonicalDocument, CanonicalPrecedent, SearchPage

CSV_FIELDS = [
    "record_kind",
    "id",
    "source",
    "court",
    "case_number",
    "registry_number",
    "decision_type",
    "precedent_type",
    "number",
    "case_class",
    "subject",
    "rapporteur",
    "judging_body",
    "origin_county",
    "judgment_date",
    "publication_date",
    "status",
    "updated_at",
    "document_url",
    "source_url",
    "extraction_status",
    "access_status",
    "legal_identity_kind",
    "legal_identity_key",
    "legal_identity_parent_key",
]

DECISION_CSV_FIELDS = [
    "id",
    "source",
    "court",
    "case_number",
    "registry_number",
    "decision_type",
    "case_class",
    "subject",
    "rapporteur",
    "judging_body",
    "origin_county",
    "judgment_date",
    "publication_date",
    "document_url",
    "source_url",
    "extraction_status",
    "access_status",
    "legal_identity_kind",
    "legal_identity_key",
    "legal_identity_parent_key",
]

PRECEDENT_CSV_FIELDS = [
    "id",
    "source",
    "court",
    "precedent_type",
    "number",
    "status",
    "question",
    "thesis",
    "updated_at",
    "paradigm_case_count",
    "source_url",
    "extraction_status",
    "access_status",
    "legal_identity_kind",
    "legal_identity_key",
    "legal_identity_parent_key",
]

DOCUMENT_CSV_FIELDS = [
    "id",
    "source",
    "document_type",
    "content_type",
    "title",
    "url",
    "sha256",
    "byte_size",
    "page_count",
    "ocr_confidence",
    "retrieved_at",
    "access_status",
    "source_url",
    "extraction_status",
    "legal_identity_kind",
    "legal_identity_key",
    "legal_identity_parent_key",
]


def to_csv(page: SearchPage) -> str:
    """Serialize a search page as CSV with canonical extraction columns."""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for record in search_page_to_canonical(page):
        writer.writerow(_record_to_row(record))
    return output.getvalue()


def decisions_to_csv(records: list[CanonicalDecision]) -> str:
    """Serialize canonical decisions as a decision-specific CSV."""

    return _rows_to_csv(DECISION_CSV_FIELDS, [_decision_row(record) for record in records])


def precedents_to_csv(records: list[CanonicalPrecedent]) -> str:
    """Serialize canonical precedents as a precedent-specific CSV."""

    return _rows_to_csv(PRECEDENT_CSV_FIELDS, [_precedent_row(record) for record in records])


def documents_to_csv(records: list[CanonicalDocument]) -> str:
    """Serialize canonical documents as a document-specific CSV."""

    return _rows_to_csv(DOCUMENT_CSV_FIELDS, [_document_row(record) for record in records])


def _record_to_row(record: CanonicalDecision | CanonicalPrecedent) -> dict[str, object]:
    if isinstance(record, CanonicalDecision):
        return {"record_kind": "decision", **_decision_row(record)}
    return {"record_kind": "precedent", **_precedent_row(record)}


def _decision_row(record: CanonicalDecision) -> dict[str, object]:
    identity = canonical_record_identity(record)
    return {
        "id": record.id,
        "source": record.source,
        "court": record.court,
        "case_number": record.case_number,
        "registry_number": record.registry_number,
        "decision_type": record.decision_type,
        "case_class": record.case_class,
        "subject": record.subject,
        "rapporteur": record.rapporteur,
        "judging_body": record.judging_body,
        "origin_county": record.origin_county,
        "judgment_date": record.judgment_date,
        "publication_date": record.publication_date,
        "document_url": record.document_url,
        "source_url": record.source_trace.source_url if record.source_trace else None,
        "extraction_status": record.extraction_trace.status.value
        if record.extraction_trace
        else None,
        "access_status": record.extraction_trace.access_status.value
        if record.extraction_trace
        else None,
        "legal_identity_kind": identity.kind,
        "legal_identity_key": identity.key,
        "legal_identity_parent_key": identity.parent_key,
    }


def _precedent_row(record: CanonicalPrecedent) -> dict[str, object]:
    identity = canonical_record_identity(record)
    return {
        "record_kind": "precedent",
        "id": record.id,
        "source": record.source,
        "court": record.court,
        "precedent_type": record.precedent_type,
        "number": record.number,
        "status": record.status,
        "updated_at": record.updated_at,
        "source_url": record.source_trace.source_url if record.source_trace else None,
        "extraction_status": record.extraction_trace.status.value
        if record.extraction_trace
        else None,
        "access_status": record.extraction_trace.access_status.value
        if record.extraction_trace
        else None,
        "legal_identity_kind": identity.kind,
        "legal_identity_key": identity.key,
        "legal_identity_parent_key": identity.parent_key,
    }


def _document_row(record: CanonicalDocument) -> dict[str, object]:
    identity = canonical_record_identity(record)
    return {
        "id": record.id,
        "source": record.source,
        "document_type": record.document_type,
        "content_type": record.content_type,
        "title": record.title,
        "url": record.url,
        "sha256": record.sha256,
        "byte_size": record.byte_size,
        "page_count": record.page_count,
        "ocr_confidence": record.ocr_confidence,
        "retrieved_at": record.retrieved_at,
        "access_status": record.access_status.value,
        "source_url": record.source_trace.source_url if record.source_trace else None,
        "extraction_status": record.extraction_trace.status.value
        if record.extraction_trace
        else None,
        "legal_identity_kind": identity.kind,
        "legal_identity_key": identity.key,
        "legal_identity_parent_key": identity.parent_key,
    }


def _rows_to_csv(fieldnames: list[str], rows: list[dict[str, object]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
