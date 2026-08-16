"""TJCE CJSG public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Any
from urllib.parse import urljoin

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
        self._last_request = 0.0
        self._last_http_metadata: dict[str, Any] = {}
        self._last_response_content = b""

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
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        self._respect_rate_limit()
        url = urljoin(self.config.tjce_cjsg_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJCE/CJSG request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJCE/CJSG returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJCE/CJSG returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJCE/CJSG rejected request with HTTP {response.status_code}"
            )
        text = decode_cjsg_response_text(response)
        content = _response_bytes(response)
        self._last_response_content = content
        response_headers = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(getattr(response, "url", url) or url),
            "content_type": response_headers.get("Content-Type")
            or response_headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if 200 <= response.status_code < 300 else "http_error",
        }
        diagnostic = diagnose_cjsg_access(text)
        if diagnostic.access_control_required:
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
