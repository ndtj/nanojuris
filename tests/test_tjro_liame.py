from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjro_liame import (
    TjroLiameProvider,
    build_tjro_search_payload,
    parse_tjro_search_response,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjro_liame_results.json"


def fixture_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, data: Any, *, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.url = "https://liame.tjro.jus.br/api/pesquisa/precedentes"
        self.headers = {"Content-Type": "application/json"}
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        return self._data


class Session:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def test_tjro_maps_qualified_precedent_to_canonical_search_shape() -> None:
    page = parse_tjro_search_response(
        fixture_data(),
        query=JurisprudenceQuery(text="empreitada", page_size=1),
        trace=SourceTrace(provider="tjro_liame", endpoint="POST /api/pesquisa/precedentes"),
    )
    result = page.results[0]
    assert result.id == "tjro-liame-TJRO-incidente_demanda_repetitiva-18"
    assert result.question == "Questão pública de fixture."
    assert result.thesis == "Tese pública de fixture."
    assert result.paradigm_cases[0].number == "08029144420258220000"
    assert result.updated_at == "2026-08-13"


def test_tjro_builds_public_payload() -> None:
    payload = build_tjro_search_payload(
        JurisprudenceQuery(
            text="dano moral",
            published_from="2026-01-01",
            published_to="2026-02-01",
            page=2,
            page_size=25,
        )
    )
    assert payload["siglas"] == ["TJRO"]
    assert payload["data_inicio"] == "2026-01-01"
    assert payload["page"] == 2
    assert payload["page_size"] == 25


def test_tjro_provider_search_and_capabilities_are_explicit() -> None:
    provider = TjroLiameProvider(
        NanoJurisConfig(rate_limit_interval=0), Session([FakeResponse(fixture_data())])
    )
    page = provider.search(JurisprudenceQuery(text="empreitada", page_size=1))
    assert page.source == "tjro_liame"
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    capabilities = provider.get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.supports_full_text is False
    assert capabilities.max_remote_page_size == 100
    with pytest.raises(NotImplementedError):
        provider.get_decisions("tjro-liame-id")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (429, RateLimitDetectedError),
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (400, QueryRejectedError),
        (422, QueryRejectedError),
        (500, SourceUnavailableError),
        (404, SourceUnavailableError),
    ],
)
def test_tjro_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjroLiameProvider(
        NanoJurisConfig(rate_limit_interval=0), Session([FakeResponse({}, status_code=status)])
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))


def test_tjro_classifies_transport_and_contract_errors() -> None:
    provider = TjroLiameProvider(
        NanoJurisConfig(rate_limit_interval=0), Session([requests.RequestException("offline")])
    )
    with pytest.raises(SourceUnavailableError, match="request failed"):
        provider.search(JurisprudenceQuery(text="teste"))

    class InvalidJsonResponse(FakeResponse):
        def json(self) -> Any:
            raise ValueError("invalid")

    provider = TjroLiameProvider(
        NanoJurisConfig(rate_limit_interval=0), Session([InvalidJsonResponse({})])
    )
    with pytest.raises(ParserContractChangedError, match="not JSON"):
        provider.search(JurisprudenceQuery(text="teste"))

    provider = TjroLiameProvider(
        NanoJurisConfig(rate_limit_interval=0), Session([FakeResponse([])])
    )
    with pytest.raises(ParserContractChangedError, match="root"):
        provider.search(JurisprudenceQuery(text="teste"))


@pytest.mark.parametrize(
    "payload",
    [{}, {"data": {}}, {"data": {"results": [{"registro": {}}]}}],
)
def test_tjro_rejects_incomplete_payloads(payload: dict) -> None:
    with pytest.raises(ParserContractChangedError):
        parse_tjro_search_response(
            payload,
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="tjro_liame", endpoint="search"),
        )


def test_tjro_normalizes_empty_and_unknown_public_values() -> None:
    item = {
        "sigla": "TJRO",
        "especie": "iac",
        "registro": {
            "numero": "19",
            "questao": "nao informado(a)",
            "tese": "nÃ£o definida.",
            "situacao": "",
            "relator": None,
            "dataAtualizacao": "2026-08-13",
            "dataJulgamento": "13/08/2026",
            "dataPublicacao": "data futura desconhecida",
            "processosParadigma": [
                {"numero": "1", "classe": "Classe", "link": "https://tjro.jus.br/doc"},
                {"numero": "2", "link": "/relative"},
                {"classe": "sem numero"},
            ],
        },
    }
    page = parse_tjro_search_response(
        {"data": {"total": "invalid", "results": [item]}},
        query=JurisprudenceQuery(text="teste", page=2, page_size=100),
        trace=SourceTrace(provider="tjro_liame", endpoint="search"),
    )
    result = page.results[0]
    assert page.total == 1
    assert result.question is None
    assert result.thesis is not None
    assert result.judgment_date == "2026-08-13"
    assert result.publication_date == "data futura desconhecida"
    assert len(result.paradigm_cases) == 2


def test_tjro_payload_uses_explicit_types_and_safe_page_limits() -> None:
    payload = build_tjro_search_payload(
        JurisprudenceQuery(exact_phrase="tese", types=["iac"], page=1, page_size=100)
    )
    assert payload["especies"] == ["iac"]
    assert payload["texto"] == "tese"
    assert payload["page"] == 1
    assert payload["page_size"] == 100
