from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.bnp_pangea import BnpPangeaProvider

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, payload, status_code: int = 200, text: str = ""):
        self.payload = payload
        self.status_code = status_code
        self.text = text

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


class RaisingSession:
    def request(self, method, url, **kwargs):
        raise requests.RequestException("offline")


def test_search_maps_bnp_response():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "total": 1,
                    "posicao_inicial": 1,
                    "posicao_final": 1,
                    "aggsEspecies": [{"tipo": "RG", "total": 1}],
                    "aggsOrgaos": [{"tipo": "STF", "total": 1}],
                    "resultados": [
                        {
                            "id": "stf-rg-615",
                            "orgao": "STF",
                            "tipo": "RG",
                            "nr": 615,
                            "questao": "Questao publica",
                            "tese": "Tese publica",
                            "situacao": "Vigente",
                            "ultimaAtualizacao": "20/06/2024",
                            "highlight": {"tese": "<mark>Tese</mark> publica"},
                            "processosParadigma": [
                                {
                                    "numero": "680089",
                                    "classe": 1348,
                                    "link": "https://portal.stf.jus.br/processos/detalhe.asp",
                                }
                            ],
                        }
                    ],
                }
            )
        ]
    )
    provider = BnpPangeaProvider(NanoJurisConfig(), session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="ICMS",
            courts=["STF"],
            types=["RG"],
            page=2,
            page_size=5,
        )
    )

    assert page.total == 1
    assert page.start == 1
    assert page.end == 1
    assert page.aggregations["species"][0]["tipo"] == "RG"
    assert page.results[0].id == "stf-rg-615"
    assert page.results[0].court == "STF"
    assert page.results[0].type == "RG"
    assert page.results[0].number == 615
    assert page.results[0].paradigm_cases[0].number == "680089"
    assert page.results[0].source_trace is not None

    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/precedentes")
    assert call["kwargs"]["json"]["filtro"]["buscaGeral"] == "ICMS"
    assert call["kwargs"]["json"]["filtro"]["orgaos"] == ["STF"]
    assert call["kwargs"]["json"]["filtro"]["tipos"] == ["RG"]


def test_get_decisions_maps_response():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "relator": "MIN. EXEMPLO",
                    "linkAcompanhamentoProcesssual": "https://example.test/processo",
                    "textos": [{"tipo": "Acordao", "texto": "Conteudo"}],
                }
            )
        ]
    )
    provider = BnpPangeaProvider(session=session)

    bundle = provider.get_decisions("stf-rg-615")

    assert bundle.precedent_id == "stf-rg-615"
    assert bundle.rapporteur == "MIN. EXEMPLO"
    assert bundle.procedural_follow_url == "https://example.test/processo"
    assert bundle.texts[0]["tipo"] == "Acordao"
    assert session.calls[0]["url"].endswith("/precedentes/stf-rg-615/decisoes")


def test_get_parameters_returns_dict():
    session = FakeSession([FakeResponse({"orgaos": [], "especies": []})])
    provider = BnpPangeaProvider(session=session)

    assert provider.get_parameters() == {"orgaos": [], "especies": []}


def test_get_catalog_normalizes_courts_and_species():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "orgaos": [
                        {
                            "sigla": "STF",
                            "descricao": "Supremo Tribunal Federal",
                            "apelido": "",
                            "semPrecedentes": False,
                        },
                        {
                            "sigla": "TSE",
                            "descricao": "Tribunal Superior Eleitoral",
                            "apelido": "",
                            "semPrecedentes": True,
                        },
                    ],
                    "especies": [
                        {"sigla": "RG", "descricao": "Tema de Repercussao Geral"},
                        {"sigla": "RR", "descricao": "Recurso Especial Repetitivo"},
                    ],
                    "gruposEspecies": [{"id": 1, "especies": ["RG", "RR"]}],
                }
            )
        ]
    )
    provider = BnpPangeaProvider(session=session)

    catalog = provider.get_catalog()

    assert catalog.source == "bnp_pangea"
    assert catalog.courts[0].code == "STF"
    assert catalog.courts[0].description == "Supremo Tribunal Federal"
    assert catalog.courts[1].code == "TSE"
    assert catalog.courts[1].disabled is True
    assert catalog.species[0].code == "RG"
    assert catalog.species_groups[0]["id"] == 1
    assert catalog.source_trace is not None


def test_list_courts_filters_disabled_by_default():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "orgaos": [
                        {"sigla": "STF", "descricao": "Supremo Tribunal Federal"},
                        {
                            "sigla": "TSE",
                            "descricao": "Tribunal Superior Eleitoral",
                            "semPrecedentes": True,
                        },
                    ],
                    "especies": [{"sigla": "RG", "descricao": "Tema de Repercussao Geral"}],
                }
            ),
            FakeResponse(
                {
                    "orgaos": [
                        {"sigla": "STF", "descricao": "Supremo Tribunal Federal"},
                        {
                            "sigla": "TSE",
                            "descricao": "Tribunal Superior Eleitoral",
                            "semPrecedentes": True,
                        },
                    ],
                    "especies": [{"sigla": "RG", "descricao": "Tema de Repercussao Geral"}],
                }
            ),
        ]
    )
    provider = BnpPangeaProvider(session=session)

    assert [court.code for court in provider.list_courts()] == ["STF"]
    assert [court.code for court in provider.list_courts(include_disabled=True)] == ["STF", "TSE"]


def test_list_species_returns_catalog_species():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "orgaos": [{"sigla": "STF", "descricao": "Supremo Tribunal Federal"}],
                    "especies": [
                        {"sigla": "RG", "descricao": "Tema de Repercussao Geral"},
                        {"sigla": "SV", "descricao": "Sumula Vinculante"},
                    ],
                }
            )
        ]
    )
    provider = BnpPangeaProvider(session=session)

    assert [species.code for species in provider.list_species()] == ["RG", "SV"]


def test_list_suggestions_maps_response():
    session = FakeSession([FakeResponse(["icms", "icms consumidor final"])])
    provider = BnpPangeaProvider(session=session)

    assert provider.list_suggestions("ic") == ["icms", "icms consumidor final"]
    assert session.calls[0]["kwargs"]["params"] == {"texto": "ic"}


def test_list_suggestions_ignores_blank_text_without_request():
    session = FakeSession([])
    provider = BnpPangeaProvider(session=session)

    assert provider.list_suggestions("   ") == []
    assert session.calls == []


def test_list_suggestions_returns_empty_when_endpoint_is_not_public():
    session = FakeSession([FakeResponse({}, status_code=404)])
    provider = BnpPangeaProvider(session=session)

    assert provider.list_suggestions("icms") == []


def test_search_maps_all_core_species_fixture():
    payload = json.loads((FIXTURES / "bnp_precedentes_species.json").read_text(encoding="utf-8"))
    session = FakeSession([FakeResponse(payload)])
    provider = BnpPangeaProvider(session=session)

    page = provider.search(JurisprudenceQuery(text="teste", page_size=6))

    assert page.total == 6
    assert {result.type for result in page.results} == {"RG", "RR", "IAC", "IRDR", "SUM", "SV"}
    assert page.results[0].paradigm_cases[0].url == "https://example.test/stf"
    assert page.aggregations["species"][0]["tipo"] == "RG"


def test_list_suggestions_rejects_invalid_contract():
    session = FakeSession([FakeResponse({"items": []})])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(ParserContractChangedError):
        provider.list_suggestions("ic")


def test_get_catalog_rejects_missing_required_keys():
    session = FakeSession([FakeResponse({"orgaos": []})])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(ParserContractChangedError):
        provider.get_catalog()


def test_get_catalog_rejects_invalid_option():
    session = FakeSession([FakeResponse({"orgaos": [{}], "especies": []})])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(ParserContractChangedError):
        provider.get_catalog()


def test_search_rejects_invalid_contract():
    session = FakeSession([FakeResponse({"total": 1})])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(ParserContractChangedError):
        provider.search(JurisprudenceQuery(text="ICMS"))


def test_search_rejects_result_without_id():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "total": 1,
                    "posicao_inicial": 1,
                    "posicao_final": 1,
                    "resultados": [{"orgao": "STF", "tipo": "RG"}],
                }
            )
        ]
    )
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(ParserContractChangedError):
        provider.search(JurisprudenceQuery(text="ICMS"))


def test_get_decisions_rejects_invalid_contract():
    session = FakeSession([FakeResponse([])])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(ParserContractChangedError):
        provider.get_decisions("stf-rg-615")


def test_invalid_json_becomes_parser_error():
    session = FakeSession([FakeResponse(ValueError("bad json"))])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(ParserContractChangedError):
        provider.get_parameters()


def test_http_429_becomes_rate_limit_error():
    session = FakeSession([FakeResponse({}, status_code=429)])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(RateLimitDetectedError):
        provider.get_parameters()


def test_http_500_becomes_source_unavailable():
    session = FakeSession([FakeResponse({}, status_code=500)])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(SourceUnavailableError):
        provider.get_parameters()


def test_http_400_becomes_query_rejected():
    session = FakeSession([FakeResponse({}, status_code=400, text="Requisição inválida")])
    provider = BnpPangeaProvider(session=session)

    with pytest.raises(QueryRejectedError) as exc_info:
        provider.search(JurisprudenceQuery(text="infanticidio"))

    message = str(exc_info.value)
    assert "HTTP 400" in message
    assert "Requisição inválida" in message
    assert "infanticidio" in message


def test_request_exception_becomes_source_unavailable():
    provider = BnpPangeaProvider(session=RaisingSession())

    with pytest.raises(SourceUnavailableError):
        provider.get_parameters()
