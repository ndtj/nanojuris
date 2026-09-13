from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjce_cjsg import TjceCjsgProvider

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"
        self.url = "https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do"
        self.headers: dict[str, str] = {"Content-Type": "text/html; charset=utf-8"}


class FakeSession:
    def __init__(self, responses: list[Any]):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.mounts: list[tuple[str, Any]] = []

    def mount(self, prefix: str, adapter: Any) -> None:
        self.mounts.append((prefix, adapter))

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _fixture_html() -> str:
    return (FIXTURES / "tjce_cjsg_result.html").read_text(encoding="utf-8")


def _ack_html() -> str:
    return (FIXTURES / "tjsp_cjsg_ack.html").read_text(encoding="utf-8")


def test_tjce_search_reuses_cjsg_contract_with_own_identity() -> None:
    session = FakeSession([FakeResponse(_ack_html()), FakeResponse(_fixture_html())])
    provider = TjceCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page_size=2))

    assert page.source == "tjce_cjsg"
    assert page.results[0].source == "tjce_cjsg"
    assert page.results[0].court == "TJCE"
    assert (page.results[0].degree, page.results[0].instance) == ("second", "second")
    assert (page.results[0].branch, page.results[0].authority, page.results[0].collection) == (
        "state",
        "TJCE",
        "CJSG",
    )
    assert page.results[0].id.startswith("tjce-cjsg-")
    assert session.calls[0]["url"] == "https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do"
    assert session.calls[1]["method"] == "GET"
    assert session.calls[1]["url"].endswith("trocaDePagina.do?tipoDeDecisao=A&pagina=1")
    assert session.mounts and session.mounts[0][0] == "https://esaj.tjce.jus.br/"


def test_tjce_ignores_access_flags_in_post_ack_when_get_has_results() -> None:
    """The e-SAJ POST ack may contain captcha markup; GET is authoritative."""

    session = FakeSession(
        [
            FakeResponse("<html><div class='g-recaptcha'></div></html>"),
            FakeResponse(_fixture_html()),
        ]
    )
    provider = TjceCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page_size=2))

    assert page.results
    assert page.access_status.value == "public"


def test_tjce_fixture_has_ceara_provenance_not_tjsp_records() -> None:
    html = _fixture_html()

    assert ".8.06." in html
    assert "Fortaleza" in html
    assert "tjsp" not in html.lower()


def test_tjce_page_two_uses_public_session_route() -> None:
    fixture = _fixture_html()
    session = FakeSession(
        [
            FakeResponse(_ack_html()),
            FakeResponse(fixture),
            FakeResponse(fixture),
        ]
    )
    provider = TjceCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    provider.search(JurisprudenceQuery(text="responsabilidade civil", page=2))

    assert len(session.calls) == 3
    assert "/trocaDePagina.do?" in session.calls[1]["url"]
    assert "pagina=1" in session.calls[1]["url"]
    assert "/trocaDePagina.do?" in session.calls[2]["url"]
    assert "pagina=2" in session.calls[2]["url"]


def test_tjce_document_preserves_raw_bytes_and_source_identity() -> None:
    session = FakeSession([FakeResponse("<html><body>inteiro teor</body></html>")])
    provider = TjceCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    document = provider.get_document("tjce-cjsg-2471822-0")

    assert document.source == "tjce_cjsg"
    assert document.raw_bytes
    assert document.sha256
    assert document.source_trace is not None
    assert document.source_trace.provider == "tjce_cjsg"


def test_tjce_does_not_bypass_access_control() -> None:
    session = FakeSession([FakeResponse("<html><div class='g-recaptcha'></div></html>")])
    provider = TjceCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_tjce_invalid_document_id_is_rejected() -> None:
    provider = TjceCjsgProvider(NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]))

    with pytest.raises(ParserContractChangedError):
        provider.get_document("invalid")


def test_tjce_transport_failure_is_not_empty_result() -> None:
    provider = TjceCjsgProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )

    with pytest.raises(Exception, match="TJCE/CJSG request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_tjce_capabilities_use_official_host() -> None:
    capabilities = TjceCjsgProvider(NanoJurisConfig(rate_limit_interval=0)).get_capabilities()

    assert capabilities.source == "tjce_cjsg"
    assert capabilities.source_url == "https://esaj.tjce.jus.br/cjsg"
    assert capabilities.supports_full_text
    assert capabilities.supports_unified_search
