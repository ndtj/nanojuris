from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjto_jurisprudencia import (
    TjtoJurisprudenciaProvider,
    build_tjto_search_parameters,
    parse_tjto_search_response,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjto_jurisprudencia_results.json"


class FakeResponse:
    def __init__(self, content: bytes | str, *, url: str, content_type: str = "text/html") -> None:
        self.status_code = 200
        self.url = url
        self.headers = {"Content-Type": content_type}
        self.content = content.encode("utf-8") if isinstance(content, str) else content
        self.text = self.content.decode("utf-8", errors="replace")


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def fixture_html() -> str:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["html"]


def trace() -> SourceTrace:
    return SourceTrace(
        provider="tjto_jurisprudencia",
        endpoint="POST /consulta.php",
        source_url="https://jurisprudencia.tjto.jus.br/consulta.php",
    )


def test_tjto_parser_extracts_card_and_stable_document_uuid() -> None:
    page = parse_tjto_search_response(
        fixture_html().encode("utf-8"),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=2),
        trace=trace(),
    )
    result = page.results[0]
    assert page.total == 2
    assert result.id == "tjto-jurisprudencia-abcdef1234567890"
    assert result.number == "0000001-23.2026.8.27.0001"
    assert result.judgment_date == "2026-02-15"
    assert result.summary.startswith("Ementa pública de fixture")
    assert result.raw["document_uuid"] == "abcdef1234567890"


def test_tjto_builds_offset_and_type_parameters() -> None:
    params = build_tjto_search_parameters(
        JurisprudenceQuery(
            text="dano moral",
            exact_phrase="transporte aereo",
            types=["sentenca"],
            source_origin="2",
            rapporteur="RELATOR FIXTURE",
            page=3,
            page_size=25,
        )
    )
    assert params["start"] == "50"
    assert params["rows"] == "25"
    assert params["soementa"] == "on"
    assert params["tipo_decisao_sentenca"] == "true"
    assert params["tip_criterio_inst"] == "2"
    assert params["fq_magistrado[RELATOR FIXTURE]"] == "on"


def test_tjto_fetch_details_preserves_document_metadata() -> None:
    document = "<html><body>Inteiro teor HTML publico de fixture.</body></html>"
    session = FakeSession(
        [
            FakeResponse(fixture_html(), url="https://jurisprudencia.tjto.jus.br/consulta.php"),
            FakeResponse(
                document,
                url="https://jurisprudencia.tjto.jus.br/documento.php?uuid=abcdef1234567890",
            ),
        ]
    )
    provider = TjtoJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)
    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=2, fetch_details=True))
    assert page.results[0].full_text == "Inteiro teor HTML publico de fixture."
    assert page.results[0].raw["content_sha256"]
    assert page.results[0].raw["document_content_type"] == "text/html"
    assert session.calls[1]["method"] == "GET"
