from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import QueryRejectedError, SourceUnavailableError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjac_ementario_jurisprudencia import (
    TjacEmentarioJurisprudenciaProvider,
    parse_tjac_ementario_text,
)
from nanojuris.transport.models import TransportResponse, TransportStatus

FIXTURES = Path(__file__).parent / "fixtures"


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="tjac_ementario_jurisprudencia",
        endpoint="GET /Ementario_TJAC_Vol_XXX_2026.pdf",
        source_url="https://www.tjac.jus.br/wp-content/uploads/2026/07/Ementario_TJAC_Vol_XXX_2026.pdf",
    )


def test_parser_extracts_cnj_identity_and_second_degree() -> None:
    text = (FIXTURES / "tjac_ementario_success.txt").read_text(encoding="utf-8")
    records = parse_tjac_ementario_text(
        text,
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=10),
        trace=_trace(),
    )
    assert len(records) == 1
    record = records[0]
    assert record.authority == "TJAC"
    assert record.branch == "state"
    assert record.degree == "second"
    assert record.instance == "second"
    assert record.collection == "TJAC_EMENTARIO"
    assert record.number == "1002263-13.2025.8.01.0000"
    assert record.judgment_date == "2026-04-01"
    assert "responsabilidade civil" in (record.summary or "").casefold()
    assert record.document_url == _trace().source_url
    assert record.raw["source_record_id"] == record.id
    assert "source_record_id" in record.field_provenance


def test_parser_applies_number_and_negative_terms() -> None:
    text = (FIXTURES / "tjac_ementario_success.txt").read_text(encoding="utf-8")
    trace = _trace()
    exact = parse_tjac_ementario_text(
        text,
        query=JurisprudenceQuery(number="1001922-84.2025.8.01.0000"),
        trace=trace,
    )
    assert len(exact) == 1
    assert exact[0].number == "1001922-84.2025.8.01.0000"
    excluded = parse_tjac_ementario_text(
        text,
        query=JurisprudenceQuery(text="servidor publico", without_words="prova documental"),
        trace=trace,
    )
    assert excluded == []


def test_provider_rejects_invalid_scope_and_empty_query() -> None:
    provider = TjacEmentarioJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError, match="termo"):
        provider.search(JurisprudenceQuery())
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="x", degree="first"))
    with pytest.raises(QueryRejectedError, match="colecao"):
        provider.search(JurisprudenceQuery(text="x", collection="CJPG"))


def test_provider_capability_is_partial_but_federated() -> None:
    capabilities = TjacEmentarioJurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert capabilities.completeness_contract == "static_volume_total_unknown"
    assert capabilities.supports_full_text is False
    assert "case_class" in capabilities.unsupported_filters


def test_empty_and_invalid_fixtures_are_not_success_records() -> None:
    empty = (FIXTURES / "tjac_ementario_empty.txt").read_text(encoding="utf-8")
    invalid = (FIXTURES / "tjac_ementario_schema_invalid.txt").read_text(encoding="utf-8")
    trace = _trace()
    assert parse_tjac_ementario_text(empty, query=JurisprudenceQuery(text="x"), trace=trace) == []
    assert parse_tjac_ementario_text(invalid, query=JurisprudenceQuery(text="x"), trace=trace) == []


def test_pdf_download_uses_shared_transport_and_preserves_trace(monkeypatch) -> None:
    provider = TjacEmentarioJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    calls = []
    response = TransportResponse(
        status_code=200,
        url=provider.volume_url,
        final_url=provider.volume_url,
        headers={"Content-Type": "application/pdf"},
        body=b"%PDF-1.4\nbounded fixture",
        elapsed_ms=12.5,
        status=TransportStatus.COMPLETE,
    )

    def request(envelope):
        calls.append(envelope)
        return response

    monkeypatch.setattr(provider.http, "request", request)
    body, trace = provider._request_pdf(JurisprudenceQuery(text="responsabilidade civil"))

    assert body.startswith(b"%PDF-")
    assert calls[0].operation == "tjac_ementario_pdf"
    assert calls[0].method == "GET"
    assert trace.http_status == 200
    assert trace.response_bytes == len(body)


def test_pdf_transport_failure_is_not_classified_as_empty(monkeypatch) -> None:
    provider = TjacEmentarioJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    response = TransportResponse(
        status_code=None,
        url=provider.volume_url,
        final_url=None,
        headers={},
        body=b"",
        elapsed_ms=1.0,
        status=TransportStatus.RESPONSE_TOO_LARGE,
        error_type="response_too_large",
    )
    monkeypatch.setattr(provider.http, "request", lambda envelope: response)

    with pytest.raises(SourceUnavailableError, match="transport failed"):
        provider._request_pdf(JurisprudenceQuery(text="x"))
