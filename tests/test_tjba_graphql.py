from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjba_graphql import (
    TjbaGraphqlProvider,
    build_tjba_filter,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        body: str,
        *,
        status_code: int = 200,
        content_type: str = "application/json",
    ):
        self.status_code = status_code
        self.url = "https://jurisprudenciaws.tjba.jus.br/graphql"
        self.headers = {"Content-Type": content_type}
        self.content = body.encode("utf-8")
        self.text = body

    def json(self):
        return json.loads(self.text)


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_build_filter_matches_public_frontend_defaults():
    payload = build_tjba_filter(
        JurisprudenceQuery(
            text="dano moral E consumidor OU contrato",
            number="0000001-23.2026.8.05.0001",
            published_from="01/01/2026",
            published_to="31/12/2026",
        )
    )

    assert payload["assunto"] == "dano moral AND consumidor OR contrato"
    assert payload["numeroRecurso"] == "0000001-23.2026.8.05.0001"
    assert payload["dataInicial"] == "2026-01-01"
    assert payload["dataFinal"] == "2026-12-31"
    assert payload["segundoGrau"] is True
    assert payload["turmasRecursais"] is True
    assert payload["tipoAcordaos"] is True
    assert payload["tipoDecisoesMonocraticas"] is True
    assert payload["ordenadoPor"] == "dataPublicacao"


def test_search_maps_graphql_decision_and_preserves_facets():
    session = FakeSession([FakeResponse(fixture("tjba_graphql_success.json"))])
    provider = TjbaGraphqlProvider(session=session)

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))
    result = page.results[0]

    assert page.total == 2
    assert page.page_size == 1
    assert page.is_complete is False
    assert result.id == "tjba-graphql-831bc363-c057-3941-a5d6-79584cb02536"
    assert result.number == "0000001-23.2026.8.05.0001"
    assert result.judgment_date == "2026-08-05"
    assert result.publication_date == "2026-08-10"
    assert result.source_updated_at == "2026-08-13"
    assert result.raw["case_class"] == "Apelacao Civel"
    assert page.aggregations["page_count"] == 2
    assert session.calls[0]["kwargs"]["json"]["variables"]["pageNumber"] == 0


def test_search_maps_second_page_to_zero_based_graphql_page():
    session = FakeSession([FakeResponse(fixture("tjba_graphql_success.json"))])
    provider = TjbaGraphqlProvider(session=session)

    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=1))

    assert page.page == 2
    assert page.start == 2
    assert session.calls[0]["kwargs"]["json"]["variables"]["pageNumber"] == 1


def test_search_accepts_empty_source_result():
    response = FakeResponse(fixture("tjba_graphql_empty.json"))
    provider = TjbaGraphqlProvider(session=FakeSession([response]))

    page = provider.search(JurisprudenceQuery(text="termo improvavel"))

    assert page.results == []
    assert page.total == 0
    assert page.is_complete is True


def test_provider_get_document_uses_public_uuid_and_hashes_content():
    session = FakeSession(
        [
            FakeResponse(
                fixture("tjba_graphql_detail.html"),
                content_type="text/html",
            )
        ]
    )
    provider = TjbaGraphqlProvider(session=session)

    document = provider.get_document("tjba-graphql-831bc363-c057-3941-a5d6-79584cb02536")

    assert document.text == "Inteiro teor TJBA Inteiro teor Texto integral publico de fixture TJBA."
    assert document.sha256
    assert document.extraction_trace is not None
    assert session.calls[0]["url"].endswith("/inteiroTeor/831bc363-c057-3941-a5d6-79584cb02536")


def test_provider_catalog_and_capabilities_are_explicit():
    session = FakeSession([FakeResponse(fixture("tjba_graphql_catalog.json"))])
    provider = TjbaGraphqlProvider(session=session)

    catalog = provider.get_catalog()
    capabilities = provider.get_capabilities()

    assert catalog.courts[0].code == "org-1"
    assert catalog.species[0].description == "Apelacao Civel"
    assert catalog.raw["relatores"][0]["code"] == "rel-1"
    assert capabilities.supports_full_text is True
    assert capabilities.supports_catalog is True
    assert "number" in capabilities.supported_filters


def test_provider_rejects_invalid_queries_and_identifiers():
    provider = TjbaGraphqlProvider(session=FakeSession([]))

    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery())
    with pytest.raises(ParserContractChangedError, match="id deve usar"):
        provider.get_decisions("tjba-graphql-invalid")


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (429, RateLimitDetectedError),
        (403, AccessControlRequiredError),
        (500, SourceUnavailableError),
    ],
)
def test_provider_classifies_http_errors(status, error):
    provider = TjbaGraphqlProvider(session=FakeSession([FakeResponse("{}", status_code=status)]))

    with pytest.raises(error):
        provider._request("POST", "/graphql", json={})


def test_provider_rejects_graphql_errors_and_non_json():
    graphql_error = '{"errors": [{"message": "Internal Server Error"}]}'
    provider = TjbaGraphqlProvider(session=FakeSession([FakeResponse(graphql_error)]))
    with pytest.raises(ParserContractChangedError, match="errors"):
        provider._request_json({"query": "query"})

    provider = TjbaGraphqlProvider(
        session=FakeSession([FakeResponse("not-json", content_type="text/html")])
    )
    with pytest.raises(ParserContractChangedError, match="not JSON"):
        provider._request_json({"query": "query"})
