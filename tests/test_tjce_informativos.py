from __future__ import annotations

from pathlib import Path

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjce_informativos import (
    TjceInformativosProvider,
    parse_tjce_informativos,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status_code
        self.url = "https://www.tjce.jus.br/informativo-jurisprudencia/"
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def load_fixture() -> str:
    return (FIXTURES / "tjce_informativos_results.html").read_text(encoding="utf-8")


def trace() -> SourceTrace:
    return SourceTrace(provider="tjce_informativos", endpoint="GET /informativo-jurisprudencia/")


def test_parse_tjce_informativos_maps_editions_and_curated_fields():
    page = parse_tjce_informativos(
        load_fixture(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=5),
        trace=trace(),
        base_url="https://www.tjce.jus.br",
    )
    assert page.source == "tjce_informativos"
    assert page.total == 2
    first = page.results[0]
    assert first.court == "TJCE"
    assert first.type == "informativo_item"
    assert first.number == "0000001-01.2026.8.06.0001"
    assert first.publication_date == "2026-07-01"
    assert first.judgment_date == "2026-06-06"
    assert first.rapporteur == "Des. Ana TJCE"
    assert first.raw["judging_body"] == "1ª Câmara Cível"
    assert first.raw["edition_number"] == "23"
    assert first.raw["document_url"].endswith("/852314/")

    second = page.results[1]
    assert second.raw["edition_number"] == "22"
    assert second.publication_date is None


def test_provider_sends_public_form_filters():
    session = FakeSession([FakeResponse(load_fixture())])
    provider = TjceInformativosProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,
    )
    provider.search(
        JurisprudenceQuery(
            text="cartorios",
            number="23",
            types=["Ordinária"],
            published_from="01/01/2026",
            published_to="31/12/2026",
        )
    )
    params = session.calls[0]["kwargs"]["params"]
    assert params["busca_livre"] == "cartorios"
    assert params["numero_edicao"] == "23"
    assert params["tipos_edicao[]"] == ["Ordinária"]
    assert session.calls[0]["kwargs"]["verify"] is True


def test_client_registers_tjce_provider_with_curated_scope():
    client = NanoJurisClient()
    assert "tjce_informativos" in {item.source for item in client.list_sources()}
    capabilities = TjceInformativosProvider(session=FakeSession([])).get_capabilities()
    assert capabilities.category == "curated_jurisprudence"
    assert capabilities.supports_full_text is False


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (FakeResponse("captcha", 403), AccessControlRequiredError),
        (FakeResponse("", 429), RateLimitDetectedError),
        (FakeResponse("", 503), SourceUnavailableError),
    ],
)
def test_provider_normalizes_http_failures(response, expected):
    provider = TjceInformativosProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([response]),
    )
    with pytest.raises(expected):
        provider.search(JurisprudenceQuery(text="teste"))


def test_parser_detects_changed_contract_and_transport_failure():
    with pytest.raises(ParserContractChangedError):
        parse_tjce_informativos(
            "<html><body>estrutura desconhecida</body></html>",
            query=JurisprudenceQuery(text="teste"),
            trace=trace(),
            base_url="https://www.tjce.jus.br",
        )
    provider = TjceInformativosProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession([requests.RequestException("offline")]),
    )
    with pytest.raises(SourceUnavailableError, match="TJCE Informativos request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_public_recaptcha_asset_does_not_mark_page_as_blocked():
    html = load_fixture().replace(
        "</body>",
        '<script src="https://www.google.com/recaptcha/api.js"></script></body>',
    )
    page = parse_tjce_informativos(
        html,
        query=JurisprudenceQuery(text="teste"),
        trace=trace(),
        base_url="https://www.tjce.jus.br",
    )
    assert page.results
