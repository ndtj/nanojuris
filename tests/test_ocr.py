from __future__ import annotations

import pytest

from nanojuris.ocr import extract_pdf_text, extract_tiff_text


def test_ocr_rejects_non_pdf_and_invalid_limits() -> None:
    with pytest.raises(ValueError, match="PDF"):
        extract_pdf_text(b"not a pdf")
    with pytest.raises(ValueError, match="max_pages"):
        extract_pdf_text(b"%PDF-1.7", max_pages=0)
    with pytest.raises(ValueError, match="timeout_seconds"):
        extract_pdf_text(b"%PDF-1.7", timeout_seconds=0)


def test_ocr_is_explicit_and_reports_missing_optional_dependencies() -> None:
    result = extract_pdf_text(b"%PDF-1.7\n%%EOF")
    assert result.status in {"unsupported", "failed", "empty"}
    if result.status == "unsupported":
        assert result.pages_processed == 0
        assert result.text is None
        assert result.warnings


def test_tiff_ocr_rejects_wrong_magic_and_is_bounded() -> None:
    with pytest.raises(ValueError, match="TIFF"):
        extract_tiff_text(b"not a tiff")
    with pytest.raises(ValueError, match="max_pages"):
        extract_tiff_text(b"II*\x00", max_pages=0)
    with pytest.raises(ValueError, match="timeout_seconds"):
        extract_tiff_text(b"II*\x00", timeout_seconds=0)


def test_tiff_ocr_reports_optional_dependency_boundary() -> None:
    result = extract_tiff_text(b"II*\x00")
    assert result.status in {"unsupported", "failed", "empty"}
    if result.status == "unsupported":
        assert result.pages_processed == 0
        assert result.text is None
        assert result.warnings
