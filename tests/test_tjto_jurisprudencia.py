from __future__ import annotations

import json
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
from nanojuris.providers.tjto_jurisprudencia import (
    TjtoJurisprudenciaProvider,
    build_tjto_search_parameters,
    parse_tjto_search_response,
)
from nanojuris.quality import validate_record

FIXTURE = Path(__file__).parent / "fixtures" / "tjto_jurisprudencia_results.json"
CJPG_FIXTURE = Path(__file__).parent / "fixtures" / "tjto_cjpg_results.html"


class FakeResponse:
    def __init__(
        self,
        content: bytes | str,
        *,
        url: str,
        content_type: str = "text/html",
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": content_type, **(headers or {})}
        self.content = content.encode("utf-8") if isinstance(content, str) else content
        self.text = self.content.decode("utf-8", errors="replace")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def fixture_html() -> str:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["html"]


def trace() -> SourceTrace:
    return SourceTrace(
        provider="tjto_jurisprudencia",
        endpoint="POST /consulta.php",
        source_url="https://jurisprudencia.tjto.jus.br/consulta.php",
    )


def test_tjto_parser_extracts_card_and_stable_document_uuid() -> None:
    page = parse_tjto_search_response(
        fixture_html().encode("utf-8"),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=2),
        trace=trace(),
    )
    result = page.results[0]
    assert page.total == 2
    assert result.id == "tjto-jurisprudencia-abcdef1234567890"
    assert result.number == "0000001-23.2026.8.27.0001"
    assert result.judgment_date == "2026-02-15"
    assert result.summary.startswith("Ementa pública de fixture")
    assert result.raw["document_uuid"] == "abcdef1234567890"
    assert result.authority == "TJTO"
    assert result.branch == "state"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "CJSG"
    assert result.document_type == "acordao"
    assert result.case_class
    assert result.judging_body
    assert validate_record(search_page_to_canonical(page)[0]) == ()


def test_tjto_explicit_empty_wins_over_adaptive_selector_memory() -> None:
    from nanojuris.adaptive_selectors import SelectorMemory

    memory = SelectorMemory(":memory:", seed=False)
    parse_tjto_search_response(
        fixture_html().encode("utf-8"),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=2),
        trace=trace(),
        memory=memory,
    )
    # The explicit marker must win even when a previously successful selector
    # is stored in the caller-provided adaptive memory.
    page = parse_tjto_search_response(
        b"<html><body><p>Nenhum resultado encontrado.</p></body></html>",
        query=JurisprudenceQuery(text="sem resultado"),
        trace=trace(),
        memory=memory,
    )

    assert page.results == []
    assert page.is_explicit_empty is True
    memory.close()


def test_tjto_builds_offset_and_type_parameters() -> None:
    params = build_tjto_search_parameters(
        JurisprudenceQuery(
            text="dano moral",
            exact_phrase="transporte aereo",
            types=["acordao"],
            source_origin="2",
            rapporteur="RELATOR FIXTURE",
            page=3,
            page_size=25,
        )
    )
    assert params["start"] == "50"
    assert params["rows"] == "25"
    assert params["soementa"] == "on"
    assert params["tipo_decisao_acordao"] == "true"
    assert params["tip_criterio_inst"] == "2"
    assert params["fq_magistrado[RELATOR FIXTURE]"] == "on"


def test_tjto_builds_first_degree_scope_and_sentence_type() -> None:
    first = build_tjto_search_parameters(JurisprudenceQuery(text="teste", instance="1"))
    assert first["tip_criterio_inst"] == "1"
    sentence = build_tjto_search_parameters(
        JurisprudenceQuery(text="teste", degree="first", types=["sentenca"])
    )
    assert sentence["tip_criterio_inst"] == "1"
    assert sentence["type_minuta_selected"] == "3"
    with pytest.raises(QueryRejectedError, match="sentenca"):
        build_tjto_search_parameters(JurisprudenceQuery(text="teste", types=["sentenca"]))


def test_tjto_parser_maps_first_degree_scope() -> None:
    page = parse_tjto_search_response(
        CJPG_FIXTURE.read_bytes(),
        query=JurisprudenceQuery(text="sentenca", degree="first", collection="CJPG"),
        trace=trace(),
    )
    result = page.results[0]
    assert result.degree == "first"
    assert result.instance == "first"
    assert result.collection == "CJPG"
    assert result.source_origin == "1"


def test_tjto_provider_executes_first_degree_route() -> None:
    session = FakeSession(
        [
            FakeResponse(
                CJPG_FIXTURE.read_bytes(), url="https://jurisprudencia.tjto.jus.br/consulta.php"
            )
        ]
    )
    provider = TjtoJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(
        JurisprudenceQuery(
            text="dano moral",
            degree="first",
            instance="first",
            collection="CJPG",
            types=["sentenca"],
        )
    )
    assert page.results[0].degree == "first"
    assert session.calls[0]["kwargs"]["data"]["tip_criterio_inst"] == "1"
    assert session.calls[0]["kwargs"]["data"]["type_minuta_selected"] == "3"


def test_tjto_uses_official_get_route_when_post_is_waf_challenged() -> None:
    session = FakeSession(
        [
            FakeResponse(
                "challenge",
                url="https://jurisprudencia.tjto.jus.br/consulta.php",
                status_code=202,
                headers={"x-amzn-waf-action": "challenge"},
            ),
            FakeResponse(fixture_html(), url="https://jurisprudencia.tjto.jus.br/consulta.php"),
        ]
    )
    provider = TjtoJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=2))
    assert page.results
    assert page.source_trace.endpoint == "GET /consulta.php"
    assert [call["method"] for call in session.calls] == ["POST", "GET"]
    assert "q" in session.calls[1]["kwargs"]["params"]


def test_tjto_fetch_details_preserves_document_metadata() -> None:
    document = "<html><body>Inteiro teor HTML publico de fixture.</body></html>"
    session = FakeSession(
        [
            FakeResponse(fixture_html(), url="https://jurisprudencia.tjto.jus.br/consulta.php"),
            FakeResponse(
                document,
                url="https://jurisprudencia.tjto.jus.br/documento.php?uuid=abcdef1234567890",
            ),
        ]
    )
    provider = TjtoJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=2, fetch_details=True))
    assert page.results[0].full_text == "Inteiro teor HTML publico de fixture."
    assert page.results[0].raw["content_sha256"]
    assert page.results[0].raw["document_content_type"] == "text/html"
    assert session.calls[1]["method"] == "GET"


def test_tjto_detail_access_error_preserves_base_result_as_partial() -> None:
    session = FakeSession(
        [
            FakeResponse(fixture_html(), url="https://jurisprudencia.tjto.jus.br/consulta.php"),
            FakeResponse(
                "Access Denied",
                url="https://jurisprudencia.tjto.jus.br/documento.php?uuid=abcdef1234567890",
                status_code=403,
            ),
        ]
    )
    provider = TjtoJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=2, fetch_details=True))
    result = page.results[0]
    assert result.summary
    assert result.full_text is None
    assert result.extraction_status.value == "partial"
    assert result.raw["detail_status"] == "error"
    assert result.raw["detail_error_type"] == "AccessControlRequiredError"


def test_tjto_rejects_missing_term_and_exposes_capabilities() -> None:
    provider = TjtoJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), FakeSession([]))
    with pytest.raises(ValueError, match="requires text"):
        provider.search(JurisprudenceQuery())
    with pytest.raises(SourceUnavailableError, match="public document UUID"):
        provider.get_decisions("id")
    capabilities = provider.get_capabilities()
    assert capabilities.supports_full_text is True
    assert capabilities.pagination_mode == "offset"
    assert capabilities.max_remote_page_size == 100


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (429, RateLimitDetectedError),
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (400, QueryRejectedError),
        (422, QueryRejectedError),
        (500, SourceUnavailableError),
        (202, SourceUnavailableError),
        (404, SourceUnavailableError),
    ],
)
def test_tjto_classifies_http_outcomes(status: int, expected: type[Exception]) -> None:
    provider = TjtoJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession(
            [FakeResponse("error", url="https://tjto.test", status_code=status) for _ in range(3)]
        ),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))


def test_tjto_classifies_transport_and_document_contract_errors() -> None:
    class FailingSession:
        def request(self, method: str, url: str, **kwargs: Any) -> Any:
            raise requests.RequestException("offline")

    provider = TjtoJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FailingSession(),  # type: ignore[arg-type]
    )
    with pytest.raises(SourceUnavailableError, match="request failed"):
        provider.search(JurisprudenceQuery(text="teste"))

    provider = TjtoJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        FakeSession([FakeResponse("plain text", url="https://tjto.test/documento.php")]),
    )
    with pytest.raises(ParserContractChangedError, match="not HTML"):
        provider.get_document("abcdef1234567890")

    with pytest.raises(ValueError, match="document_id"):
        provider.get_document("bad-id")


def test_tjto_classifies_waf_challenge_without_treating_it_as_empty() -> None:
    response = FakeResponse("", url="https://tjto.test", status_code=202)
    response.headers["x-amzn-waf-action"] = "challenge"
    get_response = FakeResponse("", url="https://tjto.test", status_code=202)
    get_response.headers["x-amzn-waf-action"] = "challenge"
    provider = TjtoJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession([response, get_response])
    )
    with pytest.raises(AccessControlRequiredError, match="WAF challenge"):
        provider.search(JurisprudenceQuery(text="teste", page=2))


def test_tjto_parser_rejects_missing_cards_or_card_body() -> None:
    empty_trace = trace()
    with pytest.raises(ParserContractChangedError, match="cards"):
        parse_tjto_search_response(
            b"<html><body>(10 resultados)</body></html>",
            query=JurisprudenceQuery(text="teste"),
            trace=empty_trace,
        )
    with pytest.raises(ParserContractChangedError, match="panel-body"):
        parse_tjto_search_response(
            (
                b"<div class='container align-self-center panel panel-default'>"
                b"<div class='panel_doc'>0000001-23.2026.8.27.0001</div></div>"
            ),
            query=JurisprudenceQuery(text="teste"),
            trace=empty_trace,
        )


def test_tjto_parser_supports_process_number_without_uuid_and_partial_summary() -> None:
    content = (
        "<div class='container align-self-center panel panel-default'>"
        "<div class='panel_doc'>Ementa Processo 0000001-23.2026.8.27.0001</div>"
        "<div class='panel-body'>Classe Apelação Cível Tipo Julgamento Mérito "
        "Assunto(s) Responsabilidade Civil Competência Câmara Cível "
        "Relator RELATOR FIXTURE Data Autuação 01/01/2026 Data Julgamento 15/02/2026</div>"
        "</div>"
    )
    page = parse_tjto_search_response(
        content.encode("utf-8"),
        query=JurisprudenceQuery(text="teste"),
        trace=trace(),
    )
    result = page.results[0]
    assert result.id == "tjto-jurisprudencia-0000001-23.2026.8.27.0001"
    assert result.extraction_status.value == "partial"
    assert result.raw["document_uuid"] is None
    # The judgment date is captured even when the card carries no EMENTA section.
    assert result.summary is None
    assert result.judgment_date == "2026-02-15"
    assert page.total_known is False
    assert page.effective_total is None
    assert page.is_complete is None


def test_tjto_parameter_helpers_cover_order_branches() -> None:
    assert (
        build_tjto_search_parameters(JurisprudenceQuery(text="teste", order_by="oldest"))[
            "tip_criterio_data"
        ]
        == "ASC"
    )
    assert (
        build_tjto_search_parameters(JurisprudenceQuery(text="teste", order_by="relevance"))[
            "tip_criterio_data"
        ]
        == "RELEV"
    )
    assert (
        build_tjto_search_parameters(JurisprudenceQuery(text="teste", order_by="Text"))[
            "tip_criterio_data"
        ]
        == "DESC"
    )
