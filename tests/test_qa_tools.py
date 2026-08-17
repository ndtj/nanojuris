from __future__ import annotations

import sys

from tools.qa_jurisprudence_documents import _summary


def test_document_qa_counts_probe_failures_as_partial_not_success() -> None:
    payload = _summary(
        [
            {
                "source": "provider_loaded",
                "status": "checked",
                "search": {"returned": 1},
                "provider_document": {"status": "loaded"},
            },
            {
                "source": "provider_partial",
                "status": "partial",
                "search": {"returned": 1},
                "public_url": {"status": "http_error", "http_status": 405},
                "document_failures": [{"surface": "public_url", "status": 405}],
            },
            {
                "source": "provider_error",
                "status": "error",
                "search": {},
            },
        ]
    )

    assert payload["sources_checked"] == 3
    assert payload["provider_document_loaded"] == 1
    assert payload["document_probe_failures"] == 1
    assert payload["partial"] == 1
    assert payload["errors"] == 1


def test_package_size_budget_passes_for_current_static_assets(monkeypatch):
    import tools.check_package_size as size_check

    monkeypatch.setattr(size_check, "directory_size", lambda _path: 1)
    previous = sys.argv
    try:
        sys.argv = ["check_package_size", "--static-dir", "static"]
        assert size_check.main() == 0
    finally:
        sys.argv = previous


def test_package_size_budget_rejects_oversized_static_assets(monkeypatch):
    import tools.check_package_size as size_check

    monkeypatch.setattr(size_check, "directory_size", lambda _path: 300_001)
    previous = sys.argv
    try:
        sys.argv = ["check_package_size", "--static-dir", "static"]
        assert size_check.main() == 1
    finally:
        sys.argv = previous
