from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.falcao_jt import FalcaoJtProvider
from nanojuris.transport.models import TransportResponse

FIXTURES = Path(__file__).parent / "fixtures"


def _response(name: str) -> TransportResponse:
    body = (FIXTURES / name).read_bytes()
    return TransportResponse(
        status_code=200,
        url="https://jurisprudencia.jt.jus.br/",
        final_url="https://jurisprudencia.jt.jus.br/",
        headers={"Content-Type": "text/html"},
        body=body,
        elapsed_ms=1.0,
    )


def _provider(response: TransportResponse) -> FalcaoJtProvider:
    provider = FalcaoJtProvider(NanoJurisConfig(rate_limit_interval=0))
    provider.transport.request = lambda request: response  # type: ignore[method-assign]
    return provider


def test_cloudfront_is_access_control_not_empty() -> None:
    provider = _provider(_response("falcao_cloudfront.html"))
    with pytest.raises(AccessControlRequiredError, match="bloqueio"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_public_shell_without_api_is_contract_change() -> None:
    provider = _provider(_response("falcao_shell.html"))
    with pytest.raises(ParserContractChangedError, match="shell"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_falcao_capabilities_are_opt_in_and_unverified() -> None:
    capabilities = FalcaoJtProvider().get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.filter_status("text") == "unsupported"
    assert capabilities.pagination_mode == "unknown_until_contract"


def test_falcao_public_api_contract_parses_appellate_result() -> None:
    response = TransportResponse(
        status_code=200,
        url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        final_url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        headers={"Content-Type": "application/json"},
        body=(FIXTURES / "falcao_search_success.json").read_bytes(),
        elapsed_ms=1.0,
    )
    provider = _provider(response)
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=5))
    assert page.total == 1
    assert page.total_known is True
    assert page.results[0].degree == "second"
    assert page.results[0].collection == "acordaos"
    assert page.results[0].full_text is not None
    bundle = provider.get_decisions("TRT9-42")
    assert bundle.texts[0]["content"]


def test_falcao_authorized_search_uses_ephemeral_oidc_token() -> None:
    response = TransportResponse(
        status_code=200,
        url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        final_url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        headers={"Content-Type": "application/json"},
        body=(FIXTURES / "falcao_search_success.json").read_bytes(),
        elapsed_ms=1.0,
    )
    calls = []
    provider = FalcaoJtProvider(NanoJurisConfig(rate_limit_interval=0))

    def request(transport_request):
        calls.append(transport_request)
        return response

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade", page_size=5),
        access_token="ephemeral-oidc-token",
    )

    assert page.results[0].degree == "second"
    assert calls[0].headers["Authorization"] == "Bearer ephemeral-oidc-token"
    assert calls[0].cacheable is False
    assert "ephemeral-oidc-token" not in str(page.source_trace.to_dict())
    assert "ephemeral-oidc-token" not in str(page.results[0].raw)


def test_falcao_authorized_search_requires_a_caller_token() -> None:
    provider = FalcaoJtProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(AccessControlRequiredError, match="token OIDC"):
        provider.search_authorized(
            JurisprudenceQuery(text="responsabilidade"),
            access_token=" ",
        )


def test_falcao_unknown_empty_window_is_not_authoritative() -> None:
    response = TransportResponse(
        status_code=200,
        url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        final_url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        headers={"Content-Type": "application/json"},
        body=b'{"documentos": []}',
        elapsed_ms=1.0,
    )
    page = _provider(response).search(JurisprudenceQuery(text="responsabilidade"))
    assert page.results == []
    assert page.total_known is False
    assert page.is_complete is False
    assert page.extraction_status.value == "partial"
    assert "nao confirmada" in (page.completeness_reason or "")


def test_falcao_rejects_contradictory_zero_total() -> None:
    payload = json.loads((FIXTURES / "falcao_search_success.json").read_text(encoding="utf-8"))
    payload["quantidadeTotal"] = 0
    response = TransportResponse(
        status_code=200,
        url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        final_url="https://jurisprudencia.jt.jus.br/jurisprudencia-nacional-backend/api/no-auth/pesquisa",
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload).encode("utf-8"),
        elapsed_ms=1.0,
    )
    with pytest.raises(ParserContractChangedError, match="quantidadeTotal=0"):
        _provider(response).search(JurisprudenceQuery(text="responsabilidade"))


def test_falcao_public_api_metadata_exposes_official_routes() -> None:
    parameters = FalcaoJtProvider().get_parameters()
    assert parameters["public_search_endpoint"].endswith("/no-auth/pesquisa")
    assert "/no-auth/informacao/versao" in parameters["metadata_endpoints"]


def test_falcao_public_trt_catalog_is_normalized() -> None:
    response = TransportResponse(
        status_code=200,
        url=(
            "https://jurisprudencia.jt.jus.br/"
            "jurisprudencia-nacional-backend/api/no-auth/informacao/tribunais/codigosTrt"
        ),
        final_url=(
            "https://jurisprudencia.jt.jus.br/"
            "jurisprudencia-nacional-backend/api/no-auth/informacao/tribunais/codigosTrt"
        ),
        headers={"Content-Type": "application/json"},
        body=(FIXTURES / "falcao_trt_codes.json").read_bytes(),
        elapsed_ms=1.0,
    )
    catalog = _provider(response).get_catalog()
    assert len(catalog.courts) == 24
    assert catalog.courts[0].code == "TRT1"
    assert catalog.courts[-1].code == "TRT24"
