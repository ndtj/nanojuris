from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjmt_jurisprudencia_api import (
    TjmtJurisprudenciaApiProvider,
    build_tjmt_search_params,
    parse_tjmt_response,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjmt_jurisprudencia_results.json"


class FakeResponse:
    def __init__(self, data: Any, *, status_code: int = 200, url: str = "") -> None:
        self._data = data
        self.status_code = status_code
        self.url = (
            url or "https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/Acordao"
        )
        self.headers = {"Content-Type": "application/json"}
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        if isinstance(self._data, BaseException):
            raise ValueError("not json")
        return self._data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def fixture_data() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def config_data() -> dict[str, Any]:
    return {
        "api_url": "https://hellsgate-preview.tjmt.jus.br/jurisprudencia",
        "api_hellsgate_token": "public-runtime-token",
        "production": True,
    }


def test_tjmt_parser_extracts_inline_full_text_and_separates_dates() -> None:
    page = parse_tjmt_response(
        fixture_data(),
        query=JurisprudenceQuery(text="transporte aereo", page_size=5),
        trace=None,  # type: ignore[arg-type]
        api_type="Acordao",
    )

    result = page.results[0]
    assert page.total == 2
    assert page.is_complete is False
    assert result.id == "tjmt-jurisprudencia-390659362"
    assert result.number == "1008103-19.2025.8.11.0002"
    assert result.judgment_date == "2026-08-14"
    assert result.publication_date == "2026-08-15"
    assert result.summary == "DANO MORAL em transporte aereo."
    assert result.full_text == (
        "Tribunal de Justica do Estado de Mato Grosso Inteiro teor publico do acordao."
    )
    assert result.raw["document_content_type"] == "text/html"
    assert result.raw["full_text_status"] == "inline"


def test_tjmt_builds_public_query_contract() -> None:
    params = build_tjmt_search_params(
        JurisprudenceQuery(
            text="dano moral",
            exact_phrase="transporte aereo",
            published_from="2026-01-02",
            published_to="03/02/2026",
            types=["acordao"],
            page=2,
            page_size=25,
        ),
        page_size=25,
    )

    assert params["filtro.indicePagina"] == "2"
    assert params["filtro.quantidadePagina"] == "25"
    assert params["filtro.tipoConsulta"] == "Acordao"
    assert params["filtro.termoDeBusca"] == 'dano moral "transporte aereo"'
    assert params["filtro.periodoDataDe"] == "02/01/2026"
    assert params["filtro.periodoDataAte"] == "03/02/2026"
    assert params["filtro.ordenacao.ordenarPor"] == "DataDecrescente"


def test_tjmt_provider_reads_config_and_never_traces_runtime_token() -> None:
    session = FakeSession(
        [
            FakeResponse(
                config_data(), url="https://jurisprudencia.tjmt.jus.br/assets/config/config.json"
            ),
            FakeResponse(
                fixture_data(),
                url=(
                    "https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/Acordao"
                    "?token=public-runtime-token&filtro.indicePagina=2"
                ),
            ),
        ]
    )
    provider = TjmtJurisprudenciaApiProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=25))

    assert len(page.results) == 1
    assert page.source_trace is not None
    trace_text = json.dumps(page.source_trace.to_dict(), ensure_ascii=False)
    assert "public-runtime-token" not in trace_text
    assert session.calls[1]["kwargs"]["params"]["filtro.indicePagina"] == "2"
    assert session.calls[1]["kwargs"]["params"]["token"] == "public-runtime-token"


def test_tjmt_rejects_contract_root_without_collection() -> None:
    with pytest.raises(ParserContractChangedError, match="AcordaoCollection"):
        parse_tjmt_response(
            {"CountTotal": 0},
            query=JurisprudenceQuery(text="teste"),
            trace=None,  # type: ignore[arg-type]
            api_type="Acordao",
        )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (429, RateLimitDetectedError),
        (400, QueryRejectedError),
        (500, SourceUnavailableError),
    ],
)
def test_tjmt_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjmtJurisprudenciaApiProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(config_data()),
                FakeResponse({}, status_code=status),
            ]
        ),
    )

    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_tjmt_is_registered_and_declares_inline_contract() -> None:
    client = NanoJurisClient()
    assert "tjmt_jurisprudencia_api" in client.providers
    capabilities = client.providers["tjmt_jurisprudencia_api"].get_capabilities()
    assert capabilities.pagination_mode == "page"
    assert capabilities.max_remote_page_size == 100
    assert capabilities.supports_full_text is True
    assert capabilities.full_text_access == "inline"
