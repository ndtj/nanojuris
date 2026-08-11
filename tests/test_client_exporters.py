from __future__ import annotations

import pytest
import requests

from nanojuris.canonical import (
    result_to_canonical_decision,
    result_to_canonical_precedent,
    search_page_to_canonical,
)
from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import SourceUnavailableError, UnsupportedProviderError
from nanojuris.exporters import (
    decisions_to_csv,
    documents_to_csv,
    precedents_to_csv,
    search_page_to_markdown,
    to_canonical_jsonl,
    to_csv,
    to_jsonl,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDecision,
    CanonicalDocument,
    CanonicalPrecedent,
    DecisionBundle,
    ExtractionStatus,
    ExtractionTrace,
    JurisprudenceQuery,
    JurisprudenceResult,
    ParadigmCase,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.bnp_pangea import BnpPangeaProvider
from nanojuris.store import SQLiteStore


class FakeProvider:
    name = "fake"

    def __init__(self):
        self.query = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self.query = query
        return SearchPage(
            source="fake",
            total=1,
            start=1,
            end=1,
            page=query.page,
            page_size=query.page_size,
            results=[
                JurisprudenceResult(
                    id="fake-1",
                    source="fake",
                    court="STF",
                    type="RG",
                    number=1,
                    question="Questao",
                    thesis="Tese",
                )
            ],
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(precedent_id=precedent_id, source="fake")

    def get_document(self, document_id: str) -> CanonicalDocument:
        return CanonicalDocument(
            id=document_id,
            source="fake",
            document_type="acordao",
            content_type="text/html",
            text="Inteiro teor publico",
        )

    def get_parameters(self):
        return {"ok": True}

    def get_catalog(self):
        return ProviderCatalog(
            source="fake",
            courts=[ProviderOption(code="STF", description="Supremo Tribunal Federal")],
            species=[ProviderOption(code="RG", description="Tema de Repercussao Geral")],
        )

    def get_capabilities(self):
        return ProviderCapabilities(
            source="fake",
            display_name="Fonte Fake",
            source_url="https://example.test",
            category="jurisprudence",
            search_modes=["text"],
            canonical_records=["CanonicalPrecedent"],
        )

    def list_suggestions(self, text):
        return [text, f"{text} sugestao"]


class FailingProvider:
    name = "failing"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        raise RuntimeError("fonte indisponivel")

    def get_capabilities(self):
        return ProviderCapabilities(
            source="failing",
            display_name="Fonte Falha",
            source_url="https://example.test/failing",
            category="court_jurisprudence",
            search_modes=["text"],
            canonical_records=["CanonicalDecision"],
            supports_mcp=True,
            supported_filters=["text"],
        )


class ProxyFailingProvider:
    name = "proxy_failing"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        proxy_error = requests.exceptions.ProxyError("Unable to connect to proxy")
        raise SourceUnavailableError("provider request failed") from proxy_error

    def get_capabilities(self):
        return ProviderCapabilities(
            source="proxy_failing",
            display_name="Fonte com proxy local invalido",
            source_url="https://example.test/proxy",
            category="court_jurisprudence",
            search_modes=["text"],
            canonical_records=["CanonicalDecision"],
            supports_mcp=True,
        )


class CaseLookupProvider:
    name = "case_lookup"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return SearchPage(
            source="case_lookup",
            total=1,
            start=1,
            end=1,
            page=query.page,
            page_size=query.page_size,
            results=[
                JurisprudenceResult(
                    id="case-1",
                    source="case_lookup",
                    court="TJSP",
                    type="processo",
                    number=query.number,
                )
            ],
        )

    def get_capabilities(self):
        return ProviderCapabilities(
            source="case_lookup",
            display_name="Consulta Processual",
            source_url="https://example.test/case",
            category="case_lookup",
            search_modes=["case_number"],
            canonical_records=["CanonicalDecision"],
            supports_mcp=True,
        )


class CommunicationsProvider:
    name = "communications"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        raise AssertionError("communications should be skipped for jurisprudence search")

    def get_capabilities(self):
        return ProviderCapabilities(
            source="communications",
            display_name="Comunicacoes Judiciais",
            source_url="https://example.test/communications",
            category="judicial_communications",
            search_modes=["text"],
            canonical_records=["CanonicalDecision"],
            supports_mcp=True,
        )


def test_client_builds_query_for_provider():
    provider = FakeProvider()
    client = NanoJurisClient(providers=[provider])

    page = client.search("ICMS", source="fake", courts=["STF"], types=["RG"], page=3, page_size=7)

    assert page.total == 1
    assert provider.query is not None
    assert provider.query.text == "ICMS"
    assert provider.query.courts == ["STF"]
    assert provider.query.types == ["RG"]
    assert provider.query.page == 3
    assert provider.query.page_size == 7


def test_client_search_canonical_and_store_workflow():
    provider = FakeProvider()
    client = NanoJurisClient(providers=[provider])
    store = SQLiteStore(":memory:")

    records = client.search_canonical("ICMS", source="fake")
    stored_records = client.search_and_store("ICMS", source="fake", store=store)

    assert isinstance(records[0], CanonicalPrecedent)
    assert stored_records[0].id == "fake-1"
    assert store.count(kind="precedent") == 1
    assert store.get("precedent", "fake-1")["court"] == "STF"


def test_client_search_many_unifies_results_and_keeps_source_errors():
    client = NanoJurisClient(providers=[FakeProvider(), FailingProvider()])

    payload = client.search_many("ICMS", sources=["fake", "failing"])

    assert payload["sources"] == ["fake", "failing"]
    assert payload["total_returned"] == 1
    assert isinstance(payload["results"][0], CanonicalPrecedent)
    assert payload["errors"] == [
        {
            "source": "failing",
            "error_type": "RuntimeError",
            "message": "fonte indisponivel",
        }
    ]
    assert payload["routing_summary"] == [
        {
            "source": "fake",
            "action": "searched",
            "reason": "source_applicable",
            "message": "A fonte foi consultada por cobrir jurisprudencia textual publica.",
        },
        {
            "source": "failing",
            "action": "failed",
            "reason": "RuntimeError",
            "message": "fonte indisponivel",
        },
    ]


def test_default_unified_sources_include_all_jurisprudence_categories():
    client = NanoJurisClient(
        providers=[
            FakeProvider(),
            FailingProvider(),
            CaseLookupProvider(),
            CommunicationsProvider(),
        ]
    )

    assert client._default_unified_sources() == ["failing", "fake"]


def test_client_search_many_classifies_proxy_configuration_errors():
    client = NanoJurisClient(providers=[ProxyFailingProvider()])

    payload = client.search_many("incidente", sources=["proxy_failing"])

    assert payload["total_returned"] == 0
    assert payload["errors"] == [
        {
            "source": "proxy_failing",
            "error_type": "NetworkConfigurationError",
            "message": (
                "A configuracao local de proxy impediu a conexao com a fonte publica. "
                "A busca foi roteada corretamente, mas nao conseguiu acessar a internet."
            ),
            "hint": (
                "Verifique HTTP_PROXY, HTTPS_PROXY, ALL_PROXY ou rode o Studio com "
                "--ignore-env-proxy quando o proxy local estiver invalido."
            ),
        }
    ]
    assert payload["routing_summary"] == [
        {
            "source": "proxy_failing",
            "action": "failed",
            "reason": "NetworkConfigurationError",
            "message": (
                "A configuracao local de proxy impediu a conexao com a fonte publica. "
                "A busca foi roteada corretamente, mas nao conseguiu acessar a internet."
            ),
        }
    ]


def test_config_can_disable_requests_environment_proxy(monkeypatch):
    monkeypatch.setenv("NANOJURIS_TRUST_ENV", "0")

    config = NanoJurisConfig()
    provider = BnpPangeaProvider(config)

    assert config.trust_env is False
    assert provider.session.trust_env is False


def test_client_search_many_reports_skipped_sources_by_semantic_reason():
    client = NanoJurisClient(
        providers=[FakeProvider(), CaseLookupProvider(), CommunicationsProvider()]
    )

    payload = client.search_many(
        "idpj",
        sources=["fake", "case_lookup", "communications"],
    )

    assert payload["sources"] == ["fake", "case_lookup", "communications"]
    assert payload["searched_sources"] == ["fake"]
    assert payload["total_returned"] == 1
    assert payload["skipped_sources"] == [
        {
            "source": "case_lookup",
            "category": "case_lookup",
            "reason": "case_lookup_requires_identifier",
            "message": (
                "Consulta processual exige numero CNJ, parte, documento, OAB "
                "ou outro identificador; nao e uma busca textual de jurisprudencia."
            ),
        },
        {
            "source": "communications",
            "category": "judicial_communications",
            "reason": "not_jurisprudence_source",
            "message": (
                "A fonte retorna comunicacoes/intimacoes judiciais, nao julgados "
                "de jurisprudencia para estudo jurimetrico."
            ),
        },
    ]
    assert payload["routing_summary"] == [
        {
            "source": "fake",
            "action": "searched",
            "reason": "source_applicable",
            "message": "A fonte foi consultada por cobrir jurisprudencia textual publica.",
        },
        {
            "source": "case_lookup",
            "action": "skipped",
            "reason": "case_lookup_requires_identifier",
            "message": (
                "Consulta processual exige numero CNJ, parte, documento, OAB "
                "ou outro identificador; nao e uma busca textual de jurisprudencia."
            ),
        },
        {
            "source": "communications",
            "action": "skipped",
            "reason": "not_jurisprudence_source",
            "message": (
                "A fonte retorna comunicacoes/intimacoes judiciais, nao julgados "
                "de jurisprudencia para estudo jurimetrico."
            ),
        },
    ]


def test_client_search_many_allows_case_lookup_when_identifier_is_present():
    client = NanoJurisClient(providers=[FakeProvider(), CaseLookupProvider()])

    payload = client.search_many(
        "0003938-14.2017.8.26.0323",
        sources=["fake", "case_lookup"],
        number="0003938-14.2017.8.26.0323",
        canonical=False,
    )

    assert payload["searched_sources"] == ["fake", "case_lookup"]
    assert payload["skipped_sources"] == []
    assert payload["total_returned"] == 2


def test_client_search_many_skips_jurisprudence_sources_without_identifier_contract():
    client = NanoJurisClient(providers=[FailingProvider()])

    payload = client.search_many(
        "0802253-46.2017.8.15.2003",
        sources=["failing"],
        number="0802253-46.2017.8.15.2003",
    )

    assert payload["searched_sources"] == []
    assert payload["errors"] == []
    assert payload["skipped_sources"] == [
        {
            "source": "failing",
            "category": "court_jurisprudence",
            "reason": "identifier_filter_not_supported",
            "message": (
                "A fonte nao declara suporte ao filtro identificador: number. "
                "Ela foi pulada para evitar resultados textuais sem correspondencia exata."
            ),
        }
    ]


def test_client_search_and_store_run_returns_saved_run():
    provider = FakeProvider()
    client = NanoJurisClient(providers=[provider])
    store = SQLiteStore(":memory:")

    run = client.search_and_store_run("ICMS", source="fake", store=store, label="Temas ICMS")

    assert run.id.startswith("run-")
    assert run.label == "Temas ICMS"
    assert run.record_count == 1
    assert store.get_research_run(run.id)["query"]["text"] == "ICMS"
    assert store.get_research_run_records(run.id)[0]["id"] == "fake-1"


def test_client_delegates_decisions_and_parameters():
    provider = FakeProvider()
    client = NanoJurisClient(providers=[provider])

    assert client.get_decisions("fake-1", source="fake").precedent_id == "fake-1"
    assert client.get_document("doc-1", source="fake").text == "Inteiro teor publico"
    assert client.get_parameters(source="fake") == {"ok": True}
    assert client.get_catalog(source="fake").courts[0].code == "STF"
    assert client.get_capabilities(source="fake").display_name == "Fonte Fake"
    assert client.list_sources()[0].source == "fake"
    assert client.list_suggestions("icms", source="fake") == ["icms", "icms sugestao"]


def test_client_rejects_unknown_provider():
    client = NanoJurisClient(providers=[FakeProvider()])

    with pytest.raises(UnsupportedProviderError):
        client.search("ICMS", source="missing")


def test_exporters_render_results():
    provider = FakeProvider()
    page = provider.search(JurisprudenceQuery(text="ICMS"))

    jsonl = to_jsonl(page)
    canonical_jsonl = to_canonical_jsonl(page)
    markdown = search_page_to_markdown(page)
    csv_output = to_csv(page)

    assert '"id": "fake-1"' in jsonl
    assert '"precedent_type": "RG"' in canonical_jsonl
    assert "# Resultados NanoJuris" in markdown
    assert "### Tese" in markdown
    assert "record_kind,id,source,court" in csv_output
    assert "precedent,fake-1,fake,STF" in csv_output


def test_markdown_renders_all_optional_sections():
    page = SearchPage(
        source="fake",
        total=1,
        start=1,
        end=1,
        page=1,
        page_size=1,
        results=[
            JurisprudenceResult(
                id="fake-2",
                source="fake",
                court="STJ",
                type="RR",
                number=2,
                question="Questao completa",
                thesis="Tese completa",
                summary="Resumo completo",
                status="Vigente",
                rapporteur="Ministro Exemplo",
                updated_at="01/01/2026",
                paradigm_cases=[
                    ParadigmCase(
                        number="123",
                        case_class="REsp",
                        url="https://example.test",
                    )
                ],
                source_trace=SourceTrace(provider="fake", endpoint="/fake"),
            )
        ],
    )

    rendered = search_page_to_markdown(page)

    assert "Ministro Exemplo" in rendered
    assert "### Resumo" in rendered
    assert "Processos paradigma" in rendered
    assert "Provider: `fake`" in rendered


def test_type_specific_csv_exporters_render_canonical_records():
    decision = CanonicalDecision(
        id="dec-1",
        source="fake",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        subject="Homicidio Qualificado",
    )
    precedent = CanonicalPrecedent(
        id="prec-1",
        source="fake",
        court="STJ",
        precedent_type="RR",
        number=1,
        paradigm_cases=[ParadigmCase(number="123")],
    )
    document = CanonicalDocument(
        id="doc-1",
        source="fake",
        document_type="acordao",
        title="Inteiro teor",
    )

    decision_csv = decisions_to_csv([decision])
    precedent_csv = precedents_to_csv([precedent])
    document_csv = documents_to_csv([document])

    assert "case_number" in decision_csv
    assert "0003938-14.2017.8.26.0323" in decision_csv
    assert "paradigm_case_count" in precedent_csv
    assert "prec-1" in precedent_csv
    assert "document_type" in document_csv
    assert "acordao" in document_csv


def test_model_to_dict_methods():
    trace = SourceTrace(provider="fake", endpoint="/fake")
    extraction = ExtractionTrace(parser="fake-parser", parser_version="1")
    case = ParadigmCase(number="123")
    result = JurisprudenceResult(id="r1", source="fake", court="STF", type="RG")
    page = SearchPage(source="fake", total=0, start=0, end=0, page=1, page_size=10, results=[])
    bundle = DecisionBundle(precedent_id="r1", source="fake")
    option = ProviderOption(code="STF", description="Supremo Tribunal Federal")
    catalog = ProviderCatalog(source="fake", courts=[option])
    capabilities = ProviderCapabilities(
        source="fake",
        display_name="Fonte Fake",
        source_url="https://example.test",
        category="jurisprudence",
    )
    document = CanonicalDocument(
        id="doc-1",
        source="fake",
        document_type="acordao",
        extraction_trace=extraction,
    )
    decision = CanonicalDecision(
        id="dec-1",
        source="fake",
        court="TJSP",
        case_number="0003938-14.2017.8.26.0323",
        extraction_trace=extraction,
    )
    precedent = CanonicalPrecedent(
        id="prec-1",
        source="fake",
        court="STJ",
        precedent_type="repetitivo",
        paradigm_cases=[case],
        extraction_trace=extraction,
    )

    assert trace.to_dict()["provider"] == "fake"
    assert extraction.to_dict()["status"] == ExtractionStatus.COMPLETE
    assert extraction.to_dict()["access_status"] == AccessStatus.PUBLIC
    assert case.to_dict()["number"] == "123"
    assert result.to_dict()["id"] == "r1"
    assert page.to_dict()["source"] == "fake"
    assert bundle.to_dict()["precedent_id"] == "r1"
    assert option.to_dict()["code"] == "STF"
    assert catalog.to_dict()["courts"][0]["code"] == "STF"
    assert capabilities.to_dict()["display_name"] == "Fonte Fake"
    assert document.to_dict()["document_type"] == "acordao"
    assert decision.to_dict()["case_number"] == "0003938-14.2017.8.26.0323"
    assert precedent.to_dict()["paradigm_cases"][0]["number"] == "123"


def test_base_provider_default_parameters():
    class MinimalProvider(JurisprudenceProvider):
        name = "minimal"

        def search(self, query):
            raise NotImplementedError

        def get_decisions(self, precedent_id):
            raise NotImplementedError

    assert MinimalProvider().get_parameters() == {}
    assert MinimalProvider().get_capabilities().source == "minimal"


def test_canonical_decision_mapping_uses_extracted_provider_fields():
    result = JurisprudenceResult(
        id="tjsp-cjsg-20787558-0",
        source="tjsp_cjsg",
        court="TJSP",
        type="acordao",
        number="0003938-14.2017.8.26.0323",
        summary="Ementa publica",
        rapporteur="Airton Vieira",
        updated_at="30/07/2026",
        source_trace=SourceTrace(provider="tjsp_cjsg", endpoint="/resultadoCompleta.do"),
        raw={
            "classe": "Apelacao Criminal",
            "assunto": "Homicidio Qualificado",
            "comarca": "Lorena",
            "orgao_julgador": "3a Camara de Direito Criminal",
            "full_text_url": "https://example.test/getArquivo.do",
        },
    )

    decision = result_to_canonical_decision(result)

    assert decision.case_number == "0003938-14.2017.8.26.0323"
    assert decision.case_class == "Apelacao Criminal"
    assert decision.subject == "Homicidio Qualificado"
    assert decision.origin_county == "Lorena"
    assert decision.judging_body == "3a Camara de Direito Criminal"
    assert decision.document_url == "https://example.test/getArquivo.do"
    assert decision.extraction_trace is not None
    assert decision.extraction_trace.parser == "tjsp_cjsg.canonical_result_mapper"


def test_canonical_precedent_mapping_uses_extracted_provider_fields():
    result = JurisprudenceResult(
        id="stf-rg-615",
        source="bnp_pangea",
        court="STF",
        type="RG",
        number=615,
        question="Questao publica",
        thesis="Tese publica",
        status="Vigente",
        paradigm_cases=[ParadigmCase(number="680089", case_class=1348)],
        source_trace=SourceTrace(provider="bnp_pangea", endpoint="/precedentes"),
    )

    precedent = result_to_canonical_precedent(result)

    assert precedent.precedent_type == "RG"
    assert precedent.number == 615
    assert precedent.question == "Questao publica"
    assert precedent.thesis == "Tese publica"
    assert precedent.paradigm_cases[0].number == "680089"
    assert precedent.extraction_trace is not None
    assert precedent.extraction_trace.parser == "bnp_pangea.canonical_result_mapper"


def test_search_page_to_canonical_splits_decisions_and_precedents():
    page = SearchPage(
        source="mixed",
        total=2,
        start=1,
        end=2,
        page=1,
        page_size=2,
        results=[
            JurisprudenceResult(
                id="decision-1",
                source="tjsp_cjsg",
                court="TJSP",
                type="acordao",
            ),
            JurisprudenceResult(
                id="decision-2",
                source="trf4_eproc_jurisprudencia",
                court="TRF4",
                type="despacho/decisao da vice-presidencia",
            ),
            JurisprudenceResult(
                id="precedent-1",
                source="bnp_pangea",
                court="STJ",
                type="RR",
            ),
        ],
    )

    canonical = search_page_to_canonical(page)

    assert isinstance(canonical[0], CanonicalDecision)
    assert isinstance(canonical[1], CanonicalDecision)
    assert isinstance(canonical[2], CanonicalPrecedent)
