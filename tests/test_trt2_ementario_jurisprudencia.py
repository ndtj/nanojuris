from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import QueryRejectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.trt2_ementario_jurisprudencia import (
    Trt2EmentarioJurisprudenciaProvider,
    _parse_index,
    _parse_topic,
)

FIXTURES = Path(__file__).parent / "fixtures"


class _Response:
    def __init__(self, content: bytes, url: str, content_type: str = "text/html") -> None:
        self.content = content
        self.url = url
        self.status_code = 200
        self.headers = {"Content-Type": content_type}


class _Session:
    def __init__(self, responses: list[_Response]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []

    def get(self, url: str, **kwargs: object) -> _Response:
        del kwargs
        self.calls.append(url)
        if not self.responses:
            raise AssertionError(f"unexpected request: {url}")
        response = self.responses.pop(0)
        response.url = url
        return response

    def request(self, method: str, url: str, **kwargs: object) -> _Response:
        assert method == "GET"
        return self.get(url, **kwargs)


def _url(path: str) -> str:
    return f"https://trt2.jus.br/{path.lstrip('/')}"


def test_parse_index_keeps_only_official_topic_links() -> None:
    content = (FIXTURES / "trt2_ementario_index.html").read_bytes()
    rows = _parse_index(
        content,
        source_url=_url("geral/tribunal2/Ementario/Tribunal_Pleno.html"),
        scope="tribunal_pleno",
    )
    assert [row["label"] for row in rows][0] == "Responsabilidade civil"
    assert [row["label"] for row in rows][1].startswith("Div")
    assert all("trt2.jus.br" in row["url"] for row in rows)


def test_parse_topic_normalizes_second_degree_and_document_link() -> None:
    content = (FIXTURES / "trt2_ementario_topic.html").read_bytes()
    result = _parse_topic(
        content,
        source_url=_url("geral/tribunal2/Ementario/Tribunal_Pleno/RESPONSABILIDADE_Civil.html"),
        topic="Responsabilidade civil",
        scope="tribunal_pleno",
        trace=SourceTrace(provider="trt2_ementario_jurisprudencia", endpoint="GET /topic"),
    )
    assert result is not None
    assert result.authority == "TRT2"
    assert result.branch == "labor"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "TRT2_EMENTARIO"
    assert result.document_url and result.document_url.endswith("Ac_12345_25.pdf")
    assert result.publication_date == "2025-01-10"


def test_provider_search_uses_bounded_live_topic_window() -> None:
    index = (FIXTURES / "trt2_ementario_index.html").read_bytes()
    topic = (FIXTURES / "trt2_ementario_topic.html").read_bytes()
    session = _Session(
        [
            _Response(index, _url("geral/tribunal2/Ementario/Tribunal_Pleno.html")),
            _Response(
                topic, _url("geral/tribunal2/Ementario/Tribunal_Pleno/RESPONSABILIDADE_Civil.html")
            ),
        ]
    )
    provider = Trt2EmentarioJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )
    page = provider.search(
        JurisprudenceQuery(text="responsabilidade", collection="tribunal_pleno", page_size=10)
    )
    assert len(page.results) == 1
    assert page.total_known is False
    assert page.is_complete is False
    assert page.results[0].degree == "second"


def test_provider_rejects_first_degree_and_unsupported_collection() -> None:
    provider = Trt2EmentarioJurisprudenciaProvider()
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="x", degree="first"))
    with pytest.raises(QueryRejectedError, match="colecao"):
        provider.search(JurisprudenceQuery(text="x", collection="PJE"))


def test_provider_capability_is_federated_as_partial_and_documented() -> None:
    capabilities = Trt2EmentarioJurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert capabilities.supports_full_text is True
    assert "judging_body" in capabilities.unsupported_filters
