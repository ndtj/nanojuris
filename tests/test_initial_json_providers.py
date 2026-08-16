from __future__ import annotations

from typing import Any

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tcu_jurisprudencia import (
    TcuJurisprudenciaProvider,
    parse_tcu_manifest,
)
from nanojuris.providers.tjpa_jurisprudencia_bff import (
    TjpaJurisprudenciaBffProvider,
    _as_int,
    _date_br,
    _nested_name,
    build_tjpa_search_payload,
    parse_tjpa_search_response,
)
from nanojuris.providers.tjpb_pje_jurisprudencia import (
    TjpbPjeJurisprudenciaProvider,
    parse_tjpb_search_response,
)
from nanojuris.providers.tjrs_solr import (
    TjrsSolrProvider,
    build_tjrs_search_parameters,
)


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
    response_data = {
        "total": 48_534,
        "hits": [
            {
                "_id": "ABC123",
                "_score": 1.0,
                "dt_ementa": "2026-01-01",
                "ementa": "Dano moral e responsabilidade civil.",
                "numero_processo": "0000001-10.2024.8.15.0001",
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

    page = provider.search(
        JurisprudenceQuery(text="dano moral", number="0000001-10.2024.8.15.0001", page_size=1)
    )

    assert page.total == 48_534
    assert page.results[0].id == "tjpb-pje-ABC123"
    assert page.results[0].judgment_date == "2026-01-01"
    assert page.results[0].raw["document_url"].endswith("/jurisprudencia/view/ABC123")
    assert session.calls[0]["method"] == "GET"
    payload = session.calls[1]["kwargs"]["json"]
    assert payload["_token"] == "csrf-test"
    assert payload["jurisprudencia"]["nr_processo"] == "0000001-10.2024.8.15.0001"


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
    assert payload["dataPublicacaoInicio"] == "01/01/2026"

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
    assert page.results[0].publication_date == "01/02/2026"
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


def test_tjpa_normalization_helpers_keep_public_shapes() -> None:
    assert _date_br("2026-08-11") == "11/08/2026"
    assert _date_br("unknown") == "unknown"
    assert _nested_name({"name": "Relator"}) == "Relator"
    assert _nested_name("Relatora") == "Relatora"
    assert _nested_name(None) is None
    assert _as_int("10", default=0) == 10
    assert _as_int("invalid", default=7) == 7


def test_tjpa_detail_contract_is_explicitly_unimplemented() -> None:
    provider = TjpaJurisprudenciaBffProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(NotImplementedError, match="nao validadas"):
        provider.get_decisions("42")


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
