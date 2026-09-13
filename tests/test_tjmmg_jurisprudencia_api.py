from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    ParserContractChangedError,
    QueryRejectedError,
    SourceUnavailableError,
)
from nanojuris.models import AccessStatus, JurisprudenceQuery
from nanojuris.providers.tjmmg_jurisprudencia_api import TjmmgJurisprudenciaApiProvider
from nanojuris.transport.models import TransportResponse, TransportStatus

FIXTURES = Path(__file__).parent / "fixtures"


def _response(
    body: bytes,
    *,
    status: TransportStatus = TransportStatus.COMPLETE,
    content_type: str = "application/json",
    path: str = "jurisprudencia/search",
) -> TransportResponse:
    url = f"https://jurisprudencia.tjmmg.jus.br/jurisprudencia-api/api/{path}"
    return TransportResponse(
        status_code=200,
        url=url,
        final_url=url,
        headers={"Content-Type": content_type},
        body=body,
        elapsed_ms=1.0,
        status=status,
        error_type="response_too_large" if status is TransportStatus.RESPONSE_TOO_LARGE else None,
    )


def _bounded_query(**kwargs: str) -> JurisprudenceQuery:
    return JurisprudenceQuery(
        text="responsabilidade",
        judgment_date_from="2020-01-02",
        judgment_date_to="2020-01-02",
        **kwargs,
    )


def test_metadata_route_exposes_only_redacted_contract_fields() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    response = _response(
        (FIXTURES / "tjmmg_metadata.json").read_bytes(),
        path="jurisprudencia/get",
    )
    provider.transport.request = lambda request: response  # type: ignore[method-assign]
    parameters = provider.get_parameters()
    assert parameters["status"] == "metadata_public_bounded_search"
    assert "classnames" in parameters["metadata_keys"]
    assert "search_fields" in parameters


def test_unbounded_search_is_rejected_before_network_call() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    called = False

    def request(request: object) -> TransportResponse:
        nonlocal called
        called = True
        return _response(b'{"truncated":true}', status=TransportStatus.RESPONSE_TOO_LARGE)

    provider.transport.request = request  # type: ignore[method-assign]
    with pytest.raises(QueryRejectedError, match="intervalo fechado"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))
    assert called is False


def test_response_limit_is_not_converted_to_empty() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    provider.transport.request = lambda request: _response(  # type: ignore[method-assign]
        b'{"truncated":true}', status=TransportStatus.RESPONSE_TOO_LARGE
    )
    with pytest.raises(SourceUnavailableError, match="safe transport"):
        provider.search(_bounded_query())


def test_search_does_not_invent_client_side_pagination_fields() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    seen: dict[str, object] = {}

    def request(request: object) -> TransportResponse:
        seen.update(getattr(request, "json_body", {}) or {})
        return _response(b'{"collection":[]}')

    provider.transport.request = request  # type: ignore[method-assign]
    provider.search(_bounded_query(page_size=30))
    assert "page" not in seen
    assert "page_size" not in seen


def test_authoritative_empty_collection_is_explicit_empty() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    provider.transport.request = lambda request: _response(  # type: ignore[method-assign]
        b'{"collection":[]}'
    )
    page = provider.search(_bounded_query())
    assert page.total == 0
    assert page.total_known is True
    assert page.is_explicit_empty is True
    assert page.access_status is AccessStatus.PUBLIC


def test_complete_json_without_known_schema_is_contract_change() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    provider.transport.request = lambda request: _response(b"{}")  # type: ignore[method-assign]
    with pytest.raises(ParserContractChangedError, match="collection"):
        provider.search(_bounded_query())


def test_bounded_collection_preserves_canonical_fields_and_pdf_url() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    provider.transport.request = lambda request: _response(  # type: ignore[method-assign]
        (FIXTURES / "tjmmg_search.json").read_bytes()
    )
    page = provider.search(_bounded_query())
    result = page.results[0]
    assert result.authority == "TJMMG"
    assert result.branch == "military"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "CJSG"
    assert result.case_class == "Apelação Cível"
    assert result.summary and "responsabilidade" in result.summary
    assert result.full_text and "Texto integral" in result.full_text
    assert result.document_url and result.document_url.endswith("acordao-sanitizado-2020.pdf")
    assert result.raw["document_id"] == "tjmmg-file-acordao-sanitizado-2020.pdf"


def test_pdf_document_route_requires_pdf_and_builds_canonical_document() -> None:
    provider = TjmmgJurisprudenciaApiProvider(NanoJurisConfig(rate_limit_interval=0))
    provider.transport.request = lambda request: _response(  # type: ignore[method-assign]
        b"%PDF-1.5\n% sanitized fixture\n",
        content_type="application/pdf",
        path="jurisprudencia/file?filename=acordao-sanitizado-2020.pdf",
    )
    document = provider.get_document("tjmmg-file-acordao-sanitizado-2020.pdf")
    assert document.source == "tjmmg_jurisprudencia_api"
    assert document.document_type == "inteiro_teor"
    assert document.access_status is AccessStatus.PUBLIC


def test_tjmmg_is_opt_in_only() -> None:
    capabilities = TjmmgJurisprudenciaApiProvider().get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.filter_status("text") == "native"
    assert capabilities.filter_status("page") == "unsupported"
