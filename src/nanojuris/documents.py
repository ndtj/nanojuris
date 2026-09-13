"""Shared helpers for preserving and extracting public legal documents."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from dataclasses import asdict, dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    ExtractionStatus,
    ExtractionTrace,
    SourceTrace,
)
from nanojuris.ocr import extract_pdf_text, extract_tiff_text
from nanojuris.parsing import parse_html
from nanojuris.transport import (
    ContentResponseCache,
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)


@dataclass(frozen=True, slots=True)
class DocumentReference:
    """A document URL discovered during search, never fetched implicitly."""

    id: str
    source: str
    url: str
    document_type: str = "inteiro_teor"
    expected_content_types: tuple[str, ...] = ("application/pdf", "text/html", "text/plain")
    # The relation is optional because several portals expose a document URL
    # before they expose a stable decision id.  When present, retaining it in
    # the canonical metadata makes the decision↔document link deterministic
    # and auditable instead of relying on URL heuristics.
    decision_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("document URL must be an HTTPS absolute URL")
        if not self.id.strip() or not self.source.strip():
            raise ValueError("document id and source must not be empty")
        if self.decision_id is not None and not self.decision_id.strip():
            raise ValueError("decision_id must not be blank when provided")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContentAddressedDocumentCache:
    """Immutable document bytes addressed by SHA-256.

    The cache stores only raw bytes and a small JSON metadata sidecar.  It is
    intentionally separate from provider search caches and can be cleaned by
    age or size without touching source records.
    """

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _paths(self, digest: str) -> tuple[Path, Path]:
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("digest must be a SHA-256 hex string")
        root = self.directory / digest[:2]
        return root / f"{digest}.bin", root / f"{digest}.json"

    def put(self, content: bytes, *, metadata: dict[str, Any] | None = None) -> str:
        digest = hashlib.sha256(content).hexdigest()
        data_path, metadata_path = self._paths(digest)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        if not data_path.exists():
            _atomic_write_bytes(data_path, content)
        if not metadata_path.exists():
            payload = {
                "sha256": digest,
                "byte_size": len(content),
                "stored_at": time.time(),
                "metadata": dict(metadata or {}),
            }
            _atomic_write_text(
                metadata_path, json.dumps(payload, ensure_ascii=False, sort_keys=True)
            )
        return digest

    def get(self, digest: str) -> bytes | None:
        data_path, _metadata_path = self._paths(digest)
        try:
            return data_path.read_bytes()
        except OSError:
            return None

    def metadata(self, digest: str) -> dict[str, Any] | None:
        _data_path, metadata_path = self._paths(digest)
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
            return dict(payload) if isinstance(payload, dict) else None
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None

    def cleanup(
        self, *, max_age_seconds: float | None = None, max_bytes: int | None = None
    ) -> dict[str, int]:
        if max_age_seconds is not None and max_age_seconds < 0:
            raise ValueError("max_age_seconds must be non-negative")
        if max_bytes is not None and max_bytes < 0:
            raise ValueError("max_bytes must be non-negative")
        now = time.time()
        entries: list[tuple[Path, float, int]] = []
        for path in self.directory.glob("*/*.bin"):
            try:
                stat = path.stat()
            except OSError:
                continue
            entries.append((path, stat.st_mtime, stat.st_size))
        entries.sort(key=lambda item: (item[1], item[0].name))
        selected: list[Path] = []
        for path, mtime, _size in entries:
            if max_age_seconds is not None and now - mtime > max_age_seconds:
                selected.append(path)
        selected_set = set(selected)
        if max_bytes is not None:
            total = sum(size for path, _mtime, size in entries if path not in selected_set)
            for path, _mtime, size in entries:
                if path in selected_set:
                    continue
                if total <= max_bytes:
                    break
                selected.append(path)
                selected_set.add(path)
                total -= size
        deleted = 0
        deleted_bytes = 0
        for path in selected:
            try:
                size = path.stat().st_size
                path.unlink()
                path.with_suffix(".json").unlink(missing_ok=True)
            except OSError:
                continue
            deleted += 1
            deleted_bytes += size
        return {"deleted_files": deleted, "deleted_bytes": deleted_bytes}


def fetch_document_reference(
    reference: DocumentReference,
    *,
    policy: TransportPolicy,
    session: Any | None = None,
    response_cache: ContentResponseCache | None = None,
    document_cache: ContentAddressedDocumentCache | None = None,
    title: str | None = None,
) -> CanonicalDocument:
    """Fetch one explicit public reference through the shared transport.

    Search providers should return ``DocumentReference`` only.  This function
    is the opt-in boundary for downloading a document and refuses unexpected
    formats, access-control responses and transport failures instead of
    returning an empty document.
    """

    client = SharedHttpClient(policy, session=session, cache=response_cache)
    response = client.request(
        TransportRequest(
            source=reference.source,
            operation="document_fetch",
            method="GET",
            url=reference.url,
            headers={"Accept": ",".join(reference.expected_content_types)},
            cacheable=response_cache is not None,
        )
    )
    if response.status is not TransportStatus.COMPLETE:
        raise SourceUnavailableError(f"document transport failed: {response.status.value}")
    status_code = response.status_code or 0
    if status_code in {401, 403, 407, 451}:
        raise AccessControlRequiredError("document access requires authorization")
    if status_code == 429:
        raise RateLimitDetectedError("document source returned HTTP 429")
    if status_code < 200 or status_code >= 300:
        raise SourceUnavailableError("document source returned an HTTP error")
    content_type = detect_content_type(response.body, response.content_type)
    expected = {
        item.split(";", 1)[0].strip().casefold() for item in reference.expected_content_types
    }
    if expected and content_type.casefold() not in expected:
        raise ParserContractChangedError(
            f"document content type {content_type!r} is outside the reference contract"
        )
    # A few public portals label an error body as ``application/pdf`` and
    # return HTTP 200.  Do not cache or expose that response as an official
    # document.  ``build_canonical_document`` still remains available for
    # diagnostics and preserves malformed bytes when a caller explicitly
    # constructs a document, but the network fetch boundary must reject it.
    if content_type.casefold() == "application/pdf" and not response.body.startswith(b"%PDF-"):
        raise ParserContractChangedError(
            "document declared PDF but failed structural validation: invalid_magic"
        )
    digest = (
        document_cache.put(
            response.body,
            metadata={
                "source": reference.source,
                "document_id": reference.id,
                "url": reference.url,
                "content_type": content_type,
            },
        )
        if document_cache is not None
        else hashlib.sha256(response.body).hexdigest()
    )
    trace = SourceTrace(
        provider=reference.source,
        endpoint="GET document_reference",
        source_url=reference.url,
        http_status=response.status_code,
        final_url=response.final_url,
        content_type=content_type,
        content_sha256=digest,
        response_bytes=response.byte_size,
        elapsed_ms=response.elapsed_ms,
        retrieval_status="ok",
        transformations=["transport_shared", "content_addressed_cache"],
    )
    return build_canonical_document(
        document_id=reference.id,
        source=reference.source,
        document_type=reference.document_type,
        content=response.body,
        content_type=content_type,
        url=response.final_url or reference.url,
        title=title,
        source_trace=trace,
        access_status=AccessStatus.PUBLIC,
        raw_metadata={"reference": reference.to_dict(), "cache_sha256": digest},
        parser=f"{reference.source}.document",
        parser_version="1",
        max_bytes=policy.max_bytes,
    )


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
    ocr_allowed: bool = False,
    ocr_max_pages: int = 5,
    ocr_timeout_seconds: float = 30.0,
    max_bytes: int | None = None,
) -> CanonicalDocument:
    """Create a document without losing the original response bytes.

    Providers may use different HTTP clients and response wrappers, but the
    canonical document contract must be identical.  Extraction is performed
    after hashing and the original bytes remain available on ``raw_bytes``.
    """

    if max_bytes is not None and max_bytes < 1:
        raise ValueError("max_bytes must be positive when provided")
    if max_bytes is not None and len(content) > max_bytes:
        raise ParserContractChangedError("document exceeds the configured byte limit")

    normalized_content_type = detect_content_type(content, content_type)
    quality = assess_document_content(
        content,
        content_type,
        max_bytes=max_bytes,
    )
    content_validation_warnings = _content_validation_warnings(
        content, content_type, normalized_content_type
    )
    ocr_confidence: float | None = None
    if text_override is None:
        text, extraction_status, warnings, transformations = extract_text(
            content, normalized_content_type
        )
        if (
            ocr_allowed
            and normalized_content_type in {"application/pdf", "image/tiff"}
            and extraction_status is ExtractionStatus.UNSUPPORTED_FORMAT
            and (
                normalized_content_type == "image/tiff"
                or any("sem camada textual" in item.casefold() for item in warnings)
            )
        ):
            ocr = (
                extract_tiff_text(
                    content,
                    max_pages=ocr_max_pages,
                    timeout_seconds=ocr_timeout_seconds,
                )
                if normalized_content_type == "image/tiff"
                else extract_pdf_text(
                    content,
                    max_pages=ocr_max_pages,
                    timeout_seconds=ocr_timeout_seconds,
                )
            )
            warnings.extend(item for item in ocr.warnings if item not in warnings)
            if ocr.text:
                text = ocr.text
                extraction_status = (
                    ExtractionStatus.COMPLETE
                    if ocr.status == "complete"
                    else ExtractionStatus.PARTIAL
                )
                transformations.append(
                    "tiff_ocr_extracted"
                    if normalized_content_type == "image/tiff"
                    else "pdf_ocr_extracted"
                )
                ocr_confidence = ocr.confidence
            elif ocr.status == "partial":
                extraction_status = ExtractionStatus.PARTIAL
            elif ocr.status == "failed":
                extraction_status = ExtractionStatus.FAILED
    else:
        text = text_override.strip() or None
        extraction_status = ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY
        warnings = []
        transformations = ["provider_text_extracted"]
    if extraction_status_override is not None:
        extraction_status = extraction_status_override
    if extraction_warnings:
        warnings.extend(item for item in extraction_warnings if item not in warnings)
    warnings.extend(item for item in content_validation_warnings if item not in warnings)
    if access_status != AccessStatus.PUBLIC and extraction_status == ExtractionStatus.COMPLETE:
        extraction_status = ExtractionStatus.PARTIAL
        warnings.append("O acesso da fonte nao foi classificado como publico completo.")
    digest = hashlib.sha256(content).hexdigest()
    page_count = (
        _safe_pdf_page_count(content) if normalized_content_type == "application/pdf" else None
    )
    metadata = dict(raw_metadata or {})
    metadata.update(
        {
            "raw_content_sha256": digest,
            "raw_content_bytes": len(content),
            "source_content_type": content_type,
            "detected_content_type": normalized_content_type,
            "page_count": page_count,
            "ocr_confidence": ocr_confidence,
            "extraction_method": transformations[-1] if transformations else "none",
            "content_validation": {
                "mime_validated": not any(
                    item.startswith("content_type_mismatch:")
                    for item in content_validation_warnings
                ),
                "warnings": list(content_validation_warnings),
            },
            "document_quality": quality,
            "raw_content_preserved": True,
        }
    )
    reference_metadata = metadata.get("reference")
    if isinstance(reference_metadata, dict):
        referenced_decision_id = reference_metadata.get("decision_id")
        if isinstance(referenced_decision_id, str) and referenced_decision_id.strip():
            metadata["decision_document_link"] = {
                "decision_id": referenced_decision_id,
                "document_id": document_id,
                "relation": "decision_document",
                "evidence": "explicit_document_reference",
            }
    trace = source_trace or SourceTrace(
        provider=source,
        endpoint="",
        source_url=url,
        content_type=content_type,
        content_sha256=digest,
        response_bytes=len(content),
    )
    # Keep the trace aligned with the validated type, while the original
    # declaration remains available in ``raw_metadata`` for audit purposes.
    trace.content_type = normalized_content_type
    if trace.content_sha256 and trace.content_sha256 != digest:
        trace.transformations.append("trace_hash_corrected")
    trace.content_sha256 = digest
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
        page_count=page_count,
        ocr_confidence=ocr_confidence,
    )


def detect_content_type(content: bytes, content_type: str | None) -> str:
    """Return a stable media type, correcting a misleading PDF header."""

    header_type = (content_type or "").split(";", 1)[0].strip().lower()
    # Public court portals frequently return ``text/html`` for a PDF download
    # (or omit the header entirely).  The PDF magic marker is unambiguous and
    # must win so that we do not index binary bytes as HTML text.
    if content.startswith(b"%PDF-"):
        return "application/pdf"
    if header_type:
        return header_type
    if re.search(rb"<html|<!doctype html", content[:4096], re.IGNORECASE):
        return "text/html"
    if content.lstrip().startswith((b"{", b"[")):
        return "application/json"
    return "text/plain"


def assess_document_content(
    content: bytes,
    declared_content_type: str | None,
    *,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Return deterministic, JSON-safe quality facts for one response.

    This is deliberately a *classification* boundary, not a best-effort
    parser fallback.  A malformed, encrypted, over-sized or empty document is
    represented explicitly so callers cannot mistake it for an authoritative
    empty search result.  The function never executes content and never
    attempts to solve an access-control challenge.
    """

    if max_bytes is not None and max_bytes < 1:
        raise ValueError("max_bytes must be positive when provided")
    detected = detect_content_type(content, declared_content_type)
    declared = (declared_content_type or "").split(";", 1)[0].strip().lower() or None
    digest = hashlib.sha256(content).hexdigest()
    quality: dict[str, Any] = {
        "status": "valid",
        "byte_size": len(content),
        "sha256": digest,
        "declared_content_type": declared,
        "detected_content_type": detected,
        "size_status": "within_limit",
        "mime_status": "not_declared" if declared is None else "matched",
        "pdf_status": None,
        "warnings": [],
    }
    if not content:
        quality["status"] = "empty"
        quality["size_status"] = "empty"
        quality["warnings"].append("document_has_no_bytes")
        return quality
    if max_bytes is not None and len(content) > max_bytes:
        quality["status"] = "too_large"
        quality["size_status"] = "exceeded"
        quality["warnings"].append("document_exceeds_configured_byte_limit")
        return quality
    if declared is not None and declared != detected:
        quality["mime_status"] = (
            "mismatch_corrected" if detected == "application/pdf" else "mismatch"
        )
        quality["warnings"].append(f"content_type_mismatch:{declared}->{detected}")
    if detected == "application/pdf":
        pdf_status, page_count = _inspect_pdf(content)
        quality["pdf_status"] = pdf_status
        quality["page_count"] = page_count
        if pdf_status in {"malformed", "invalid_magic", "encrypted", "zero_pages"}:
            quality["status"] = "invalid"
            quality["warnings"].append(f"pdf_{pdf_status}")
    elif detected.startswith("text/") and not content.decode("utf-8", errors="replace").strip():
        quality["status"] = "empty_text"
        quality["warnings"].append("document_text_is_empty")
    return quality


def _content_validation_warnings(
    content: bytes, declared_content_type: str | None, detected_content_type: str
) -> list[str]:
    """Describe safe, deterministic mismatches without discarding source bytes."""

    declared = (declared_content_type or "").split(";", 1)[0].strip().lower()
    if not declared or declared == detected_content_type:
        return []
    # A PDF magic marker is a correction rather than a parser error.  Other
    # mismatches are retained as evidence because portals occasionally return
    # an HTML login/challenge page with a JSON/PDF content type.
    return [f"content_type_mismatch:{declared}->{detected_content_type}"]


def _safe_pdf_page_count(content: bytes) -> int | None:
    """Return a PDF page count without turning malformed input into a crash."""

    try:
        from pypdf import PdfReader

        return len(PdfReader(BytesIO(content)).pages)
    except Exception:  # noqa: BLE001 - metadata is best effort
        return None


def _inspect_pdf(content: bytes) -> tuple[str, int | None]:
    """Validate the small amount of PDF structure needed by the contract."""

    if not content.startswith(b"%PDF-"):
        return "invalid_magic", None
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content), strict=False)
        if bool(getattr(reader, "is_encrypted", False)):
            return "encrypted", None
        pages = len(reader.pages)
        if pages == 0:
            return "zero_pages", 0
        return "valid", pages
    except Exception:  # noqa: BLE001 - malformed remote PDF is a data fact
        return "malformed", None


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
        transformations.extend(("pdf_structure_validated", "pdf_text_extracted"))
        if not pages:
            return (
                None,
                ExtractionStatus.UNSUPPORTED_FORMAT,
                ["PDF sem paginas; documento vazio ou estruturalmente invalido."],
                transformations,
            )
        if not text and pages:
            # A scanned/image-only PDF is not an empty legal document.  Keep
            # the bytes and make the missing OCR capability explicit so
            # callers do not mistake it for a successful empty extraction.
            return (
                None,
                ExtractionStatus.UNSUPPORTED_FORMAT,
                ["PDF sem camada textual; OCR autorizado ainda nao configurado."],
                transformations,
            )
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


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _atomic_write_text(path: Path, content: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
