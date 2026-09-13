from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.trt8_pje_jurisprudencia import Trt8PjeJurisprudenciaProvider

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> object:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class _Response:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self.content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.url = "https://pje.trt8.jus.br/juris-backend/api/documentos"

    def json(self) -> object:
        return json.loads(self.text)


class _Session:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> _Response:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        assert isinstance(response, _Response)
        response.url = url
        return response


def _provider(*responses: object) -> Trt8PjeJurisprudenciaProvider:
    return Trt8PjeJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), _Session(list(responses))
    )


def test_search_constrains_and_parses_second_degree_appellate_records() -> None:
    provider = _provider(_Response(_fixture("trt8_pje_success.json")))

    page = provider.search(
        JurisprudenceQuery(
            text="responsabilidade civil",
            degree="second",
            instance="second",
            document_type="acordao",
            page_size=10,
        )
    )

    result = page.results[0]
    assert page.total == 2
    assert page.total_known is True
    assert result.authority == "TRT8"
    assert result.branch == "labor"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "CJSG"
    assert result.document_type == "acordao"
    assert result.case_class == "Recurso Ordinário"
    assert result.summary == "Responsabilidade civil. Dano moral trabalhista."
    assert page.filters_applied["degree"] == "validated_scope"


def test_page_two_and_detail_preserve_full_text() -> None:
    provider = _provider(
        _Response(_fixture("trt8_pje_page2.json")),
        _Response(_fixture("trt8_pje_detail.json")),
    )
    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=1))
    assert page.page == 2
    assert page.start == 2
    assert page.results[0].id == "trt8-pje2_1002"

    document = provider.get_document("trt8-pje2_1001")
    assert document.access_status.value == "public"
    assert document.extraction_status.value == "complete"
    assert "Conhecido e parcialmente provido" in (document.text or "")


def test_authoritative_empty_is_distinct_from_external_states() -> None:
    provider = _provider(_Response(_fixture("trt8_pje_empty.json")))
    page = provider.search(JurisprudenceQuery(text="termo inexistente"))
    assert page.results == []
    assert page.total == 0
    assert page.total_known is True
    assert page.is_explicit_empty is True

    blocked = _provider(_Response(_fixture("trt8_pje_blocked.json")))
    with pytest.raises(AccessControlRequiredError):
        blocked.search(JurisprudenceQuery(text="dano"))

    invalid = _provider(_Response(_fixture("trt8_pje_schema_invalid.json")))
    with pytest.raises(ParserContractChangedError):
        invalid.search(JurisprudenceQuery(text="dano"))


def test_query_rejects_first_degree_and_unsupported_filters() -> None:
    provider = Trt8PjeJurisprudenciaProvider()
    with pytest.raises(Exception, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="x", degree="first"))
    with pytest.raises(Exception, match="nao suporta"):
        provider.search(JurisprudenceQuery(text="x", legal_area="civil"))


def test_capabilities_are_promoted_after_live_contract_gates() -> None:
    capabilities = Trt8PjeJurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_full_text is True
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert capabilities.filter_status("case_class") == "native"
    assert capabilities.filter_status("degree") == "validated_scope"


def test_client_exposes_trt8_in_default_federation() -> None:
    client = NanoJurisClient()
    assert "trt8_pje_jurisprudencia" in client.providers
    assert "trt8_pje_jurisprudencia" in client._default_unified_sources()


def test_transport_failure_is_not_empty() -> None:
    provider = _provider(requests.RequestException("offline"))
    with pytest.raises(SourceUnavailableError):
        provider.search(JurisprudenceQuery(text="direito"))
