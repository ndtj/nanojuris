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
from nanojuris.providers.tjce_sjuris import (
    TjceSjurisProvider,
    build_tjce_sjuris_search_payload,
    parse_tjce_sjuris_response,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjce_sjuris_results.json"


class FakeResponse:
    def __init__(self, data: Any = None, *, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.url = "https://gateway.tjce.jus.br/sjuris/api/v1/jurisprudencia/?page=0&size=20"
        self.headers = {"Content-Type": "application/json"}
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


def fixture_data() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_sjuris_parser_preserves_inline_full_text_and_pdf_metadata() -> None:
    page = parse_tjce_sjuris_response(
        fixture_data(),
        query=JurisprudenceQuery(text="transporte aereo", page_size=5),
        trace=None,  # type: ignore[arg-type]
    )

    result = page.results[0]
    assert page.total == 1
    assert page.is_complete is True
    assert result.id == "tjce-sjuris-02486960420248060001_33695153"
    assert result.judgment_date == "2026-02-11"
    assert result.publication_date is None
    assert result.summary == "Ementa pública de fixture."
    assert result.full_text == "Inteiro teor público de fixture."
    assert result.raw["pdf_status"] == "inline_base64"
    assert result.raw["pdf_response_bytes"] == 16
    assert result.raw["pdf_content_sha256"]


def test_sjuris_builds_browser_payload_and_boolean_expression() -> None:
    payload = build_tjce_sjuris_search_payload(
        JurisprudenceQuery(
            text="transporte",
            exact_phrase="dano moral",
            all_words="aereo companhia",
            any_words="bagagem voo",
            without_words="milhas",
            types=["acordao"],
            source_origins=["PJE"],
        )
    )

    assert payload == {
        "dataJulgamento": [],
        "busca": 'transporte "dano moral" aereo e companhia bagagem ou voo não milhas',
        "ordenacao": "order1",
        "nomeDocumento": ["ACÓRDÃO"],
        "baseDocumento": ["2º GRAU"],
        "origem": ["PJE"],
    }


def test_sjuris_provider_uses_zero_based_page_and_clamps_size() -> None:
    session = FakeSession([FakeResponse(fixture_data())])
    provider = TjceSjurisProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=50))

    call = session.calls[0]
    assert call["method"] == "POST"
    assert "?page=1&size=20" in call["url"]
    assert call["kwargs"]["data"].startswith(b'{"dataJulgamento":[]')
    assert call["kwargs"]["headers"]["Origin"] == "https://sjuris.tjce.jus.br"
    assert page.page == 2
    assert page.page_size == 20


def test_sjuris_rejects_wrong_root_and_declares_no_detail_route() -> None:
    with pytest.raises(ParserContractChangedError, match="pagina.content"):
        parse_tjce_sjuris_response(
            {"content": []},
            query=JurisprudenceQuery(text="teste"),
            trace=None,  # type: ignore[arg-type]
        )

    with pytest.raises(NotImplementedError, match="inline"):
        TjceSjurisProvider(NanoJurisConfig(rate_limit_interval=0)).get_decisions("x")


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
def test_sjuris_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjceSjurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status)]),
    )

    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_sjuris_is_registered_and_declares_inline_contract() -> None:
    client = NanoJurisClient()
    assert "tjce_sjuris" in client.providers
    capabilities = client.providers["tjce_sjuris"].get_capabilities()
    assert capabilities.pagination_mode == "page"
    assert capabilities.max_remote_page_size == 20
    assert capabilities.supports_full_text is True
    assert capabilities.full_text_access == "inline"
