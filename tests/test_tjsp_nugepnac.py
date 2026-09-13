from __future__ import annotations

from pathlib import Path

from nanojuris.canonical import search_page_to_canonical
from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjsp_nugepnac import (
    TjspNugepnacProvider,
    parse_nugepnac_detail,
    parse_nugepnac_list,
)

FIXTURES = Path(__file__).parent / "fixtures"

LIST_HTML = (FIXTURES / "tjsp_nugepnac_list.html").read_text(encoding="utf-8")
IAC_LIST_HTML = (FIXTURES / "tjsp_nugepnac_iac_list.html").read_text(encoding="utf-8")

DETAIL_HTML = (FIXTURES / "tjsp_nugepnac_detail.html").read_text(encoding="utf-8")
IAC_DETAIL_NO_THESIS_HTML = (FIXTURES / "tjsp_nugepnac_iac_detail_no_thesis.html").read_text(
    encoding="utf-8"
)
DOCUMENT_HTML = (FIXTURES / "tjsp_nugepnac_document.html").read_text(encoding="utf-8")


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
        self.raw = None

    def iter_content(self, chunk_size=65536):
        yield self.content

    def close(self):
        return None

    @property
    def is_redirect(self):
        return False


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


def test_parse_nugepnac_list_extracts_detail_links():
    links = parse_nugepnac_list(
        LIST_HTML,
        source_url="https://www.tjsp.jus.br/NugepNac/Irdr",
        precedent_type="irdr",
    )

    assert len(links) == 1
    assert links[0].precedent_type == "irdr"
    assert links[0].detail_path == "/NugepNac/Irdr/DetalheTema?codigoNoticia=50879&pagina=1"


def test_parse_nugepnac_iac_list_extracts_public_detail_links():
    links = parse_nugepnac_list(
        IAC_LIST_HTML,
        source_url="https://www.tjsp.jus.br/NugepNac/Iac",
        precedent_type="iac",
    )

    assert len(links) == 2
    assert all(link.precedent_type == "iac" for link in links)
    assert links[0].detail_path == "/NugepNac/Iac/DetalheTema?codigoNoticia=51493&pagina=1"


def test_parse_nugepnac_detail_maps_precedent_fields():
    result = parse_nugepnac_detail(
        DETAIL_HTML,
        source_url="https://www.tjsp.jus.br/NugepNac/Irdr/DetalheTema?codigoNoticia=50879&pagina=1",
        precedent_type="irdr",
        trace=SourceTrace(provider="tjsp_nugepnac", endpoint="/NugepNac/Irdr"),
    )

    assert result.id == "tjsp-nugepnac-irdr-50879"
    assert result.type == "irdr"
    assert result.number == 1
    assert result.status == "TRANSITO EM JULGADO"
    assert result.paradigm_cases[0].number == "2059683-75.2016.8.26.0000"
    assert result.rapporteur == "Desembargador RICARDO PESSOA DE MELLO BELLI"
    assert result.judgment_date == "28/03/2017"
    assert result.publication_date == "14/09/2017"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "NUGEP_NAC"
    assert result.document_url == (
        "https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=9531760&cdForo=0"
    )
    assert result.question == "Discussao sobre limite maximo da garantia."
    assert result.thesis.startswith("Incidente de resolucao")
    assert result.raw["judging_body"] == "Turma Especial - Privado 2"


def test_parse_nugepnac_iac_detail_allows_missing_thesis_and_document_link():
    result = parse_nugepnac_detail(
        IAC_DETAIL_NO_THESIS_HTML,
        source_url="https://www.tjsp.jus.br/NugepNac/Iac/DetalheTema?codigoNoticia=52107&pagina=1",
        precedent_type="iac",
        trace=SourceTrace(provider="tjsp_nugepnac", endpoint="/NugepNac/Iac"),
    )

    assert result.id == "tjsp-nugepnac-iac-52107"
    assert result.type == "iac"
    assert result.thesis is None
    assert result.question is not None
    assert result.paradigm_cases[0].url is not None
    assert result.raw["related_links"]


def test_provider_search_fetches_list_and_detail():
    session = FakeSession(
        [
            FakeResponse(LIST_HTML, "https://www.tjsp.jus.br/NugepNac/Irdr"),
            FakeResponse(
                DETAIL_HTML,
                "https://www.tjsp.jus.br/NugepNac/Irdr/DetalheTema?codigoNoticia=50879&pagina=1",
            ),
        ]
    )
    provider = TjspNugepnacProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="garantia", types=["irdr"], page_size=1))

    assert page.source == "tjsp_nugepnac"
    assert page.results[0].id == "tjsp-nugepnac-irdr-50879"
    assert page.total_known is False
    assert session.calls[0]["url"].endswith("/NugepNac/Irdr")
    assert "codigoNoticia=50879" in session.calls[1]["url"]


def test_provider_search_supports_iac_and_does_not_promote_process_link():
    session = FakeSession(
        [
            FakeResponse(IAC_LIST_HTML, "https://www.tjsp.jus.br/NugepNac/Iac"),
            FakeResponse(
                IAC_DETAIL_NO_THESIS_HTML,
                "https://www.tjsp.jus.br/NugepNac/Iac/DetalheTema?codigoNoticia=52107&pagina=1",
            ),
        ]
    )
    provider = TjspNugepnacProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(types=["iac"], page_size=1))

    assert page.results[0].type == "iac"
    assert page.results[0].thesis is None
    assert provider._document_urls == {}


def test_nugepnac_canonicalizes_as_precedent():
    session = FakeSession(
        [
            FakeResponse(LIST_HTML, "https://www.tjsp.jus.br/NugepNac/Irdr"),
            FakeResponse(
                DETAIL_HTML,
                "https://www.tjsp.jus.br/NugepNac/Irdr/DetalheTema?codigoNoticia=50879&pagina=1",
            ),
        ]
    )
    provider = TjspNugepnacProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    records = search_page_to_canonical(
        provider.search(JurisprudenceQuery(text="garantia", types=["irdr"], page_size=1))
    )

    assert records[0].source == "tjsp_nugepnac"
    assert records[0].precedent_type == "irdr"
    assert records[0].thesis is not None


def test_nugepnac_fetches_observed_related_decision_document():
    session = FakeSession(
        [
            FakeResponse(LIST_HTML, "https://www.tjsp.jus.br/NugepNac/Irdr"),
            FakeResponse(
                DETAIL_HTML,
                "https://www.tjsp.jus.br/NugepNac/Irdr/DetalheTema?codigoNoticia=50879&pagina=1",
            ),
            FakeResponse(
                DOCUMENT_HTML,
                "https://esaj.tjsp.jus.br/cjsg/getArquivo.do?cdAcordao=9531760&cdForo=0",
                content_type="text/html",
            ),
        ]
    )
    provider = TjspNugepnacProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="garantia", types=["irdr"], page_size=1))
    document = provider.get_document(page.results[0].id)

    assert document.content_type == "text/html"
    assert "official decision" in (document.text or "")
    assert document.access_status.value == "public"
    assert session.calls[-1]["url"].startswith("https://esaj.tjsp.jus.br/")


def test_nugepnac_catalog_total_is_known_without_content_filter():
    session = FakeSession(
        [
            FakeResponse(LIST_HTML, "https://www.tjsp.jus.br/NugepNac/Irdr"),
            FakeResponse(
                DETAIL_HTML,
                "https://www.tjsp.jus.br/NugepNac/Irdr/DetalheTema?codigoNoticia=50879&pagina=1",
            ),
        ]
    )
    provider = TjspNugepnacProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(types=["irdr"], page_size=1))

    assert page.total == 1
    assert page.total_known is True
    assert page.is_complete is True


def test_nugepnac_rejects_untrusted_related_document_url():
    provider = TjspNugepnacProvider(NanoJurisConfig(rate_limit_interval=0), session=FakeSession([]))

    try:
        provider.get_document("https://evil.example/document.pdf")
    except ValueError as exc:
        assert "official host allowlist" in str(exc)
    else:
        raise AssertionError("untrusted document URL must be rejected")
