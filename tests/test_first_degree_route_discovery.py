from __future__ import annotations

from tools.discover_first_degree_routes import _candidate_urls, _classification, _route_scope


def test_candidate_urls_extracts_first_degree_markers_without_fetching() -> None:
    html = b"""<html><a href="/cjpg/pesquisar">CJPG 1o grau</a>
    <a href="/processos">Consulta processual</a>
    <script src="/assets/app.js"></script>
    <script>const endpoint = "https://example.test/api/jurisprudencia/1g";</script></html>"""

    candidates, scripts = _candidate_urls(html, "https://tj.example/")

    assert scripts == ["https://tj.example/assets/app.js"]
    assert any(item.kind == "link" and "cjpg" in item.url for item in candidates)
    assert any(item.kind == "inline_url" and "jurisprudencia" in item.url for item in candidates)
    assert all("processos" not in item.url for item in candidates)


def test_classification_keeps_access_controlled_distinct_from_empty() -> None:
    assert _classification(403) == "access_controlled"
    assert _classification(429) == "access_controlled"
    assert _classification(200) == "reachable"
    assert _classification(None) == "transport_error"


def test_route_scope_separates_process_from_jurisprudence_candidates() -> None:
    assert _route_scope("https://esaj.example/cpopg/open.do") == "process_surface"
    assert _route_scope("https://juris.example/cjpg/pesquisar") == "jurisprudence_candidate"
