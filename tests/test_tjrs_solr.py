from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, RateLimitDetectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjrs_solr import (
    TjrsSolrProvider,
    parse_tjrs_search_response,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, payload, *, status_code: int = 200):
        self.payload = payload
        self.status_code = status_code
        self.url = "https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php"
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
        self.content = json.dumps(payload).encode("utf-8") if isinstance(payload, dict) else b""
        self.text = self.content.decode("utf-8")

    def json(self):
        if not isinstance(self.payload, dict):
            raise ValueError("invalid json")
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def _fixture() -> dict:
    return json.loads(
        (ROOT / "tests" / "fixtures" / "tjrs_solr_results.json").read_text(encoding="utf-8")
    )


def test_tjrs_parser_keeps_identity_and_separates_dates():
    page = parse_tjrs_search_response(
        _fixture(),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=1),
        trace=SourceTrace(provider="tjrs_solr", endpoint="/buscas/jurisprudencia/ajax.php"),
    )

    result = page.results[0]
    assert result.id == "tjrs-solr-TJRS-0001"
    assert result.judgment_date == "2026-01-10"
    assert result.publication_date == "2026-01-20"
    assert result.updated_at is None
    assert result.access_status.value == "public"
    assert page.is_complete is False


def test_tjrs_parser_unwraps_solr_multivalue_fields():
    """Solr text fields arrive as single-element lists; the canonical summary
    must not leak the Python list repr (``['...']``)."""

    page = parse_tjrs_search_response(
        _fixture(),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=1),
        trace=SourceTrace(provider="tjrs_solr", endpoint="/buscas/jurisprudencia/ajax.php"),
    )

    result = page.results[0]
    assert result.summary == "Ementa publica de fixture do TJRS."
    assert not result.summary.startswith("[")
    assert result.court == "TJRS"
    assert result.rapporteur == "Relator de Fixture"
    assert result.type == "Acordao"


def test_tjrs_search_trace_contains_http_evidence():
    response = FakeResponse(_fixture())
    provider = TjrsSolrProvider(NanoJurisConfig(rate_limit_interval=0), FakeSession([response]))

    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page_size=1))
    trace = page.source_trace

    assert trace is not None
    assert trace.http_status == 200
    assert trace.content_type == "application/json; charset=utf-8"
    assert trace.response_bytes == len(response.content)
    assert trace.content_sha256 == hashlib.sha256(response.content).hexdigest()
    assert trace.retrieval_status == "ok"


def test_tjrs_parser_rejects_missing_stable_identifier():
    payload = _fixture()
    payload["response"]["docs"][0].pop("cod_ementa")
    payload["response"]["docs"][0].pop("numero_processo")
    payload["response"]["docs"][0].pop("_version_", None)

    with pytest.raises(ParserContractChangedError, match="stable identifier"):
        parse_tjrs_search_response(
            payload,
            query=JurisprudenceQuery(text="termo"),
            trace=SourceTrace(provider="tjrs_solr", endpoint="/buscas/jurisprudencia/ajax.php"),
        )


def test_tjrs_classifies_rate_limit():
    provider = TjrsSolrProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession([FakeResponse({}, status_code=429)])
    )

    with pytest.raises(RateLimitDetectedError):
        provider.search(JurisprudenceQuery(text="termo"))


def test_tjrs_capability_declares_parser_identity():
    capability = TjrsSolrProvider(NanoJurisConfig(rate_limit_interval=0)).get_capabilities()
    assert "id" in capability.extracted_fields


def test_tjrs_public_detail_decodes_and_preserves_tiff_bytes():
    tiff = b"II*\x00" + b"fixture-tiff"
    response = FakeResponse({"documento": base64.b64encode(tiff).decode("ascii")})
    provider = TjrsSolrProvider(NanoJurisConfig(rate_limit_interval=0), FakeSession([response]))

    document = provider.get_document("tjrs-solr-5228633")

    assert document.id == "tjrs-solr-5228633"
    assert document.content_type == "image/tiff"
    assert document.document_type == "inteiro_teor_tiff"
    assert document.raw_bytes == tiff
    assert document.extraction_status.value == "unsupported_format"
    assert document.source_trace is not None
    assert document.source_trace.query["codigo_documento"] == "5228633"


def test_tjrs_public_detail_rejects_non_tiff_payload():
    response = FakeResponse({"documento": base64.b64encode(b"not-tiff").decode("ascii")})
    provider = TjrsSolrProvider(NanoJurisConfig(rate_limit_interval=0), FakeSession([response]))

    with pytest.raises(ParserContractChangedError, match="not a TIFF"):
        provider.get_document("5228633")


def test_tjrs_tiff_ocr_is_explicit_and_bounded():
    tiff = b"II*\x00" + b"fixture-tiff"
    response = FakeResponse({"documento": base64.b64encode(tiff).decode("ascii")})
    provider = TjrsSolrProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([response]),
        ocr_allowed=True,
        ocr_max_pages=1,
        ocr_timeout_seconds=5,
    )

    document = provider.get_document("5228633")

    assert document.raw_bytes == tiff
    assert document.extraction_trace is not None
    assert document.extraction_status.value in {"unsupported_format", "failed", "partial"}
