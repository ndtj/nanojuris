from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjmsp_jurisprudencia import TjmspJurisprudenciaProvider
from nanojuris.transport.models import TransportResponse

FIXTURES = Path(__file__).parent / "fixtures"


def _response(status: int, body: bytes) -> TransportResponse:
    return TransportResponse(
        status_code=status,
        url="https://jurisprudencia-client.tjmsp.jus.br/",
        final_url="https://jurisprudencia-client.tjmsp.jus.br/",
        headers={"Content-Type": "text/html"},
        body=body,
        elapsed_ms=1.0,
    )


def test_tjmsp_forbidden_is_access_control_not_empty() -> None:
    provider = TjmspJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    provider.transport.request = lambda request: _response(403, b"Forbidden")  # type: ignore[method-assign]
    with pytest.raises(AccessControlRequiredError, match="403"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_tjmsp_reached_shell_without_result_contract() -> None:
    provider = TjmspJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    body = (FIXTURES / "tjmsp_portal.html").read_bytes()
    provider.transport.request = lambda request: _response(200, body)  # type: ignore[method-assign]
    with pytest.raises(ParserContractChangedError, match="contract"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_tjmsp_capabilities_are_opt_in() -> None:
    provider = TjmspJurisprudenciaProvider()
    capabilities = provider.get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.filter_status("text") == "unsupported"
    assert "GET /v1/tema/retornaRegistrosAtivos" in capabilities.endpoints
    assert provider.get_parameters()["status"] == "access_control_required"
    assert provider.get_parameters()["api_base_url"].endswith("/v1")
