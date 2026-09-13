from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import QueryRejectedError, SourceUnavailableError
from nanojuris.models import (
    AccessStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.tre_sjur_jurisprudencia import (
    TRE_AUTHORITIES as PUBLIC_TRE_AUTHORITIES,
)
from nanojuris.providers.tre_sjur_jurisprudencia import (
    TRE_STATES as PUBLIC_TRE_STATES,
)
from nanojuris.providers.tre_sjur_jurisprudencia import (
    TreSjurJurisprudenciaFamilyProvider as PublicFamilyProvider,
)
from nanojuris.providers.tre_sjur_jurisprudencia import (
    TreSjurJurisprudenciaProvider as PublicTreProvider,
)
from nanojuris.providers.tse_sjur_jurisprudencia import (
    TRE_AUTHORITIES,
    TRE_STATES,
    TreSjurFirstDegreeFamilyProvider,
    TreSjurFirstDegreeProvider,
    TreSjurJurisprudenciaFamilyProvider,
    TreSjurJurisprudenciaProvider,
    _infer_tre_degree,
    build_tse_query,
)
from nanojuris.transport.models import TransportResponse

ROOT = Path(__file__).parent / "fixtures"


def test_tre_provider_has_catalogue_named_import_path() -> None:
    assert PublicFamilyProvider is TreSjurJurisprudenciaFamilyProvider
    assert PublicTreProvider is TreSjurJurisprudenciaProvider


def test_tre_registry_contains_exactly_the_27_regional_courts() -> None:
    assert len(TRE_STATES) == 27
    assert len(set(TRE_STATES)) == 27
    assert TRE_AUTHORITIES == tuple(f"TRE-{state}" for state in TRE_STATES)
    assert set(TRE_AUTHORITIES) == {
        "TRE-AC",
        "TRE-AL",
        "TRE-AP",
        "TRE-AM",
        "TRE-BA",
        "TRE-CE",
        "TRE-DF",
        "TRE-ES",
        "TRE-GO",
        "TRE-MA",
        "TRE-MG",
        "TRE-MS",
        "TRE-MT",
        "TRE-PA",
        "TRE-PB",
        "TRE-PE",
        "TRE-PI",
        "TRE-PR",
        "TRE-RJ",
        "TRE-RN",
        "TRE-RO",
        "TRE-RR",
        "TRE-RS",
        "TRE-SC",
        "TRE-SE",
        "TRE-SP",
        "TRE-TO",
    }
    assert PUBLIC_TRE_STATES is TRE_STATES
    assert PUBLIC_TRE_AUTHORITIES is TRE_AUTHORITIES


def test_tre_second_degree_capabilities_expose_validated_filters() -> None:
    capabilities = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    ).get_capabilities()

    assert {"degree", "document_type", "authority"} <= set(capabilities.supported_filters)
    assert capabilities.filter_status("degree") == "validated_scope"
    assert capabilities.filter_status("document_type") == "native"
    assert capabilities.filter_status("authority") == "validated_scope"
    assert capabilities.document_types == ["acordao", "decisao", "resolucao"]
    assert "document_type" not in capabilities.unsupported_filters
    assert "degree" not in capabilities.unsupported_filters


def test_tre_capabilities_expose_official_spa_structured_filters() -> None:
    capabilities = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    ).get_capabilities()

    expected = {
        "election_year",
        "observations",
        "tags",
        "municipality",
        "publication_source",
        "publication_number",
        "publication_volume",
        "uf",
    }
    assert expected <= set(capabilities.supported_filters)
    assert all(capabilities.filter_status(name) == "native" for name in expected)
    assert not expected.intersection(capabilities.unsupported_filters)


def test_tre_builds_official_spa_structured_filters() -> None:
    query = JurisprudenceQuery(
        text="eleicao",
        election_year="2020,2022",
        observations="urna eletronica",
        tags="fraude,propaganda",
        municipality="Sao Paulo,Campinas",
        publication_source="DJE",
        publication_number="12",
        publication_volume="3",
        uf="SP,RJ",
    )
    dsl = build_tse_query(query)
    filters = dsl["bool"]["filter"]
    assert {"terms": {"anoEleicao": [2020, 2022]}} in filters
    assert {"terms": {"etiquetas.etiqueta.keyword": ["fraude", "propaganda"]}} in filters
    assert {"terms": {"nomeMunicipio.keyword": ["Sao Paulo", "Campinas"]}} in filters
    assert {"terms": {"publicacoes.siglaFontePublicacao.keyword": ["DJE"]}} in filters
    assert {"terms": {"publicacoes.numeroPublicacao": ["12"]}} in filters
    assert {"terms": {"publicacoes.numeroVolume": ["3"]}} in filters
    assert {"terms": {"siglaUF.keyword": ["SP", "RJ"]}} in filters
    observation = next(
        clause["query_string"]
        for clause in dsl["bool"]["must"]
        if "query_string" in clause and clause["query_string"]["query"] == "urna eletronica"
    )
    assert "textoObservacaoGeral" in observation["fields"]
    assert "decisoesOutrosTribunais" in observation["fields"]


def test_tre_rejects_malformed_election_year_before_transport() -> None:
    with pytest.raises(QueryRejectedError, match="election_year"):
        build_tse_query(JurisprudenceQuery(text="eleicao", election_year="2022,abc"))


def test_tre_route_is_scoped_and_reuses_textual_contract() -> None:
    payload = json.loads((ROOT / "tse_sjur_success.json").read_text(encoding="utf-8"))
    payload["content"][0]["descricaoTipoDecisao"] = "Acordao"
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="divórcio", page_size=1))

    assert provider.name == "tre_sp_sjur_jurisprudencia"
    assert page.source == provider.name
    assert page.results[0].authority == "TRE-SP"
    assert page.results[0].court == "TRE-SP"
    assert page.results[0].branch == "electoral"
    assert page.results[0].collection == "SJUR"
    assert page.total_known is False
    assert page.is_complete is False
    assert "/tre-sp/" in page.source_trace.source_url
    request = calls[0]
    body = request.json_body  # type: ignore[attr-defined]
    assert body["tribunais"] == ["tre-sp"]
    assert "TRE-SP" in json.dumps(body["termoPesquisa"], ensure_ascii=False)


def test_tre_type_filter_preserves_official_utf8_wire_spelling() -> None:
    payload = json.loads((ROOT / "tse_sjur_success.json").read_text(encoding="utf-8"))
    payload["content"][0]["descricaoTipoDecisao"] = "Acórdão"
    provider = PublicTreProvider(NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP")
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    provider.search(JurisprudenceQuery(text="divórcio", page_size=1))

    body = calls[0].json_body  # type: ignore[attr-defined]
    dsl = json.loads(body["termoPesquisa"])
    type_filter = next(
        clause["terms"]["descricaoTipoDecisao.keyword"]
        for clause in dsl["bool"]["filter"]
        if "descricaoTipoDecisao.keyword" in clause.get("terms", {})
    )
    assert "Acórdão" in type_filter
    assert "AcÃ³rdÃ£o" not in type_filter


def test_tre_provider_rejects_first_degree_and_unknown_labels() -> None:
    payload = json.loads((ROOT / "tse_sjur_success.json").read_text(encoding="utf-8"))
    original = dict(payload["content"][0])
    original["descricaoTipoDecisao"] = "Acordao"
    first = dict(original)
    first["codigoDecisao"] = 900001
    first["descricaoTipoDecisao"] = "SentenÃ§a"
    unknown = dict(original)
    unknown["codigoDecisao"] = 900002
    unknown["descricaoTipoDecisao"] = "Ato sem classificaÃ§Ã£o"
    payload["content"] = [first, unknown, original]
    payload["totalRegistros"] = 3

    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )

    def request(request: object) -> TransportResponse:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="divÃ³rcio", page_size=3))

    assert len(page.results) == 1
    assert page.results[0].degree == "second"
    assert page.total_known is False
    assert page.is_complete is False
    assert page.filters_applied == {"degree": "remote+local:second"}
    assert "1 first-instance" in (page.completeness_reason or "")
    assert "1 unknown" in (page.completeness_reason or "")


def test_tre_first_degree_provider_keeps_first_degree_separate() -> None:
    payload = json.loads((ROOT / "tre_sjur_first_degree_success.json").read_text(encoding="utf-8"))
    provider = TreSjurFirstDegreeProvider(NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-MG")

    def request(request: object) -> TransportResponse:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-mg/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-mg/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="sentença", page_size=2))

    assert provider.name == "tre_mg_sjur_first_degree"
    assert len(page.results) == 1
    assert page.results[0].degree == "first"
    assert page.results[0].instance == "first"
    assert page.results[0].authority == "TRE-MG"
    # The fixture explicitly declares that no PDF is available.  The adapter
    # must not synthesize a document URL; inline decision text remains valid.
    assert page.results[0].document_url is None
    assert page.results[0].full_text
    assert page.results[0].raw.get("temInteiroTeorPDF") == "false"
    assert page.filters_applied == {"degree": "remote+local:first"}
    assert "1 second-instance" in (page.completeness_reason or "")


def test_tre_first_degree_document_uses_inline_text_without_pdf_url() -> None:
    payload = json.loads((ROOT / "tre_sjur_first_degree_success.json").read_text(encoding="utf-8"))
    provider = TreSjurFirstDegreeProvider(NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-MG")

    def request(request: object) -> TransportResponse:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-mg/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-mg/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="sentenÃ§a", page_size=2))
    document = provider.get_document(page.results[0].id)

    assert document.content_type == "text/plain"
    assert document.text
    assert document.raw_metadata.get("fallback") == "official_search_inline_text"
    assert document.access_status == AccessStatus.PUBLIC


def test_tre_first_degree_uses_official_remote_type_filter() -> None:
    payload = json.loads((ROOT / "tse_sjur_empty.json").read_text(encoding="utf-8"))
    provider = TreSjurFirstDegreeProvider(NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP")
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="sentença", page_size=1))

    assert page.is_explicit_empty
    assert page.total_known is True
    assert page.filters_applied == {"degree": "remote:first"}
    body = calls[0].json_body  # type: ignore[attr-defined]
    dsl = json.loads(body["termoPesquisa"])
    assert {"terms": {"descricaoTipoDecisao.keyword": ["Sentença"]}} in dsl["bool"]["filter"]


def test_tre_first_degree_does_not_report_second_only_window_as_empty() -> None:
    payload = json.loads((ROOT / "tse_sjur_success.json").read_text(encoding="utf-8"))
    payload["content"][0]["descricaoTipoDecisao"] = "Acordao"
    payload["totalRegistros"] = 1
    provider = TreSjurFirstDegreeProvider(NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP")

    def request(request: object) -> TransportResponse:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="sentença", page_size=1))

    assert page.results == []
    assert page.total == 0
    assert page.total_known is False
    assert page.is_complete is False
    assert "does not prove an empty" in (page.completeness_reason or "")


def test_tre_second_degree_uses_official_remote_type_filter() -> None:
    payload = json.loads((ROOT / "tse_sjur_empty.json").read_text(encoding="utf-8"))
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="acórdão", page_size=1))

    assert page.is_explicit_empty
    assert page.total_known is True
    assert page.filters_applied == {"degree": "remote:second"}
    body = calls[0].json_body  # type: ignore[attr-defined]
    dsl = json.loads(body["termoPesquisa"])
    assert {
        "terms": {
            "descricaoTipoDecisao.keyword": [
                "Acórdão",
                "Decisão monocrática",
                "Resolução",
                "Decisão sem resolução",
            ]
        }
    } in dsl["bool"]["filter"]


def test_tre_document_type_filter_translates_to_official_label() -> None:
    payload = json.loads((ROOT / "tse_sjur_success.json").read_text(encoding="utf-8"))
    payload["content"][0]["descricaoTipoDecisao"] = "Acordão"
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(
        JurisprudenceQuery(text="divórcio", document_type="acordão", page_size=1)
    )

    assert page.results[0].degree == "second"
    body = calls[0].json_body  # type: ignore[attr-defined]
    dsl = json.loads(body["termoPesquisa"])
    assert {"terms": {"descricaoTipoDecisao.keyword": ["Acórdão"]}} in dsl["bool"]["filter"]


def test_tre_types_filter_translates_multiple_official_labels() -> None:
    payload = json.loads((ROOT / "tse_sjur_empty.json").read_text(encoding="utf-8"))
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(
        JurisprudenceQuery(text="eleição", types=["acordao", "resolucao"], page_size=1)
    )

    assert page.is_explicit_empty
    assert page.filters_applied == {"degree": "remote:second", "types": "remote"}
    body = calls[0].json_body  # type: ignore[attr-defined]
    dsl = json.loads(body["termoPesquisa"])
    assert {
        "terms": {
            "descricaoTipoDecisao.keyword": [
                "Acórdão",
                "Resolução",
            ]
        }
    } in dsl["bool"]["filter"]


def test_tre_capabilities_declare_types_as_native() -> None:
    capabilities = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    ).get_capabilities()

    assert "types" in capabilities.supported_filters
    assert capabilities.filter_status("types") == "native"
    assert "types" not in capabilities.unsupported_filters


def test_tre_rejects_conflicting_scalar_and_types_filters() -> None:
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )

    with pytest.raises(QueryRejectedError, match="precisam representar o mesmo tipo"):
        provider.search(
            JurisprudenceQuery(text="eleição", document_type="acordao", types=["resolucao"])
        )


def test_tre_document_type_filter_rejects_incompatible_degree() -> None:
    provider = TreSjurFirstDegreeProvider(NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP")

    with pytest.raises(QueryRejectedError, match="primeiro grau"):
        provider.search(JurisprudenceQuery(text="sentença", document_type="acordao"))


def test_tre_official_spa_filters_are_translated_and_preserved() -> None:
    payload = json.loads((ROOT / "tse_sjur_empty.json").read_text(encoding="utf-8"))
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )
    calls: list[object] = []

    def request(request: object) -> TransportResponse:
        calls.append(request)
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    query = JurisprudenceQuery(
        text="divórcio",
        case_class="RC",
        rapporteur="Maria Silva",
        party_name="João da Silva",
        judgment_date_from="2024-01-02",
        judgment_date_to="2024-02-03",
        published_from="04/03/2024",
        published_to="2024-04-05",
        document_type="acordao",
        page_size=1,
    )
    page = provider.search(query)

    assert page.is_explicit_empty
    assert page.filters_applied == {
        "degree": "remote:second",
        "case_class": "remote",
        "rapporteur": "remote",
        "party_name": "remote",
        "judgment_date_from": "remote",
        "judgment_date_to": "remote",
        "published_from": "remote",
        "published_to": "remote",
        "document_type": "remote",
    }
    body = calls[0].json_body  # type: ignore[attr-defined]
    dsl = json.loads(body["termoPesquisa"])
    assert {"terms": {"siglaTribunalJE.keyword": ["TRE-SP"]}} in dsl["bool"]["filter"]
    assert {"terms": {"siglaClasse.keyword": ["RC"]}} in dsl["bool"]["filter"]
    assert {"range": {"dataDecisao": {"gte": "02/01/2024", "lte": "03/02/2024"}}} in dsl["bool"][
        "filter"
    ]
    assert {
        "range": {"publicacoes.dataPublicacao": {"gte": "04/03/2024", "lte": "05/04/2024"}}
    } in dsl["bool"]["filter"]
    assert {
        "query_string": {
            "query": "Maria Silva",
            "fields": ["relatores.nome"],
            "default_operator": "AND",
        }
    } in dsl["bool"]["must"]
    assert {
        "query_string": {
            "query": "João da Silva",
            "fields": ["partes.nomeParte"],
            "default_operator": "AND",
        }
    } in dsl["bool"]["must"]


def test_tre_rejects_unproven_filter_before_network() -> None:
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )

    def unexpected(_: object) -> TransportResponse:
        raise AssertionError("filtro não comprovado não deve chamar a fonte")

    provider.transport.request = unexpected  # type: ignore[method-assign]
    with pytest.raises(QueryRejectedError, match="legal_area"):
        provider.search(JurisprudenceQuery(text="eleição", legal_area="eleitoral"))


def test_build_tse_query_uses_ui_field_paths_for_supported_filters() -> None:
    dsl = build_tse_query(
        JurisprudenceQuery(
            text="eleição",
            case_class="RC",
            rapporteur="Relator",
            party_name="Parte",
            judgment_date_from="2024-01-01",
            published_to="31/12/2024",
        )
    )
    assert {"terms": {"siglaClasse.keyword": ["RC"]}} in dsl["bool"]["filter"]
    assert {"range": {"dataDecisao": {"gte": "01/01/2024"}}} in dsl["bool"]["filter"]
    assert {"range": {"publicacoes.dataPublicacao": {"lte": "31/12/2024"}}} in dsl["bool"]["filter"]


def test_build_tse_query_translates_ui_word_refinements() -> None:
    dsl = build_tse_query(
        JurisprudenceQuery(
            all_words="responsabilidade civil",
            any_words="administrativa gestão",
            without_words="tributária",
        )
    )

    must_queries = [item["query_string"]["query"] for item in dsl["bool"]["must"]]
    assert len(must_queries) == 1
    assert "responsabilidade AND civil" in must_queries[0]
    assert "(administrativa OR gestão)" in must_queries[0]
    assert dsl["bool"]["must_not"] == [
        {
            "query_string": {
                "query": "tributária",
                "fields": [
                    "indexacoes",
                    "textoEmenta",
                    "textoDecisao",
                    "descricaoClasse",
                    "descricaoTipoDecisao",
                    "numeroProcesso",
                    "numeroDecisao",
                    "numeroUnico",
                    "numeroUnicoFormatado",
                    "partes.nomeParte",
                    "relatores.nome",
                    "referenciasLegislativas.legislacao",
                    "referenciasLegislativas.dispositivos.dispositivo",
                    "textoObservacaoGeral",
                    "textoObservacaoLegado",
                ],
                "default_operator": "AND",
            }
        }
    ]


def test_tre_capabilities_declare_word_refinements_as_translated() -> None:
    capabilities = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    ).get_capabilities()

    for name in ("all_words", "any_words", "without_words"):
        assert name in capabilities.supported_filters
        assert capabilities.filter_status(name) == "translated"
        assert name not in capabilities.unsupported_filters


def test_tre_first_degree_family_is_opt_in_and_authority_scoped() -> None:
    default = NanoJurisClient()
    candidate = NanoJurisClient(include_candidate_providers=True)
    assert "tre_sjur_first_degree" in default.providers
    assert "tre_sjur_first_degree" in candidate.providers
    family = candidate.providers["tre_sjur_first_degree"]
    assert isinstance(family, TreSjurFirstDegreeFamilyProvider)
    assert family.get_capabilities().supports_unified_search is False
    assert family.get_capabilities().semantic_discriminator.endswith(
        "degree=first;instance=first;collection=SJUR"
    )
    assert family.get_capabilities().filter_status("degree") == "validated_scope"
    assert family.get_capabilities().filter_status("document_type") == "native"
    assert all(
        f"tre_{state.casefold()}_sjur_first_degree" in candidate.providers
        for state in (
            "AC",
            "AL",
            "AP",
            "AM",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MG",
            "MS",
            "MT",
            "PA",
            "PB",
            "PE",
            "PI",
            "PR",
            "RJ",
            "RN",
            "RO",
            "RR",
            "RS",
            "SC",
            "SE",
            "TO",
            "SP",
        )
    )


def test_tre_family_normalizes_page_source_to_registered_family() -> None:
    family = TreSjurJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))

    class StubProvider:
        def search(self, query: JurisprudenceQuery) -> SearchPage:
            return SearchPage(
                source="tre_sp_sjur_jurisprudencia",
                total=0,
                start=0,
                end=0,
                page=query.page,
                page_size=query.page_size,
                results=[],
                source_trace=SourceTrace(
                    provider="tre_sp_sjur_jurisprudencia", endpoint="POST /simples"
                ),
            )

        def search_partitioned(
            self, query: JurisprudenceQuery, *, max_partitions: int
        ) -> SearchPage:
            assert max_partitions == 12
            return self.search(query)

    family._providers["TRE-SP"] = StubProvider()  # type: ignore[assignment]
    page = family.search(JurisprudenceQuery(text="divórcio", authority="TRE-SP"))

    assert page.source == "tre_sjur_jurisprudencia"
    assert page.source_trace is not None
    assert page.source_trace.provider == "tre_sjur_jurisprudencia"
    assert page.source_trace.transformations[-1] == "family_authority=TRE-SP"

    partitioned = family.search_partitioned(
        JurisprudenceQuery(text="divÃ³rcio", authority="TRE-SP"), max_partitions=12
    )
    assert partitioned.source == "tre_sjur_jurisprudencia"
    assert partitioned.source_trace is not None
    assert partitioned.source_trace.provider == "tre_sjur_jurisprudencia"


def test_tre_family_explicit_authority_batch_preserves_per_uf_status() -> None:
    family = TreSjurJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))

    class StubProvider:
        def __init__(self, authority: str) -> None:
            self.authority = authority

        def search(self, query: JurisprudenceQuery) -> SearchPage:
            result = JurisprudenceResult(
                id=f"{self.authority}-1",
                source="tre_sjur_jurisprudencia",
                court=self.authority,
                type="Acórdão",
                summary="Decisão eleitoral",
                authority=self.authority,
                degree="second",
                instance="second",
            )
            return SearchPage(
                source="tre_sjur_jurisprudencia",
                total=1,
                start=1,
                end=1,
                page=query.page,
                page_size=query.page_size,
                results=[result],
                source_trace=SourceTrace(
                    provider="tre_sjur_jurisprudencia", endpoint="POST /simples"
                ),
                total_known=False,
                is_complete=False,
            )

    family._providers["TRE-SP"] = StubProvider("TRE-SP")  # type: ignore[assignment]
    family._providers["TRE-RJ"] = StubProvider("TRE-RJ")  # type: ignore[assignment]
    page = family.search_authorities(
        JurisprudenceQuery(text="direito"), ["TRE-SP", "TRE-RJ", "TRE-SP"]
    )

    assert page.source == "tre_sjur_jurisprudencia"
    assert [result.authority for result in page.results] == ["TRE-SP", "TRE-RJ"]
    assert page.pagination_mode == "authority_batch"
    assert page.total_known is False
    assert page.is_complete is False
    assert page.aggregations["authority_batch"] == ["TRE-SP", "TRE-RJ"]
    assert page.aggregations["authority_trace"]["TRE-SP"]["trace_status"] == "available"
    assert page.aggregations["authority_trace"]["TRE-RJ"]["trace_status"] == "available"
    assert "query" not in page.aggregations["authority_trace"]["TRE-SP"]
    assert all(
        outcome["status"] == "success_with_results"
        for outcome in page.aggregations["authority_status"].values()
    )


def test_tre_family_authority_batch_requires_explicit_authorities() -> None:
    family = TreSjurJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError, match="ao menos uma authority"):
        family.search_authorities(JurisprudenceQuery(text="direito"), [])

    with pytest.raises(QueryRejectedError, match="nao aceita authority"):
        family.search_authorities(
            JurisprudenceQuery(text="direito", authority="TRE-SP"), ["TRE-RJ"]
        )


def test_tre_family_authority_batch_keeps_source_failure_out_of_empty_state() -> None:
    family = TreSjurJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))

    class UnavailableProvider:
        def search(self, query: JurisprudenceQuery) -> SearchPage:
            del query
            raise SourceUnavailableError("rota oficial indisponivel")

    family._providers["TRE-RR"] = UnavailableProvider()  # type: ignore[assignment]
    page = family.search_authorities(JurisprudenceQuery(text="direito"), ["TRE-RR"])

    assert page.results == []
    assert page.is_explicit_empty is False
    assert page.total_known is False
    assert page.aggregations["authority_status"]["TRE-RR"]["status"] == "source_unavailable"
    assert page.aggregations["authority_trace"]["TRE-RR"] == {
        "trace_status": "unavailable",
        "status": "source_unavailable",
    }
    assert "TRE-RR=source_unavailable" in (page.access_reason or "")


def test_tre_degree_classifier_handles_replacement_character_without_guessing() -> None:
    assert _infer_tre_degree("Ac�rd�o") == "second"
    assert _infer_tre_degree("Decis�o monocr�tica") == "second"
    assert _infer_tre_degree("Senten�a") == "first"
    assert _infer_tre_degree("Ato sem classifica��o") is None


def test_tre_pagination_fixture_keeps_remote_total_unresolved() -> None:
    payload = json.loads((ROOT / "tre_sjur_pagination_duplicate.json").read_text(encoding="utf-8"))
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )

    def request(request: object) -> TransportResponse:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search(JurisprudenceQuery(text="divórcio", page=1, page_size=10))

    assert page.pagination_mode == "none"
    assert page.total == 1
    assert page.total_known is False
    assert page.is_complete is False
    assert page.results[0].id == "tre_sp_sjur_jurisprudencia-617075"


def test_tre_provider_rejects_unverified_remote_pages() -> None:
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )

    with pytest.raises(QueryRejectedError, match="pagina remota comprovada"):
        provider.search(JurisprudenceQuery(text="divÃ³rcio", page=2))


def test_tre_date_partition_collection_marks_bounded_month_complete() -> None:
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )
    payload = {
        "totalRegistros": 2,
        "content": [
            {
                "codigoDecisao": 101,
                "descricaoTipoDecisao": "Acórdão",
                "descricaoClasse": "RECURSO",
                "textoEmenta": "<p>Direito eleitoral</p>",
                "dataDecisao": "15/01/2025",
            },
            {
                "codigoDecisao": 102,
                "descricaoTipoDecisao": "Acórdão",
                "descricaoClasse": "RECURSO",
                "textoEmenta": "<p>Propaganda eleitoral</p>",
                "dataDecisao": "20/01/2025",
            },
        ],
    }

    def request(request: object) -> TransportResponse:
        del request
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return TransportResponse(
            status_code=200,
            url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            final_url="https://sjur-pesquisa-api.tse.jus.br/tre-sp/sjur-pesquisa-backend/rest/public/pesquisa/simples",
            headers={"Content-Type": "application/json"},
            body=body,
            elapsed_ms=2.0,
        )

    provider.transport.request = request  # type: ignore[method-assign]
    page = provider.search_partitioned(
        JurisprudenceQuery(
            text="direito",
            judgment_date_from="2025-01-01",
            judgment_date_to="2025-01-31",
        )
    )

    assert page.pagination_mode == "date_partition"
    assert page.total == 2
    assert page.total_known is True
    assert page.is_complete is True
    assert page.source_trace is not None
    assert page.source_trace.query["date_partition_count"] == 1


def test_tre_date_partition_requires_bounded_explicit_range() -> None:
    provider = TreSjurJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), tribunal="TRE-SP"
    )

    with pytest.raises(QueryRejectedError, match="judgment_date_from"):
        provider.search_partitioned(JurisprudenceQuery(text="direito"))

    with pytest.raises(QueryRejectedError, match="limite de particoes"):
        provider.search_partitioned(
            JurisprudenceQuery(
                text="direito",
                judgment_date_from="2020-01-01",
                judgment_date_to="2025-01-31",
            )
        )


def test_tre_family_is_runtime_discoverable_but_uf_adapters_are_opt_in() -> None:
    default = NanoJurisClient()
    candidate = NanoJurisClient(include_candidate_providers=True)
    expected = {
        f"tre_{state.casefold()}_sjur_jurisprudencia"
        for state in (
            "AC",
            "AL",
            "AP",
            "AM",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MG",
            "MS",
            "MT",
            "PA",
            "PB",
            "PE",
            "PI",
            "PR",
            "RJ",
            "RN",
            "RO",
            "RR",
            "RS",
            "SC",
            "SE",
            "TO",
            "SP",
        )
    }
    assert "tre_sjur_jurisprudencia" in default.providers
    assert expected.isdisjoint(default.providers)
    assert expected <= candidate.providers.keys()
    assert all(
        candidate.providers[name].get_capabilities().supports_unified_search is False
        for name in expected
    )
    assert default.providers["tre_sjur_jurisprudencia"].get_capabilities().opt_in_unified_search


def test_tre_provider_rejects_non_tre_scope() -> None:
    try:
        TreSjurJurisprudenciaProvider(tribunal="TSE")
    except ValueError as exc:
        assert "TRE-XX" in str(exc)
    else:  # pragma: no cover - assertion helper
        raise AssertionError("TSE não deve ser aceito pelo provider de TRE")


def test_tre_family_requires_explicit_authority() -> None:
    provider = TreSjurJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(QueryRejectedError, match="authority explicita"):
        provider.search(JurisprudenceQuery(text="divÃ³rcio"))


def test_tre_provider_rejects_unknown_regional_authority() -> None:
    with pytest.raises(ValueError, match="27 UFs"):
        TreSjurJurisprudenciaProvider(tribunal="TRE-XX")

    family = TreSjurJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError, match="27 UFs"):
        family.search(JurisprudenceQuery(text="eleicao", authority="TRE-XX"))


def test_tre_family_exposes_one_opt_in_binding_and_scopes_authority() -> None:
    provider = TreSjurJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))
    capabilities = provider.get_capabilities()

    assert provider.name == "tre_sjur_jurisprudencia"
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert "authority" in capabilities.supported_filters
    assert len(provider.get_parameters()["authorities"]) == 27


def test_tre_degree_classifier_does_not_guess_unvalidated_categories() -> None:
    assert _infer_tre_degree("Consulta") is None
    assert _infer_tre_degree("Instrucao") is None
