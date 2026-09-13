from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    CanonicalDocument,
    ExtractionStatus,
    JurisprudenceQuery,
    SourceTrace,
)
from nanojuris.providers.tjro_jurisprudencia import (
    TjroJurisprudenciaProvider,
    build_tjro_payload,
    parse_tjro_related_response,
    parse_tjro_response,
)
from nanojuris.quality import validate_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "tjro_jurisprudencia_results.json"
EMPTY_FIXTURE = ROOT / "tests" / "fixtures" / "tjro_jurisprudencia_empty.json"
RELATED_FIXTURE = ROOT / "tests" / "fixtures" / "tjro_jurisprudencia_related.json"


class FakeResponse:
    def __init__(
        self,
        data: Any,
        *,
        status_code: int = 200,
        content_type: str = "application/json",
        url: str = "https://juris-back.tjro.jus.br/search/varios_parametros/",
    ) -> None:
        self._data = data
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": content_type}
        if isinstance(data, bytes):
            self.content = data
        else:
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


def fixture_data(path: Path = FIXTURE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def outcome_fixture(name: str) -> tuple[int, dict[str, Any]]:
    payload = fixture_data(FIXTURE.parent / name)
    return int(payload["status"]), payload["body"]


def trace() -> SourceTrace:
    return SourceTrace(
        provider="tjro_jurisprudencia",
        endpoint="POST /search/varios_parametros/",
        http_status=200,
        content_type="application/json",
    )


def test_parser_maps_source_fields_and_preserves_raw() -> None:
    page = parse_tjro_response(
        fixture_data(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=trace(),
    )

    assert page.total == 2
    assert page.start == 1
    assert page.end == 2
    assert page.pagination_mode == "offset"
    assert page.is_complete is True
    assert page.total_known is True
    assert page.effective_total == 2
    first, second = page.results
    assert first.id == "tjro-jurisprudencia-fixture-1-PJEPG"
    assert first.number == "0000001-00.2026.8.22.0001"
    assert first.type == "sentenca"
    assert first.summary is not None
    assert "responsabilidade civil" in first.summary.casefold()
    assert first.judgment_date == "2026-06-10"
    assert first.publication_date == "2026-06-12"
    assert first.raw["native_id"] == "fixture-1-PJEPG"
    assert first.raw["source"]["ds_modelo_documento"].startswith("<div>")
    assert first.raw["degree"] == 1
    assert first.degree == "first"
    assert first.instance == "first"
    assert first.authority == "TJRO"
    assert first.collection == "JURISPRUDENCIA"
    assert first.document_type == first.type
    assert first.highlights["ds_modelo_documento"] == "responsabilidade civil por dano moral"
    assert second.type == "voto"
    assert second.raw["degree"] == 2
    assert second.degree == "second"
    assert second.publication_date is None
    assert validate_record(search_page_to_canonical(page)[0]) == ()


def test_parser_marks_authoritative_zero_complete() -> None:
    page = parse_tjro_response(
        fixture_data(EMPTY_FIXTURE),
        query=JurisprudenceQuery(text="termo sem resultado"),
        trace=trace(),
    )

    assert page.total == 0
    assert page.results == []
    assert page.is_complete is True
    assert page.completeness_reason == "A fonte informou total zero para a consulta."


def test_parser_rejects_schema_drift() -> None:
    query = JurisprudenceQuery(text="responsabilidade")
    with pytest.raises(ParserContractChangedError, match="hits object"):
        parse_tjro_response({}, query=query, trace=trace())
    with pytest.raises(ParserContractChangedError, match="hits.total.value"):
        parse_tjro_response({"hits": {"total": {}, "hits": []}}, query=query, trace=trace())
    with pytest.raises(ParserContractChangedError, match="hits.hits list"):
        parse_tjro_response(
            {"hits": {"total": {"value": 0}, "hits": {}}}, query=query, trace=trace()
        )
    invalid = outcome_fixture("tjro_jurisprudencia_invalid.json")[1]
    with pytest.raises(ParserContractChangedError, match="hit 0 is not an object"):
        parse_tjro_response(invalid, query=query, trace=trace())
    drift = outcome_fixture("tjro_jurisprudencia_schema_drift.json")[1]
    with pytest.raises(ParserContractChangedError, match="hits.hits list"):
        parse_tjro_response(drift, query=query, trace=trace())


def test_payload_uses_confirmed_offset_contract_without_divergent_tipo() -> None:
    payload = build_tjro_payload(
        JurisprudenceQuery(
            text="responsabilidade",
            exact_phrase="dano moral",
            number="00000010020268220001",
            rapporteur="Relator de fixture",
            updated_from="2026-01-01",
            updated_to="2026-12-31",
            page=2,
            page_size=25,
        )
    )

    assert payload["from"] == 25
    assert payload["size"] == 25
    assert payload["fields"]["query"] == 'responsabilidade "dano moral"'
    assert payload["fields"]["nr_processo"] == "00000010020268220001"
    assert payload["fields"]["ds_nome"] == "Relator de fixture"
    assert payload["fields"]["dtjulgamento_inicio"] == "2026-01-01"
    assert payload["fields"]["dtjulgamento_fim"] == "2026-12-31"
    assert "tipo" not in payload["fields"]


def test_payload_keeps_local_refinements_and_rejects_empty_query() -> None:
    # ``types`` is now a bounded local post-filter over the explicit ``tipo``
    # field returned by the source; it must not be sent as an unverified JSON
    # field to Elasticsearch.
    payload = build_tjro_payload(JurisprudenceQuery(text="responsabilidade", types=["voto"]))
    assert "tipo" not in payload["fields"]
    with pytest.raises(QueryRejectedError, match="exige texto"):
        build_tjro_payload(JurisprudenceQuery())


def test_parser_applies_degree_and_type_postfilters_without_claiming_completeness() -> None:
    page = parse_tjro_response(
        fixture_data(),
        query=JurisprudenceQuery(
            text="responsabilidade",
            degree="second",
            types=["voto"],
            all_words="pretensao indenizatoria",
        ),
        trace=trace(),
    )

    assert len(page.results) == 1
    assert page.results[0].degree == "second"
    assert page.results[0].type == "voto"
    assert page.is_complete is False
    assert page.filters_applied["degree"] == "local_postfilter"
    assert page.filters_applied["types"] == "local_postfilter"


def test_provider_search_uses_public_json_and_trace() -> None:
    session = FakeSession([FakeResponse(fixture_data())])
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=2))

    assert len(page.results) == 2
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["kwargs"]["json"]["from"] == 0
    assert "tipo" not in session.calls[0]["kwargs"]["json"]["fields"]
    assert page.source_trace is not None
    assert page.source_trace.content_sha256
    assert page.source_trace.retrieval_status == "ok"


def test_provider_downloads_public_pdf_with_browser_headers_and_trace() -> None:
    session = FakeSession(
        [
            FakeResponse(
                b"%PDF-1.7\nfixture document bytes",
                content_type="application/pdf",
                url=("https://juris-back.tjro.jus.br/pje/buscar_pdf_ou_docx/PJEPG/137613154/pdf/"),
            )
        ]
    )
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    document = provider.get_document("tjro-jurisprudencia-137613154-PJEPG")

    assert document.id == "tjro-jurisprudencia-document-137613154-PJEPG"
    assert document.content_type == "application/pdf"
    assert document.raw_bytes == b"%PDF-1.7\nfixture document bytes"
    assert document.sha256
    assert document.source_trace is not None
    assert document.source_trace.endpoint.endswith("/PJEPG/137613154/pdf/")
    assert session.calls[0]["method"] == "GET"
    headers = session.calls[0]["kwargs"]["headers"]
    assert headers["Origin"] == "https://juris.tjro.jus.br"
    assert headers["Referer"].endswith("/jurisprudencia/")


def test_provider_fetch_details_and_decision_bundle_preserve_document() -> None:
    session = FakeSession([FakeResponse(fixture_data())])
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )
    document = CanonicalDocument(
        id="tjro-jurisprudencia-document-fixture-1-PJEPG",
        source="tjro_jurisprudencia",
        document_type="inteiro_teor",
        content_type="text/plain",
        text="Inteiro teor publico de fixture",
        raw_bytes=b"fixture",
        extraction_status=ExtractionStatus.COMPLETE,
    )
    requested_ids: list[str] = []

    def get_document(document_id: str) -> CanonicalDocument:
        requested_ids.append(document_id)
        return document

    provider.get_document = get_document  # type: ignore[method-assign]

    page = provider.search(JurisprudenceQuery(text="responsabilidade", fetch_details=True))
    assert page.results[0].full_text == "Inteiro teor publico de fixture"
    assert page.results[0].raw["full_text_status"] == "loaded"
    assert page.results[0].extraction_status.value == "complete"
    # The source's explicit document id is used instead of duplicating the
    # PJEPG suffix from the Elasticsearch hit identifier.
    assert requested_ids == ["100001-PJEPG", "100002-PJESG"]

    bundle = provider.get_decisions("tjro-jurisprudencia-fixture-1-PJEPG")
    assert bundle.precedent_id.endswith("fixture-1-PJEPG")
    assert bundle.texts[0]["content"] == "Inteiro teor publico de fixture"
    assert bundle.raw_bytes == b"fixture"


def test_related_documents_parser_preserves_order_and_parent_identity() -> None:
    page = parse_tjro_related_response(
        fixture_data(RELATED_FIXTURE),
        principal_id="principal",
        trace=trace(),
    )

    assert page.total == 4
    assert page.pagination_mode == "single_response"
    assert page.is_complete is True
    assert page.filters_applied == {"related_to": "principal"}
    assert [item.type for item in page.results] == ["acordao", "ementa", "relatorio", "voto"]
    assert all(item.raw["related_to"] == "principal" for item in page.results)


def test_provider_fetches_related_pjesg_documents_on_demand() -> None:
    session = FakeSession(
        [
            FakeResponse(
                fixture_data(RELATED_FIXTURE),
                url=("https://juris-back.tjro.jus.br/search/documentos_relacionados/principal"),
            )
        ]
    )
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    page = provider.get_related_documents("principal")

    assert len(page.results) == 4
    assert session.calls[0]["method"] == "GET"
    assert session.calls[0]["url"].endswith("/search/documentos_relacionados/principal")
    assert page.source_trace is not None
    assert page.source_trace.endpoint.endswith("/search/documentos_relacionados/principal")


def test_provider_rejects_invalid_related_document_id() -> None:
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([]),  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="invalid characters"):
        provider.get_related_documents("principal/../../secret")


def test_related_parser_rejects_schema_drift() -> None:
    with pytest.raises(ParserContractChangedError, match="hits object"):
        parse_tjro_related_response({}, principal_id="principal", trace=trace())
    with pytest.raises(ParserContractChangedError, match="hits.hits list"):
        parse_tjro_related_response(
            {"hits": {"total": {"value": 1}, "hits": {}}},
            principal_id="principal",
            trace=trace(),
        )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (403, AccessControlRequiredError),
        (420, AccessControlRequiredError),
        (429, RateLimitDetectedError),
        (500, SourceUnavailableError),
    ],
)
def test_provider_classifies_related_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(
                    b"error",
                    status_code=status,
                    content_type="text/plain",
                    url=("https://juris-back.tjro.jus.br/search/documentos_relacionados/principal"),
                )
            ]
        ),  # type: ignore[arg-type]
    )

    with pytest.raises(expected):
        provider.get_related_documents("principal")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (420, AccessControlRequiredError),
        (429, RateLimitDetectedError),
        (500, SourceUnavailableError),
    ],
)
def test_provider_classifies_document_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(
                    b"error",
                    status_code=status,
                    content_type="text/plain",
                    url="https://juris-back.tjro.jus.br/pje/document",
                )
            ]
        ),  # type: ignore[arg-type]
    )

    with pytest.raises(expected):
        provider.get_document("137613154-PJEPG")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (429, RateLimitDetectedError),
        (400, QueryRejectedError),
        (422, QueryRejectedError),
        (500, SourceUnavailableError),
        (503, SourceUnavailableError),
    ],
)
def test_provider_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status)]),  # type: ignore[arg-type]
    )

    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_provider_replays_sanitized_access_and_upstream_error_fixtures() -> None:
    access_status, access_body = outcome_fixture("tjro_jurisprudencia_access_control.json")
    access_provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(access_body, status_code=access_status)]),  # type: ignore[arg-type]
    )
    with pytest.raises(AccessControlRequiredError):
        access_provider.search(JurisprudenceQuery(text="responsabilidade"))

    error_status, error_body = outcome_fixture("tjro_jurisprudencia_error.json")
    error_provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(error_body, status_code=error_status)]),  # type: ignore[arg-type]
    )
    with pytest.raises(SourceUnavailableError):
        error_provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_provider_rejects_invalid_json_root() -> None:
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse([])]),  # type: ignore[arg-type]
    )

    with pytest.raises(ParserContractChangedError, match="root is not an object"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_provider_does_not_convert_timeout_to_empty_page() -> None:
    class TimeoutSession:
        def request(self, method: str, url: str, **kwargs: Any) -> Any:
            raise requests.Timeout("bounded timeout")

    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=TimeoutSession(),  # type: ignore[arg-type]
    )
    with pytest.raises(SourceUnavailableError, match="request failed"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_capabilities_enable_federation_and_declare_detail_support() -> None:
    capabilities = TjroJurisprudenciaProvider(NanoJurisConfig()).get_capabilities()

    assert capabilities.source == "tjro_jurisprudencia"
    assert capabilities.pagination_mode == "offset"
    assert capabilities.supports_unified_search is True
    assert capabilities.supports_full_text is True
    assert capabilities.filter_status("types") == "local_postfilter"
    assert capabilities.filter_status("fetch_details") == "translated"
    assert capabilities.filter_status("degree") == "translated"


def test_payload_translates_cjsg_degree_to_official_field() -> None:
    payload = build_tjro_payload(
        JurisprudenceQuery(text="responsabilidade", collection="CJSG", page_size=2)
    )
    assert payload["fields"]["grau_jurisdicao"] == [2]

    first = build_tjro_payload(
        JurisprudenceQuery(text="responsabilidade", degree="first", page_size=2)
    )
    assert first["fields"]["grau_jurisdicao"] == [1]


def test_first_degree_search_is_explicit_and_never_mixes_pjesg() -> None:
    """The PJEPG binding must be enforced by the remote degree field."""

    session = FakeSession([FakeResponse(fixture_data())])
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    page = provider.search(
        JurisprudenceQuery(
            text="responsabilidade",
            degree="first",
            instance="first",
            collection="CJPG",
            page_size=10,
        )
    )

    assert session.calls[0]["kwargs"]["json"]["fields"]["grau_jurisdicao"] == [1]
    assert page.results
    assert all(result.degree == "first" for result in page.results)
    assert all(result.instance == "first" for result in page.results)
    assert all(result.raw["source_system"] == "PJEPG" for result in page.results)
    assert page.filters_applied["collection"] == "local_postfilter"


def test_provider_is_registered_in_default_federation() -> None:
    default_client = NanoJurisClient()
    assert "tjro_jurisprudencia" in default_client.providers
    assert "tjro_liame" in default_client.providers

    opt_in_client = NanoJurisClient(include_candidate_providers=True)
    assert "tjro_jurisprudencia" in opt_in_client.providers
    assert "tjro_liame" in opt_in_client.providers
    assert (
        opt_in_client.get_capabilities(source="tjro_jurisprudencia").supports_unified_search is True
    )
    assert "tjro_jurisprudencia" in default_client._default_unified_sources()


def test_provider_returns_canonical_record_through_federated_search() -> None:
    provider = TjroJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(fixture_data())]),  # type: ignore[arg-type]
    )
    client = NanoJurisClient(providers=[provider])

    payload = client.search_many(
        sources=["tjro_jurisprudencia"],
        text="responsabilidade",
        page_size=1,
    )

    assert payload["errors"] == []
    assert payload["searched_sources"] == ["tjro_jurisprudencia"]
    assert payload["source_totals"]["tjro_jurisprudencia"] == 2
    assert len(payload["results"]) == 1
    assert payload["results"][0].source == "tjro_jurisprudencia"
