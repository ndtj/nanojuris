from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    UnsupportedQueryError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjmrs_jurisprudencia import (
    TjmrsJurisprudenciaProvider,
    parse_tjmrs_process_result,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, text: str, url: str, status_code: int = 200) -> None:
        self.text = text
        self.url = url
        self.status_code = status_code
        self.encoding = "utf-8"
        self.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.content = text.encode("utf-8")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def _trace() -> SourceTrace:
    return SourceTrace(provider="tjmrs_jurisprudencia", endpoint="/abreJurisprudencia.php")


def test_parse_tjmrs_exact_process_maps_second_degree_and_text() -> None:
    html = (FIXTURES / "tjmrs_jurisprudencia_result.html").read_text(encoding="utf-8")

    result = parse_tjmrs_process_result(
        html,
        trace=_trace(),
        source_url="https://www.tjmrs.jus.br/abreJurisprudencia.php?processo=00704302520239210002",
    )

    assert result is not None
    assert result.number == "0070430-25.2023.9.21.0002"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.branch == "military"
    assert result.authority == "TJMRS"
    assert result.collection == "TJMRS_JURISPRUDENCIA"
    assert result.document_type == "acordao"
    assert "OMISSÃO" in (result.summary or "")
    assert result.rapporteur == "Desembargador Militar RELATOR FICTÍCIO"


def test_tjmrs_parser_accepts_authoritative_empty() -> None:
    html = (FIXTURES / "tjmrs_jurisprudencia_empty.html").read_text(encoding="utf-8")

    assert (
        parse_tjmrs_process_result(
            html,
            trace=_trace(),
            source_url="https://www.tjmrs.jus.br/abreJurisprudencia.php?processo=00000000000000000000",
        )
        is None
    )


def test_tjmrs_parser_rejects_unknown_shape() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_tjmrs_process_result(
            "<html><body>Resposta inesperada</body></html>",
            trace=_trace(),
            source_url="https://www.tjmrs.jus.br/abreJurisprudencia.php",
        )


def test_tjmrs_search_uses_exact_process_route() -> None:
    listing = (FIXTURES / "tjmrs_jurisprudencia_result.html").read_text(encoding="utf-8")
    session = FakeSession(
        [
            FakeResponse(
                listing,
                "https://www.tjmrs.jus.br/abreJurisprudencia.php?processo=00704302520239210002",
            )
        ]
    )
    provider = TjmrsJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )

    page = provider.search(JurisprudenceQuery(number="0070430-25.2023.9.21.0002"))

    assert page.total == 1
    assert page.total_known is True
    assert page.results[0].degree == "second"
    assert session.calls[0]["url"].endswith("/abreJurisprudencia.php")
    assert session.calls[0]["kwargs"]["params"] == {"processo": "00704302520239210002"}


def test_tjmrs_search_preserves_authoritative_empty() -> None:
    empty = (FIXTURES / "tjmrs_jurisprudencia_empty.html").read_text(encoding="utf-8")
    provider = TjmrsJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [FakeResponse(empty, "https://www.tjmrs.jus.br/abreJurisprudencia.php")]
        ),  # type: ignore[arg-type]
    )

    page = provider.search(JurisprudenceQuery(number="00000000000000000000"))

    assert page.results == []
    assert page.is_explicit_empty is True
    assert page.access_status.value == "public"
    assert page.extraction_status.value == "empty"


def test_tjmrs_access_control_is_not_empty() -> None:
    provider = TjmrsJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [
                FakeResponse(
                    "<html><body>Forbidden</body></html>",
                    "https://www.tjmrs.jus.br/abreJurisprudencia.php",
                    status_code=403,
                )
            ]
        ),  # type: ignore[arg-type]
    )

    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(number="00704302520239210002"))


def test_tjmrs_rejects_free_text_and_second_page() -> None:
    provider = TjmrsJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0))

    with pytest.raises(UnsupportedQueryError):
        provider.search(JurisprudenceQuery(text="responsabilidade civil"))
    with pytest.raises(UnsupportedQueryError):
        provider.search(JurisprudenceQuery(number="00704302520239210002", page=2))


def test_tjmrs_get_document_preserves_html() -> None:
    html = (FIXTURES / "tjmrs_jurisprudencia_result.html").read_text(encoding="utf-8")
    provider = TjmrsJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=FakeSession(
            [FakeResponse(html, "https://www.tjmrs.jus.br/abreJurisprudencia.php")]
        ),  # type: ignore[arg-type]
    )

    document = provider.get_document("00704302520239210002")

    assert document.access_status.value == "public"
    assert document.extraction_status.value == "complete"
    assert "EMENTA" in (document.text or "")
    assert document.raw_bytes == html.encode("utf-8")


def test_tjmrs_is_runtime_opt_in_not_default_federation() -> None:
    client = NanoJurisClient()
    provider = client.providers["tjmrs_jurisprudencia"]

    assert provider.get_capabilities().supports_unified_search is False
    assert provider.get_capabilities().opt_in_unified_search is True
