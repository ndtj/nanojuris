from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.trt2_pje_jurisprudencia import Trt2PjeJurisprudenciaProvider
from nanojuris.transport.models import TransportResponse

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _response(payload: object, path: str) -> TransportResponse:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    url = f"https://pje.trt2.jus.br{path}"
    return TransportResponse(
        status_code=200,
        url=url,
        final_url=url,
        headers={"Content-Type": "application/json"},
        body=body,
        elapsed_ms=1.0,
    )


def _provider() -> tuple[Trt2PjeJurisprudenciaProvider, list[object]]:
    provider = Trt2PjeJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        path = str(getattr(request, "url", "")).split("pje.trt2.jus.br", 1)[-1]
        if path == "/juris-backend/api/opcoes":
            return _response(_fixture("trt2_pje_opcoes.json"), path)
        if path == "/juris-backend/api/filtros":
            return _response(_fixture("trt2_pje_filtros.json"), path)
        return _response(_fixture("trt2_pje_challenge.json"), path)

    provider.transport.request = request  # type: ignore[method-assign]
    return provider, calls


def test_public_options_are_exposed_without_secret_or_challenge_material() -> None:
    provider, _ = _provider()

    options = provider.get_parameters()

    assert options["regional"] == "TRT da 2a Regiao"
    assert options["captchaOption"] == "2"
    assert "recaptchaSecretKey" not in options


def test_public_filter_catalog_is_diagnostic() -> None:
    provider, calls = _provider()

    catalog = provider.get_filter_catalog()

    assert catalog["hits"] > 0
    assert "classeJudicial" in catalog["aggregation_fields"]
    payload = calls[-1].json_body
    assert payload["paginationSize"] == 0
    assert payload["paginationPosition"] == 1
    assert payload["name"] == "query parameters"
    assert "filtros" not in payload


def test_document_challenge_is_explicit_access_error_not_empty() -> None:
    provider, _ = _provider()

    with pytest.raises(AccessControlRequiredError, match="desafio humano"):
        provider.search(JurisprudenceQuery(text="responsabilidade civil"))


def test_payload_preserves_second_degree_scope() -> None:
    provider, calls = _provider()

    with pytest.raises(AccessControlRequiredError):
        provider.search(
            JurisprudenceQuery(
                text="divórcio",
                page=2,
                page_size=100,
                degree="second",
                case_class="Apelação Cível",
            )
        )

    request = calls[-1]
    payload = request.json_body
    assert payload["paginationPosition"] == 2
    assert payload["paginationSize"] == 20
    assert payload["classeJudicial"] == ["Apelação Cível"]
    assert payload["andField"] == ["divórcio"]
    assert payload["tipoDocumento"] is None


def test_explicit_capabilities_remain_opt_in() -> None:
    provider, _ = _provider()

    capabilities = provider.get_capabilities()

    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.pagination_mode == "offset_unverified"
    assert capabilities.filter_status("degree") == "validated_scope"


def test_payload_uses_official_term_channels_and_publication_dates() -> None:
    provider, calls = _provider()

    with pytest.raises(AccessControlRequiredError):
        provider.search(
            JurisprudenceQuery(
                text='"dano moral"',
                any_words="indenizacao reparacao",
                without_words="eleitoral",
                published_from="2024-01-01",
                published_to="2024-12-31",
                order_by="date",
                degree="second",
            )
        )

    payload = calls[-1].json_body
    assert payload["andField"] == ["dano moral"]
    assert payload["orField"] == ["indenizacao", "reparacao"]
    assert payload["notField"] == ["eleitoral"]
    assert payload["dataPublicacaoStart"] == "2024-01-01"
    assert payload["dataPublicacaoEnd"] == "2024-12-31"
    assert payload["ordenarPor"] == "dataPublicacao"


def test_authorized_search_uses_ephemeral_challenge_token() -> None:
    provider = Trt2PjeJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        payload = request.json_body
        if payload.get("token") == "ephemeral-human-token":
            return _response(
                _fixture("trt2_pje_authorized_success.json"), "/juris-backend/api/documentos"
            )
        return _response(_fixture("trt2_pje_challenge.json"), "/juris-backend/api/documentos")

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade civil", degree="second"),
        challenge_token="ephemeral-human-token",
    )

    assert page.total == 1
    assert page.results[0].authority == "TRT2"
    assert page.results[0].degree == "second"
    assert page.source_trace is not None
    assert "token" not in page.source_trace.query
    assert "token" not in page.results[0].raw
    assert calls[-1].json_body["token"] == "ephemeral-human-token"


def test_unknown_empty_public_window_is_not_complete() -> None:
    provider = Trt2PjeJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    def request(request: object) -> TransportResponse:
        path = str(getattr(request, "url", "")).split("pje.trt2.jus.br", 1)[-1]
        return _response({"documents": []}, path)

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="responsabilidade civil"))

    assert page.results == []
    assert page.total_known is False
    assert page.is_complete is False
    assert page.extraction_status.value == "partial"


def test_unknown_empty_authorized_window_is_not_complete() -> None:
    provider = Trt2PjeJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    def request(request: object) -> TransportResponse:
        path = str(getattr(request, "url", "")).split("pje.trt2.jus.br", 1)[-1]
        return _response({"documents": []}, path)

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade civil"),
        challenge_token="ephemeral-human-token",
    )

    assert page.results == []
    assert page.total_known is False
    assert page.is_complete is False
    assert page.extraction_status.value == "partial"
