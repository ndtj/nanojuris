from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjsc_eproc_jurisprudencia import TjscEprocJurisprudenciaProvider
from nanojuris.providers.tjsp_eproc_jurisprudencia import (
    _infer_degree,
    parse_eproc_jurisprudencia_results,
)
from nanojuris.providers.trf4_eproc_jurisprudencia import Trf4EprocJurisprudenciaProvider

FIXTURES = Path(__file__).parent / "fixtures"
TJRJ_FIXTURE = FIXTURES / "tjrj_eproc_jurisprudencia_result.html"


class FakeResponse:
    def __init__(self, text: str, url: str) -> None:
        self.text = text
        self.status_code = 200
        self.encoding = "iso-8859-1"
        self.url = url


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.response


def test_tjrj_eproc_uses_own_endpoint_and_court() -> None:
    session = FakeSession(
        FakeResponse(
            TJRJ_FIXTURE.read_text(encoding="utf-8"),
            "https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php",
        )
    )
    provider = TjrjEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.source == "tjrj_eproc_jurisprudencia"
    assert page.results[0].court == "TJRJ"
    assert page.results[0].id.startswith("tjrj-eproc-jurisprudencia-")
    assert page.results[0].number == "0000000-00.2026.8.19.0001"
    assert page.results[0].raw["state"] == "RJ"
    assert "DANO MORAL" in (page.results[0].summary or "")
    assert session.calls[0]["method"] == "POST"
    assert "eproc1g.tjrj.jus.br" in str(session.calls[0]["url"])
    assert provider.get_capabilities().source_url.endswith("/eproc")


def test_eproc_translates_second_degree_query_to_source_origin() -> None:
    session = FakeSession(
        FakeResponse(
            TJRJ_FIXTURE.read_text(encoding="utf-8"),
            "https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php",
        )
    )
    provider = TjrjEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    # The fixture is intentionally first-instance (Vara/Sentenca).  The
    # explicit second-degree query must not accept it as an appellate hit.
    with pytest.raises(ParserContractChangedError, match="degree"):
        provider.search(JurisprudenceQuery(text="dano moral", degree="second", page_size=1))

    payload = session.calls[0]["kwargs"]["data"]
    assert isinstance(payload, dict)
    # TJRJ's public eproc vocabulary calls the appellate corpus ``1``;
    # TJSP's installation uses ``5``.  The adapter must not reuse a numeric
    # code from another court.
    assert payload["selOrigem[]"] == ["1"]


def test_eproc_parser_assigns_first_degree_from_vara_signal() -> None:
    results = parse_eproc_jurisprudencia_results(
        TJRJ_FIXTURE.read_text(encoding="utf-8"),
        trace=SourceTrace(provider="tjrj_eproc_jurisprudencia", endpoint="/search"),
        source_url="https://eproc1g.tjrj.jus.br/eproc/",
        source="tjrj_eproc_jurisprudencia",
        court="TJRJ",
        id_prefix="tjrj-eproc-jurisprudencia",
        source_label="TJRJ/eproc jurisprudence",
    )

    assert results[0].degree == "first"
    assert results[0].instance == "first"
    assert results[0].authority == "TJRJ"
    assert results[0].branch == "state"
    assert results[0].collection == "JURISPRUDENCIA"


def test_tjsp_eproc_capabilities_describe_translated_and_local_filters() -> None:
    provider = TjrjEprocJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))
    capabilities = provider.get_capabilities()

    assert capabilities.filter_status("source_origin") == "translated"
    assert capabilities.filter_status("degree") == "local_postfilter"
    assert capabilities.filter_status("instance") == "local_postfilter"


def test_tjsc_eproc_uses_own_endpoint_and_court() -> None:
    session = FakeSession(
        FakeResponse(
            (FIXTURES / "tjsc_eproc_jurisprudencia_result.html").read_text(encoding="utf-8"),
            "https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php",
        )
    )
    provider = TjscEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.source == "tjsc_eproc_jurisprudencia"
    assert page.results[0].court == "TJSC"
    assert page.results[0].id.startswith("tjsc-eproc-jurisprudencia-")
    assert "eprocwebcon.tjsc.jus.br" in str(session.calls[0]["url"])


def test_eproc_page_reports_translated_and_native_filters() -> None:
    session = FakeSession(
        FakeResponse(
            (FIXTURES / "tjsc_eproc_jurisprudencia_result.html").read_text(encoding="utf-8"),
            "https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php",
        )
    )
    provider = TjscEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(
        JurisprudenceQuery(
            text="dano moral",
            number="5070037-16.2026.8.24.0000",
            types=["acordao"],
            source_origin="segundo_grau",
            degree="second",
            published_from="2026-01-01",
            page_size=1,
        )
    )

    assert page.filters_applied["text"] == "native"
    assert page.filters_applied["number"] == "native"
    assert page.filters_applied["types"] == "translated"
    assert page.filters_applied["source_origin"] == "translated"
    assert page.filters_applied["degree"] == "local_postfilter"
    assert page.filters_applied["published_from"] == "native"


def test_trf4_eproc_declares_shared_filter_contract() -> None:
    capabilities = Trf4EprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()

    assert capabilities.filter_status("source_origin") == "translated"
    assert capabilities.filter_status("degree") == "local_postfilter"
    assert capabilities.filter_status("case_class") == "unsupported"


def test_tjsc_eproc_appellate_document_label_proves_second_degree() -> None:
    html = (FIXTURES / "tjsc_eproc_jurisprudencia_result.html").read_text(encoding="utf-8")

    results = parse_eproc_jurisprudencia_results(
        html,
        trace=SourceTrace(provider="tjsc_eproc_jurisprudencia", endpoint="/search"),
        source_url="https://eprocwebcon.tjsc.jus.br/consulta1g/",
        source="tjsc_eproc_jurisprudencia",
        court="TJSC",
        id_prefix="tjsc-eproc-jurisprudencia",
        source_label="TJSC/eproc jurisprudence",
    )

    assert results[0].degree == "second"
    assert results[0].instance == "second"


def test_eproc_appellate_plural_document_labels_prove_second_degree() -> None:
    assert _infer_degree(None, None, "Acordaos do Conselho da Magistratura") == "second"


def test_tjrj_eproc_second_degree_fixture_preserves_appellate_identity() -> None:
    html = (FIXTURES / "tjrj_eproc_jurisprudencia_second.html").read_text(encoding="utf-8")

    results = parse_eproc_jurisprudencia_results(
        html,
        trace=SourceTrace(provider="tjrj_eproc_jurisprudencia", endpoint="/search"),
        source_url="https://eproc1g.tjrj.jus.br/eproc/",
        source="tjrj_eproc_jurisprudencia",
        court="TJRJ",
        id_prefix="tjrj-eproc-jurisprudencia",
        source_label="TJRJ/eproc jurisprudence",
    )

    assert results[0].degree == "second"
    assert results[0].instance == "second"
    assert results[0].judging_body == "1 Camara de Direito Privado"
    assert results[0].document_type == "acordao"


def test_tjsc_eproc_accepts_short_numeric_public_identifier() -> None:
    session = FakeSession(
        FakeResponse(
            "<html><body>Inteiro teor TJSC</body></html>",
            "https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php",
        )
    )
    provider = TjscEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    document = provider.get_document("tjsc-eproc-jurisprudencia-4870937")

    assert document.raw_metadata["id_jurisprudencia"] == "4870937"
    assert document.text == "Inteiro teor TJSC"
    assert session.calls[0]["kwargs"]["params"] == {"id_jurisprudencia": "4870937"}


def test_tjsc_eproc_rejects_identifier_without_numeric_suffix() -> None:
    provider = TjscEprocJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(ParserContractChangedError, match="numeric"):
        provider.get_document("tjsc-eproc-jurisprudencia-not-a-number")


def test_tjrj_eproc_empty_search_page_is_not_a_schema_failure() -> None:
    html = (FIXTURES / "tjrj_eproc_jurisprudencia_empty.html").read_text(encoding="utf-8")

    results = parse_eproc_jurisprudencia_results(
        html,
        trace=SourceTrace(provider="tjrj_eproc_jurisprudencia", endpoint="/search"),
        source_url="https://eproc1g.tjrj.jus.br/eproc/",
        source="tjrj_eproc_jurisprudencia",
        court="TJRJ",
        id_prefix="tjrj-eproc-jurisprudencia",
        source_label="TJRJ/eproc jurisprudence",
    )

    assert results == []


def test_eproc_zero_result_form_is_authoritative_empty() -> None:
    results = parse_eproc_jurisprudencia_results(
        "<form id='frmJurisprudenciaResultado'><span>0 documentos encontrados</span></form>",
        trace=SourceTrace(provider="tjrj_eproc_jurisprudencia", endpoint="/search"),
        source_url="https://eproc1g.tjrj.jus.br/eproc/",
        source="tjrj_eproc_jurisprudencia",
        court="TJRJ",
        id_prefix="tjrj-eproc-jurisprudencia",
        source_label="TJRJ/eproc jurisprudence",
    )

    assert results == []


def test_tjrj_eproc_get_document_uses_public_id_and_preserves_trace() -> None:
    session = FakeSession(
        FakeResponse(
            "<html>inteiro teor TJRJ</html>",
            "https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php",
        )
    )
    provider = TjrjEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    document = provider.get_document("tjrj-eproc-jurisprudencia-21786042808698528830162508954")

    assert document.source == "tjrj_eproc_jurisprudencia"
    assert document.text == "inteiro teor TJRJ"
    assert document.raw_metadata["id_jurisprudencia"] == "21786042808698528830162508954"
    assert document.source_trace is not None
    assert document.source_trace.http_status == 200


def test_tjrj_eproc_access_challenge_is_not_reported_as_empty() -> None:
    html = (FIXTURES / "tjrj_eproc_jurisprudencia_access_control.html").read_text(encoding="utf-8")

    try:
        parse_eproc_jurisprudencia_results(
            html,
            trace=SourceTrace(provider="tjrj_eproc_jurisprudencia", endpoint="/search"),
            source_url="https://eproc1g.tjrj.jus.br/eproc/",
            source="tjrj_eproc_jurisprudencia",
            court="TJRJ",
            id_prefix="tjrj-eproc-jurisprudencia",
            source_label="TJRJ/eproc jurisprudence",
        )
    except AccessControlRequiredError:
        return
    raise AssertionError("TJRJ access challenge was misreported as an empty page")


def test_state_eproc_providers_are_registered() -> None:
    client = NanoJurisClient()

    assert "tjrj_eproc_jurisprudencia" in client.providers
    assert "tjsc_eproc_jurisprudencia" in client.providers
