"""Route and selector candidate extraction from captured public content."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from urllib.parse import urljoin, urlparse

from nanojuris.discovery.models import FilterCandidate, RouteCandidate, SelectorCandidate
from nanojuris.parsing import parse_html

_ENDPOINT_RE = re.compile(
    r"(?:fetch|axios\.(?:get|post|put|delete)|url)\s*\(\s*['\"]([^'\"]+)",
    re.I,
)
_URL_RE = re.compile(r"(?<![\w])(?:https?://|/)[A-Za-z0-9_./?=&%:#-]{2,}")


def extract_route_candidates(
    base_url: str,
    body: bytes,
    content_type: str = "",
    *,
    depth: int = 0,
) -> list[RouteCandidate]:
    """Extract deduplicated links, forms and likely API endpoints."""

    text = body.decode("utf-8", errors="replace")
    candidates: list[RouteCandidate] = []
    if "html" in content_type.lower() or "<html" in text.lower() or "<a " in text.lower():
        document = parse_html(body)
        for tag_name, attribute, source, reason, confidence in (
            ("a", "href", "link", "HTML link", 0.55),
            ("link", "href", "asset", "HTML resource link", 0.35),
            ("script", "src", "script", "script source", 0.40),
        ):
            for tag in document.css(tag_name):
                value = tag.get(attribute)
                if isinstance(value, str):
                    _append_candidate(
                        candidates,
                        base_url,
                        value,
                        source,
                        reason,
                        confidence,
                        depth,
                    )
        for form in document.forms():
            action = form.get("action") or base_url
            _append_candidate(
                candidates,
                base_url,
                action,
                "form",
                "HTML form action",
                0.70,
                depth,
                method=str(form.get("method") or "GET").upper(),
            )
        for script in document.css("script"):
            _extract_script_candidates(candidates, base_url, script.text(strip=False), depth)

    if "json" in content_type.lower() or text.lstrip().startswith(("{", "[")):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if payload is not None:
            for value in _walk_strings(payload):
                if _looks_like_endpoint(value):
                    _append_candidate(
                        candidates,
                        base_url,
                        value,
                        "json",
                        "JSON string endpoint",
                        0.60,
                        depth,
                    )

    for value in _URL_RE.findall(text):
        if "/api" in value.lower() or "search" in value.lower() or "juris" in value.lower():
            _append_candidate(
                candidates,
                base_url,
                value,
                "text",
                "endpoint-like text",
                0.35,
                depth,
            )
    return candidates


def suggest_selector_candidates(
    html: bytes,
    field_labels: Mapping[str, Iterable[str]],
) -> list[SelectorCandidate]:
    """Suggest structural selectors; never treats them as canonical parsers."""

    document = parse_html(html)
    suggestions: list[SelectorCandidate] = []
    for field, labels in field_labels.items():
        for label in labels:
            matches = document.find_by_text(label)
            if not matches:
                continue
            tag = matches.first
            if tag is None:
                continue
            selector = tag.generate_css_selector()
            count = len(document.css(selector)) if selector else len(matches)
            confidence = 0.75 if count == 1 else 0.45 if count <= 3 else 0.25
            suggestions.append(
                SelectorCandidate(
                    field=field,
                    selector=selector,
                    label=label,
                    matches=count,
                    confidence=confidence,
                    evidence=f"label:{label}; structural-match-count:{count}",
                )
            )
            break
    return suggestions


def extract_filter_candidates(
    base_url: str,
    body: bytes,
    content_type: str = "",
) -> list[FilterCandidate]:
    """Extract observable search fields without claiming a canonical contract.

    HTML inputs/selects and shallow JSON keys are evidence only. Values are
    bounded and never submitted automatically by discovery.
    """

    text = body.decode("utf-8", errors="replace")
    candidates: list[FilterCandidate] = []
    if "html" in content_type.lower() or "<form" in text.lower() or "<input" in text.lower():
        document = parse_html(body)
        for form in document.forms():
            for field_node in form.css("input, select, textarea"):
                name = str(field_node.get("name") or field_node.get("id") or "").strip()
                if not name:
                    continue
                field_type = str(field_node.get("type") or field_node.tag or "unknown").lower()
                label = str(
                    field_node.get("aria-label") or field_node.get("placeholder") or ""
                ).strip()
                values: list[str] = []
                if field_node.tag == "select":
                    values = [
                        option.get("value") or option.visible_text()
                        for option in field_node.css("option")
                        if (option.get("value") or option.visible_text())
                    ][:50]
                required = field_node.get("required") is not None
                candidate = FilterCandidate(
                    name=name,
                    field_type=field_type,
                    label=label,
                    values=[str(value) for value in values],
                    required=required,
                    source="html_form",
                    confidence=0.85 if form.get("action") else 0.70,
                    evidence=f"form:{form.get('action') or base_url};name:{name}",
                )
                _append_filter(candidates, candidate)

    if "json" in content_type.lower() or text.lstrip().startswith(("{", "[")):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, Mapping):
            for name, value in payload.items():
                if not isinstance(name, str) or not _looks_like_filter_name(name):
                    continue
                values = value if isinstance(value, list) else []
                _append_filter(
                    candidates,
                    FilterCandidate(
                        name=name,
                        field_type="json_array"
                        if isinstance(value, list)
                        else type(value).__name__,
                        values=[str(item) for item in values[:50]],
                        source="json_key",
                        confidence=0.55,
                        evidence=f"json-key:{name}",
                    ),
                )
    return candidates


def _append_filter(candidates: list[FilterCandidate], candidate: FilterCandidate) -> None:
    if not any(
        item.name == candidate.name and item.source == candidate.source for item in candidates
    ):
        candidates.append(candidate)


def _looks_like_filter_name(name: str) -> bool:
    lowered = name.lower()
    return any(
        marker in lowered
        for marker in (
            "filter",
            "filtro",
            "query",
            "search",
            "page",
            "sort",
            "tipo",
            "classe",
            "orgao",
            "relator",
            "data",
        )
    )


def _append_candidate(
    candidates: list[RouteCandidate],
    base_url: str,
    value: str,
    source: str,
    reason: str,
    confidence: float,
    depth: int,
    *,
    method: str = "GET",
) -> None:
    value = value.strip()
    if not value or value.startswith(("#", "javascript:", "mailto:", "tel:")):
        return
    url = urljoin(base_url, value)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return
    key = (method.upper(), url)
    if any((candidate.method, candidate.url) == key for candidate in candidates):
        return
    candidates.append(
        RouteCandidate(
            url=url,
            method=method.upper(),
            source=source,
            reason=reason,
            confidence=confidence,
            depth=depth + 1,
        )
    )


def _extract_script_candidates(
    candidates: list[RouteCandidate],
    base_url: str,
    script: str,
    depth: int,
) -> None:
    for value in _ENDPOINT_RE.findall(script):
        _append_candidate(candidates, base_url, value, "script", "script API call", 0.65, depth)


def _walk_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def _looks_like_endpoint(value: str) -> bool:
    lowered = value.lower()
    return value.startswith(("/", "http://", "https://")) and any(
        marker in lowered for marker in ("/api", "search", "juris", "document", "query")
    )
