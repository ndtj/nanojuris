from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.errors import QueryRejectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjrr_juris import TjrrJurisProvider, parse_tjrr_results

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, body: str, url: str = "https://jurisprudencia.tjrr.jus.br/index.xhtml"):
        self.status_code = 200
        self.url = url
        self.headers = {"Content-Type": "text/html; charset=UTF-8"}
        self._content = body.encode("utf-8")
        self.text = body
        self.content = self._content


class FakeSession:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_tjrr_result_maps_metadata_and_full_text():
    page = parse_tjrr_results(
        _fixture("tjrr_juris_result.html"),
        query=JurisprudenceQuery(text="dano moral", page_size=1),
        trace=SourceTrace(provider="tjrr_juris", endpoint="/index.xhtml"),
        base_url="https://jurisprudencia.tjrr.jus.br",
    )

    result = page.results[0]
    assert page.total == 2
    assert page.pagination_mode == "page"
    assert page.is_complete is False
    assert result.id == "tjrr-juris-321"
    assert result.number == "0000001-23.2026.8.23.0001"
    assert result.summary == "Ementa publica de fixture."
    assert result.full_text == "Texto integral publico de fixture."
    assert result.raw["case_class"] == "Apelacao Civel"
    assert result.raw["judging_body"] == "Câmara de Fixture"
    assert result.raw["document_url"] == "/inteiroTeor.xhtml?id=321"


def test_provider_posts_public_form_and_supports_primefaces_page_request():
    result = _fixture("tjrr_juris_result.html")
    partial = (
        '<partial-response><changes><update id="table"><![CDATA['
        f"{result}"
        "]]></update></changes></partial-response>"
    )
    session = FakeSession(
        [
            FakeResponse(_fixture("tjrr_juris_form.html")),
            FakeResponse(result),
            FakeResponse(partial),
        ]
    )
    provider = TjrrJurisProvider(session=session)

    page = provider.search(JurisprudenceQuery(text="dano moral", page=2, page_size=1))

    assert page.results[0].number == "0000001-23.2026.8.23.0001"
    assert [call["method"] for call in session.calls] == ["GET", "POST", "POST"]
    ajax = session.calls[2]["kwargs"]
    assert isinstance(ajax, dict)
    assert ajax["headers"]["Faces-Request"] == "partial/ajax"
    assert ajax["data"]["formPesquisa:j_idt155:dataTablePesquisa_first"] == "1"


def test_provider_get_document_uses_observed_public_id():
    session = FakeSession([FakeResponse(_fixture("tjrr_juris_detail.html"))])
    provider = TjrrJurisProvider(session=session)

    document = provider.get_document("tjrr-juris-321")

    assert document.text == "Inteiro teor Texto integral publico de fixture TJRR."
    assert session.calls[0]["url"].endswith("/inteiroTeor.xhtml?id=321")


def test_provider_rejects_unbounded_empty_search():
    provider = TjrrJurisProvider(session=FakeSession([]))

    with pytest.raises(QueryRejectedError, match="exige termo"):
        provider.search(JurisprudenceQuery())
