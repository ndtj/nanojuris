"""Bounded HTTP discovery client."""

from __future__ import annotations

import time
import uuid
from collections.abc import Mapping
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from requests import Response as RequestsResponse

from nanojuris.discovery.extract import (
    extract_filter_candidates,
    extract_route_candidates,
    suggest_selector_candidates,
)
from nanojuris.discovery.cache import DiscoveryCache
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


class HttpDiscoveryClient:
    """Discover public routes using a clean, bounded requests session."""

    def __init__(
        self,
        policy: DiscoveryPolicy,
        *,
        session: requests.Session | None = None,
        cache_dir: str | None = None,
    ) -> None:
        self.policy = policy
        self.session = session or requests.Session()
        self.session.trust_env = False
        self.session.headers.update({"User-Agent": policy.user_agent})
        self._robots: dict[str, RobotFileParser | None] = {}
        self.cache = DiscoveryCache(cache_dir) if cache_dir else None

    def discover(self, url: str, *, method: str = "GET", query: Mapping[str, Any] | None = None, body: Any = None) -> DiscoveryRun:
        run = DiscoveryRun(run_id=uuid.uuid4().hex, started_at=_utc_now(), policy=self.policy)
        evidence = self.fetch(
            run_id=run.run_id,
            seed_url=url,
            request=DiscoveryRequest(method=method, url=url, query=dict(query or {}), body=body),
        )
        run.evidences.append(evidence)
        run.finished_at = _utc_now()
        return run

    def fetch(self, *, run_id: str, seed_url: str, request: DiscoveryRequest) -> DiscoveryEvidence:
        assert_allowed_url(request.url, self.policy)
        if self.cache is not None:
            cached = self.cache.get(request)
            if cached is not None:
                cached.run_id = run_id
                cached.seed_url = seed_url
                cached.source = "cache"
                cached.limitations = [*cached.limitations, "response replayed from discovery cache"]
                return cached
        if self.policy.respect_robots and not self._can_fetch(request.url):
            response = DiscoveryResponse(
                status_code=None,
                url=request.url,
                final_url=request.url,
                transport_status="robots_disallowed",
            )
            return DiscoveryEvidence(
                run_id=run_id,
                captured_at=_utc_now(),
                seed_url=seed_url,
                request=request,
                response=response,
                status=DiscoveryStatus.ROBOTS_DISALLOWED,
                limitations=["robots.txt disallowed this URL"],
            )

        current_url = request.url
        redirects: list[dict[str, Any]] = []
        started = time.perf_counter()
        response: RequestsResponse | None = None
        body_bytes = b""
        transport_status = "complete"
        error_type: str | None = None
        error: str | None = None
        try:
            for _ in range(self.policy.max_redirects + 1):
                assert_allowed_url(current_url, self.policy)
                response = self.session.request(
                    request.method.upper(),
                    current_url,
                    params=request.query,
                    json=request.body if request.method.upper() not in {"GET", "HEAD"} else None,
                    timeout=self.policy.timeout_seconds,
                    allow_redirects=False,
                    headers=request.headers,
                    stream=True,
                )
                location = response.headers.get("Location")
                if response.is_redirect and location:
                    redirects.append({"status": response.status_code, "url": current_url, "location": location})
                    current_url = urljoin(current_url, location)
                    response.close()
                    continue
                body_bytes = _read_bounded(response, self.policy.max_bytes_per_response)
                break
            else:
                transport_status = "redirect_limit"
                error_type = "redirect_limit"
                error = "redirect limit exceeded"
        except ValueError as exc:
            transport_status, error_type, error = "redirect_outside_allowlist", "redirect_outside_allowlist", str(exc)
        except requests.exceptions.Timeout as exc:
            transport_status, error_type, error = "timeout", "timeout", str(exc)
        except requests.exceptions.SSLError as exc:
            transport_status, error_type, error = "tls_error", "tls_error", str(exc)
        except requests.exceptions.RequestException as exc:
            transport_status, error_type, error = "source_unavailable", "request_error", str(exc)
        finally:
            if response is not None:
                response.close()

        elapsed_ms = (time.perf_counter() - started) * 1000
        status_code = response.status_code if response is not None and transport_status == "complete" else None
        content_type = response.headers.get("Content-Type", "") if response is not None else ""
        response_model = DiscoveryResponse(
            status_code=status_code,
            url=request.url,
            final_url=current_url if status_code is not None else None,
            content_type=content_type,
            headers=redact_headers(response.headers if response is not None else {}),
            body=body_bytes,
            elapsed_ms=elapsed_ms,
            redirects=redirects,
            transport_status=transport_status,
            error_type=error_type,
            error=error,
        )
        route_candidates = extract_route_candidates(request.url, body_bytes, content_type)
        filter_candidates = extract_filter_candidates(request.url, body_bytes, content_type)
        selector_candidates = suggest_selector_candidates(
            body_bytes,
            {
                "decision_text": ("ementa", "decisão", "decisao"),
                "rapporteur": ("relator", "relatora"),
                "judging_body": ("órgão julgador", "orgao julgador", "turma", "câmara"),
                "full_text": ("inteiro teor", "documento", "pdf"),
            },
        )
        probe = analyze_route_response(
            url=request.url,
            final_url=response_model.final_url,
            method=request.method,
            status_code=response_model.status_code or 0,
            content=body_bytes,
            content_type=content_type,
            elapsed_ms=elapsed_ms,
        )
        status = (
            _status_from_transport(transport_status)
            if transport_status != "complete"
            else _status_from_probe(probe.route_status, response_model)
        )
        limitations: list[str] = []
        if response_model.response_bytes >= self.policy.max_bytes_per_response:
            limitations.append("response body bounded by max_bytes_per_response")
        if probe.recommendation:
            limitations.append(probe.recommendation)
        evidence = DiscoveryEvidence(
            run_id=run_id,
            captured_at=_utc_now(),
            seed_url=seed_url,
            request=DiscoveryRequest(
                method=request.method,
                url=request.url,
                query=dict(request.query),
                body=redact_payload(request.body),
                headers=redact_headers(request.headers),
            ),
            response=response_model,
            status=status,
            access_status=_access_status(status),
            extraction_status=_extraction_status(status, bool(body_bytes)),
            route_candidates=route_candidates,
            selector_candidates=selector_candidates,
            filter_candidates=filter_candidates,
            access_signals=probe.access_signals,
            legal_signals=probe.legal_signals,
            limitations=limitations,
        )
        if self.cache is not None:
            self.cache.put(evidence)
        return evidence

    def _can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots:
            robots_url = f"{origin}/robots.txt"
            try:
                response = self.session.get(robots_url, timeout=self.policy.timeout_seconds, allow_redirects=False)
                if response.status_code == 404:
                    parser: RobotFileParser | None = None
                elif 200 <= response.status_code < 300:
                    parser = RobotFileParser()
                    parser.set_url(robots_url)
                    parser.parse(response.text.splitlines())
                else:
                    parser = RobotFileParser()
                    parser.parse(["User-agent: *", "Disallow: /"])
                self._robots[origin] = parser
            except requests.RequestException:
                self._robots[origin] = RobotFileParser()
                self._robots[origin].parse(["User-agent: *", "Disallow: /"])
        parser = self._robots[origin]
        return parser is None or parser.can_fetch(self.policy.user_agent, url)


def _read_bounded(response: RequestsResponse, maximum: int) -> bytes:
    chunks: list[bytes] = []
    remaining = maximum
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        chunks.append(chunk[:remaining])
        remaining -= len(chunks[-1])
        if remaining <= 0:
            break
    return b"".join(chunks)


def _status_from_transport(transport_status: str) -> DiscoveryStatus:
    return {
        "timeout": DiscoveryStatus.TIMEOUT,
        "tls_error": DiscoveryStatus.TLS_ERROR,
        "source_unavailable": DiscoveryStatus.SOURCE_UNAVAILABLE,
        "redirect_limit": DiscoveryStatus.SOURCE_UNAVAILABLE,
        "redirect_outside_allowlist": DiscoveryStatus.REDIRECT_OUTSIDE_ALLOWLIST,
    }.get(transport_status, DiscoveryStatus.UNKNOWN)


def _status_from_response(response: DiscoveryResponse) -> DiscoveryStatus:
    status_code = response.status_code
    if status_code is None:
        return DiscoveryStatus.UNKNOWN
    if status_code in {401, 403, 407, 451}:
        return DiscoveryStatus.ACCESS_CONTROLLED
    if status_code == 429:
        return DiscoveryStatus.RATE_LIMITED
    if status_code == 404:
        return DiscoveryStatus.EMPTY
    if status_code >= 500:
        return DiscoveryStatus.SOURCE_UNAVAILABLE
    if 200 <= status_code < 300:
        return DiscoveryStatus.VALID if response.body else DiscoveryStatus.EMPTY
    return DiscoveryStatus.UNKNOWN


def _status_from_probe(route_status: str, response: DiscoveryResponse) -> DiscoveryStatus:
    """Prefer content-aware route classification over status-only heuristics."""

    mapped = {
        "live_valid": DiscoveryStatus.VALID,
        "candidate": DiscoveryStatus.CANDIDATE,
        "partial_response": DiscoveryStatus.CANDIDATE,
        "access_control_or_login": DiscoveryStatus.ACCESS_CONTROLLED,
        "not_found": DiscoveryStatus.EMPTY,
        "source_unavailable": DiscoveryStatus.SOURCE_UNAVAILABLE,
        "invalid_response": DiscoveryStatus.UNKNOWN,
    }
    return mapped.get(route_status, _status_from_response(response))


def _access_status(status: DiscoveryStatus):
    from nanojuris.models import AccessStatus

    if status == DiscoveryStatus.ACCESS_CONTROLLED:
        return AccessStatus.ACCESS_CONTROL_REQUIRED
    if status == DiscoveryStatus.REDIRECT_OUTSIDE_ALLOWLIST:
        return AccessStatus.ACCESS_CONTROL_REQUIRED
    if status in {DiscoveryStatus.SOURCE_UNAVAILABLE, DiscoveryStatus.TIMEOUT, DiscoveryStatus.TLS_ERROR}:
        return AccessStatus.SOURCE_UNAVAILABLE
    if status == DiscoveryStatus.EMPTY:
        return AccessStatus.NOT_FOUND
    return AccessStatus.PUBLIC if status in {DiscoveryStatus.VALID, DiscoveryStatus.CANDIDATE} else AccessStatus.PARTIAL


def _extraction_status(status: DiscoveryStatus, has_body: bool):
    from nanojuris.models import ExtractionStatus

    if status == DiscoveryStatus.EMPTY or not has_body:
        return ExtractionStatus.EMPTY
    if status in {DiscoveryStatus.ACCESS_CONTROLLED, DiscoveryStatus.RATE_LIMITED}:
        return ExtractionStatus.PARTIAL
    if status in {DiscoveryStatus.SOURCE_UNAVAILABLE, DiscoveryStatus.TIMEOUT, DiscoveryStatus.TLS_ERROR}:
        return ExtractionStatus.FAILED
    return ExtractionStatus.COMPLETE


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
