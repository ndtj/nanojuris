"""Browser acceptance tests for the Workbench migration route."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")
expect = playwright_sync.expect


def _capture(page: Any, filename: str) -> None:
    if os.getenv("NANOJURIS_CAPTURE_WORKBENCH") != "1":
        return
    output = Path("artifacts/workbench")
    output.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=output / filename, full_page=True)


@pytest.mark.e2e
def test_workbench_loads_real_api_mode(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")

    expect(page).to_have_title("NanoJuris Studio")
    expect(page.locator(".wb-shell")).to_be_visible()
    expect(page.locator(".wb-result").first).to_be_visible()
    expect(page.locator(".wb-reader")).to_be_visible()
    expect(page.locator(".wb-sidebar-sources")).to_contain_text("TJDFT")
    expect(page.locator(".wb-sidebar-sources")).to_be_visible()
    expect(page.locator(".wb-columns .wb-source-rail")).to_have_count(0)
    _capture(page, "desktop-search.png")


@pytest.mark.e2e
def test_workbench_reader_and_provenance(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")

    page.locator(".wb-result").first.click()
    expect(page.locator(".wb-reader")).to_be_visible()
    _capture(page, "desktop-reading.png")
    page.locator(".wb-tabs button").nth(3).click()
    expect(page.locator(".wb-trace")).to_contain_text("provider")
    expect(page.locator(".wb-trace")).to_contain_text("extraction_status")
    _capture(page, "desktop-provenance.png")


@pytest.mark.e2e
def test_workbench_states_and_command_palette(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")

    expect(page.locator(".wb-eyebrow")).to_contain_text(re.compile("mock|api"))
    state_picker = page.locator(".wb-toolbar > select:last-child")
    if "mock" in page.locator(".wb-eyebrow").inner_text():
        state_picker.select_option("blocked")
        expect(page.locator(".wb-empty")).to_contain_text("Acesso limitado")
        expect(page.locator(".wb-empty")).not_to_contain_text("Nenhuma correspond")
    else:
        expect(state_picker).to_be_disabled()

    page.get_by_role("button", name="Abrir command palette").click()
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("dialog")).to_have_count(0)


@pytest.mark.e2e
def test_workbench_initial_loading_and_catalog_are_explicit(page: Any, studio_url: str) -> None:
    """The first paint explains the query and exposes the source catalog independently."""

    page.add_init_script(
        """
        (() => {
          const originalFetch = window.fetch.bind(window);
          window.fetch = (input, init) => {
            const url = typeof input === 'string' ? input : input.url;
            if (url.includes('/api/search')) return new Promise(() => {});
            return originalFetch(input, init);
          };
        })();
        """
    )
    page.goto(f"{studio_url}/studio", wait_until="commit")
    page.wait_for_timeout(250)

    expect(page.locator(".wb-loading-state")).to_contain_text("Preparando pesquisa federada")
    expect(page.locator(".wb-loading-state")).to_contain_text(
        "Consultando fontes públicas elegíveis"
    )
    expect(page.locator(".wb-loading-state")).not_to_contain_text("Nenhuma correspondência")
    expect(page.locator(".wb-results")).to_have_attribute("aria-busy", "true")
    expect(page.locator(".wb-result-skeleton")).to_have_count(5)
    expect(page.locator(".wb-sidebar-sources .wb-source-row")).to_have_count(6)
    expect(page.locator(".wb-sidebar-sources")).to_contain_text("TJDFT")
    expect(page.get_by_role("button", name=re.compile("TJDFT"))).to_be_visible()


@pytest.mark.e2e
def test_workbench_search_focus_is_single_compact_control(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")
    page.locator(".wb-search input").focus()

    metrics = page.evaluate(
        """
        () => {
          const search = document.querySelector('.wb-search');
          const input = document.querySelector('.wb-search input');
          const searchStyle = search && getComputedStyle(search);
          const inputStyle = input && getComputedStyle(input);
              return {
            searchHeight: search?.getBoundingClientRect().height,
            inputHeight: input?.getBoundingClientRect().height,
            inputMinHeight: inputStyle?.minHeight,
            inputOutline: inputStyle?.outlineStyle,
            inputShadow: inputStyle?.boxShadow,
            searchShadow: searchStyle?.boxShadow,
          };
        }
        """
    )
    assert metrics["searchHeight"] == 28
    assert metrics["inputHeight"] <= metrics["searchHeight"]
    assert metrics["inputMinHeight"] == "0px"
    assert metrics["inputOutline"] == "none"
    assert metrics["inputShadow"] == "none"
    assert "0px 0px 0px 1px" in metrics["searchShadow"]


@pytest.mark.e2e
def test_workbench_elite_typography_and_touch_targets(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")
    expect(page.locator(".wb-result").first).to_be_visible()
    metrics = page.evaluate(
        """
        () => {
          const measure = (selector) => {
            const element = document.querySelector(selector);
            const style = element && getComputedStyle(element);
            const rect = element?.getBoundingClientRect();
            return {
              fontSize: Number.parseFloat(style?.fontSize || '0'),
              lineHeight: Number.parseFloat(style?.lineHeight || '0'),
              width: rect?.width || 0,
              height: rect?.height || 0,
            };
          };
          return {
            heading: measure('.wb-heading h1'),
            resultTitle: measure('.wb-result h3'),
            resultSummary: measure('.wb-result p'),
            resultMeta: measure('.wb-result-meta'),
            resultAction: measure('.wb-result-actions button'),
            topAction: measure('.wb-topbar .wb-icon-button:not(.wb-mobile-menu)'),
            category: measure('.wb-sidebar-sources h3'),
          };
        }
        """
    )
    assert metrics["heading"]["fontSize"] >= 20
    assert metrics["resultTitle"]["fontSize"] >= 15
    assert metrics["resultSummary"]["fontSize"] >= 13
    assert metrics["resultMeta"]["fontSize"] >= 10.9
    assert metrics["resultAction"]["width"] >= 40
    assert metrics["resultAction"]["height"] >= 40
    assert metrics["topAction"]["width"] >= 40
    assert metrics["topAction"]["height"] >= 40
    assert all(
        "_" not in heading for heading in page.locator(".wb-sidebar-sources h3").all_text_contents()
    )


@pytest.mark.e2e
@pytest.mark.parametrize("width,height", [(1280, 800), (1920, 1080)])
def test_workbench_heading_flow_has_no_vertical_overlap(
    page: Any, studio_url: str, width: int, height: int
) -> None:
    page.set_viewport_size({"width": width, "height": height})
    page.goto(f"{studio_url}/studio")
    expect(page.locator(".wb-result").first).to_be_visible()
    metrics = page.evaluate(
        """
        () => {
          const rect = (selector) => document.querySelector(selector).getBoundingClientRect();
          const heading = rect('.wb-heading');
          const h1 = rect('.wb-heading h1');
          const subtitle = rect('.wb-heading p');
          const actions = rect('.wb-heading-actions');
          const query = rect('.wb-query-line');
          const children = [h1, subtitle, actions];
          const bottom = Math.max(...children.map((item) => item.bottom));
          const overlap = (first, second) => Math.max(
            0,
            Math.min(first.bottom, second.bottom) - Math.max(first.top, second.top),
          );
          return {
            headingHeight: heading.height,
            headingTop: heading.top,
            headingMinHeight: getComputedStyle(document.querySelector('.wb-heading')).minHeight,
            queryTop: query.top,
            contentBottom: bottom,
            queryOverlap: Math.max(...children.map((item) => overlap(item, query))),
            titleOverlap: overlap(h1, subtitle),
          };
        }
        """
    )
    assert metrics["headingHeight"] >= metrics["contentBottom"] - metrics["headingTop"] - 1
    assert metrics["headingMinHeight"] != "0px"
    assert metrics["queryTop"] >= metrics["contentBottom"] - 1
    assert metrics["queryOverlap"] <= 1
    assert metrics["titleOverlap"] <= 1


@pytest.mark.e2e
def test_workbench_mobile_text_and_controls_remain_readable(page: Any, studio_url: str) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{studio_url}/studio")
    expect(page.locator(".wb-result").first).to_be_visible()
    metrics = page.evaluate(
        """
        () => {
          const summary = document.querySelector('.wb-result p');
          const control = document.querySelector('.wb-toolbar button');
          const actions = document.querySelector('.wb-heading-actions');
          const query = document.querySelector('.wb-query-line');
          return {
                summaryFontSize: Number.parseFloat(getComputedStyle(summary).fontSize),
                controlHeight: control.getBoundingClientRect().height,
                actionsBottom: actions.getBoundingClientRect().bottom,
                queryTop: query.getBoundingClientRect().top,
              };
        }
        """
    )
    assert metrics["summaryFontSize"] >= 16
    assert metrics["controlHeight"] >= 44
    assert metrics["queryTop"] >= metrics["actionsBottom"] - 1


@pytest.mark.e2e
def test_workbench_long_summary_cannot_overlap_next_result(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")
    page.locator(".wb-result p").first.evaluate(
        "element => { element.textContent = 'Ementa jurídica longa '.repeat(80); }"
    )

    metrics = page.locator(".wb-result").first.evaluate(
        """
        element => {
          const summary = element.querySelector('p');
          return {
            resultHeight: element.getBoundingClientRect().height,
            resultScrollHeight: element.scrollHeight,
            summaryHeight: summary?.getBoundingClientRect().height,
            summaryScrollHeight: summary?.scrollHeight,
          };
        }
        """
    )
    assert metrics["resultScrollHeight"] <= metrics["resultHeight"] + 1
    assert metrics["summaryHeight"] <= 61.9
    assert metrics["summaryScrollHeight"] >= metrics["summaryHeight"]


@pytest.mark.e2e
def test_workbench_served_text_has_no_mojibake(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")
    text = page.locator(".wb-shell").inner_text()
    assert not re.search(r"Ã[\x80-\xBF]", text)
    assert not re.search(r"Â[\x80-\xBF]", text)
    assert not re.search(r"â[\x80-\xBF]", text)
    assert "�" not in text


@pytest.mark.e2e
def test_workbench_has_no_mobile_horizontal_overflow(page: Any, studio_url: str) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{studio_url}/studio")

    expect(page.locator(".wb-shell")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.locator(".wb-mobile-menu").click()
    expect(page.locator(".wb-sidebar.open")).to_be_visible()
    _capture(page, "mobile-search.png")


@pytest.mark.e2e
def test_workbench_mobile_drawers_start_closed_and_close_with_escape(
    page: Any, studio_url: str
) -> None:
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"{studio_url}/studio")

    expect(page.locator(".wb-reader")).to_be_hidden()
    page.locator(".wb-mobile-menu").click()
    expect(page.locator(".wb-sidebar.open")).to_be_visible()
    expect(page.locator(".wb-drawer-backdrop.is-visible")).to_be_visible()
    assert page.locator(".wb-sidebar").evaluate(
        "element => element.contains(document.activeElement)"
    )
    page.keyboard.press("Escape")
    expect(page.locator(".wb-sidebar.open")).to_have_count(0)
    expect(page.locator(".wb-drawer-backdrop.is-visible")).to_have_count(0)

    page.locator(".wb-result").first.click()
    expect(page.locator(".wb-reader.open")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator(".wb-reader")).to_be_hidden()


@pytest.mark.e2e
def test_workbench_provider_filter_routes_selected_source_and_all_restores(
    page: Any, studio_url: str
) -> None:
    page.goto(f"{studio_url}/studio")

    source_rows = page.locator(".wb-sidebar-sources .wb-source-row")
    assert source_rows.count() >= 2
    assert page.locator(".wb-sidebar-sources input[type=checkbox]").count() == 0

    with page.expect_request("**/api/search") as request_info:
        source_rows.nth(0).click()

    payload = json.loads(request_info.value.post_data or "{}")
    assert len(payload["sources"]) == 1
    assert page.locator(".wb-source-row.is-selected").count() == 1

    with page.expect_request("**/api/search") as request_info:
        page.get_by_role("combobox", name="Provider").select_option("")

    payload = json.loads(request_info.value.post_data or "{}")
    assert payload["sources"] == []
    assert page.evaluate(
        "document.querySelector('.wb-shell').scrollHeight <= window.innerHeight + 1"
    )


@pytest.mark.e2e
def test_workbench_served_bundle_has_no_fabricated_content(page: Any, studio_url: str) -> None:
    page.goto(f"{studio_url}/studio")

    script_urls = page.locator("script[src]").evaluate_all("els => els.map(el => el.src)")
    for script_url in script_urls:
        body = page.request.get(script_url).text()
        assert "mockResults" not in body
        assert "Julgo procedente" not in body
        assert "#fonte-oficial" not in body

    links = page.locator(".wb-reader-link")
    if links.count():
        href = links.first.get_attribute("href")
        assert href and not href.startswith("#")


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("width", "height"),
    [
        (1920, 1080),
        (1440, 900),
        (1280, 800),
        (1180, 800),
        (1024, 768),
        (768, 1024),
        (390, 844),
        (375, 812),
    ],
)
def test_workbench_responsive_contract(page: Any, studio_url: str, width: int, height: int) -> None:
    """Keep the workbench bounded at the target IDE viewports."""

    page.set_viewport_size({"width": width, "height": height})
    page.goto(f"{studio_url}/studio")
    expect(page.locator(".wb-shell")).to_be_visible()
    expect(page.locator(".wb-result").first).to_be_visible()

    metrics = page.evaluate(
        """
        () => {
          const shell = document.querySelector('.wb-shell');
          const topbar = document.querySelector('.wb-topbar');
          const toolbar = document.querySelector('.wb-toolbar');
          const readerBody = document.querySelector('.wb-reader-body');
          const sidebarSources = document.querySelector('.wb-sidebar-sources');
          const rect = shell?.getBoundingClientRect();
          return {
            documentWidth: document.documentElement.scrollWidth,
            documentHeight: document.documentElement.scrollHeight,
            shellWidth: rect?.width,
            shellHeight: rect?.height,
            topbarHeight: topbar?.getBoundingClientRect().height,
            toolbarWidth: toolbar?.clientWidth,
            toolbarScrollWidth: toolbar?.scrollWidth,
            readerOverflowY: readerBody ? getComputedStyle(readerBody).overflowY : null,
            sidebarOverflowY: sidebarSources ? getComputedStyle(sidebarSources).overflowY : null,
          };
        }
        """
    )
    assert metrics["documentWidth"] <= width
    assert metrics["documentHeight"] <= height
    assert metrics["shellWidth"] <= width + 1
    assert metrics["shellHeight"] <= height + 1
    assert 47 <= metrics["topbarHeight"] <= 49
    assert metrics["toolbarScrollWidth"] <= metrics["toolbarWidth"] + 1
    assert metrics["sidebarOverflowY"] == "auto"
    assert page.locator(".wb-sidebar-sources input[type=checkbox]").count() == 0

    if width > 1180:
        expect(page.locator(".wb-reader")).to_be_visible()
        assert metrics["readerOverflowY"] == "auto"
    elif width >= 760:
        expect(page.locator(".wb-reader")).to_have_count(0)
        page.locator(".wb-result").first.click()
        expect(page.locator(".wb-reader.open")).to_be_visible()
        assert (
            page.locator(".wb-reader").evaluate("element => getComputedStyle(element).position")
            == "fixed"
        )
        page.keyboard.press("Escape")
        expect(page.locator(".wb-reader")).to_have_count(0)
    else:
        expect(page.locator(".wb-reader")).to_have_count(0)
        page.locator(".wb-mobile-menu").click()
        expect(page.locator(".wb-sidebar.open")).to_be_visible()
        assert page.locator(".wb-sidebar").evaluate(
            "element => element.contains(document.activeElement)"
        )
        page.keyboard.press("Escape")
        expect(page.locator(".wb-sidebar.open")).to_have_count(0)
        page.locator(".wb-result").first.click()
        expect(page.locator(".wb-reader.open")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.locator(".wb-reader")).to_have_count(0)

    if os.getenv("NANOJURIS_CAPTURE_WORKBENCH") == "1":
        output = Path("artifacts/workbench-responsive")
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=output / f"{width}x{height}.png", full_page=False)
