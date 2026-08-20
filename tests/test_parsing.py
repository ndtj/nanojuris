from __future__ import annotations

import pytest

from nanojuris.parsing import HtmlDocument, parse_html


HTML = """
<html><body>
  <main id="content">
    <article class="decision"><h2>Acórdão 1</h2><p class="summary">Ementa sobre direito civil.</p></article>
    <article class="decision"><h2>Acórdão 2</h2><p class="summary">Ementa sobre direito penal.</p></article>
    <form action="/jurisprudencia" method="post"><input name="q" value="civil"></form>
    <a href="/documentos/1.pdf">inteiro teor</a>
  </main>
</body></html>
""".encode("utf-8")


def test_parser_supports_css_text_attributes_links_and_forms() -> None:
    document = parse_html(HTML, base_url="https://example.test/pesquisa")

    assert document.backend in {"lxml", "beautifulsoup"}
    assert document.css("article.decision").getall() == [
        "Acórdão 1 Ementa sobre direito civil.",
        "Acórdão 2 Ementa sobre direito penal.",
    ]
    assert document.css("form").first is not None
    assert document.css("form").first.get("method") == "post"
    assert document.links().first.urljoin(document.links().first.get("href")) == (
        "https://example.test/documentos/1.pdf"
    )


def test_parser_exposes_visible_text_and_title() -> None:
    document = parse_html(
        b"<html><head><title>Busca</title><script>segredo()</script></head>"
        b"<body><p>Texto p\xc3\xbablico</p></body></html>"
    )

    assert document.title == "Busca"
    assert document.visible_text() == "Busca Texto público"


def test_parser_supports_xpath_when_lxml_is_available() -> None:
    document = parse_html(HTML)
    if document.backend != "lxml":
        pytest.skip("lxml opcional não instalado")
    assert document.xpath("//article[@class='decision']").getall()[0].startswith("Acórdão 1")


def test_parser_falls_back_to_beautifulsoup_without_lxml(monkeypatch) -> None:
    import nanojuris.parsing as parsing

    monkeypatch.setattr(parsing, "lxml_html", None)
    monkeypatch.setattr(parsing, "etree", None)
    document = parsing.parse_html(HTML)

    assert document.backend == "beautifulsoup"
    assert document.select_one("article.decision").get_text().startswith("Acórdão 1")


def test_parser_finds_text_generates_selector_and_suggests_similar_nodes() -> None:
    document = HtmlDocument(HTML)
    match = document.find_by_text("Ementa sobre direito civil", exact=False, limit=1).first

    assert match is not None
    assert "summary" in match.generate_css_selector()
    similar = match.find_similar(threshold=0.5)
    assert len(similar) >= 2


def test_parser_accepts_empty_or_whitespace_documents() -> None:
    assert parse_html(b"").visible_text() == ""
    assert parse_html(b" \n\t").visible_text() == ""
    assert parse_html(b"\x00\x00").backend in {"lxml", "beautifulsoup"}


def test_parser_rejects_oversized_documents() -> None:
    with pytest.raises(ValueError, match="limite de bytes"):
        parse_html(b"<p>texto</p>", max_bytes=3)
