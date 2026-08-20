from __future__ import annotations

from types import SimpleNamespace

from tools.discover_all_providers import _materialize_endpoint, _normalize_filter_name, _provider_todo


def test_materialize_endpoint_keeps_method_and_skips_unusable_placeholders():
    assert _materialize_endpoint("https://example.test/api", "GET /search") == (
        "GET",
        "https://example.test/api/search",
    )
    assert _materialize_endpoint("https://example.test/api", "POST /search") == (
        "POST",
        "https://example.test/api/search",
    )
    assert _materialize_endpoint("https://example.test/api", "GET <official-pdf>") is None


def test_filter_normalization_maps_observed_provider_names_to_canonical_semantics():
    assert _normalize_filter_name("texto_busca") == "text"
    assert _normalize_filter_name("processo_numero") == "number"
    assert _normalize_filter_name("data_publicacao_de") == "published_from"
    assert _normalize_filter_name("pagina") == "page"


def test_provider_todo_does_not_convert_controlled_access_into_empty_results():
    evidence = SimpleNamespace(
        status=SimpleNamespace(value="access_controlled"),
        request=SimpleNamespace(url="https://example.test/search"),
        legal_signals={},
    )
    capabilities = SimpleNamespace(supported_filters=["text"])
    todos = _provider_todo(
        capabilities,
        [evidence],
        [{"method": "POST", "url": "https://example.test/search"}],
        {},
    )
    assert "documentar controle de acesso/SSO e confirmar rota pública alternativa" in todos
    assert "capturar fixture de formulário/JSON para confirmar filtros" in todos
