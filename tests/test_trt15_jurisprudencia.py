from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.trt15_jurisprudencia import Trt15JurisprudenciaProvider

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self.content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.url = "https://jurisprudencia.trt15.jus.br/backend/pesquisar"

    def json(self) -> object:
        return json.loads(self.text)


class FakeSession:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        assert isinstance(response, FakeResponse)
        return response


def test_public_options_catalog_is_available_without_search() -> None:
    options = json.loads(
        (FIXTURES / "trt15_jurisprudencia_options.json").read_text(encoding="utf-8")
    )
    provider = Trt15JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession([FakeResponse(options)])
    )

    catalog = provider.get_catalog()

    assert catalog.courts[0].code == "TRT15"
    assert len(catalog.raw["listaOrgaosJulgadores"]) == 2
    assert len(catalog.raw["listaRelatores"]) == 2


def test_search_preserves_captcha_boundary() -> None:
    provider = Trt15JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse(_fixture("trt15_jurisprudencia_captcha.json"))]),
    )

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="responsabilidade civil"))


def test_search_parses_authorized_contract_fixture() -> None:
    response = {
        "sucesso": 1,
        "resultadosEncontrados": 1,
        "documentos": [
            {
                "id": 2_100_001,
                "nrProcesso": "0001234-56.2024.5.15.0001",
                "classeJudicialSigla": "ROT",
                "ementa": "Responsabilidade civil. Dano moral.",
                "dataAssinatura": "2024-05-06",
                "orgaoJulgador": "10ª Câmara",
                "relator": "RELATOR DE TESTE",
                "link": "https://jurisprudencia.trt15.jus.br/documento/2100001",
            }
        ],
    }
    provider = Trt15JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession([FakeResponse(response)])
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=10))

    assert page.total == 1
    assert page.results[0].authority == "TRT15"
    assert page.results[0].branch == "labor"
    assert page.results[0].degree is None
    assert page.results[0].case_class == "ROT"
    assert page.filters_applied["text"] == "native"


def test_search_page_two_uses_fixture_and_does_not_overlap() -> None:
    provider = Trt15JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse(_fixture("trt15_jurisprudencia_page2.json"))]),
    )

    page = provider.search(JurisprudenceQuery(text="trabalho", page=2, page_size=2))

    assert page.page == 2
    assert page.results[0].id == "trt15-2100003"
    assert page.start == 3
    assert page.end == 3
    assert page.is_complete is True


def test_authoritative_empty_fixture_is_distinct() -> None:
    provider = Trt15JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse(_fixture("trt15_jurisprudencia_empty.json"))]),
    )

    page = provider.search(JurisprudenceQuery(text="termo inexistente"))

    assert page.results == []
    assert page.total == 0
    assert page.total_known is True


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (FakeResponse({"sucesso": 0}), ParserContractChangedError),
        (FakeResponse({}, 503), SourceUnavailableError),
        (FakeResponse({}, 429), RateLimitDetectedError),
    ],
)
def test_external_states_are_not_empty(response: FakeResponse, expected: type[Exception]) -> None:
    provider = Trt15JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession([response])
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="direito"))


def test_capabilities_are_diagnostic_only() -> None:
    provider = Trt15JurisprudenciaProvider(session=FakeSession([]))
    capabilities = provider.get_capabilities()

    assert capabilities.supports_catalog is True
    assert capabilities.supports_unified_search is False
    assert capabilities.filter_status("case_class") == "native"
    assert capabilities.filter_status("degree") == "unsupported"


def test_client_registers_trt15_without_default_federation() -> None:
    client = NanoJurisClient()

    assert "trt15_jurisprudencia" in client.providers
    assert "trt15_jurisprudencia" not in client._default_unified_sources()


def test_transport_exception_is_explicit() -> None:
    provider = Trt15JurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([requests.RequestException("offline")]),
    )
    with pytest.raises(SourceUnavailableError):
        provider.search(JurisprudenceQuery(text="direito"))


def test_authorized_search_uses_one_caller_token_and_redacts_trace() -> None:
    session = FakeSession([FakeResponse(_fixture("trt15_jurisprudencia_success.json"))])
    provider = Trt15JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session)

    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade"),
        captcha_response="human-token-only",
    )

    assert page.results
    assert page.source_trace is not None
    assert "captchaResponse" not in page.source_trace.query
    assert "recaptcha" not in page.source_trace.query
    body = session.calls[0]["kwargs"]["json"]
    assert isinstance(body, dict)
    assert body["captchaResponse"] == "human-token-only"
    assert body["recaptcha"] == "human-token-only"


def test_authorized_search_rejects_missing_token() -> None:
    provider = Trt15JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(AccessControlRequiredError, match="CAPTCHA"):
        provider.search_authorized(
            JurisprudenceQuery(text="responsabilidade"),
            captcha_response="",
        )
