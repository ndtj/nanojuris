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
from nanojuris.providers.tcu_jurisprudencia import (
    TcuJurisprudenciaProvider,
    parse_tcu_manifest,
)
from nanojuris.providers.tjpa_jurisprudencia_bff import (
    TjpaJurisprudenciaBffProvider,
    _as_int,
    _date_br,
    _date_iso,
    _nested_name,
    build_tjpa_search_payload,
    parse_tjpa_search_response,
)
from nanojuris.providers.tjpb_pje_jurisprudencia import (
    TjpbPjeJurisprudenciaProvider,
    _clean_tjpb_ementa,
    parse_tjpb_search_response,
)
from nanojuris.providers.tjrs_solr import (
    TjrsSolrProvider,
    build_tjrs_search_parameters,
)
from nanojuris.providers.tst_jurisprudencia import TstJurisprudenciaProvider


class FakeResponse:
    def __init__(
        self,
        data: Any = None,
        *,
        text: str = "",
        status_code: int = 200,
        url: str = "https://example.test/",
    ) -> None:
        self._data = data
        self.text = text
        self.status_code = status_code
        self.url = url
        self.content = (
            json.dumps(data, ensure_ascii=False).encode("utf-8") if data is not None else b""
        )
        self.headers = {"Content-Type": "application/json"} if data is not None else {}

    def json(self) -> Any:
        if self._data is None:
            raise ValueError("not json")
        return self._data


class StreamResponse(FakeResponse):
    def __init__(self, content: bytes, *, url: str) -> None:
        super().__init__(url=url)
        self.content = content
        self.closed = False

    def iter_lines(self, *, decode_unicode: bool = False):
        for line in self.content.splitlines():
            yield line.decode("utf-8") if decode_unicode else line

    def close(self) -> None:
        self.closed = True


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": "GET", "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def test_tjpb_parser_and_public_token_flow() -> None:
    response_data = json.loads(
        (Path(__file__).parent / "fixtures" / "tjpb_pje_jurisprudencia_success.json").read_text(
            encoding="utf-8"
        )
    )
    session = FakeSession(
        [
            FakeResponse(text='<meta name="_token" content="csrf-test">'),
            FakeResponse(
                response_data,
                url="https://pje-jurisprudencia.tjpb.jus.br/api/jurisprudencia/pesquisar",
            ),
        ]
    )
    provider = TjpbPjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(
        JurisprudenceQuery(text="dano moral", number="0000001-10.2024.8.15.0001", page_size=1)
    )

    assert page.total == 1
    assert page.total_known is True
    assert page.access_status.value == "public"
    assert page.extraction_status.value == "complete"
    assert page.results[0].id == "tjpb-pje-fixture-tjpb-abc123"
    assert page.results[0].judgment_date == "2026-01-01"
    assert page.results[0].degree == "second"
    assert page.results[0].instance == "second"
    assert page.results[0].branch == "state"
    assert page.results[0].authority == "TJPB"
    assert page.results[0].collection == "CJSG"
    assert page.results[0].document_type == "acordao"
    assert page.results[0].raw["document_url"].endswith("/jurisprudencia/view/fixture-tjpb-abc123")
    assert session.calls[0]["method"] == "GET"
    payload = session.calls[1]["kwargs"]["json"]
    assert payload["_token"] == "csrf-test"
    assert payload["jurisprudencia"]["nr_rocesso"] == "0000001-10.2024.8.15.0001"
    assert payload["jurisprudencia"]["id_origem"] == "8,2"
    assert payload["jurisprudencia"]["teor"] == ""
    assert "nr_processo" not in payload["jurisprudencia"]
    assert session.calls[1]["kwargs"]["headers"]["X-Requested-With"] == "XMLHttpRequest"


def test_tjpb_maps_canonical_class_rapporteur_and_judgment_dates() -> None:
    response_data = {
        "total": 0,
        "hits": [],
    }
    session = FakeSession(
        [
            FakeResponse(text='<meta name="_token" content="csrf-test">'),
            FakeResponse(response_data, url="https://example.test/api"),
        ]
    )
    provider = TjpbPjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )
    provider.search(
        JurisprudenceQuery(
            text="tributario",
            case_class="Apelacao Civel",
            rapporteur="Desembargador Exemplo",
            judgment_date_from="2025-01-01",
            judgment_date_to="2025-12-31",
        )
    )
    payload = session.calls[1]["kwargs"]["json"]["jurisprudencia"]
    assert payload["id_classe_judicial"] == "Apelacao Civel"
    assert payload["id_relator"] == "Desembargador Exemplo"
    assert payload["dt_inicio"] == "2025-01-01"
    assert payload["dt_fim"] == "2025-12-31"


def test_tjpb_rejects_first_degree_scope() -> None:
    provider = TjpbPjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    )
    with pytest.raises(QueryRejectedError, match="only second-degree"):
        provider.search(JurisprudenceQuery(text="teste", types=("sentenca",)))


def test_tjpb_rejects_first_degree_canonical_filter() -> None:
    provider = TjpbPjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([])
    )
    with pytest.raises(QueryRejectedError, match="only second-degree"):
        provider.search(JurisprudenceQuery(text="teste", degree="first"))


def test_tjpb_ementa_strips_process_and_parties_header() -> None:
    raw = (
        "Processo nº: 0803419-27.2014.8.15.2001 Classe: RECURSO INOMINADO (460) "
        "Assuntos: [Acidente de Trânsito] RECORRENTE: FULANO RECORRIDO: BELTRANO "
        "EMENTA: RECURSO INOMINADO. ACIDENTE DE TRÂNSITO. DANO MATERIAL COMPROVADO. "
        "SENTENÇA MANTIDA."
    )
    assert _clean_tjpb_ementa(raw) == (
        "RECURSO INOMINADO. ACIDENTE DE TRÂNSITO. DANO MATERIAL COMPROVADO. SENTENÇA MANTIDA."
    )
    # A clean ementa is returned untouched.
    assert _clean_tjpb_ementa("Dano moral in re ipsa.") == "Dano moral in re ipsa."
    # A metadata-only header with no ementa is dropped rather than surfaced.
    assert _clean_tjpb_ementa("Processo nº: 0803419-27.2014.8.15.2001 Classe: RI") is None
    # A "Poder Judiciário Gab. Des. <relator>" prefix is stripped from the ementa.
    assert (
        _clean_tjpb_ementa(
            "Poder Judiciário Gab. Des. Marcos William de Oliveira   "
            "APELAÇÃO CÍVEL. RESPONSABILIDADE CIVIL. AÇÃO INDENIZATÓRIA. IMPROVIMENTO."
        )
        == "APELAÇÃO CÍVEL. RESPONSABILIDADE CIVIL. AÇÃO INDENIZATÓRIA. IMPROVIMENTO."
    )


def test_tjpb_parser_uses_cleaned_ementa_for_summary() -> None:
    response_data = {
        "total": 1,
        "hits": [
            {
                "_id": "HDR1",
                "_score": 1.0,
                "dt_ementa": "2026-01-01",
                "ementa": (
                    "Processo nº: 0803419-27.2014.8.15.2001 Classe: RECURSO INOMINADO "
                    "RECORRENTE: FULANO EMENTA: CONSUMIDOR. INSCRIÇÃO INDEVIDA. DANO "
                    "MORAL IN RE IPSA."
                ),
                "numero_processo": "0803419-27.2014.8.15.2001",
            }
        ],
    }
    session = FakeSession(
        [
            FakeResponse(text='<meta name="_token" content="csrf-test">'),
            FakeResponse(
                response_data,
                url="https://pje-jurisprudencia.tjpb.jus.br/api/jurisprudencia/pesquisar",
            ),
        ]
    )
    provider = TjpbPjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.results[0].summary == "CONSUMIDOR. INSCRIÇÃO INDEVIDA. DANO MORAL IN RE IPSA."


def test_tjpb_does_not_reject_appellate_ementa_that_mentions_sentence() -> None:
    response_data = {
        "total": 1,
        "hits": [
            {
                "_id": "APELACAO1",
                "dt_ementa": "2026-01-01",
                "ementa": "APELACAO CIVEL. SENTENCA MANTIDA. RESPONSABILIDADE CIVIL.",
                "classe": "APELACAO CIVEL",
            }
        ],
    }
    page = parse_tjpb_search_response(
        response_data,
        query=JurisprudenceQuery(text="responsabilidade civil"),
        trace=SourceTrace(provider="tjpb_pje_jurisprudencia", endpoint="POST /api"),
        base_url="https://example.test",
    )

    assert len(page.results) == 1
    assert page.results[0].degree == "second"


def test_tjpb_parser_reports_translated_filter_plan() -> None:
    page = parse_tjpb_search_response(
        {
            "total": 1,
            "hits": [{"_id": "APELACAO-FILTRO", "ementa": "APELACAO CIVEL"}],
        },
        query=JurisprudenceQuery(
            text="responsabilidade",
            number="0000000-00.2026.8.15.0001",
            case_class="APELACAO",
            judging_body="CAMARA-1",
            source_origin="2",
            degree="second",
            instance="2",
            published_from="2026-01-01",
            judgment_date_to="2026-12-31",
        ),
        trace=SourceTrace(provider="tjpb_pje_jurisprudencia", endpoint="POST /api"),
        base_url="https://example.test",
    )

    assert page.filters_applied["text"] == "translated"
    assert page.filters_applied["case_class"] == "translated"
    assert page.filters_applied["source_origin"] == "translated"
    assert page.filters_applied["degree"] == "validated_scope"
    assert page.filters_applied["judgment_date_to"] == "translated"


def test_tjpb_rejects_structured_first_degree_marker() -> None:
    response_data = {
        "total": 1,
        "hits": [
            {
                "_id": "SENTENCA1",
                "dt_ementa": "2026-01-01",
                "ementa": "DECISAO",
                "grau": "primeiro grau",
            }
        ],
    }
    with pytest.raises(ParserContractChangedError, match="first-degree"):
        parse_tjpb_search_response(
            response_data,
            query=JurisprudenceQuery(text="teste"),
            trace=SourceTrace(provider="tjpb_pje_jurisprudencia", endpoint="POST /api"),
            base_url="https://example.test",
        )


def test_tjpb_does_not_treat_process_class_as_degree_marker() -> None:
    response_data = {
        "total": 1,
        "hits": [
            {
                "_id": "APELACAO2",
                "dt_ementa": "2026-01-01",
                "ementa": "SENTENCA MANTIDA. RESPONSABILIDADE CIVIL.",
                "classe": "Sentenca",
            }
        ],
    }
    page = parse_tjpb_search_response(
        response_data,
        query=JurisprudenceQuery(text="responsabilidade civil"),
        trace=SourceTrace(provider="tjpb_pje_jurisprudencia", endpoint="POST /api"),
        base_url="https://example.test",
    )

    assert len(page.results) == 1
    assert page.results[0].degree == "second"


def test_tjpb_detail_is_normalized_as_public_document() -> None:
    html = "<html><body><main><h1>Acórdão</h1><p>Conteúdo público.</p></main></body></html>"
    provider = TjpbPjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(text=html, url="https://example.test/detail")]),
    )

    document = provider.get_document("tjpb-pje-ABC123")

    assert document.source == "tjpb_pje_jurisprudencia"
    assert document.text == "Acórdão Conteúdo público."
    assert document.sha256


def test_tjpb_parser_rejects_missing_hits() -> None:
    with pytest.raises(ParserContractChangedError, match="hits"):
        parse_tjpb_search_response(
            {},
            query=JurisprudenceQuery(text="teste"),
            trace=None,  # type: ignore[arg-type]
            base_url="https://example.test",
        )


def test_tjpb_access_challenge_is_not_misreported_as_schema_change() -> None:
    fixture = (Path(__file__).parent / "fixtures" / "tjpb_access_control.html").read_text(
        encoding="utf-8"
    )
    provider = TjpbPjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(text=fixture)]),
    )

    with pytest.raises(AccessControlRequiredError, match="challenge"):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_tjpa_payload_parser_and_catalog() -> None:
    query = JurisprudenceQuery(
        text="dano moral",
        source_origins=["1"],
        types=["ACORDAO"],
        published_from="2026-01-01",
        published_to="2026-08-11",
    )
    payload = build_tjpa_search_payload(query)
    assert payload["query"] == "dano moral"
    assert payload["origens"] == ["1"]
    assert payload["dataPublicacaoInicio"] == "2026-01-01"
    assert payload["dataPublicacaoFim"] == "2026-08-11"

    details_payload = build_tjpa_search_payload(
        JurisprudenceQuery(text="dano moral", fetch_details=True)
    )
    assert details_payload["queryScope"] == "inteiroTeor"

    data = {
        "message": "ok",
        "data": {
            "content": [
                {
                    "id": 42,
                    "numeroprocesso": "0800000-00.2024.8.14.0001",
                    "ementatextopuro": "Ementa TJPA.",
                    "textopuro": "Inteiro teor disponivel.",
                    "datapublicacao": "01/02/2026",
                    "relator": {"nome": "Desembargador Exemplo"},
                }
            ],
            "totalElements": 1,
            "facets": [],
        },
    }
    page = parse_tjpa_search_response(
        data,
        query=JurisprudenceQuery(text="dano moral", page_size=1),
        trace=None,  # type: ignore[arg-type]
    )
    assert page.total == 1
    assert page.results[0].id == "tjpa-bff-42"
    assert page.results[0].rapporteur == "Desembargador Exemplo"
    assert page.results[0].publication_date == "2026-02-01"
    assert page.results[0].raw["full_text"] == "Inteiro teor disponivel."

    session = FakeSession(
        [
            FakeResponse(data, url="https://example.test/bff/api/decisoes/buscar"),
            FakeResponse(
                {
                    "data": {
                        "tipos": [{"id": "A", "descricao": "Acordao"}],
                        "orgaosJulgadoresColegiados": [{"id": "O", "descricao": "Camara Exemplo"}],
                    }
                }
            ),
        ]
    )
    provider = TjpaJurisprudenciaBffProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )
    searched = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))
    assert searched.results[0].id == "tjpa-bff-42"
    catalog = provider.get_catalog()
    assert catalog.species[0].code == "A"
    assert catalog.courts[0].description == "Camara Exemplo"


def test_tjpa_versioned_success_fixture_preserves_contract() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "tjpa_jurisprudencia_bff_results.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))

    page = parse_tjpa_search_response(
        data,
        query=JurisprudenceQuery(text="dano moral", page_size=1),
        trace=None,  # type: ignore[arg-type]
    )

    result = page.results[0]
    assert page.total == 1
    assert page.total_known is True
    assert page.access_status.value == "public"
    assert page.extraction_status.value == "complete"
    assert result.id == "tjpa-bff-42"
    assert result.rapporteur == "Desembargador de Fixture"
    assert result.publication_date == "2026-02-01"
    assert result.raw["publication_date_raw"] == "01/02/2026"
    assert result.raw["full_text"] == "Inteiro teor publico sanitizado."


def test_tjpa_parser_exposes_bff_filter_plan_and_scope_validation() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "tjpa_jurisprudencia_bff_results.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    query = JurisprudenceQuery(
        text="dano moral",
        case_class="APELACAO",
        rapporteur="Desembargador",
        source_origin="TJPA",
        degree="second",
        instance="2",
        branch="state",
        authority="TJPA",
        collection="CJSG",
        published_from="2026-01-01",
    )

    page = parse_tjpa_search_response(
        data,
        query=query,
        trace=None,  # type: ignore[arg-type]
    )

    assert page.filters_applied["text"] == "translated"
    assert page.filters_applied["case_class"] == "unsupported"
    assert page.filters_applied["degree"] == "validated_scope"
    assert page.filters_applied["published_from"] == "translated"

    provider = TjpaJurisprudenciaBffProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError, match="ramo estadual"):
        provider.search(JurisprudenceQuery(text="teste", branch="federal"))


@pytest.mark.parametrize(
    "status,exception",
    [
        (429, RateLimitDetectedError),
        (401, AccessControlRequiredError),
        (403, AccessControlRequiredError),
        (500, SourceUnavailableError),
        (400, SourceUnavailableError),
    ],
)
def test_tjpa_maps_public_http_errors(status: int, exception: type[Exception]) -> None:
    provider = TjpaJurisprudenciaBffProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({}, status_code=status)]),
    )

    with pytest.raises(exception):
        provider.search(JurisprudenceQuery(text="dano moral"))


def test_tjpa_rejects_invalid_json_and_non_object_root() -> None:
    provider = TjpaJurisprudenciaBffProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(None)]),
    )
    with pytest.raises(ParserContractChangedError, match="not JSON"):
        provider.search(JurisprudenceQuery(text="teste"))

    provider = TjpaJurisprudenciaBffProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse([])]),
    )
    with pytest.raises(ParserContractChangedError, match="root"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_tjpa_rejects_incomplete_search_and_catalog_contracts() -> None:
    with pytest.raises(ParserContractChangedError, match="content"):
        parse_tjpa_search_response(
            {"data": {}},
            query=JurisprudenceQuery(text="teste"),
            trace=None,  # type: ignore[arg-type]
        )

    with pytest.raises(ParserContractChangedError, match="stable id"):
        parse_tjpa_search_response(
            {"data": {"content": [{}]}},
            query=JurisprudenceQuery(text="teste"),
            trace=None,  # type: ignore[arg-type]
        )

    provider = TjpaJurisprudenciaBffProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse({"data": []})]),
    )
    with pytest.raises(ParserContractChangedError, match="data object"):
        provider.get_catalog()


def test_tjpa_preserves_raw_dates_and_marks_textless_records_partial() -> None:
    page = parse_tjpa_search_response(
        {
            "data": {
                "content": [
                    {
                        "id": "textless",
                        "datadocumento": "2026-03-04T10:20:00Z",
                        "datapublicacao": "04/03/2026",
                    }
                ],
                "totalElements": 1,
            }
        },
        query=JurisprudenceQuery(text="teste"),
        trace=None,  # type: ignore[arg-type]
    )

    result = page.results[0]
    assert result.judgment_date is None
    assert result.publication_date == "2026-03-04"
    assert result.updated_at == "2026-03-04"
    assert result.extraction_status.value == "partial"
    assert result.raw["publication_date_raw"] == "04/03/2026"


def test_tjpa_missing_total_is_explicitly_unknown() -> None:
    page = parse_tjpa_search_response(
        {
            "data": {
                "content": [
                    {
                        "id": "without-total",
                        "ementatextopuro": "Ementa publica.",
                    }
                ]
            }
        },
        query=JurisprudenceQuery(text="teste", page_size=1),
        trace=None,  # type: ignore[arg-type]
    )

    assert page.total == 1
    assert page.total_known is False
    assert page.is_complete is None


def test_tjpa_normalization_helpers_keep_public_shapes() -> None:
    assert _date_br("2026-08-11") == "11/08/2026"
    assert _date_iso("2026-08-11") == "2026-08-11"
    assert _date_iso("11/08/2026") == "2026-08-11"
    assert _date_br("unknown") == "unknown"
    assert _nested_name({"name": "Relator"}) == "Relator"
    assert _nested_name("Relatora") == "Relatora"
    assert _nested_name(None) is None
    assert _as_int("10", default=0) == 10
    assert _as_int("invalid", default=7) == 7


def test_tjpa_detail_contract_is_explicitly_unimplemented() -> None:
    provider = TjpaJurisprudenciaBffProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(SourceUnavailableError, match="observed search"):
        provider.get_decisions("42")


def test_tst_catalog_routes_are_normalized_and_raw_payloads_preserved() -> None:
    catalog_payloads = [
        [{"id": "1", "descricao": "Orgao julgador"}],
        {"content": [{"codigo": "2", "nome": "Ministro"}]},
        [{"value": "3", "label": "Convocado"}],
        {"data": [{"id": "4", "description": "Classe"}]},
        [{"id": "5", "name": "Indicador"}],
        {"results": [{"cod": "6", "descricao": "Assunto"}]},
    ]
    session = FakeSession([FakeResponse(payload) for payload in catalog_payloads])
    provider = TstJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    catalog = provider.get_catalog()

    assert catalog.courts[0].code == "TST"
    assert [option.code for option in catalog.species] == ["4"]
    assert len(catalog.species_groups) == 6
    assert catalog.raw["assuntos"]["results"][0]["cod"] == "6"
    assert all(call["method"] == "GET" for call in session.calls)


def test_tst_catalog_non_json_is_a_contract_failure() -> None:
    provider = TstJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([FakeResponse(None)])
    )

    with pytest.raises(ParserContractChangedError, match="catalog"):
        provider.get_catalog()


def test_tjrs_preserves_nested_query_separators_and_parses_solr() -> None:
    query = JurisprudenceQuery(text="dano moral", page=2, page_size=1)
    parameters = build_tjrs_search_parameters(query)
    assert parameters["pagina_atual"] == 2

    data = {
        "response": {
            "numFound": 612_403,
            "start": 1,
            "docs": [
                {
                    "cod_ementa": "123",
                    "numero_processo": "70000000000",
                    "ementa": "Ementa TJRS.",
                    "nome_relator": "Relator Exemplo",
                    "orgao_julgador": "Camara Exemplo",
                    "tipo_documento": "Acordao",
                    "nome_tribunal": "TJRS",
                }
            ],
        },
        "facets": [],
    }
    session = FakeSession([FakeResponse(data)])
    provider = TjrsSolrProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(query)

    nested = session.calls[0]["kwargs"]["data"]["parametros"]
    assert "aba=jurisprudencia&realizando_pesquisa=1" in nested
    assert page.total == 612_403
    assert page.results[0].number == "70000000000"
    assert page.results[0].raw["orgao_julgador"] == "Camara Exemplo"
    assert provider.get_capabilities().supports_catalog is False


def test_tcu_manifest_and_streaming_summary_search() -> None:
    manifest = (
        "Data de publicacao: 2026-08-11\n"
        '"ANO"|"BASE"|"TAMANHO"|"ARQUIVO"\n'
        '"2026"|"Acordaos completos"|"10 MB"|"acordao.csv"\n'
    )
    rows = parse_tcu_manifest(manifest)
    assert rows[0]["BASE"] == "Acordaos completos"
    assert rows[0]["ARQUIVO"] == "acordao.csv"

    csv_data = (
        b"KEY|VISAOGERAL\n"
        b'"AC-1"|"<p>Responsabilidade administrativa e dano moral.</p>"\n'
        b'"AC-2"|"Outro assunto."\n'
    )
    stream = StreamResponse(csv_data, url="https://sites.tcu.gov.br/summary.csv")
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([stream])
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.total == 1
    assert page.results[0].id == "tcu-acordao-resumo-AC-1"
    assert page.results[0].summary == "Responsabilidade administrativa e dano moral."
    assert stream.closed is True


def test_initial_providers_are_registered_by_default() -> None:
    client = NanoJurisClient()

    assert {
        "tjpa_jurisprudencia_bff",
        "tjpb_pje_jurisprudencia",
        "tjrs_solr",
        "tcu_jurisprudencia",
    } <= set(client.providers)


def test_tcu_requires_a_search_term() -> None:
    provider = TcuJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(ValueError, match="requires a term"):
        provider.search(JurisprudenceQuery())


def test_tcu_catalog_reads_manifest_stream() -> None:
    manifest = (
        b'Data de publicacao: 2026-08-11\n"ANO"|"BASE"|"TAMANHO"|"ARQUIVO"\n'
        b'"2026"|"Acordaos"|"1 MB"|"acordaos.csv"\n'
    )
    response = StreamResponse(manifest, url="https://sites.tcu.gov.br/manifest.csv")
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    catalog = provider.get_catalog()

    assert catalog.species[0].description == "Acordaos"
    assert catalog.species[0].metadata["url"] == "acordaos.csv"
    assert response.closed is True


def test_tcu_rejects_invalid_manifest() -> None:
    response = StreamResponse(b"manifesto sem cabecalho", url="https://example.test/manifest.csv")
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    with pytest.raises(ParserContractChangedError, match="manifest"):
        provider.get_catalog()


@pytest.mark.parametrize(
    "status,exception",
    [
        (429, RateLimitDetectedError),
        (401, AccessControlRequiredError),
        (500, SourceUnavailableError),
        (400, SourceUnavailableError),
    ],
)
def test_tcu_maps_public_http_errors(status: int, exception: type[Exception]) -> None:
    response = StreamResponse(b"blocked", url="https://example.test/summary.csv")
    response.status_code = status
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    with pytest.raises(exception):
        provider.search(JurisprudenceQuery(text="dano moral"))

    assert response.closed is True


def test_tcu_skips_header_and_malformed_csv_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    csv_data = b'KEY|VISAOGERAL\n"AC-1"|"Dano moral."\nlinha"invalida|"x"\n'
    monkeypatch.setattr("nanojuris.providers.tcu_jurisprudencia.MAX_SCAN_BYTES", 10_000)
    response = StreamResponse(csv_data, url="https://example.test/summary.csv")
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=2))

    assert [item.id for item in page.results] == ["tcu-acordao-resumo-AC-1"]
