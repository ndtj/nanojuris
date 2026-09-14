from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.trt6_jurisprudencia import (
    Trt6JurisprudenciaProvider,
    parse_trt6_filter_catalog,
)
from nanojuris.transport.models import TransportRequest, TransportResponse, TransportStatus

FIXTURES = Path(__file__).parent / "fixtures"


def _response(body: bytes, *, content_type: str = "application/json") -> TransportResponse:
    return TransportResponse(
        status_code=200,
        url="https://pje.trt6.jus.br/juris-backend/api/documentos",
        final_url="https://pje.trt6.jus.br/juris-backend/api/documentos",
        headers={"Content-Type": content_type},
        body=body,
        elapsed_ms=1.0,
        status=TransportStatus.COMPLETE,
    )


def _legacy_response(body: bytes) -> TransportResponse:
    return TransportResponse(
        status_code=200,
        url="https://apps.trt6.jus.br/acordaos/pesquisar",
        final_url="https://apps.trt6.jus.br/acordaos/pesquisar",
        headers={"Content-Type": "text/html; charset=UTF-8"},
        body=body,
        elapsed_ms=1.0,
        status=TransportStatus.COMPLETE,
    )


def test_search_uses_public_legacy_contract() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    provider._legacy_transport.request = lambda request: _legacy_response(  # type: ignore[method-assign]
        (FIXTURES / "trt6_legacy_search_success.html").read_bytes()
    )
    page = provider.search(JurisprudenceQuery(text="responsabilidade civil"))
    assert page.results[0].authority == "TRT6"
    assert page.results[0].degree == "second"
    assert page.results[0].document_url is not None
    assert page.access_status is not None


def test_legacy_search_preserves_utf8_accents() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    html = (FIXTURES / "trt6_legacy_search_success.html").read_text(encoding="utf-8")
    html = html.replace("Ementa sanitizada.", "Ementa com decisão.")
    provider._legacy_transport.request = lambda request: _legacy_response(  # type: ignore[method-assign]
        html.encode("utf-8")
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade civil"))

    assert "decisão" in (page.results[0].summary or "")
    assert "decisÃ" not in (page.results[0].summary or "")


def test_legacy_search_translates_page_and_filters() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    captured: list[TransportRequest] = []

    def request(request: TransportRequest) -> TransportResponse:
        captured.append(request)
        return _legacy_response((FIXTURES / "trt6_legacy_search_success.html").read_bytes())

    provider._legacy_transport.request = request  # type: ignore[method-assign]
    page = provider.search(
        JurisprudenceQuery(
            text="responsabilidade civil",
            rapporteur="Relator Sanitizado",
            judging_body="Segunda Turma",
            page=2,
        )
    )
    assert page.page == 2
    assert captured[0].data["pagina"] == "2"
    assert captured[0].data["redator"] == "Relator Sanitizado"
    assert captured[0].data["orgaoJulgador"] == "Segunda Turma"


def test_public_options_are_redacted_to_contract_metadata() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    provider._pje_transport.request = lambda request: _response(  # type: ignore[method-assign]
        (FIXTURES / "trt6_pje_options.json").read_bytes()
    )
    parameters = provider.get_parameters()
    assert parameters["status"] == "metadata_public_search_requires_recaptcha"
    assert parameters["metadata"]["regional"] == "TRT6"
    assert "recaptchaSiteKey" in parameters["metadata"]


def test_public_filter_catalog_is_metadata_only() -> None:
    payload = {
        "hits": 123,
        "documents": [],
        "aggregations": [
            {"fieldName": "classeJudicial", "list": [{"key": "Acao", "qte": 1}]},
            {"fieldName": "tipoDocumento", "list": [{"key": "Acordao", "qte": 3}]},
        ],
    }
    summary = parse_trt6_filter_catalog(payload, response_bytes=512)
    assert summary["status"] == "metadata_public"
    assert summary["search_results_observed"] is False
    assert summary["recaptcha_required_for_documents"] is True
    assert summary["fields"] == [
        {"field_name": "classeJudicial", "value_count": 1},
        {"field_name": "tipoDocumento", "value_count": 1},
    ]


def test_public_filter_catalog_rejects_missing_aggregations() -> None:
    with pytest.raises(ParserContractChangedError, match="agrega"):
        parse_trt6_filter_catalog({"hits": 0, "documents": []})


def test_capabilities_declare_public_legacy_search() -> None:
    capabilities = Trt6JurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert "degree=second" in capabilities.semantic_discriminator


def test_legacy_parser_preserves_ementa_and_decision() -> None:
    from nanojuris.providers.trt6_jurisprudencia import parse_trt6_legacy_results

    page = parse_trt6_legacy_results(
        (FIXTURES / "trt6_legacy_search_success.html").read_text(encoding="utf-8"),
        trace=None,  # type: ignore[arg-type]
        base_url="https://apps.trt6.jus.br",
    )
    assert page[0].case_class == "Recurso Ordinario"
    assert page[0].judging_body == "Segunda Turma"
    assert "responsabilidade civil" in (page[0].summary or "").casefold()
    assert "ACORDAM" in (page[0].full_text or "")


def test_query_scope_is_explicit() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="x", degree="first"))


def test_authorized_search_uses_ephemeral_recaptcha_token_and_parses_documents() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    captured: list[TransportRequest] = []

    def request(request: TransportRequest) -> TransportResponse:
        captured.append(request)
        return _response((FIXTURES / "trt6_pje_authorized_success.json").read_bytes())

    provider._pje_transport.request = request  # type: ignore[method-assign]
    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade civil", page_size=5),
        recaptcha_token="ephemeral-recaptcha-token",
    )

    assert page.total == 1
    assert page.total_known is True
    assert page.results[0].degree == "second"
    assert page.results[0].instance == "second"
    assert page.results[0].authority == "TRT6"
    assert page.results[0].summary == "Ementa sanitizada"
    assert "token" not in page.results[0].raw
    assert page.results[0].source_trace is not None
    assert "token" not in page.results[0].source_trace.query
    assert captured
    payload = captured[0].json_body
    assert payload["token"] == "ephemeral-recaptcha-token"


def test_authorized_search_requires_human_token() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(AccessControlRequiredError, match="token reCAPTCHA"):
        provider.search_authorized(
            JurisprudenceQuery(text="acordao"),
            recaptcha_token="",
        )


def test_unknown_empty_authorized_window_is_not_complete() -> None:
    provider = Trt6JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    def request(request: TransportRequest) -> TransportResponse:
        return _response(b'{"documents": []}')

    provider._pje_transport.request = request  # type: ignore[method-assign]
    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade civil"),
        recaptcha_token="ephemeral-recaptcha-token",
    )

    assert page.results == []
    assert page.total_known is False
    assert page.is_complete is False
    assert page.extraction_status.value == "partial"
