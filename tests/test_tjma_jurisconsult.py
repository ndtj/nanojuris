from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjma_jurisconsult import (
    TjmaJurisconsultProvider,
    parse_tjma_catalog,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjma_jurisconsult_catalog.json"


class FakeResponse:
    def __init__(self, data: Any, url: str, *, status_code: int = 200) -> None:
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": "application/json"}
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        return json.loads(self.content)


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        return self.responses.pop(0)


class CapturingSession(FakeSession):
    def __init__(self, responses: list[FakeResponse]) -> None:
        super().__init__(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return super().request(method, url, **kwargs)


def payloads() -> dict[str, dict[str, Any]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_tjma_catalog_parser_preserves_public_vocabularies() -> None:
    catalog = parse_tjma_catalog(
        payloads(),
        trace=SourceTrace(provider="tjma_jurisconsult", endpoint="catalog"),
    )
    assert catalog.source == "tjma_jurisconsult"
    assert catalog.species[0].description == "Acórdãos"
    assert catalog.raw["classes"][0]["str_classe"].startswith("Apelação")
    assert catalog.raw["search_access_status"] == "access_control_required"


def test_tjma_search_remains_explicitly_gated() -> None:
    provider = TjmaJurisconsultProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(AccessControlRequiredError):
        provider.search(None)


def test_tjma_detail_remains_explicitly_gated() -> None:
    provider = TjmaJurisconsultProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(AccessControlRequiredError):
        provider.get_decisions("public-id")


def test_tjma_provider_reads_catalog_endpoints() -> None:
    responses = [
        FakeResponse(payloads()[key], f"https://apijuris.tjma.jus.br/v1/{key}")
        for key in (
            "reports",
            "types",
            "classes",
            "magistrates",
            "chambers",
            "counties",
            "precedent_links",
        )
    ]
    provider = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession(responses)
    )
    assert provider.get_catalog().species


def test_tjma_authorized_search_uses_ephemeral_human_tokens() -> None:
    response = {
        "response": {
            "processos": [
                {
                    "pkJurisprudencia": "123",
                    "int_count": 1,
                    "txEmenta": "Responsabilidade civil. Dano moral.",
                    "txAcordao": "ACÓRDÃO. Vistos e relatados estes autos.",
                    "numeroProcesso": "0800000-00.2024.8.10.0001",
                    "strClasse": "Apelação Cível",
                    "strCamara": "1ª Câmara Cível",
                    "relator": "Relator de teste",
                    "dtaJulgamento": "2024-05-06",
                    "arquivosAcordao": [
                        {
                            "bol_permite_consulta_publica": True,
                            "strArquivo": "acordao-123",
                            "strTipoDocumento": "pdf",
                        }
                    ],
                }
            ]
        }
    }
    session = CapturingSession([FakeResponse(response, "https://api.test/result")])
    provider = TjmaJurisconsultProvider(NanoJurisConfig(rate_limit_interval=0), session)

    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade civil", page_size=5),
        captcha_token="ephemeral-server-token",
        google_token="ephemeral-google-token",
        key_id="public-key-id",
    )

    assert page.total == 1
    result = page.results[0]
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "CJSG"
    assert result.case_class == "Apelação Cível"
    assert result.full_text == "ACÓRDÃO. Vistos e relatados estes autos."
    assert result.document_url == (
        "https://apijuris.tjma.jus.br/v1/sg/"
        "download_acordao_pauta_julgamento?filename=acordao-123.pdf"
    )
    assert page.source_trace is not None
    assert "token" not in page.source_trace.query
    request = session.calls[0]
    assert request["params"]["tokenG"] == "ephemeral-google-token"
    assert request["headers"]["Authorization"] == "Bearer ephemeral-server-token"


def test_tjma_authorized_result_can_open_observed_decision_without_tokens() -> None:
    response = {
        "response": {
            "processos": [
                {
                    "pkJurisprudencia": "456",
                    "int_count": 1,
                    "txEmenta": "Ementa autorizada.",
                    "txAcordao": "Texto integral retornado pela busca autorizada.",
                }
            ]
        }
    }
    provider = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        CapturingSession([FakeResponse(response, "https://api.test/result")]),
    )
    page = provider.search_authorized(
        JurisprudenceQuery(text="ementa"),
        captcha_token="ephemeral-server-token",
        google_token="ephemeral-google-token",
        key_id="public-key-id",
    )

    bundle = provider.get_decisions(page.results[0].id)

    assert bundle.precedent_id == "tjma-456"
    assert bundle.texts[0]["content"] == "Texto integral retornado pela busca autorizada."
    assert bundle.raw["access_status"] == "public"


def test_tjma_authorized_search_requires_all_challenge_parts() -> None:
    provider = TjmaJurisconsultProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(AccessControlRequiredError):
        provider.search_authorized(
            JurisprudenceQuery(text="jurisprudencia"),
            captcha_token="",
            google_token="google",
            key_id="key",
        )


def test_tjma_unknown_empty_authorized_window_is_not_complete() -> None:
    response = {"response": {"processos": []}}
    provider = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse(response, "https://api.test/result")]),
    )

    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade civil"),
        captcha_token="ephemeral-server-token",
        google_token="ephemeral-google-token",
        key_id="public-key-id",
    )

    assert page.results == []
    assert page.total_known is False
    assert page.is_complete is False
    assert page.extraction_status.value == "partial"


def test_tjma_authoritative_total_controls_completion_for_empty_page() -> None:
    response = {
        "response": {
            "processos": [
                {
                    "pkJurisprudencia": "25",
                    "int_count": 25,
                    "txEmenta": "Ementa de teste",
                }
            ]
        }
    }
    provider = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse(response, "https://api.test/result")]),
    )

    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade civil", page=4, page_size=10),
        captcha_token="ephemeral-server-token",
        google_token="ephemeral-google-token",
        key_id="public-key-id",
    )

    assert page.total == 25
    assert page.total_known is True
    assert page.is_complete is True


def test_tjma_capabilities_describe_catalog_only_surface() -> None:
    capabilities = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()
    assert capabilities.supports_catalog is True
    assert capabilities.supports_unified_search is False
    assert capabilities.full_text_access == "access_blocked"
    assert capabilities.detail_modes == ["authorized_search_inline"]
    assert "catalog" in capabilities.supported_filters
    assert "GET /sg/jurisprudencias/processos" in capabilities.endpoints
    assert "GET /jurisprudencia/processos/pesquisa_monocraticas" in capabilities.endpoints


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (429, RateLimitDetectedError),
        (400, SourceUnavailableError),
        (500, SourceUnavailableError),
    ],
)
def test_tjma_classifies_catalog_http_errors(status: int, expected: type[Exception]) -> None:
    provider = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse({}, "https://api.test/catalog", status_code=status)]),
    )
    with pytest.raises(expected):
        provider._request_json("/catalog")


def test_tjma_classifies_captcha_boundary_as_access_control() -> None:
    provider = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession(
            [
                FakeResponse(
                    {"error": "captcha_not_provided"},
                    "https://apijuris.tjma.jus.br/v1/sg/jurisprudencias/processos",
                    status_code=400,
                )
            ]
        ),
    )
    with pytest.raises(AccessControlRequiredError, match="human captcha"):
        provider._request_json("/sg/jurisprudencias/processos")


def test_tjma_classifies_transport_and_payload_errors() -> None:
    class FailingSession:
        def request(self, method: str, url: str, **kwargs: Any) -> Any:
            raise requests.RequestException("offline")

    transport = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FailingSession(),  # type: ignore[arg-type]
    )
    with pytest.raises(SourceUnavailableError, match="request failed"):
        transport._request_json("/catalog")

    invalid = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse([], "https://api.test/catalog")]),
    )
    with pytest.raises(SourceUnavailableError, match="root is not an object"):
        invalid._request_json("/catalog")

    class InvalidJsonResponse(FakeResponse):
        def __init__(self) -> None:
            super().__init__({}, "https://api.test/catalog")
            self.content = b"{invalid"
            self.text = "{invalid"

    malformed = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([InvalidJsonResponse()]),
    )
    with pytest.raises(SourceUnavailableError, match="invalid JSON"):
        malformed._request_json("/catalog")


def test_tjma_catalog_parser_ignores_malformed_options() -> None:
    catalog = parse_tjma_catalog(
        {
            "reports": {
                "response": {"relatorios": [{"id": 1, "titulo": "A"}, {"titulo": "B"}, "x"]}
            },
            "types": {"tipos": ["tipo"]},
            "classes": {"classes": [{"id": 2}]},
            "magistrates": {"relatores": [{"id": 3}]},
            "chambers": {"camaras": [{"id": 4}]},
            "counties": {"comarcas": [{"id": 5}]},
            "precedent_links": {"response": {"pesquisaSumulas": [{"id": 6}]}},
        },
        trace=SourceTrace(provider="tjma_jurisconsult", endpoint="catalog"),
    )
    assert [option.code for option in catalog.species] == ["1"]
    assert catalog.raw["search_types"] == ["tipo"]
