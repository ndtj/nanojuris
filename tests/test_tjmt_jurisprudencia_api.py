from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
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
        content_type = "text/html" if isinstance(data, str) else "application/json"
        self.headers = {"Content-Type": content_type}
        self.content = (
            data.encode("utf-8")
            if isinstance(data, str)
            else json.dumps(data, ensure_ascii=False).encode("utf-8")
        )
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        if isinstance(self._data, (BaseException, str)):
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


def test_tjmt_parser_uses_effective_maximum_page_size_for_window() -> None:
    data = fixture_data()
    item = data["AcordaoCollection"][0]
    data["AcordaoCollection"] = [dict(item) for _ in range(101)]

    page = parse_tjmt_response(
        data,
        query=SimpleNamespace(text="teste", page=2, page_size=150),  # type: ignore[arg-type]
        trace=None,  # type: ignore[arg-type]
        api_type="Acordao",
    )

    assert page.page == 2
    assert page.page_size == 100
    assert page.start == 101
    assert len(page.results) == 100


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

    assert params["indicePagina"] == "1"
    assert params["quantidadePagina"] == "25"
    assert params["tipoConsulta"] == "1"
    assert params["termoDeBusca"] == 'dano moral "transporte aereo"'
    assert params["periodoDataDe"] == "2026-01-02"
    assert params["periodoDataAte"] == "2026-02-03"
    assert params["OrdenarPor"] == "Julgamento"
    assert params["Decrescente"] == "true"


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
    assert session.calls[1]["kwargs"]["params"]["indicePagina"] == "1"
    assert session.calls[1]["kwargs"]["headers"]["token"] == "public-runtime-token"


def test_tjmt_provider_reads_runtime_config_from_current_spa_bundle() -> None:
    session = FakeSession(
        [
            FakeResponse(
                "<html>SPA shell</html>",
                url="https://jurisprudencia.tjmt.jus.br/assets/config/config.json",
            ),
            FakeResponse(
                "<html><script src='/main.js'></script></html>",
                url="https://jurisprudencia.tjmt.jus.br/",
            ),
            FakeResponse(
                'const environment={api_url:"https://hellsgate.tjmt.jus.br/jurisprudencia",'
                'api_hellsgate_token:"spa-runtime-token"};',
                url="https://jurisprudencia.tjmt.jus.br/main.js",
            ),
            FakeResponse(
                fixture_data(),
                url="https://hellsgate.tjmt.jus.br/jurisprudencia/api/consulta/Acordao",
            ),
        ]
    )
    provider = TjmtJurisprudenciaApiProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.results[0].number == "1008103-19.2025.8.11.0002"
    assert session.calls[2]["url"].endswith("/main.js")
    assert session.calls[3]["kwargs"]["headers"]["token"] == "spa-runtime-token"
    trace_text = json.dumps(page.source_trace.to_dict(), ensure_ascii=False)
    assert "spa-runtime-token" not in trace_text


def test_tjmt_parser_accepts_current_spa_envelope_and_camel_case_fields() -> None:
    legacy_item = fixture_data()["AcordaoCollection"][0]
    process = legacy_item["Processo"]
    current_item = {
        "id": legacy_item["Id"],
        "tipo": "Acordao",
        "conteudo": legacy_item["Conteudo"],
        "documentoHtml": legacy_item["Documento"],
        "processo": {
            "uid": process["UID"],
            "numeroUnicoFormatado": process["NumeroUnicoFormatado"],
            "nomeRelator": process["NomeRelator"],
            "dataJulgamento": process["DataJulgamento"],
            "dataPublicacao": process["DataPublicacao"],
            "julgamento": process["Julgamento"],
        },
    }
    page = parse_tjmt_response(
        {"value": {"resultados": [current_item], "countAcordaoDocumento": 1}},
        query=JurisprudenceQuery(text="dano moral", page=1, page_size=1),
        trace=None,  # type: ignore[arg-type]
        api_type="Acordao",
    )

    assert page.total == 1
    assert page.results[0].number == "1008103-19.2025.8.11.0002"
    assert page.results[0].full_text


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
