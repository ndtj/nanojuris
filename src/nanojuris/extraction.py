"""Reusable extraction pipeline primitives."""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.models import (
    AccessStatus,
    ExtractionStatus,
    ExtractionTrace,
    SourceTrace,
    utc_now_iso,
)


@dataclass(slots=True)
class FetchRequest:
    """HTTP acquisition request for a public source."""

    source: str
    url: str
    endpoint: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    json: dict[str, Any] | None = None
    timeout: float | None = None
    query: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FetchedContent:
    """Raw content fetched from a public source."""

    source: str
    url: str
    status_code: int
    content: bytes
    content_type: str | None = None
    encoding: str | None = None
    retrieved_at: str = field(default_factory=utc_now_iso)
    access_status: AccessStatus = AccessStatus.PARTIAL
    source_trace: SourceTrace | None = None

    @property
    def text(self) -> str:
        """Decode fetched bytes as text."""

        return self.content.decode(self.encoding or "utf-8", errors="replace")

    @property
    def sha256(self) -> str:
        """Return a stable hash for fetched bytes."""

        return hashlib.sha256(self.content).hexdigest()

    @property
    def byte_size(self) -> int:
        """Return the content size in bytes."""

        return len(self.content)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["content"] = self.text
        payload["sha256"] = self.sha256
        payload["byte_size"] = self.byte_size
        return payload


@dataclass(slots=True)
class ParsedContent:
    """Intermediate parser output before canonical mapping."""

    source: str
    parser: str
    parser_version: str
    records: list[dict[str, Any]] = field(default_factory=list)
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    extraction_trace: ExtractionTrace | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HttpFetcher:
    """Responsible HTTP fetcher for public extraction sources."""

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)

    def fetch(self, request: FetchRequest) -> FetchedContent:
        """Fetch raw source content without bypassing access controls."""

        headers = {"User-Agent": self.config.user_agent, **request.headers}
        started = time.perf_counter()
        response = self.session.request(
            request.method,
            request.url,
            headers=headers,
            params=request.params or None,
            data=request.data or None,
            json=request.json,
            timeout=request.timeout or self.config.timeout,
            verify=self.config.verify_ssl,
        )
        content = bytes(response.content)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        content_sha256 = hashlib.sha256(content).hexdigest()
        source_trace = SourceTrace(
            provider=request.source,
            endpoint=request.endpoint,
            query=request.query,
            source_url=request.url,
            limitations=request.limitations,
            http_status=response.status_code,
            final_url=str(getattr(response, "url", None) or request.url),
            content_type=response.headers.get("Content-Type"),
            content_sha256=content_sha256,
            response_bytes=len(content),
            elapsed_ms=elapsed_ms,
            retrieval_status="ok" if 200 <= response.status_code < 300 else "http_error",
        )
        return FetchedContent(
            source=request.source,
            url=request.url,
            status_code=response.status_code,
            content=content,
            content_type=response.headers.get("Content-Type"),
            encoding=response.encoding,
            access_status=_status_to_access_status(response.status_code),
            source_trace=source_trace,
        )


def parsed_content(
    *,
    source: str,
    parser: str,
    parser_version: str,
    records: list[dict[str, Any]] | None = None,
    text: str | None = None,
    metadata: dict[str, Any] | None = None,
    status: ExtractionStatus = ExtractionStatus.COMPLETE,
    access_status: AccessStatus = AccessStatus.PARTIAL,
    content_sha256: str | None = None,
    content_bytes: int | None = None,
    warnings: list[str] | None = None,
) -> ParsedContent:
    """Build parser output with an extraction trace."""

    trace = ExtractionTrace(
        parser=parser,
        parser_version=parser_version,
        status=status,
        access_status=access_status,
        content_sha256=content_sha256,
        content_bytes=content_bytes,
        warnings=warnings or [],
        metadata=metadata or {},
    )
    return ParsedContent(
        source=source,
        parser=parser,
        parser_version=parser_version,
        records=records or [],
        text=text,
        metadata=metadata or {},
        extraction_trace=trace,
    )


def _status_to_access_status(status_code: int) -> AccessStatus:
    if status_code == 404:
        return AccessStatus.NOT_FOUND
    if status_code == 401:
        return AccessStatus.LOGIN_REQUIRED
    if status_code == 403:
        return AccessStatus.ACCESS_CONTROL_REQUIRED
    if status_code in {408, 425, 429} or status_code >= 500:
        return AccessStatus.SOURCE_UNAVAILABLE
    if 300 <= status_code < 400:
        return AccessStatus.PARTIAL
    if 200 <= status_code < 300:
        return AccessStatus.PUBLIC
    return AccessStatus.PARTIAL
