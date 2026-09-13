from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjrj_ejuris import TjrjEjurisProvider

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, body: str, *, json_body: Any = None, status_code: int = 200) -> None:
        self.text = body
        self.content = body.encode("utf-8")
        self.status_code = status_code
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.url = "https://www3.tjrj.jus.br/ejuris/ConsultarJurisprudencia.aspx"
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self._json_body = json_body

    def json(self) -> Any:
        if self._json_body is None:
            raise ValueError("not json")
        return self._json_body


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def _provider() -> TjrjEjurisProvider:
    form = (FIXTURES / "tjrj_ejuris_form.html").read_text(encoding="utf-8")
    payload = json.loads((FIXTURES / "tjrj_ejuris_page.json").read_text(encoding="utf-8"))
    return TjrjEjurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(form),
                FakeResponse(form),
                FakeResponse(json.dumps(payload), json_body=payload),
            ]
        ),
    )


def test_tjrj_ejuris_search_replays_public_aspx_and_xhr_contract() -> None:
    provider = _provider()
    page = provider.search(
        JurisprudenceQuery(
            text="responsabilidade civil",
            published_from="2026-01-01",
            published_to="2026-12-31",
            page_size=1,
        )
    )

    assert page.source == "tjrj_ejuris"
    assert page.total == 1
    assert page.total_known is True
    assert page.results[0].authority == "TJRJ"
    assert page.results[0].degree == "second"
    assert page.results[0].instance == "second"
    assert page.results[0].collection == "CJSG"
    assert page.results[0].summary == "APELAÇÃO CÍVEL. Texto integral público."
    assert page.results[0].judgment_date == "2025-01-01"
    assert page.results[0].publication_date == "2025-01-02"
    assert len(provider.session.calls) == 3
    assert provider.session.calls[2]["kwargs"]["json"] == {"numPagina": 0, "pageSeq": "0"}
    form_payload = provider.session.calls[1]["kwargs"]["data"]
    assert form_payload["ctl00$ContentPlaceHolder1$cmbOrigem"] == "1"
    assert form_payload["ctl00$ContentPlaceHolder1$cmbAnoInicio"] == "2026"
    assert form_payload["ctl00$ContentPlaceHolder1$cmbAnoFim"] == "2026"
    trace_query = page.source_trace.query
    assert "form" not in trace_query
    assert "__VIEWSTATE" not in str(trace_query)
    assert "__EVENTVALIDATION" not in str(trace_query)
    assert "g-recaptcha-response" not in str(trace_query)
    assert trace_query["origin"] == "1"


def test_tjrj_ejuris_document_uses_embedded_public_text() -> None:
    provider = _provider()
    page = provider.search(JurisprudenceQuery(text="responsabilidade civil"))
    document = provider.get_document(page.results[0].id)
    assert document.text == page.results[0].full_text
    assert document.sha256
    assert document.extraction_trace is not None


def test_tjrj_ejuris_rejects_incompatible_scope() -> None:
    provider = _provider()
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="teste", degree="first"))


def test_tjrj_ejuris_rejects_changed_xhr_schema() -> None:
    provider = TjrjEjurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse((FIXTURES / "tjrj_ejuris_form.html").read_text(encoding="utf-8")),
                FakeResponse((FIXTURES / "tjrj_ejuris_form.html").read_text(encoding="utf-8")),
                FakeResponse("{}", json_body={"d": {"unexpected": []}}),
            ]
        ),
    )
    with pytest.raises(ParserContractChangedError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_tjrj_ejuris_accepts_authoritative_empty_payload() -> None:
    form = (FIXTURES / "tjrj_ejuris_form.html").read_text(encoding="utf-8")
    payload = json.loads((FIXTURES / "tjrj_ejuris_empty.json").read_text(encoding="utf-8"))
    provider = TjrjEjurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(form),
                FakeResponse(form),
                FakeResponse(json.dumps(payload), json_body=payload),
            ]
        ),
    )
    page = provider.search(JurisprudenceQuery(text="termo sem ocorrencias"))
    assert page.total == 0
    assert page.results == []
    assert page.extraction_status.value == "empty"


def test_tjrj_ejuris_maps_page_two_without_overlap() -> None:
    form = (FIXTURES / "tjrj_ejuris_form.html").read_text(encoding="utf-8")
    payload = json.loads((FIXTURES / "tjrj_ejuris_page2.json").read_text(encoding="utf-8"))
    provider = TjrjEjurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(form),
                FakeResponse(form),
                FakeResponse(json.dumps(payload), json_body=payload),
            ]
        ),
    )
    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page=2, page_size=1))
    assert page.page == 2
    assert page.start == 11
    assert page.end == 11
    assert page.results[0].id == "tjrj-ejuris-5988226"


def test_tjrj_ejuris_does_not_treat_access_control_as_empty() -> None:
    form = (FIXTURES / "tjrj_ejuris_form.html").read_text(encoding="utf-8")
    provider = TjrjEjurisProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([FakeResponse(form, status_code=403)]),
    )
    with pytest.raises(AccessControlRequiredError) as error:
        provider.search(JurisprudenceQuery(text="teste"))
    assert "controle de acesso" in str(error.value)


def test_tjrj_ejuris_capabilities_declare_opt_in_and_scope() -> None:
    capabilities = TjrjEjurisProvider(NanoJurisConfig()).get_capabilities()
    assert capabilities.opt_in_unified_search is False
    assert capabilities.filter_status("degree") == "validated_scope"
    assert capabilities.filter_status("all_words") == "unsupported"
    assert capabilities.filter_status("text") == "native"
    assert capabilities.filter_status("types") == "translated"
    assert capabilities.filter_status("document_type") == "translated"


def test_tjrj_ejuris_translates_document_type_to_native_checkboxes() -> None:
    provider = _provider()
    provider.search(JurisprudenceQuery(text="responsabilidade civil", document_type="acordao"))
    data = provider.session.calls[1]["kwargs"]["data"]
    prefix = "ctl00$ContentPlaceHolder1$"
    assert data[f"{prefix}chkAcordao"] == "on"
    assert f"{prefix}chkDecMon" not in data
