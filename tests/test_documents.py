from __future__ import annotations

from hashlib import sha256

from nanojuris.documents import build_canonical_document
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
