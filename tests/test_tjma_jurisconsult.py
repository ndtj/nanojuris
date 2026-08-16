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
from nanojuris.models import SourceTrace
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


def test_tjma_capabilities_describe_catalog_only_surface() -> None:
    capabilities = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()
    assert capabilities.supports_catalog is True
    assert capabilities.supports_unified_search is False
    assert capabilities.full_text_access == "not_implemented"
    assert "catalog" in capabilities.supported_filters


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
        def json(self) -> Any:
            raise ValueError("invalid")

    malformed = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([InvalidJsonResponse({}, "https://api.test/catalog")]),
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
