from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
)
from nanojuris.models import AccessStatus, JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjap_banco_sentencas import (
    TjapBancoSentencasProvider,
    parse_tjap_banco_sentencas,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str, query: JurisprudenceQuery | None = None):
    return parse_tjap_banco_sentencas(
        (FIXTURES / name).read_text(encoding="utf-8"),
        query=query or JurisprudenceQuery(text="direito", page_size=10),
        trace=SourceTrace(provider="tjap_banco_sentencas", endpoint="fixture"),
        base_url="https://bancosentencas.tjap.jus.br",
    )


def test_parser_normalizes_first_degree_result() -> None:
    page = _parse("tjap_banco_sentencas_success.html")
    assert page.total == 1 and page.total_known is True
    result = page.results[0]
    assert result.degree == result.instance == "first"
    assert result.collection == "CJPG" and result.authority == "TJAP"
    assert result.case_class == "Procedimento Comum Cível"
    assert result.document_url and "/reader/TUCUJURIS/123456" in result.document_url
    assert result.access_status is AccessStatus.PUBLIC


def test_parser_marks_sigiloso_partial() -> None:
    result = _parse("tjap_banco_sentencas_sigiloso.html").results[0]
    assert result.extraction_status.value == "partial"
    assert result.raw["sigiloso"] is True


def test_empty_is_explicit_not_blocked() -> None:
    page = _parse("tjap_banco_sentencas_empty.html")
    assert page.results == [] and page.is_explicit_empty
    assert page.access_status is AccessStatus.PUBLIC


def test_protected_markup_is_access_error() -> None:
    with pytest.raises(AccessControlRequiredError):
        _parse("tjap_banco_sentencas_blocked.html")


def test_schema_with_total_but_no_card_is_not_empty() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_tjap_banco_sentencas(
            "<main><p>Exibindo 1 até 1 de 3 resultados</p></main>",
            query=JurisprudenceQuery(text="x"),
            trace=SourceTrace(provider="tjap_banco_sentencas", endpoint="fixture"),
            base_url="https://bancosentencas.tjap.jus.br",
        )


def test_second_degree_scope_is_rejected() -> None:
    provider = TjapBancoSentencasProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="x", degree="second"))


class _Response:
    def __init__(
        self,
        content: bytes,
        status_code: int = 200,
        url: str = "https://bancosentencas.tjap.jus.br/",
    ):
        self.content = content
        self.status_code = status_code
        self.url = url
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.encoding = "utf-8"


class _Session:
    def __init__(self, initial: str, result_html: str):
        self.initial = initial
        self.result_html = result_html
        self.calls: list[dict] = []

    def request(self, method: str, url: str, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if method == "GET":
            return _Response(self.initial.encode())
        payload = kwargs.get("json") or {}
        assert payload["components"][0]["calls"][0]["method"] == "__dispatch"
        return _Response(
            json.dumps(
                {
                    "components": [
                        {"snapshot": self.initial_snapshot, "effects": {"html": self.result_html}}
                    ]
                }
            ).encode(),
            url="https://bancosentencas.tjap.jus.br/livewire-53cc04b2/update",
        )


def test_livewire_protocol_uses_public_dispatch() -> None:
    initial = "<div data-csrf='csrf'><div wire:snapshot='{\"data\":{},\"memo\":{}}'></div></div>"
    session = _Session(
        initial,
        (FIXTURES / "tjap_banco_sentencas_success.html").read_text(encoding="utf-8"),
    )
    session.initial_snapshot = '{"data":{},"memo":{}}'
    provider = TjapBancoSentencasProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="direito"))
    assert len(page.results) == 1
    assert session.calls[0]["method"] == "GET"
    body = session.calls[1]["kwargs"]["json"]
    assert body["components"][0]["calls"][0]["params"][0] == "update-filters"
