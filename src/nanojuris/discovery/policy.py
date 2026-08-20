"""URL safety, bounds and redaction policy for discovery."""

from __future__ import annotations

import ipaddress
import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

from nanojuris.discovery.models import DiscoveryPolicy

_SECRET_WORDS = ("authorization", "cookie", "password", "passwd", "secret", "token", "session", "api_key", "apikey")


def hostname_for(url: str) -> str:
    parsed = urlparse(url)
    return (parsed.hostname or "").lower().rstrip(".")


def is_private_destination(url: str) -> bool:
    """Reject literal private/reserved destinations before any network call."""

    hostname = hostname_for(url)
    if not hostname:
        return True
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def is_allowed_url(url: str, policy: DiscoveryPolicy) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        return False
    if is_private_destination(url):
        return False
    hostname = hostname_for(url)
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in policy.allowed_domains)


def assert_allowed_url(url: str, policy: DiscoveryPolicy) -> None:
    if not is_allowed_url(url, policy):
        raise ValueError(f"URL fora da política de descoberta: {url}")


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(word in normalized for word in _SECRET_WORDS)


def redact_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, (list, tuple)):
        return [redact_value(item) for item in value]
    if isinstance(value, bytes):
        return "<redacted-bytes>"
    if isinstance(value, str) and len(value) > 4096:
        return f"{value[:4096]}…<truncated>"
    return value


def redact_mapping(values: Mapping[Any, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values.items():
        text_key = str(key)
        result[text_key] = "<redacted>" if _is_secret_key(text_key) else redact_value(value)
    return result


def redact_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    return {key: str(value) if not _is_secret_key(key) else "<redacted>" for key, value in headers.items()}


def redact_payload(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return redact_value(json.loads(value))
        except json.JSONDecodeError:
            return "<redacted-text>" if len(value) > 512 else value
    return redact_value(value)
