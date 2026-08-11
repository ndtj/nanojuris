from __future__ import annotations

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tre_sp_temas import (
    TreSpTemasProvider,
    parse_tre_sp_theme_detail,
    parse_tre_sp_theme_links,
)

THEME_PATH = (
    "/jurisprudencia/arquivos-da-secao-de-jurisprudencia-sp/"
    "temas-selecionados/tre-sp-aije-temas-selecionados-2022"
)

INDEX_HTML = f"""
<html><body>
    <a href="{THEME_PATH}">
    Ação de Investigação Judicial Eleitoral - AIJE
  </a>
</body></html>
"""

DETAIL_HTML = """
<html><head><title>Ação de Investigação Judicial Eleitoral - AIJE</title></head>
<body><main>
  <h1>Ação de Investigação Judicial Eleitoral - AIJE</h1>
  <p>Coletânea temática de jurisprudência com ementas selecionadas sobre abuso de poder.</p>
  <a href="https://www.tre-sp.jus.br/jurisprudencia/decisao/123">Acórdão TRE-SP 123</a>
</main></body></html>
"""


class FakeResponse:
    def __init__(
        self,
        text: str,
        url: str,
        status_code: int = 200,
        *,
        content_type: str = "text/html",
        content: bytes | None = None,
    ):
        self.text = text
        self.url = url
        self.status_code = status_code
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.headers = {"content-type": content_type}
        self.content = content if content is not None else text.encode("utf-8")


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


def test_parse_tre_sp_theme_links_extracts_theme_paths():
    links = parse_tre_sp_theme_links(
        INDEX_HTML,
        source_url="https://www.tre-sp.jus.br/jurisprudencia/temas-selecionados-1",
    )

    assert len(links) == 1
    assert links[0].title == "Ação de Investigação Judicial Eleitoral - AIJE"
    assert links[0].path.endswith("tre-sp-aije-temas-selecionados-2022")


def test_parse_tre_sp_theme_detail_maps_theme_page():
    result = parse_tre_sp_theme_detail(
        DETAIL_HTML,
        source_url=(
            "https://www.tre-sp.jus.br/jurisprudencia/arquivos-da-secao-de-jurisprudencia-sp/"
            "temas-selecionados/tre-sp-aije-temas-selecionados-2022"
        ),
        trace=SourceTrace(provider="tre_sp_temas", endpoint="/temas"),
    )

    assert result.id == "tre-sp-tema-tre-sp-aije-temas-selecionados-2022"
    assert result.type == "tema_selecionado"
    assert result.question == "Ação de Investigação Judicial Eleitoral - AIJE"
    assert "abuso de poder" in (result.thesis or "")
    assert result.raw["document_links"][0]["label"] == "Acórdão TRE-SP 123"


def test_provider_search_fetches_theme_detail():
    session = FakeSession(
        [
            FakeResponse(
                INDEX_HTML,
                "https://www.tre-sp.jus.br/jurisprudencia/temas-selecionados-1",
            ),
            FakeResponse(
                DETAIL_HTML,
                "https://www.tre-sp.jus.br/jurisprudencia/"
                "arquivos-da-secao-de-jurisprudencia-sp/temas-selecionados/"
                "tre-sp-aije-temas-selecionados-2022",
            ),
        ]
    )
    provider = TreSpTemasProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="abuso", page_size=1))

    assert page.source == "tre_sp_temas"
    assert page.results[0].id == "tre-sp-tema-tre-sp-aije-temas-selecionados-2022"
    assert session.calls[0]["url"].endswith("/jurisprudencia/temas-selecionados-1")
    assert session.calls[1]["url"].endswith("tre-sp-aije-temas-selecionados-2022")


def test_provider_search_preserves_official_pdf_theme_link():
    session = FakeSession(
        [
            FakeResponse(
                INDEX_HTML,
                "https://www.tre-sp.jus.br/jurisprudencia/temas-selecionados-1",
            ),
            FakeResponse(
                "",
                "https://www.tre-sp.jus.br/jurisprudencia/arquivos-da-secao-de-"
                "jurisprudencia-sp/temas-selecionados/tre-sp-aije-temas-selecionados-2022",
                content_type="application/pdf",
                content=b"%PDF-1.7 public theme",
            ),
        ]
    )
    provider = TreSpTemasProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="Judicial", page_size=1))

    assert page.results[0].raw["content_type"] == "application/pdf"
    assert (
        page.results[0]
        .raw["document_links"][0]["url"]
        .endswith("tre-sp-aije-temas-selecionados-2022")
    )
