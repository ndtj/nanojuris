"""Shared helpers for preserving and extracting public legal documents."""

from __future__ import annotations

import hashlib
import re
from io import BytesIO
from typing import Any

from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    ExtractionStatus,
    ExtractionTrace,
    SourceTrace,
)
from nanojuris.parsing import parse_html


def build_canonical_document(
    *,
    document_id: str,
    source: str,
    document_type: str,
    content: bytes,
    content_type: str | None,
    url: str | None,
    title: str | None,
    source_trace: SourceTrace | None,
    access_status: AccessStatus,
    raw_metadata: dict[str, Any] | None = None,
    parser: str,
    parser_version: str = "1",
    text_override: str | None = None,
    extraction_status_override: ExtractionStatus | None = None,
    extraction_warnings: list[str] | None = None,
) -> CanonicalDocument:
    """Create a document without losing the original response bytes.

    Providers may use different HTTP clients and response wrappers, but the
    canonical document contract must be identical.  Extraction is performed
    after hashing and the original bytes remain available on ``raw_bytes``.
    """

    normalized_content_type = detect_content_type(content, content_type)
    if text_override is None:
        text, extraction_status, warnings, transformations = extract_text(
            content, normalized_content_type
        )
    else:
        text = text_override.strip() or None
        extraction_status = ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY
        warnings = []
        transformations = ["provider_text_extracted"]
    if extraction_status_override is not None:
        extraction_status = extraction_status_override
    if extraction_warnings:
        warnings.extend(item for item in extraction_warnings if item not in warnings)
    if access_status != AccessStatus.PUBLIC and extraction_status == ExtractionStatus.COMPLETE:
        extraction_status = ExtractionStatus.PARTIAL
        warnings.append("O acesso da fonte nao foi classificado como publico completo.")
    digest = hashlib.sha256(content).hexdigest()
    metadata = dict(raw_metadata or {})
    metadata.update(
        {
            "raw_content_sha256": digest,
            "raw_content_bytes": len(content),
            "source_content_type": content_type,
            "raw_content_preserved": True,
        }
    )
    trace = source_trace or SourceTrace(
        provider=source,
        endpoint="",
        source_url=url,
        content_type=content_type,
        content_sha256=digest,
        response_bytes=len(content),
    )
    trace.content_type = trace.content_type or content_type
    trace.content_sha256 = trace.content_sha256 or digest
    trace.response_bytes = trace.response_bytes or len(content)
    trace.transformations.extend(
        item for item in transformations if item not in trace.transformations
    )
    extraction_trace = ExtractionTrace(
        parser=parser,
        parser_version=parser_version,
        status=extraction_status,
        access_status=access_status,
        content_sha256=digest,
        content_bytes=len(content),
        warnings=warnings,
        transformations=transformations,
        metadata={"content_type": normalized_content_type, **metadata},
    )
    return CanonicalDocument(
        id=document_id,
        source=source,
        document_type=document_type,
        content_type=normalized_content_type,
        title=title,
        text=text,
        raw_bytes=content,
        url=url,
        sha256=digest,
        byte_size=len(content),
        retrieved_at=trace.retrieved_at,
        access_status=access_status,
        extraction_status=extraction_status,
        source_trace=trace,
        extraction_trace=extraction_trace,
        raw_metadata=metadata,
    )


def detect_content_type(content: bytes, content_type: str | None) -> str:
    """Return a stable media type using headers first and safe magic checks."""

    header_type = (content_type or "").split(";", 1)[0].strip().lower()
    if header_type:
        return header_type
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if re.search(rb"<html|<!doctype html", content[:4096], re.IGNORECASE):
        return "text/html"
    if content.lstrip().startswith((b"{", b"[")):
        return "application/json"
    return "text/plain"


def extract_text(
    content: bytes, content_type: str
) -> tuple[str | None, ExtractionStatus, list[str], list[str]]:
    """Extract searchable text while retaining the source bytes unchanged."""

    warnings: list[str] = []
    transformations: list[str] = []
    if not content:
        return None, ExtractionStatus.EMPTY, warnings, transformations
    if content_type == "application/pdf":
        try:
            from pypdf import PdfReader

            pages = PdfReader(BytesIO(content)).pages
            text = "\n\n".join((page.extract_text() or "").strip() for page in pages).strip()
        except ImportError:
            return (
                None,
                ExtractionStatus.UNSUPPORTED_FORMAT,
                ["Instale a dependencia pypdf para extrair texto PDF."],
                transformations,
            )
        except Exception as exc:  # noqa: BLE001 - parser boundary
            return None, ExtractionStatus.FAILED, [f"Falha na extracao PDF: {exc}"], transformations
        transformations.append("pdf_text_extracted")
        return (
            (text or None),
            (ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY),
            warnings,
            transformations,
        )
    if content_type in {"text/html", "application/xhtml+xml"}:
        text = _normalize_text(parse_html(content).visible_text())
        transformations.append("html_text_extracted")
        return (
            (text or None),
            (ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY),
            warnings,
            transformations,
        )
    if content_type == "application/json" or content_type.endswith("+json"):
        text = content.decode("utf-8", errors="replace").strip()
        transformations.append("json_text_preserved")
        return (
            (text or None),
            (ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY),
            warnings,
            transformations,
        )
    if content_type.startswith("text/"):
        text = content.decode("utf-8", errors="replace").strip()
        transformations.append("text_decoded_utf8")
        return (
            (text or None),
            (ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY),
            warnings,
            transformations,
        )
    return (
        None,
        ExtractionStatus.UNSUPPORTED_FORMAT,
        [f"Formato nao suportado: {content_type}"],
        transformations,
    )


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())
