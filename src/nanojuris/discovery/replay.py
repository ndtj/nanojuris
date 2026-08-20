"""Offline persistence and replay for discovery evidence."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from nanojuris.discovery.extract import (
    extract_filter_candidates,
    extract_route_candidates,
    suggest_selector_candidates,
)
from nanojuris.discovery.models import (
    DiscoveryEvidence,
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryStatus,
    FilterCandidate,
    RouteCandidate,
    SelectorCandidate,
)
from nanojuris.models import AccessStatus, ExtractionStatus
from nanojuris.route_probe import analyze_route_response


def write_evidence(evidence: DiscoveryEvidence, path: str | Path) -> None:
    """Write one evidence envelope, including bounded body bytes."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(evidence.to_dict(include_body=True), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_evidence(path: str | Path) -> DiscoveryEvidence:
    """Load one evidence envelope or the first evidence from a run artifact."""

    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    if "evidences" in payload:
        evidences = payload.get("evidences") or []
        if not evidences:
            raise ValueError("artefato de discovery não contém evidências")
        payload = evidences[0]
    request_payload = payload["request"]
    response_payload = payload["response"]
    body = base64.b64decode(response_payload.get("body_base64", ""))
    return DiscoveryEvidence(
        run_id=str(payload["run_id"]),
        captured_at=str(payload["captured_at"]),
        seed_url=str(payload["seed_url"]),
        request=DiscoveryRequest(
            method=str(request_payload.get("method", "GET")),
            url=str(request_payload["url"]),
            query=dict(request_payload.get("query") or {}),
            body=request_payload.get("body"),
            headers=dict(request_payload.get("headers") or {}),
        ),
        response=DiscoveryResponse(
            status_code=response_payload.get("status_code"),
            url=str(response_payload["url"]),
            final_url=response_payload.get("final_url"),
            content_type=str(response_payload.get("content_type", "")),
            headers=dict(response_payload.get("headers") or {}),
            body=body,
            elapsed_ms=response_payload.get("elapsed_ms"),
            redirects=list(response_payload.get("redirects") or []),
            transport_status=str(response_payload.get("transport_status", "complete")),
            error_type=response_payload.get("error_type"),
            error=response_payload.get("error"),
        ),
        status=DiscoveryStatus(str(payload["status"])),
        access_status=AccessStatus(str(payload.get("access_status", AccessStatus.PARTIAL.value))),
        extraction_status=ExtractionStatus(
            str(payload.get("extraction_status", ExtractionStatus.PARTIAL.value))
        ),
        route_candidates=[
            RouteCandidate(**candidate) for candidate in payload.get("route_candidates", [])
        ],
        selector_candidates=[
            SelectorCandidate(**candidate) for candidate in payload.get("selector_candidates", [])
        ],
        filter_candidates=[
            FilterCandidate(**candidate) for candidate in payload.get("filter_candidates", [])
        ],
        access_signals=dict(payload.get("access_signals") or {}),
        legal_signals=dict(payload.get("legal_signals") or {}),
        limitations=list(payload.get("limitations") or []),
        source=str(payload.get("source", "cache")),
    )


def read_body(path: str | Path) -> bytes:
    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    return base64.b64decode(payload["response"]["body_base64"])


def replay_analysis(path: str | Path) -> dict[str, Any]:
    """Re-run analysis from a stored body without accessing the network."""

    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    if "evidences" in payload:
        evidences = payload.get("evidences") or []
        if not evidences:
            raise ValueError("artefato de discovery não contém evidências")
        payload = evidences[0]
    body = base64.b64decode(payload["response"]["body_base64"])
    request = payload["request"]
    response = payload["response"]
    probe = analyze_route_response(
        url=request["url"],
        final_url=response.get("final_url"),
        method=request.get("method", "GET"),
        status_code=response.get("status_code"),
        content=body,
        content_type=response.get("content_type", ""),
        elapsed_ms=response.get("elapsed_ms"),
    )
    return {
        "probe": probe.to_dict(),
        "route_candidates": [
            candidate.to_dict()
            for candidate in extract_route_candidates(
                request["url"], body, response.get("content_type", "")
            )
        ],
        "selector_candidates": [
            candidate.to_dict()
            for candidate in suggest_selector_candidates(
                body, {"decision_text": ("ementa", "decisão", "decisao")}
            )
        ],
        "filter_candidates": [
            candidate.to_dict()
            for candidate in extract_filter_candidates(
                request["url"], body, response.get("content_type", "")
            )
        ],
    }
