"""Redaction helpers for transport logs and persisted evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_SECRET_PARTS = {
    "authorization",
    "cookie",
    "proxy-authorization",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "api_key",
    "apikey",
    "password",
    "passwd",
    "secret",
    "credential",
    "session",
}


def _secret_name(name: str) -> bool:
    normalized = name.casefold().replace("-", "_")
    return any(part in normalized for part in _SECRET_PARTS)


def redact_url(value: str) -> str:
    """Keep scheme/host/path while replacing sensitive query values."""

    try:
        parsed = urlsplit(value)
    except ValueError:
        return "[REDACTED_URL]"
    if not parsed.scheme or not parsed.netloc:
        return "[REDACTED_URL]"
    query = [
        (name, "[REDACTED]" if _secret_name(name) else item)
        for name, item in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    hostname = parsed.hostname or "unknown-host"
    netloc = hostname
    if parsed.port is not None:
        netloc += f":{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, urlencode(query), ""))


def redact_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(key): "[REDACTED]" if _secret_name(str(key)) else str(value)
        for key, value in headers.items()
    }


def redact_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): "[REDACTED]" if _secret_name(str(key)) else redact_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_payload(item) for item in value]
    if isinstance(value, bytes):
        return "[REDACTED_BYTES]"
    if isinstance(value, str):
        if len(value) > 512:
            return value[:512] + "…[TRUNCATED]"
        try:
            return redact_payload(json.loads(value))
        except json.JSONDecodeError:
            return value
    return value
