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
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjpe_jurisprudencia import (
    TjpeJurisprudenciaProvider,
    build_tjpe_search_parameters,
    parse_tjpe_search_response,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjpe_jurisprudencia_results.json"


class FakeResponse:
    def __init__(
        self,
        data: Any = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        url: str = "https://consultajurisprudencia.app.tjpe.jus.br/api/v1/jurisprudencias",
    ) -> None:
        self._data = data
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "application/json"}
        self.url = url
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        if self._data is None:
            raise ValueError("not json")
        return self._data


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def load_fixture() -> list[dict[str, Any]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def trace() -> SourceTrace:
    return SourceTrace(
        provider="tjpe_jurisprudencia",
        endpoint="GET /api/v1/jurisprudencias",
        source_url="https://consultajurisprudencia.app.tjpe.jus.br/api/v1/jurisprudencias",
    )


def test_tjpe_parser_preserves_text_and_normalizes_dates() -> None:
    page = parse_tjpe_search_response(
        load_fixture(),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=2),
        trace=trace(),
        reported_total=2,
    )

    assert page.total == 2
    assert page.is_complete is True
    assert [result.id for result in page.results] == [
        "tjpe-juris-fixture-1",
        "tjpe-juris-fixture-2",
    ]
    first = page.results[0]
    assert first.judgment_date == "2026-08-15"
    assert first.publication_date == "2026-08-16"
    assert first.summary == "Ementa publica de fixture."
    assert first.full_text == "Inteiro teor publico de fixture."
    assert first.raw["textoAcordao"].startswith("<p>")
    assert first.access_status.value == "public"


def test_tjpe_builds_observed_zero_based_parameters() -> None:
    params = build_tjpe_search_parameters(
        JurisprudenceQuery(
            text="dano moral",
            number="0000001-23.2024.8.17.0001",
            published_from="01/01/2024",
            published_to="31/12/2024",
            types=["A"],
            order_by="date_desc",
            page=2,
            page_size=25,
        )
    )

    assert params["page"] == 1
    assert params["size"] == 25
    assert params["pesquisaLivre.contains"] == "dano moral"
    assert params["npuSemFormatacao.equals"] == "00000012320248170001"
    assert params["dataJulgamento.greaterThanOrEqual"] == "2024-01-01"
    assert params["dataJulgamento.lessThanOrEqual"] == "2024-12-31"
    assert params["tipoSentenca.in"] == ["A"]
    assert params["sort"] == "dataJulgamento,desc"


def test_tjpe_provider_preserves_trace_and_remote_total() -> None:
    session = FakeSession(
        [
            FakeResponse(
                load_fixture(),
                headers={"X-Total-Count": "42", "Content-Type": "application/json"},
            )
        ]
    )
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=2))

    assert page.total == 42
    assert page.page == 2
    assert page.start == 3
    assert page.source_trace is not None
    assert page.source_trace.content_sha256
    assert page.source_trace.response_bytes
    assert session.calls[0]["kwargs"]["params"]["page"] == 1
    assert session.calls[0]["kwargs"]["verify"] is True


def test_tjpe_rejects_missing_stable_key_and_wrong_root() -> None:
    with pytest.raises(ParserContractChangedError, match="stable key"):
        parse_tjpe_search_response(
            [{"textoEmenta": "sem chave"}],
            query=JurisprudenceQuery(text="teste"),
            trace=trace(),
        )

    with pytest.raises(ParserContractChangedError, match="result root"):
        parse_tjpe_search_response(  # type: ignore[arg-type]
            {}, query=JurisprudenceQuery(text="teste"), trace=trace()
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
def test_tjpe_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjpeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status)]),
    )

    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_tjpe_is_registered_and_declares_public_contract() -> None:
    client = NanoJurisClient()
    assert "tjpe_jurisprudencia" in client.providers
    capabilities = client.providers["tjpe_jurisprudencia"].get_capabilities()
    assert capabilities.pagination_mode == "offset"
    assert capabilities.supports_full_text is True
    assert "GET /api/v1/jurisprudencias" in capabilities.endpoints
