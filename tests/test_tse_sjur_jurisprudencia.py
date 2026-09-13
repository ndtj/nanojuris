from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    SourceUnavailableError,
)
from nanojuris.models import AccessStatus, CanonicalDocument, ExtractionStatus, JurisprudenceQuery
from nanojuris.providers.tse_sjur_jurisprudencia import (
    TreSjurJurisprudenciaProvider,
    TseSjurJurisprudenciaProvider,
    build_tse_query,
)
from nanojuris.transport.models import TransportResponse

ROOT = Path(__file__).parent / "fixtures"


def fixture(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def response(payload: object, *, status_code: int = 200) -> TransportResponse:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return TransportResponse(
        status_code=status_code,
        url="https://sjur-pesquisa-api.tse.jus.br/tse/sjur-pesquisa-backend/rest/public/pesquisa/simples",
        final_url="https://sjur-pesquisa-api.tse.jus.br/tse/sjur-pesquisa-backend/rest/public/pesquisa/simples",
        headers={"Content-Type": "application/json"},
        body=body,
        elapsed_ms=2.0,
    )


def provider_with(payload: object, *, status_code: int = 200) -> TseSjurJurisprudenciaProvider:
    provider = TseSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
    )
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        return response(payload, status_code=status_code)

    provider.transport.request = request  # type: ignore[method-assign]
    provider._test_calls = calls  # type: ignore[attr-defined]
    return provider


def test_exact_result_maps_fields_and_trace():
    provider = provider_with(fixture("tse_sjur_success.json"))

    page = provider.search(JurisprudenceQuery(number="504401", page_size=3))
    result = page.results[0]

    assert page.total == 1
    assert page.total_known is True
    assert page.is_explicit_empty is False
    assert result.id == "tse-sjur-504401"
    assert result.authority == "TSE"
    assert result.branch == "electoral"
    assert result.degree == "superior"
    assert result.instance == "superior"
    assert result.collection == "SJUR"
    assert result.summary == "CONSULTA. INELEGIBILIDADE REFLEXA."
    assert result.full_text == "O Tribunal, por unanimidade, não conheceu da consulta."
    assert result.judgment_date == "2019-06-13"
    assert result.publication_date == "2019-08-26"
    assert result.document_url.endswith("/download/pdf/504401")


def test_request_contains_serialized_dsl_and_tse_scope():
    provider = provider_with(fixture("tse_sjur_empty.json"))

    provider.search(JurisprudenceQuery(text="divórcio", page=2, page_size=3))
    request = provider._test_calls[0]  # type: ignore[attr-defined]
    body = request.json_body  # type: ignore[attr-defined]
    assert body["tribunais"] == ["tse"]
    assert body["pagina"] == 1
    assert body["tamanho"] == 3
    dsl = json.loads(body["termoPesquisa"])
    assert dsl["bool"]["filter"] == [{"terms": {"siglaTribunalJE.keyword": ["TSE"]}}]


def test_text_window_is_not_marked_exhaustive() -> None:
    page = provider_with(fixture("tse_sjur_success.json")).search(
        JurisprudenceQuery(text="divÃ³rcio")
    )

    assert page.total_known is False
    assert page.is_complete is False
    assert "nao e exaustivo" in (page.completeness_reason or "")


def test_public_window_is_bounded_to_requested_page_size() -> None:
    payload = fixture("tse_sjur_success.json")
    first = dict(payload["content"][0])  # type: ignore[index]
    second = dict(first)
    second["codigoDecisao"] = 504402
    payload["content"] = [first, second]  # type: ignore[index]
    payload["totalRegistros"] = 2

    page = provider_with(payload).search(JurisprudenceQuery(text="termo", page_size=1))

    assert len(page.results) == 1
    assert page.results[0].id == "tse-sjur-504401"
    assert page.total == 2
    assert page.total_known is False
    assert page.is_complete is False
    assert "janela textual" in (page.completeness_reason or "")


def test_explicit_empty_is_not_unknown():
    page = provider_with(fixture("tse_sjur_empty.json")).search(
        JurisprudenceQuery(text="termo inexistente")
    )
    assert page.total == 0
    assert page.total_known is True
    assert page.is_explicit_empty is True


def test_access_control_is_not_empty():
    with pytest.raises(AccessControlRequiredError):
        provider_with({"mensagem": "captcha required"}, status_code=403).search(
            JurisprudenceQuery(text="eleição")
        )


def test_syntax_message_is_rejected():
    with pytest.raises(QueryRejectedError):
        provider_with({"mensagem": "Erro na sintaxe de pesquisa.", "content": []}).search(
            JurisprudenceQuery(text="termo")
        )


def test_schema_drift_is_explicit():
    with pytest.raises(ParserContractChangedError):
        provider_with(fixture("tse_sjur_schema_drift.json")).search(
            JurisprudenceQuery(text="termo")
        )


def test_capabilities_remain_runtime_opt_in_only():
    capabilities = TseSjurJurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.pagination_mode == "none"
    assert capabilities.filter_status("page") == "unsupported"
    assert capabilities.filter_status("page_size") == "unsupported"
    assert capabilities.filter_status("text") == "translated"
    assert capabilities.filter_status("degree") == "validated_scope"
    assert capabilities.filter_status("instance") == "validated_scope"
    assert capabilities.filter_status("authority") == "validated_scope"
    assert capabilities.filter_status("collection") == "validated_scope"
    assert "degree" not in capabilities.unsupported_filters
    assert "download/pdf" in " ".join(capabilities.endpoints)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authority", "TRE-SP"),
        ("branch", "state"),
        ("degree", "first"),
        ("instance", "first"),
        ("collection", "CJSG"),
    ],
)
def test_scope_filters_reject_surfaces_outside_tse_contract(field: str, value: str) -> None:
    provider = provider_with(fixture("tse_sjur_empty.json"))
    query = JurisprudenceQuery(text="eleicao")
    setattr(query, field, value)

    with pytest.raises(QueryRejectedError, match=field):
        provider.search(query)


def test_scope_filters_accept_the_fixed_tse_surface() -> None:
    provider = provider_with(fixture("tse_sjur_empty.json"))
    page = provider.search(
        JurisprudenceQuery(
            text="eleicao",
            authority="TSE",
            branch="electoral",
            degree="second",
            instance="superior",
            collection="SJUR",
        )
    )

    assert page.is_explicit_empty is True


def test_all_tre_authorities_are_available_as_explicit_opt_in_providers() -> None:
    """Keep the 27 official TRE bindings discoverable without federation promotion."""

    client = NanoJurisClient(
        NanoJurisConfig(rate_limit_interval=0),
        include_candidate_providers=True,
    )
    expected = {
        f"tre_{uf.casefold()}_sjur_jurisprudencia"
        for uf in (
            "AC",
            "AL",
            "AP",
            "AM",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MG",
            "MS",
            "MT",
            "PA",
            "PB",
            "PE",
            "PI",
            "PR",
            "RJ",
            "RN",
            "RO",
            "RR",
            "RS",
            "SC",
            "SE",
            "TO",
            "SP",
        )
    }
    assert expected <= set(client.providers)
    for name in expected:
        capabilities = client.providers[name].get_capabilities()
        assert capabilities.opt_in_unified_search is True
        assert capabilities.supports_unified_search is False
        assert capabilities.semantic_discriminator.startswith("authority=TRE-")


def test_query_builder_uses_identifier_without_thematic_expansion():
    query = build_tse_query(JurisprudenceQuery(number="0600092-56.2019.6.00.0000"))
    assert query["bool"]["must"] == [{"terms": {"codigoDecisao": ["0600092-56.2019.6.00.0000"]}}]


def test_document_route_is_limited_to_observed_result(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = provider_with(fixture("tse_sjur_success.json"))
    page = provider.search(JurisprudenceQuery(number="504401"))
    result_id = page.results[0].id
    expected = CanonicalDocument(
        id=result_id,
        source="tse_sjur_jurisprudencia",
        document_type="inteiro_teor",
        content_type="application/pdf",
        title="TSE SJUR",
        text="texto",
        raw_bytes=b"%PDF-1.4",
        url=page.results[0].document_url,
        sha256="0" * 64,
        byte_size=7,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
    )

    def fake_fetch(*args: object, **kwargs: object) -> CanonicalDocument:
        assert kwargs["title"] == f"TSE SJUR {result_id}"
        return expected

    monkeypatch.setattr(
        "nanojuris.providers.tse_sjur_jurisprudencia.fetch_document_reference", fake_fetch
    )
    document = provider.get_document(result_id)
    assert document.url.endswith("/download/pdf/504401")
    with pytest.raises(SourceUnavailableError):
        provider.get_document("tse-sjur-unknown")


def test_document_url_rejects_foreign_host_and_unsafe_code() -> None:
    payload = fixture("tse_sjur_success.json")
    item = dict(payload["content"][0])  # type: ignore[index]
    item["temInteiroTeorPDF"] = "true"
    item["documentUrl"] = "https://untrusted.example/document.pdf"
    item["codigoDecisao"] = "../504401"
    page = provider_with({"content": [item], "totalRegistros": 1}).search(
        JurisprudenceQuery(number="504401")
    )

    assert page.results[0].document_url is None


def test_tre_document_uses_official_inline_text_when_pdf_shell_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = fixture("tse_sjur_success.json")
    payload["content"] = [dict(payload["content"][0])]  # type: ignore[index]
    payload["content"][0]["siglaTribunalJE"] = "TRE-SP"  # type: ignore[index]
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        tribunal="TRE-SP",
    )

    def request(request: object) -> TransportResponse:
        return response(payload)

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(
        JurisprudenceQuery(
            text="termo",
            authority="TRE-SP",
            branch="electoral",
            degree="second",
            instance="second",
            collection="SJUR",
        )
    )
    result = page.results[0]

    def invalid_pdf(*args: object, **kwargs: object) -> CanonicalDocument:
        raise ParserContractChangedError(
            "document declared PDF but failed structural validation: invalid_magic"
        )

    monkeypatch.setattr(
        "nanojuris.providers.tse_sjur_jurisprudencia.fetch_document_reference",
        invalid_pdf,
    )
    document = provider.get_document(result.id)

    assert document.content_type == "text/plain"
    assert document.text == result.full_text
    assert document.raw_metadata["fallback"] == "official_search_inline_text"
    assert document.access_status is AccessStatus.PUBLIC
    assert document.extraction_status is ExtractionStatus.COMPLETE
