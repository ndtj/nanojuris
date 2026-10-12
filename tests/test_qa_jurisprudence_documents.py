from __future__ import annotations

from tools.qa_jurisprudence_documents import _result_document_url


def test_document_probe_does_not_promote_search_trace_to_document_url() -> None:
    result = {
        "raw": {},
        "source_trace": {"source_url": "https://example.test/search"},
    }

    assert _result_document_url(result) is None


def test_document_probe_prefers_explicit_document_reference() -> None:
    result = {
        "raw": {
            "document_url": "https://example.test/document/123",
            "full_text_url": "https://example.test/document/123/full",
        },
        "source_trace": {"source_url": "https://example.test/search"},
    }

    assert _result_document_url(result) == "https://example.test/document/123"


def test_document_probe_can_use_full_text_url_when_document_url_is_absent() -> None:
    result = {
        "raw": {"full_text_url": "https://example.test/document/123/full"},
        "source_trace": {"source_url": "https://example.test/search"},
    }

    assert _result_document_url(result) == "https://example.test/document/123/full"


def test_document_probe_keeps_explicit_detail_url_even_when_trace_matches() -> None:
    result = {
        "raw": {"document_url": "https://example.test/jurisprudencia/j/123"},
        "source_trace": {"source_url": "https://example.test/jurisprudencia/j/123"},
    }

    assert _result_document_url(result) == "https://example.test/jurisprudencia/j/123"


def test_document_probe_rejects_explicit_ajax_search_url() -> None:
    result = {
        "raw": {"document_url": "https://example.test/buscas/jurisprudencia/ajax.php"},
        "source_trace": {"source_url": "https://example.test/buscas/jurisprudencia/ajax.php"},
    }

    assert _result_document_url(result) is None
