from __future__ import annotations

from hashlib import sha256
from io import BytesIO

import pytest
from pypdf import PdfWriter

from nanojuris.documents import assess_document_content, build_canonical_document
from nanojuris.errors import ParserContractChangedError
from nanojuris.models import AccessStatus, ExtractionStatus, SourceTrace


def test_build_canonical_document_preserves_html_bytes_and_extracts_text():
    content = b"<html><body><h1>Acordao publico</h1><p>Inteiro teor.</p></body></html>"

    document = build_canonical_document(
        document_id="doc-html",
        source="fixture",
        document_type="acordao",
        content=content,
        content_type="text/html; charset=utf-8",
        url="https://example.test/doc-html",
        title="Acordao publico",
        source_trace=SourceTrace(provider="fixture", endpoint="/doc-html"),
        access_status=AccessStatus.PUBLIC,
        parser="fixture.document",
    )

    assert document.text == "Acordao publico Inteiro teor."
    assert document.raw_bytes == content
    assert document.sha256 == sha256(content).hexdigest()
    assert document.byte_size == len(content)
    assert document.extraction_status == ExtractionStatus.COMPLETE
    assert document.raw_metadata["raw_content_preserved"] is True
    assert document.to_dict()["raw_bytes_preserved"] is True
    assert "raw_bytes_base64" not in document.to_dict()
    assert document.to_dict(include_raw_bytes=True)["raw_bytes_base64"]


def test_build_canonical_document_keeps_binary_content_when_text_is_unavailable():
    content = b"%PDF-1.4\nnot-a-complete-pdf\n%%EOF"

    document = build_canonical_document(
        document_id="doc-pdf",
        source="fixture",
        document_type="acordao",
        content=content,
        content_type="application/pdf",
        url="https://example.test/doc-pdf",
        title="PDF publico",
        source_trace=SourceTrace(provider="fixture", endpoint="/doc-pdf"),
        access_status=AccessStatus.PUBLIC,
        parser="fixture.document",
    )

    assert document.raw_bytes == content
    assert document.sha256 == sha256(content).hexdigest()
    assert document.byte_size == len(content)
    assert document.content_type == "application/pdf"
    assert document.extraction_status in {
        ExtractionStatus.FAILED,
        ExtractionStatus.UNSUPPORTED_FORMAT,
    }
    assert document.extraction_trace is not None
    assert document.extraction_trace.access_status == AccessStatus.PUBLIC


def test_scanned_or_image_only_pdf_is_not_reported_as_empty():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(stream)

    document = build_canonical_document(
        document_id="doc-scanned",
        source="fixture",
        document_type="acordao",
        content=stream.getvalue(),
        content_type="application/pdf",
        url="https://example.test/doc-scanned",
        title="PDF sem camada textual",
        source_trace=SourceTrace(provider="fixture", endpoint="/doc-scanned"),
        access_status=AccessStatus.PUBLIC,
        parser="fixture.document",
    )

    assert document.text is None
    assert document.extraction_status is ExtractionStatus.UNSUPPORTED_FORMAT
    assert document.extraction_trace is not None
    assert any("OCR" in warning for warning in document.extraction_trace.warnings)


def test_ocr_requires_explicit_opt_in_and_preserves_bounded_state():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(stream)

    document = build_canonical_document(
        document_id="doc-scanned-ocr-opt-in",
        source="fixture",
        document_type="acordao",
        content=stream.getvalue(),
        content_type="application/pdf",
        url="https://example.test/doc-scanned-ocr-opt-in",
        title="PDF OCR opt-in",
        source_trace=SourceTrace(provider="fixture", endpoint="/doc-scanned-ocr-opt-in"),
        access_status=AccessStatus.PUBLIC,
        parser="fixture.document",
        ocr_allowed=True,
        ocr_max_pages=1,
        ocr_timeout_seconds=5,
    )

    assert document.raw_bytes
    assert document.extraction_trace is not None
    assert document.raw_metadata["ocr_confidence"] is None or isinstance(
        document.raw_metadata["ocr_confidence"], float
    )
    assert document.extraction_status is not ExtractionStatus.EMPTY


def test_pdf_magic_marker_corrects_misleading_html_header_and_records_provenance():
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(stream)

    document = build_canonical_document(
        document_id="doc-mislabeled-pdf",
        source="fixture",
        document_type="acordao",
        content=stream.getvalue(),
        content_type="text/html; charset=utf-8",
        url="https://example.test/doc-mislabeled-pdf",
        title="PDF com cabeçalho incorreto",
        source_trace=SourceTrace(provider="fixture", endpoint="/doc-mislabeled-pdf"),
        access_status=AccessStatus.PUBLIC,
        parser="fixture.document",
    )

    assert document.content_type == "application/pdf"
    assert document.source_trace is not None
    assert document.source_trace.content_type == "application/pdf"
    assert document.raw_metadata["detected_content_type"] == "application/pdf"
    assert document.page_count == 1
    assert document.ocr_confidence is None
    assert document.raw_metadata["content_validation"]["mime_validated"] is False
    assert "content_type_mismatch:text/html->application/pdf" in document.extraction_trace.warnings


def test_zero_page_pdf_is_structurally_invalid_not_real_empty_text():
    stream = BytesIO()
    PdfWriter().write(stream)

    document = build_canonical_document(
        document_id="doc-zero-pages",
        source="fixture",
        document_type="acordao",
        content=stream.getvalue(),
        content_type="application/pdf",
        url="https://example.test/doc-zero-pages",
        title="PDF sem páginas",
        source_trace=SourceTrace(provider="fixture", endpoint="/doc-zero-pages"),
        access_status=AccessStatus.PUBLIC,
        parser="fixture.document",
    )

    assert document.text is None
    assert document.extraction_status is ExtractionStatus.UNSUPPORTED_FORMAT
    assert document.page_count == 0
    assert any("sem paginas" in warning for warning in document.extraction_trace.warnings)


def test_document_quality_classifies_pdf_corruption_and_hash_without_losing_bytes():
    content = b"%PDF-1.7\nnot-a-valid-pdf"

    quality = assess_document_content(content, "application/pdf", max_bytes=1024)

    assert quality["status"] == "invalid"
    assert quality["pdf_status"] == "malformed"
    assert quality["byte_size"] == len(content)
    assert quality["sha256"] == sha256(content).hexdigest()


def test_document_quality_classifies_size_before_parser_work():
    quality = assess_document_content(b"0123456789", "text/plain", max_bytes=4)

    assert quality["status"] == "too_large"
    assert quality["size_status"] == "exceeded"
    assert quality["pdf_status"] is None


def test_build_document_rejects_explicit_oversize_limit():
    with pytest.raises(ParserContractChangedError, match="byte limit"):
        build_canonical_document(
            document_id="doc-too-large",
            source="fixture",
            document_type="acordao",
            content=b"0123456789",
            content_type="text/plain",
            url="https://example.test/doc-too-large",
            title="Documento grande",
            source_trace=SourceTrace(provider="fixture", endpoint="/doc-too-large"),
            access_status=AccessStatus.PUBLIC,
            parser="fixture.document",
            max_bytes=4,
        )


def test_trace_hash_is_aligned_with_validated_bytes():
    content = b"<html><body>hash correto</body></html>"
    trace = SourceTrace(
        provider="fixture",
        endpoint="/hash",
        content_sha256="0" * 64,
    )

    document = build_canonical_document(
        document_id="doc-hash",
        source="fixture",
        document_type="acordao",
        content=content,
        content_type="text/html",
        url="https://example.test/doc-hash",
        title="Hash",
        source_trace=trace,
        access_status=AccessStatus.PUBLIC,
        parser="fixture.document",
    )

    assert document.source_trace is not None
    assert document.source_trace.content_sha256 == sha256(content).hexdigest()
    assert "trace_hash_corrected" in document.source_trace.transformations


def test_document_reference_preserves_explicit_decision_link():
    content = b"<html><body>Inteiro teor vinculado</body></html>"
    document = build_canonical_document(
        document_id="doc-linked",
        source="fixture",
        document_type="acordao",
        content=content,
        content_type="text/html",
        url="https://example.test/doc-linked",
        title="Documento vinculado",
        source_trace=SourceTrace(provider="fixture", endpoint="/doc-linked"),
        access_status=AccessStatus.PUBLIC,
        raw_metadata={
            "reference": {
                "document_id": "doc-linked",
                "decision_id": "decision-1",
            }
        },
        parser="fixture.document",
    )

    assert document.raw_metadata["decision_document_link"] == {
        "decision_id": "decision-1",
        "document_id": "doc-linked",
        "relation": "decision_document",
        "evidence": "explicit_document_reference",
    }
