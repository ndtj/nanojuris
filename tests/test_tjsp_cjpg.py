from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjsp_cjpg import (
    TjspCjpgProvider,
    build_tjsp_cjpg_params,
    parse_tjsp_cjpg_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, content: bytes, *, status_code: int = 200, url: str = "") -> None:
        self.content = content
        self.status_code = status_code
        self.url = url or "https://esaj.tjsp.jus.br/cjpg/pesquisar.do"
        self.headers = {"Content-Type": "text/html;charset=UTF-8"}


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        response = self.responses.pop(0)
        return response


class RaisingSession:
    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        raise requests.RequestException("offline")


def fixture(name: str = "tjsp_cjpg_success.html") -> bytes:
    return (FIXTURES / name).read_bytes()


def trace() -> SourceTrace:
    return SourceTrace(provider="tjsp_cjpg", endpoint="GET /cjpg/pesquisar.do")


def test_parser_maps_first_degree_text_and_source_fields() -> None:
    page = parse_tjsp_cjpg_response(
        fixture(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=trace(),
        base_url="https://esaj.tjsp.jus.br",
    )
    assert page.source == "tjsp_cjpg"
    assert page.total == 2
    assert page.start == 1
    assert page.end == 2
    assert page.is_complete is True
    first = page.results[0]
    assert first.id == "tjsp-cjpg-IF0001ABC0000"
    assert first.court == "TJSP"
    assert first.type == "decisao_1g"
    assert first.number == "1000001-00.2024.8.26.0001"
    assert first.rapporteur == "Juíza de Fixture"
    assert first.updated_at == "2024-03-01"
    assert first.degree == "first"
    assert first.instance == "first"
    assert first.branch == "state"
    assert first.authority == "TJSP"
    assert first.collection == "CJPG"
    assert first.document_type == "decisao_1g"
    assert first.document_url == "https://esaj.tjsp.jus.br/cjpg/pesquisar.do"
    assert first.full_text == (
        "Decisão de primeiro grau de fixture sobre responsabilidade civil e reparação."
    )
    assert first.raw["classe"] == "Procedimento Comum Cível"
    assert first.raw["assunto"] == "Responsabilidade civil"
    assert first.raw["comarca"] == "Comarca de Fixture"
    assert first.raw["cd_processo"] == "IF0001ABC0000"


def test_parser_preserves_full_text_in_canonical_mapping() -> None:
    page = parse_tjsp_cjpg_response(
        fixture(),
        query=JurisprudenceQuery(text="teste"),
        trace=trace(),
        base_url="https://esaj.tjsp.jus.br",
    )
    canonical = search_page_to_canonical(page)[0]
    assert canonical.case_class == "Procedimento Comum Cível"
    assert canonical.judging_body is None
    assert canonical.origin_county == "Comarca de Fixture"
    assert canonical.full_text == page.results[0].full_text


def test_parser_empty_page_is_explicit() -> None:
    page = parse_tjsp_cjpg_response(
        fixture("tjsp_cjpg_empty.html"),
        query=JurisprudenceQuery(text="sem resultado"),
        trace=trace(),
        base_url="https://esaj.tjsp.jus.br",
    )
    assert page.results == []
    assert page.total == 0
    assert page.is_complete is True
    assert page.total_known is False


def test_cjpg_explicit_empty_wins_over_adaptive_selector_memory() -> None:
    from nanojuris.adaptive_selectors import SelectorMemory

    memory = SelectorMemory(":memory:", seed=False)
    parse_tjsp_cjpg_response(
        fixture(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=trace(),
        base_url="https://esaj.tjsp.jus.br",
        memory=memory,
    )
    page = parse_tjsp_cjpg_response(
        fixture("tjsp_cjpg_empty.html"),
        query=JurisprudenceQuery(text="sem resultado"),
        trace=trace(),
        base_url="https://esaj.tjsp.jus.br",
        memory=memory,
    )

    assert page.results == []
    assert page.is_explicit_empty is True


def test_parser_rejects_access_and_schema_drift() -> None:
    with pytest.raises(AccessControlRequiredError):
        parse_tjsp_cjpg_response(
            fixture("tjsp_cjpg_access_control.html"),
            query=JurisprudenceQuery(text="teste"),
            trace=trace(),
            base_url="https://esaj.tjsp.jus.br",
        )
    with pytest.raises(ParserContractChangedError, match="no data table"):
        parse_tjsp_cjpg_response(
            fixture("tjsp_cjpg_schema_drift.html"),
            query=JurisprudenceQuery(text="teste"),
            trace=trace(),
            base_url="https://esaj.tjsp.jus.br",
        )


def test_build_params_matches_public_contract() -> None:
    params = build_tjsp_cjpg_params(
        JurisprudenceQuery(
            text="dano moral",
            number="1000001-00.2024.8.26.0001",
            updated_from="01/01/2024",
            updated_to="31/01/2024",
        )
    )
    assert params["dadosConsulta.pesquisaLivre"] == "dano moral"
    assert params["dadosConsulta.nuProcesso"] == "10000010020248260001"
    assert params["numeroDigitoAnoUnificado"] == "100000100202482"
    assert params["foroNumeroUnificado"] == "0001"
    assert params["dadosConsulta.dtInicio"] == "01/01/2024"


def test_provider_uses_public_session_pagination_and_trace() -> None:
    session = FakeSession([FakeResponse(fixture()), FakeResponse(fixture())])
    provider = TjspCjpgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="teste", page=2, page_size=20))
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["url"].endswith("/cjpg/pesquisar.do")
    assert "/cjpg/trocarDePagina.do?pagina=2" in session.calls[1]["url"]
    assert page.page == 2
    assert page.page_size == 10
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.content_sha256

    document = provider.get_document(page.results[0].id)
    assert document.text == page.results[0].full_text
    bundle = provider.get_decisions(page.results[0].id)
    assert bundle.texts[0]["content"] == page.results[0].full_text


def test_provider_rejects_empty_query_and_transport() -> None:
    provider = TjspCjpgProvider(NanoJurisConfig(rate_limit_interval=0), session=RaisingSession())
    with pytest.raises(ValueError, match="requires text"):
        provider.search(JurisprudenceQuery())
    with pytest.raises(SourceUnavailableError, match="request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (429, RateLimitDetectedError),
        (400, QueryRejectedError),
        (422, QueryRejectedError),
        (500, SourceUnavailableError),
    ],
)
def test_provider_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjspCjpgProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(b"error", status_code=status)]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_capabilities_promote_cjpg_to_default_federation() -> None:
    capabilities = TjspCjpgProvider(NanoJurisConfig(rate_limit_interval=0)).get_capabilities()
    assert capabilities.semantic_discriminator == "collection=first_degree;route=cjpg"
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert capabilities.supports_full_text is True
    assert capabilities.max_remote_page_size == 10
    assert capabilities.filter_status("rapporteur") == "unsupported"
