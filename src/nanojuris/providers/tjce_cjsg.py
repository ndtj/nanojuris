"""TJCE CJSG public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    CanonicalDocument,
    DecisionBundle,
    JurisprudenceQuery,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.tjac_cjsg import TjacCjsgProvider
from nanojuris.providers.tjms_cjsg import _build_payload
from nanojuris.providers.tjsp_cjsg import (
    _response_bytes,
    cjsg_decision_bundle_to_document,
    decode_cjsg_response_text,
    diagnose_cjsg_access,
    extract_cjsg_document_text,
    extract_cjsg_document_text_bytes,
    fetch_cjsg_page,
)
from nanojuris.tjce_tls import TjceTlsAdapter
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus


class TjceCjsgProvider(TjacCjsgProvider):
    """Provider for TJCE's public e-SAJ/CJSG jurisprudence surface.

    The implementation intentionally reuses the tested CJSG family parser,
    while keeping the TJCE host, identity prefix and document trace distinct.
    """

    name = "tjce_cjsg"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        # TJCE's public e-SAJ endpoint still negotiates a legacy cipher level.
        # This adapter changes only cipher negotiation; certificate verification
        # remains controlled by ``config.verify_ssl``.
        host = urlparse(self.config.tjce_cjsg_url).hostname or ""
        if callable(getattr(self.session, "mount", None)) and host:
            # Scope the legacy-cipher compatibility adapter to TJCE's own
            # origin.  A caller may inject a shared requests session; mounting
            # it at ``https://`` would silently weaken TLS negotiation for
            # unrelated providers using that session.
            self.session.mount(f"https://{host}/", TjceTlsAdapter())
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self._last_response_content = b""
        self._pending_access_diagnostic: str | None = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return fetch_cjsg_page(
            self,
            query,
            payload_builder=_build_payload,
            base_url=self.config.tjce_cjsg_url,
            source=self.name,
            court="TJCE",
            id_prefix="tjce-cjsg",
            source_label="TJCE/CJSG",
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        cd_acordao, cd_foro = self._parse_precedent_id(precedent_id)
        endpoint = f"/getArquivo.do?cdAcordao={cd_acordao}&cdForo={cd_foro}"
        content = self._request_text("GET", endpoint)
        raw_content = self._last_response_content or content.encode("utf-8")
        content_type = str(self._last_http_metadata.get("content_type") or "text/html")
        is_pdf = raw_content.startswith(b"%PDF") or "application/pdf" in content_type.lower()
        if is_pdf:
            document_text, extraction_metadata = extract_cjsg_document_text_bytes(raw_content)
        else:
            document_text, extraction_metadata = extract_cjsg_document_text(content)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/getArquivo.do",
            query={"cdAcordao": cd_acordao, "cdForo": cd_foro},
            source_url=urljoin(self.config.tjce_cjsg_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=["O retorno pode ser HTML, PDF ou tela de controle da propria fonte."],
            **self._last_http_metadata,
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document_text,
                    "content_type": "application/pdf" if is_pdf else "text/plain",
                    "source_content_type": content_type,
                }
            ],
            source_trace=trace,
            raw={
                "cd_acordao": cd_acordao,
                "cd_foro": cd_foro,
                "raw_content_sha256": hashlib.sha256(raw_content).hexdigest(),
                "raw_content_bytes": len(raw_content),
                "raw_content_type": content_type,
                **extraction_metadata,
            },
            raw_bytes=raw_content,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        return cjsg_decision_bundle_to_document(
            bundle,
            document_id=document_id,
            source=self.name,
            title=f"TJCE/CJSG inteiro teor {document_id}",
            parser="tjce_cjsg.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return replace(
            super().get_capabilities(),
            source=self.name,
            display_name="TJCE Consulta de Jurisprudencia/CJSG",
            source_url=self.config.tjce_cjsg_url,
            # A bounded public smoke on 2026-09-06 returned textual second-
            # degree records.  Keep the provider in the normal federation;
            # access failures are still surfaced by the transport contract.
            supports_unified_search=True,
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        url = urljoin(self.config.tjce_cjsg_url.rstrip("/") + "/", path.lstrip("/"))
        skip_access_diagnostic = bool(kwargs.pop("skip_access_diagnostic", False))
        request_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        request_headers.update(kwargs.pop("headers", {}) or {})
        request = TransportRequest(
            source=self.name,
            operation=f"cjsg_{method.lower()}",
            method=method,
            url=url,
            headers=request_headers,
            data=kwargs.pop("data", None),
            params=kwargs.pop("params", {}),
            json_body=kwargs.pop("json", None),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except IndexError as exc:
            # A test/dry-run session may expose only the POST acknowledgement.
            # Preserve the deferred access-control classification instead of
            # turning that missing follow-up into an empty result.
            if self._pending_access_diagnostic:
                raise AccessControlRequiredError(
                    "TJCE/CJSG requires captcha or another access-control step "
                    f"({self._pending_access_diagnostic})"
                ) from exc
            raise
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJCE/CJSG request failed: {exc}") from exc
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJCE/CJSG request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJCE/CJSG transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJCE/CJSG transport returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJCE/CJSG returned HTTP 429")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJCE/CJSG returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJCE/CJSG rejected request with HTTP {status_code}")
        text = decode_cjsg_response_text(response)
        content = _response_bytes(response)
        self._last_response_content = content
        response_headers = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(getattr(response, "url", url) or url),
            "content_type": response_headers.get("Content-Type")
            or response_headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if 200 <= status_code < 300 else "http_error",
        }
        diagnostic = diagnose_cjsg_access(text)
        if skip_access_diagnostic:
            self._pending_access_diagnostic = (
                diagnostic.summary() if diagnostic.access_control_required else None
            )
        else:
            self._pending_access_diagnostic = None
        if diagnostic.access_control_required and not skip_access_diagnostic:
            raise AccessControlRequiredError(
                "TJCE/CJSG requires captcha or another access-control step "
                f"({diagnostic.summary()})"
            )
        return text

    @staticmethod
    def _parse_precedent_id(precedent_id: str) -> tuple[str, str]:
        match = re.fullmatch(r"tjce-cjsg-(?P<cd>\d+)(?:-(?P<foro>\d+))?", precedent_id)
        if not match:
            raise ParserContractChangedError(
                "TJCE/CJSG precedent id must look like tjce-cjsg-<cdAcordao>-<cdForo>"
            )
        return match.group("cd"), match.group("foro") or "0"
