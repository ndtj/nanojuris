"""Optional Playwright discovery adapter.

The adapter captures public document/XHR/fetch responses. It intentionally has
no proxy, cookie, CDP, stealth or challenge-solving configuration.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any

from nanojuris.discovery.extract import extract_filter_candidates, extract_route_candidates, suggest_selector_candidates
from nanojuris.discovery.http import _access_status, _extraction_status, _status_from_probe
from nanojuris.discovery.models import (
    DiscoveryEvidence,
    DiscoveryPolicy,
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryRun,
    DiscoveryStatus,
)
from nanojuris.discovery.policy import assert_allowed_url, redact_headers, redact_payload
from nanojuris.route_probe import analyze_route_response


class BrowserDiscoveryClient:
    """Capture a bounded public browser session when Playwright is installed."""

    def __init__(self, policy: DiscoveryPolicy) -> None:
        self.policy = policy

    def discover(self, url: str) -> DiscoveryRun:
        assert_allowed_url(url, self.policy)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("modo browser requer a dependência opcional playwright") from exc

        run = DiscoveryRun(run_id=uuid.uuid4().hex, started_at=_utc_now(), policy=self.policy)
        captured: list[DiscoveryEvidence] = []
        started = time.perf_counter()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            def allow_route(route: Any) -> None:
                if self._allowed_browser_request(route.request.url):
                    route.continue_()
                else:
                    route.abort()

            def observe(response: Any) -> None:
                if len(captured) >= self.policy.max_browser_responses:
                    return
                resource_type = response.request.resource_type
                if resource_type not in {"document", "xhr", "fetch"}:
                    return
                try:
                    body = response.body()[: self.policy.max_bytes_per_response]
                except Exception:
                    body = b""
                request = response.request
                request_model = DiscoveryRequest(
                    method=request.method,
                    url=request.url,
                    body=redact_payload(request.post_data),
                    headers=redact_headers(request.headers),
                )
                response_model = DiscoveryResponse(
                    status_code=response.status,
                    url=request.url,
                    final_url=response.url,
                    content_type=response.headers.get("content-type", ""),
                    headers=redact_headers(response.headers),
                    body=body,
                    elapsed_ms=(time.perf_counter() - started) * 1000,
                )
                probe = analyze_route_response(
                    url=request.url,
                    final_url=response.url,
                    method=request.method,
                    status_code=response.status,
                    content=body,
                    content_type=response_model.content_type,
                    elapsed_ms=response_model.elapsed_ms,
                )
                status = _status_from_probe(probe.route_status, response_model)
                captured.append(
                    DiscoveryEvidence(
                        run_id=run.run_id,
                        captured_at=_utc_now(),
                        seed_url=url,
                        request=request_model,
                        response=response_model,
                        status=status,
                        access_status=_access_status(status),
                        extraction_status=_extraction_status(status, bool(body)),
                        route_candidates=extract_route_candidates(request.url, body, response_model.content_type),
                        filter_candidates=extract_filter_candidates(request.url, body, response_model.content_type),
                        selector_candidates=suggest_selector_candidates(
                            body, {"decision_text": ("ementa", "decisão", "decisao")}
                        ),
                        access_signals=probe.access_signals,
                        legal_signals=probe.legal_signals,
                        limitations=["captured by optional Playwright browser"],
                        source=resource_type,
                    )
                )

            page.route("**/*", allow_route)
            page.on("response", observe)
            try:
                page.goto(url, wait_until="networkidle", timeout=int(self.policy.timeout_seconds * 1000))
            except Exception as exc:
                captured.append(
                    DiscoveryEvidence(
                        run_id=run.run_id,
                        captured_at=_utc_now(),
                        seed_url=url,
                        request=DiscoveryRequest(method="GET", url=url),
                        response=DiscoveryResponse(
                            status_code=None,
                            url=url,
                            transport_status="timeout",
                            error_type=type(exc).__name__,
                            error=str(exc),
                        ),
                        status=DiscoveryStatus.TIMEOUT,
                        limitations=["browser navigation failed or timed out"],
                        source="browser",
                    )
                )
            finally:
                context.close()
                browser.close()
        run.evidences = captured
        run.finished_at = _utc_now()
        return run

    def _allowed_browser_request(self, url: str) -> bool:
        from nanojuris.discovery.policy import is_allowed_url

        return is_allowed_url(url, self.policy)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
