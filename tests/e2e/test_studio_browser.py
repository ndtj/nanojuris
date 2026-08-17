"""Playwright smoke, responsive and visual-artifact tests for Studio."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")
expect = playwright_sync.expect

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.e2e
def test_studio_loads_sources_and_searches(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    expect(page).to_have_title("NanoJuris Studio")
    expect(page.locator(".source-card").first).to_be_visible()
    expect(page.locator(".source-name").first).to_contain_text("TJDFT")

    page.locator("#query").fill("responsabilidade civil")
    page.locator("#search-form button[type='submit']").click()

    expect(page.locator(".results-header")).to_contain_text("Resultados da coleta")
    expect(page.locator(".result").first).to_be_visible()
    expect(page.locator(".result-title").first).to_contain_text("Responsabilidade civil")
    expect(page.locator(".status-chip.ok").first).to_be_visible()
    _capture(page, "02-results-desktop.png")


@pytest.mark.e2e
def test_studio_reports_partial_failures(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    page.locator("[data-preset='all']").click()
    page.locator("#query").fill("responsabilidade civil")
    page.locator("#search-form button[type='submit']").click()

    expect(page.locator(".diagnostics")).to_be_visible()
    expect(page.locator(".diagnostics summary")).to_contain_text("2 observacoes")
    page.locator(".diagnostics summary").click()
    expect(page.locator(".diagnostics")).to_contain_text("Fonte indisponivel")
    expect(page.locator(".diagnostics")).to_contain_text("Fonte com controle de acesso")
    expect(page.locator(".status-chip.failed")).to_be_visible()
    expect(page.locator(".status-chip.skipped")).to_be_visible()
    expect(
        page.locator(".metric").filter(has_text="fontes com resultados").locator("strong")
    ).to_have_text("3")
    _capture(page, "05-partial-failure-desktop.png")


@pytest.mark.e2e
def test_studio_paginates_the_federated_window(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    page.locator("#query").fill("responsabilidade civil")
    page.locator("#search-form button[type='submit']").click()

    expect(page.locator(".pagination")).to_contain_text("pagina 1")
    expect(page.locator("[data-page='2']")).to_be_enabled()
    page.locator("[data-page='2']").click()

    expect(page.locator(".pagination")).to_contain_text("pagina 2")
    expect(page.locator(".result-title").first).to_contain_text("Segunda pagina")


@pytest.mark.e2e
def test_studio_sends_advanced_search_filters(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    page.locator(".advanced-filters summary").click()
    page.locator("#exact_phrase").fill("responsabilidade objetiva")
    page.locator("#all_words").fill("dano moral")
    page.locator("#rapporteur").fill("Relator de Demonstracao")

    with page.expect_request(lambda request: request.url.endswith("/api/search")) as request_info:
        page.locator("#query").fill("responsabilidade civil")
        page.locator("#search-form button[type='submit']").click()

    body = request_info.value.post_data_json
    assert body["filters"]["exact_phrase"] == "responsabilidade objetiva"
    assert body["filters"]["all_words"] == "dano moral"
    assert body["filters"]["rapporteur"] == "Relator de Demonstracao"


@pytest.mark.e2e
def test_studio_catalog_count_and_result_fields_are_visible(page: Any, studio_url: str) -> None:
    page.goto(studio_url)

    expect(page.locator(".source-policy")).to_contain_text("6 catalogadas")
    page.locator("[data-preset='all']").click()
    expect(page.locator(".selection-count")).to_have_text("6/6")

    page.locator("#query").fill("responsabilidade civil")
    page.locator("#search-form button[type='submit']").click()

    expect(page.locator(".result")).to_have_count(3)
    first_result = page.locator(".result").first
    expect(first_result).to_contain_text("TJDFT")
    expect(first_result).to_contain_text("0700000-00.2024.8.07.0001")
    expect(first_result).to_contain_text("Des. Relator de Demonstracao")
    expect(first_result).to_contain_text("Turma de Demonstracao")
    expect(first_result).to_contain_text("Responsabilidade civil e reparacao de danos")


@pytest.mark.e2e
def test_studio_can_filter_catalog_without_changing_selection(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    expect(page.locator(".source-card")).to_have_count(6)
    page.locator("#source-filter").fill("TJDFT")

    expect(page.locator(".source-card")).to_have_count(1)
    expect(page.locator(".source-name").first).to_contain_text("TJDFT")
    expect(page.locator(".selection-count")).to_have_text("3/6")
    expect(page.locator(".source-filter-count")).to_contain_text("1 de 6")


@pytest.mark.e2e
def test_studio_runs_explicit_live_validation_and_keeps_states_distinct(
    page: Any, studio_url: str
) -> None:
    page.goto(studio_url)
    page.locator("[data-preset='all']").click()
    page.locator("[data-action='validate']").click()

    panel = page.locator(".validation-panel")
    expect(panel).to_be_visible()
    expect(panel).to_contain_text("valida")
    expect(panel).to_contain_text("vazia")
    expect(panel).to_contain_text("bloqueada")
    expect(panel).to_contain_text("indisponivel")
    expect(panel).to_contain_text("provider_restricted")
    expect(page.locator(".source-meta").filter(has_text="live valida").first).to_be_visible()


@pytest.mark.e2e
def test_studio_empty_state_is_distinct(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    page.locator("#query").fill("vazio")
    page.locator("#search-form button[type='submit']").click()

    expect(page.locator(".empty")).to_contain_text("Nenhum resultado nesta coleta")
    expect(page.locator(".status-chip.ok").first).to_be_visible()
    expect(page.locator(".diagnostics")).to_have_count(0)
    _capture(page, "06-empty-state-desktop.png")


@pytest.mark.e2e
def test_studio_result_can_expand_and_copy(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    page.locator("#query").fill("tese de demonstracao")
    page.locator("#search-form button[type='submit']").click()

    result = page.locator(".result").first
    if result.get_attribute("open") is None:
        result.locator("summary").first.click()
    expect(result.locator(".metadata-grid")).to_be_visible()
    raw_payload = result.locator(".raw-payload")
    expect(raw_payload.locator(".json-view")).to_be_hidden()
    raw_payload.locator("summary").click()
    expect(raw_payload.locator(".json-view")).to_contain_text('"source"')
    document_result = page.locator(".result").filter(
        has=page.locator("a[href='https://example.org/documento-publico']")
    )
    expect(document_result).to_have_count(1)
    if document_result.get_attribute("open") is None:
        document_result.locator("summary").first.click()
    document_link = document_result.locator("a[href='https://example.org/documento-publico']")
    expect(document_link).to_have_count(1)
    expect(document_link).to_be_visible()
    _capture(page, "08-result-expanded-desktop.png")


@pytest.mark.e2e
def test_studio_loads_full_text_on_demand(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    page.locator("#query").fill("tese de demonstracao")
    page.locator("#search-form button[type='submit']").click()

    result = page.locator(".result").first
    if result.get_attribute("open") is None:
        result.locator("summary").first.click()
    result.locator("[data-load-document]").click()

    expect(result.locator(".full-text-panel")).to_contain_text("Inteiro teor carregado")
    expect(result.locator(".full-text-content")).to_contain_text("Inteiro teor publico")
    expect(result.locator(".hash-value")).to_contain_text("a" * 64)


@pytest.mark.e2e
def test_studio_has_no_horizontal_overflow_on_mobile(page: Any, studio_url: str) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(studio_url)
    page.locator("#query").fill("responsabilidade civil")
    page.locator("#search-form button[type='submit']").click()

    expect(page.locator(".result").first).to_be_visible()
    scroll_width = page.locator("body").evaluate("element => element.scrollWidth")
    client_width = page.locator("body").evaluate("element => element.clientWidth")
    assert scroll_width <= client_width
    _capture(page, "11-mobile-results.png")


@pytest.mark.e2e
def test_studio_primary_controls_are_keyboard_reachable(page: Any, studio_url: str) -> None:
    page.goto(studio_url)
    query = page.locator("#query")
    query.focus()
    query.press("Tab")
    expect(page.locator("#search-form button[type='submit']")).to_be_focused()
    page.keyboard.press("Shift+Tab")
    expect(query).to_be_focused()

    first_source = page.get_by_role("checkbox").first
    first_source.focus()
    page.keyboard.press("Space")
    expect(first_source).not_to_be_checked()


def _capture(page: Any, filename: str) -> None:
    if os.getenv("NANOJURIS_CAPTURE_STUDIO") != "1":
        return
    output = ROOT / "artifacts" / "studio"
    output.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=output / filename, full_page=True)
