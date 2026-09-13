from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjrn_jurisprudencia import (
    TjrnJurisprudenciaProvider,
    build_tjrn_payload,
    parse_tjrn_response,
)
from nanojuris.quality import validate_record

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_tjrn_payload_is_minimal_and_bounded() -> None:
    query = JurisprudenceQuery(text="dano moral", page=2, page_size=100)
    payload = build_tjrn_payload(query, page_size=100)
    assert payload == {
        "jurisprudencia": {"ementa": "dano moral"},
        "page": 2,
        "usuario": {},
    }


def test_tjrn_parser_maps_canonical_fields_and_raw_provenance() -> None:
    query = JurisprudenceQuery(text="responsabilidade civil", page_size=2)
    trace = SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar")
    page = parse_tjrn_response(
        load_fixture("tjrn_jurisprudencia_success.json"),
        query=query,
        trace=trace,
        page_size=2,
    )
    assert page.total == 2
    assert page.is_complete is True
    assert page.results[0].id == "tjrn-jurisprudencia-doc-001"
    assert page.results[0].summary.startswith("Responsabilidade civil")
    assert page.results[0].judgment_date == "2024-03-10"
    assert page.results[0].raw["system"] == "PJe"
    assert page.results[1].raw["system"] == "SAJ"
    assert page.results[0].authority == "TJRN"
    assert page.results[0].branch == "state"
    assert page.results[0].collection == "JURISPRUDENCIA"
    assert page.results[0].document_type == page.results[0].type
    assert page.results[0].instance == "second"
    assert validate_record(search_page_to_canonical(page)[0]) == ()


def test_tjrn_inline_document_is_exposed_after_search_parse() -> None:
    provider = TjrnJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    trace = SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar")
    page = parse_tjrn_response(
        load_fixture("tjrn_jurisprudencia_success.json"),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=trace,
        page_size=2,
    )
    # The provider stores references during search; seed the same parsed page
    # here to keep this unit test network-free and deterministic.
    result = page.results[0]
    provider._inline_documents[result.id] = (result.full_text or "", result.full_text or "", trace)
    document = provider.get_document(result.id)
    assert document.text == result.full_text
    assert document.raw_metadata["inline"] is True
    bundle = provider.get_decisions(result.id)
    assert bundle.texts[0]["content"] == result.full_text
    assert bundle.raw["inline"] is True


def test_tjrn_empty_is_explicit_not_error() -> None:
    page = parse_tjrn_response(
        load_fixture("tjrn_jurisprudencia_empty.json"),
        query=JurisprudenceQuery(text="termo", page_size=10),
        trace=SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar"),
        page_size=10,
    )
    assert page.results == []
    assert page.total == 0
    assert page.is_complete is True


def test_tjrn_parser_strips_rich_html_from_canonical_text_and_preserves_raw() -> None:
    payload = load_fixture("tjrn_jurisprudencia_success.json")
    source = payload["hits"]["hits"][0]["_source"]
    source["ementa"] = "<h1>EMENTA</h1><p>Responsabilidade <strong>civil</strong>.</p>"
    source["inteiro_teor"] = "<p>Inteiro <em>teor</em> da decisão.</p>"
    page = parse_tjrn_response(
        payload,
        query=JurisprudenceQuery(text="responsabilidade"),
        trace=SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar"),
        page_size=10,
    )
    result = page.results[0]
    assert result.summary == "EMENTA Responsabilidade civil."
    assert result.full_text == "Inteiro teor da decisão."
    assert result.raw["ementa"].startswith("<h1>")
    assert result.raw["inteiro_teor"].startswith("<p>")


def test_tjrn_degree_refinement_is_explicit_local_postfilter() -> None:
    page = parse_tjrn_response(
        load_fixture("tjrn_jurisprudencia_success.json"),
        query=JurisprudenceQuery(text="responsabilidade", degree="second"),
        trace=SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar"),
        page_size=10,
    )

    assert page.results
    assert all(result.degree == "second" for result in page.results)
    assert page.total_known is False
    assert page.is_complete is not True
    assert page.filters_applied["degree"] == "local_postfilter"


def test_tjrn_canonical_refinements_are_local_and_not_claimed_complete() -> None:
    page = parse_tjrn_response(
        load_fixture("tjrn_jurisprudencia_success.json"),
        query=JurisprudenceQuery(
            text="responsabilidade",
            case_class="Apelacao",
            judging_body="Segunda Camara",
            source_origin="PJe",
            decision_type="decisao",
            judgment_date_from="2024-03-01",
            judgment_date_to="2024-03-31",
        ),
        trace=SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar"),
        page_size=10,
    )

    assert len(page.results) == 1
    assert page.results[0].case_class == "Apelacao Civel"
    assert page.total_known is False
    assert page.is_complete is not True
    assert {
        "case_class",
        "judging_body",
        "source_origin",
        "decision_type",
        "judgment_date_from",
        "judgment_date_to",
    } <= set(page.filters_applied)


def test_tjrn_local_refinement_does_not_turn_mismatch_into_source_error() -> None:
    page = parse_tjrn_response(
        load_fixture("tjrn_jurisprudencia_success.json"),
        query=JurisprudenceQuery(text="responsabilidade", case_class="Habeas Corpus"),
        trace=SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar"),
        page_size=10,
    )
    assert page.results == []
    assert page.total_known is False
    assert page.access_status.value == "public"


@pytest.mark.parametrize(
    "fixture", ["tjrn_jurisprudencia_invalid.json", "tjrn_jurisprudencia_schema_drift.json"]
)
def test_tjrn_schema_drift_is_not_zero_results(fixture: str) -> None:
    with pytest.raises(ParserContractChangedError):
        parse_tjrn_response(
            load_fixture(fixture),
            query=JurisprudenceQuery(text="termo"),
            trace=SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar"),
            page_size=10,
        )


def test_tjrn_provider_classifies_http_403_without_false_empty() -> None:
    class Response:
        status_code = 403
        content = b"Access Denied"
        headers = {"Content-Type": "text/html"}
        url = "https://jurisprudencia.tjrn.jus.br/api/pesquisar"
        is_redirect = False

        def iter_content(self, chunk_size: int = 1):
            yield self.content

        def close(self) -> None:
            pass

    class Session:
        trust_env = True
        headers: dict[str, str] = {}

        def request(self, *_args, **_kwargs):
            return Response()

    provider = TjrnJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=Session(),  # type: ignore[arg-type]
    )
    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="termo"))


def test_tjrn_provider_is_default_on_client_after_live_promotion() -> None:
    from nanojuris.client import NanoJurisClient

    default = NanoJurisClient()
    candidate = NanoJurisClient(include_candidate_providers=True)
    assert "tjrn_jurisprudencia" in default.providers
    assert "tjrn_jurisprudencia" in candidate.providers
    capability = candidate.providers["tjrn_jurisprudencia"].get_capabilities()
    assert capability.supports_unified_search is True
    assert capability.opt_in_unified_search is False
    assert {"id", "document_url", "updated_at"} <= set(capability.extracted_fields)


def test_tjrn_is_visible_in_federated_outcomes(monkeypatch) -> None:
    """The live-validated provider is searchable through the default path."""

    from nanojuris.client import NanoJurisClient

    config = NanoJurisConfig(
        rate_limit_interval=0,
        unified_opt_in_sources=("tjrn_jurisprudencia",),
    )
    client = NanoJurisClient(config)
    assert "tjrn_jurisprudencia" in client.providers
    provider = client.providers["tjrn_jurisprudencia"]
    page = parse_tjrn_response(
        load_fixture("tjrn_jurisprudencia_success.json"),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=2),
        trace=SourceTrace(provider="tjrn_jurisprudencia", endpoint="POST /api/pesquisar"),
        page_size=2,
    )
    monkeypatch.setattr(provider, "search", lambda _query: page)

    payload = client.search_many(
        "responsabilidade civil",
        sources=["tjrn_jurisprudencia"],
        page_size=2,
        canonical=False,
        continue_on_error=False,
    )

    assert payload["searched_sources"] == ["tjrn_jurisprudencia"]
    assert payload["skipped_sources"] == []
    assert payload["source_outcomes"][0]["status"] == "searched"
    assert payload["source_completeness"]["tjrn_jurisprudencia"]["invalid_records"] == 0


def test_tjrn_opt_in_is_included_in_default_federation_sources() -> None:
    from nanojuris.client import NanoJurisClient

    client = NanoJurisClient(
        NanoJurisConfig(
            rate_limit_interval=0,
            unified_opt_in_sources=("tjrn_jurisprudencia",),
        )
    )

    assert "tjrn_jurisprudencia" in client._default_unified_sources()


def test_tjrn_degree_capability_is_explicit_bounded_postfilter() -> None:
    capabilities = TjrnJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()

    assert capabilities.filter_status("degree") == "local_postfilter"
    assert capabilities.filter_status("instance") == "local_postfilter"
    assert capabilities.filter_status("case_class") == "local_postfilter"
    assert capabilities.filter_status("judging_body") == "local_postfilter"
    assert capabilities.filter_status("judgment_date_from") == "local_postfilter"
