"""Run a repeatable live QA journey through the NanoJuris Studio UI.

This script is intentionally separate from the deterministic browser suite. It
uses the real Studio API and public providers, captures the rendered interface,
and records observed completeness/full-text states without treating failures as
empty results.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACTS = ROOT / "artifacts" / "studio"

CASES: list[dict[str, Any]] = [
    {
        "id": "responsabilidade-civil",
        "query": "responsabilidade civil",
        "sources": ["tjdf_juris", "tst_jurisprudencia"],
        "purpose": "amostra de referencia com fontes publicas validadas",
    },
    {
        "id": "infanticidio",
        "query": "infanticidio",
        "sources": ["stj_scon", "tjrs_solr", "tjba_graphql", "trf5_jurisprudencia"],
        "purpose": "tese penal com fontes superiores, estadual e federal",
    },
    {
        "id": "improbidade-administrativa",
        "query": "improbidade administrativa",
        "sources": [
            "tjpa_jurisprudencia_bff",
            "tjpb_pje_jurisprudencia",
            "tjpr_jurisprudencia",
            "tjpi_juspi",
        ],
        "purpose": "comparacao entre providers estaduais",
    },
    {
        "id": "acesso-controlado-e-contrato",
        "query": "responsabilidade civil",
        "sources": ["stf_juris", "cjf_jurisprudencia", "tjsp_cjsg", "tjsc_eproc_jurisprudencia"],
        "purpose": "verificacao de diagnosticos sem confundir bloqueio com vazio",
    },
    {
        "id": "tjpr-legado-inteiro-teor",
        "query": "contrato",
        "sources": ["tjpr_jurisprudencia"],
        "mode": "legacy",
        "fetch_details": True,
        "filters": {"published_from": "2025-01-01"},
        "purpose": "compatibilidade legada com filtro nativo e link de inteiro teor",
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8766")
    parser.add_argument("--artifacts-dir", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Arquivo JSON de saida; por padrao, cria um artefato versionado por execucao.",
    )
    parser.add_argument("--timeout", type=int, default=180_000)
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    args.artifacts_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "studio_url": args.url,
        "viewport_cases": {
            "desktop": {"width": 1440, "height": 1000},
            "mobile": {"width": 390, "height": 844},
        },
        "cases": [],
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.headed)
        try:
            context_options = {"ignore_https_errors": _is_local_url(args.url)}
            desktop = browser.new_context(
                viewport={"width": 1440, "height": 1000}, **context_options
            )
            try:
                for case in CASES:
                    report["cases"].append(_run_case(desktop, args.url, case, args))
            finally:
                desktop.close()

            mobile = browser.new_context(viewport={"width": 390, "height": 844}, **context_options)
            try:
                report["mobile_case"] = _run_case(
                    mobile,
                    args.url,
                    CASES[0],
                    args,
                    screenshot_suffix="mobile",
                )
            finally:
                mobile.close()
        finally:
            browser.close()

    output = args.output or (
        args.artifacts_dir
        / f"qa-studio-live-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Artefato: {output}")
    return 0


def _is_local_url(url: str) -> bool:
    """Allow the local self-signed HTTPS certificate in headed/local QA."""

    return bool(re.match(r"^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/|$)", url))


def _run_case(
    context: Any,
    base_url: str,
    case: dict[str, Any],
    args: argparse.Namespace,
    *,
    screenshot_suffix: str = "desktop",
) -> dict[str, Any]:
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console", lambda message: errors.append(message.text) if message.type == "error" else None
    )
    result: dict[str, Any] = {
        "id": case["id"],
        "query": case["query"],
        "sources_requested": case["sources"],
        "purpose": case["purpose"],
        "screenshot": None,
        "browser_errors": errors,
    }
    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=args.timeout)
        page.locator(".source-row-filter[data-source]").first.wait_for(
            state="visible", timeout=args.timeout
        )
        available = set(
            page.locator(".source-row-filter[data-source]").evaluate_all(
                "items => items.map(item => item.dataset.source)"
            )
        )
        selected = [source for source in case["sources"] if source in available]
        missing = [source for source in case["sources"] if source not in available]
        # The production UI intentionally exposes one explicit source selector;
        # use the first requested source for a bounded, reproducible case.
        chosen = selected[0] if selected else next(iter(sorted(available)), "")
        if not chosen:
            raise RuntimeError("nenhuma fonte publica foi carregada")
        page.locator("#search-mode").select_option(case.get("mode", "selected"))
        page.locator("#source").select_option(chosen)
        page.locator("#page-size").select_option("5")
        case_filters = case.get("filters") or {}
        if case.get("fetch_details") or case_filters:
            page.locator("#advanced-filters").click()
        for name, value in case_filters.items():
            field = page.locator(f'[data-search-filter="{name}"]')
            if field.get_attribute("type") == "checkbox":
                field.check(force=True)
            else:
                field.fill(str(value))
        if case.get("fetch_details"):
            page.locator('[data-search-filter="fetch_details"]').check(force=True)
        page.locator("#query").fill(case["query"])
        with page.expect_response(
            lambda response: response.url.endswith("/api/v1/search"),
            timeout=args.timeout,
        ) as response_info:
            page.locator("#search-form button[type='submit']").click()
        response = response_info.value
        payload = response.json()
        # The API response is the synchronization point.  A short render
        # settle avoids coupling QA to transient button-state animations while
        # still ensuring cards/reader are present before the screenshot.
        page.wait_for_timeout(500)

        slug = f"live-{case['id']}-{screenshot_suffix}"
        screenshot = args.artifacts_dir / f"{slug}.png"
        page.screenshot(path=screenshot, full_page=True)
        result.update(
            {
                "http_status": response.status,
                "available_sources": sorted(available),
                "sources_selected": [chosen],
                "sources_missing": missing,
                "payload": _payload_summary(payload),
                "rendered": _rendered_summary(page),
                "screenshot": str(screenshot),
            }
        )
    except PlaywrightTimeoutError as exc:
        result["error"] = f"timeout: {exc}"
        page.screenshot(
            path=args.artifacts_dir / f"live-{case['id']}-{screenshot_suffix}-timeout.png",
            full_page=True,
        )
    except Exception as exc:  # noqa: BLE001 - QA runner must report the case and continue
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        page.close()
    return result


def _payload_summary(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results") or []
    return {
        "total_available": payload.get("total_available"),
        "total_returned": payload.get("total_returned", len(results)),
        "deduplicated_total": payload.get("deduplicated_total"),
        "searched_sources": payload.get("searched_sources", []),
        "skipped_sources": payload.get("skipped_sources", []),
        "errors": payload.get("errors", []),
        "source_status": payload.get("source_status", {}),
        "source_completeness": payload.get("source_completeness", {}),
        "collection_complete": payload.get("collection_complete"),
        "completeness_reason": payload.get("completeness_reason"),
        "results": [_result_summary(item) for item in results],
    }


def _rendered_summary(page: Any) -> dict[str, Any]:
    text_script = "items => items.map(item => item.textContent?.trim()).filter(Boolean)"
    return {
        "result_cards": page.locator(".result").count(),
        "nonempty_titles": page.locator(".result h2").evaluate_all(text_script),
        "nonempty_excerpts": page.locator(".result > p").evaluate_all(text_script),
        "ranking_score_chips": page.locator(".ranking-score").count(),
        "ranking_native_chips": page.locator(".ranking-native").count(),
        "query_state": page.locator("#query-state").inner_text(),
        "notice": page.locator("#notice").inner_text()
        if page.locator("#notice").count() and not page.locator("#notice").get_attribute("hidden")
        else None,
        "reader_source": page.locator("#reader .reader-source").inner_text()
        if page.locator("#reader .reader-source").count()
        else None,
        "reader_full_text": page.locator("#reader .reader-full-text").count(),
        "reader_official_link": page.locator("#reader .reader-source-link").count(),
        "replacement_chars": page.evaluate(
            "document.body.innerText.split('').filter(char => char === '\\ufffd').length"
        ),
        "horizontal_overflow": page.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth"
        ),
    }


def _result_summary(item: dict[str, Any]) -> dict[str, Any]:
    trace = item.get("extraction_trace") or {}
    return {
        "id": item.get("id"),
        "source": item.get("source"),
        "court": item.get("court"),
        "title": item.get("title") or item.get("case_class") or item.get("decision_type"),
        "case_number": item.get("case_number") or item.get("number"),
        "summary_present": bool(item.get("summary") or item.get("thesis") or item.get("full_text")),
        "full_text_status": item.get("full_text_status")
        or (
            "loaded"
            if item.get("full_text")
            else "document_available"
            if item.get("document_url")
            else "not_returned"
        ),
        "document_url": item.get("document_url") or item.get("url"),
        "access_status": item.get("access_status") or trace.get("access_status"),
        "extraction_status": item.get("extraction_status") or trace.get("extraction_status"),
        "content_sha256": trace.get("content_sha256"),
        "response_bytes": trace.get("response_bytes"),
        "source_url": trace.get("source_url"),
        "text_sample": _text_sample(item),
    }


def _text_sample(item: dict[str, Any]) -> str:
    value = item.get("summary") or item.get("thesis") or item.get("full_text") or ""
    return re.sub(r"\\s+", " ", str(value)).strip()[:240]


if __name__ == "__main__":
    raise SystemExit(main())
