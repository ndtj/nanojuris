from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, SourceUnavailableError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.eproc_jurisprudencia_federal import (
    FederalEprocJurisprudenciaFamilyProvider,
)
from nanojuris.providers.tjsp_eproc_jurisprudencia import (
    _build_payload,
    parse_eproc_jurisprudencia_results,
)
from nanojuris.providers.tnu_eproc_jurisprudencia import TnuEprocJurisprudenciaProvider
from nanojuris.providers.trf2_eproc_jurisprudencia import Trf2EprocJurisprudenciaProvider
from nanojuris.providers.trf6_eproc_jurisprudencia import Trf6EprocJurisprudenciaProvider
from nanojuris.transport import SharedHttpClient

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        text: str,
        status_code: int = 200,
        url: str = "https://eproc.example.test/eproc/externo_controlador.php",
    ):
        self.text = text
        self.status_code = status_code
        self.encoding = "iso-8859-1"
        self.url = url


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="latin-1")


@pytest.mark.parametrize(
    ("provider_cls", "fixture_name", "court", "source", "prefix", "first_number"),
    [
        (
            TnuEprocJurisprudenciaProvider,
            "tnu_eproc_aposentadoria.html",
            "TNU",
            "tnu_eproc_jurisprudencia",
            "tnu-eproc-jurisprudencia",
            "1094873-66.2021.4.01.3300",
        ),
        (
            Trf2EprocJurisprudenciaProvider,
            "trf2_eproc_aposentadoria.html",
            "TRF2",
            "trf2_eproc_jurisprudencia",
            "trf2-eproc-jurisprudencia",
            "5002335-67.2025.4.02.5001",
        ),
        (
            Trf6EprocJurisprudenciaProvider,
            "trf6_eproc_aposentadoria.html",
            "TRF6",
            "trf6_eproc_jurisprudencia",
            "trf6-eproc-jurisprudencia",
            "1008909-53.2022.4.01.9999",
        ),
    ],
)
def test_parse_federal_eproc_real_fixtures(
    provider_cls,
    fixture_name,
    court,
    source,
    prefix,
    first_number,
):
    provider = provider_cls(NanoJurisConfig(rate_limit_interval=0))
    trace = SourceTrace(provider=source, endpoint="/listar")

    results = parse_eproc_jurisprudencia_results(
        _fixture(fixture_name),
        trace=trace,
        source_url=provider.source_url,
        source=source,
        court=court,
        id_prefix=prefix,
        source_label=provider.source_label,
    )

    assert len(results) == 10
    assert results[0].source == source
    assert results[0].court == court
    assert results[0].number == first_number
    assert results[0].summary
    assert results[0].raw["id_jurisprudencia"]
    assert results[0].raw["full_text_url"]


@pytest.mark.parametrize(
    ("provider_cls", "fixture_name", "source", "base_url"),
    [
        (
            TnuEprocJurisprudenciaProvider,
            "tnu_eproc_aposentadoria.html",
            "tnu_eproc_jurisprudencia",
            "https://eproctnu-jur.cjf.jus.br/eproc",
        ),
        (
            Trf2EprocJurisprudenciaProvider,
            "trf2_eproc_aposentadoria.html",
            "trf2_eproc_jurisprudencia",
            "https://eproc.trf2.jus.br/eproc",
        ),
        (
            Trf6EprocJurisprudenciaProvider,
            "trf6_eproc_aposentadoria.html",
            "trf6_eproc_jurisprudencia",
            "https://eproc-jur.trf6.jus.br/eproc",
        ),
    ],
)
def test_federal_eproc_provider_search_posts_payload_and_canonicalizes(
    provider_cls,
    fixture_name,
    source,
    base_url,
):
    session = FakeSession([FakeResponse(_fixture(fixture_name))])
    provider = provider_cls(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(
        JurisprudenceQuery(
            text="aposentadoria",
            number="1094873-66.2021.4.01.3300",
            page_size=3,
        )
    )
    canonical = search_page_to_canonical(page)

    assert page.source == source
    # The source-reported total is distinct from the current page window.
    assert page.total > len(page.results)
    assert len(page.results) == 3
    assert canonical[0].source == source
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"].startswith(base_url)
    assert call["kwargs"]["data"]["txtPesquisa"] == "aposentadoria"
    assert call["kwargs"]["data"]["txtProcesso"] == "10948736620214013300"


def test_federal_eproc_uses_shared_transport_boundary() -> None:
    provider = Trf2EprocJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    assert isinstance(provider.transport, SharedHttpClient)
    assert "eproc.trf2.jus.br" in provider.transport.policy.allowed_hosts


def test_federal_eproc_get_document_returns_public_html():
    provider = Trf2EprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse("<html>inteiro teor federal</html>")]),
    )

    document = provider.get_document("trf2-eproc-jurisprudencia-21786042808698528830162508954")

    assert document.source == "trf2_eproc_jurisprudencia"
    assert document.text == "inteiro teor federal"
    assert document.raw_bytes == b"<html>inteiro teor federal</html>"
    assert document.sha256
    assert document.byte_size == len(document.raw_bytes)
    assert document.raw_metadata["id_jurisprudencia"] == "21786042808698528830162508954"


def test_federal_eproc_detects_access_control_without_bypass():
    provider = TnuEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse("<html><div class='g-recaptcha'></div></html>")]),
    )

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_federal_eproc_classifies_http_210_maintenance_page_as_source_unavailable():
    maintenance = """
    <html><head><title>Estamos indispon&iacute;veis</title></head>
    <body>O servico sera restabelecido em breve.</body></html>
    """
    provider = TnuEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(maintenance, status_code=210)]),
    )

    with pytest.raises(SourceUnavailableError, match="temporarily unavailable"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_federal_eproc_request_exception_becomes_source_error():
    provider = Trf6EprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )

    with pytest.raises(Exception, match="TRF6/eproc jurisprudence request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_federal_eproc_uses_public_ajax_pagination_contract():
    fixture = _fixture("tnu_eproc_aposentadoria.html")
    session = FakeSession([FakeResponse(fixture), FakeResponse(fixture)])
    provider = TnuEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="teste", page=2, page_size=50))

    assert page.pagination_mode == "page"
    assert len(session.calls) == 2
    assert "ajax_paginar_resultado" in session.calls[1]["url"]
    assert session.calls[1]["kwargs"]["data"]["hdnPaginaAtual"] == "2"
    assert session.calls[1]["kwargs"]["data"]["selTamanhoPagina"] == "50"


def test_federal_eproc_capabilities_describe_instances():
    tnu = TnuEprocJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    trf2 = Trf2EprocJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    trf6 = Trf6EprocJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    assert tnu.get_capabilities().source == "tnu_eproc_jurisprudencia"
    assert trf2.get_capabilities().source_url == "https://eproc.trf2.jus.br/eproc"
    assert trf6.get_capabilities().supports_full_text is True
    assert "CanonicalDocument" in trf6.get_capabilities().canonical_records


def test_federal_eproc_translates_second_degree_to_each_official_origin():
    query = JurisprudenceQuery(text="responsabilidade civil", degree="second")
    for court in ("TRF2", "TRF4", "TRF6"):
        assert _build_payload(query, court=court)["selOrigem[]"] == ["1"]


def test_federal_eproc_family_requires_explicit_authority():
    family = FederalEprocJurisprudenciaFamilyProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(Exception, match="authority"):
        family.search(JurisprudenceQuery(text="aposentadoria"))


def test_federal_eproc_family_routes_to_existing_binding():
    fixture = _fixture("trf2_eproc_aposentadoria.html")
    session = FakeSession([FakeResponse(fixture)])
    family = FederalEprocJurisprudenciaFamilyProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = family.search(JurisprudenceQuery(text="aposentadoria", authority="TRF02", page_size=2))

    assert page.source == "trf2_eproc_jurisprudencia"
    assert len(page.results) == 2
    assert family.get_parameters()["provider_bindings"]["TRF4"] == ("trf4_eproc_jurisprudencia")
    capabilities = family.get_capabilities()
    assert capabilities.source == "eproc_jurisprudencia_federal"
    assert "authority" in capabilities.supported_filters
    assert capabilities.opt_in_unified_search is True
