"""TJAM CJSG public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
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
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    JurisprudenceQuery,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
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


class TjamCjsgProvider(JurisprudenceProvider):
    """Provider for the public TJAM CJSG jurisprudence search."""

    name = "tjam_cjsg"

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
            base_url=self.config.tjam_cjsg_url,
            source=self.name,
            court="TJAM",
            id_prefix="tjam-cjsg",
            source_label="TJAM/CJSG",
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
            source_url=urljoin(self.config.tjam_cjsg_url.rstrip("/") + "/", endpoint.lstrip("/")),
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
            title=f"TJAM/CJSG inteiro teor {document_id}",
            parser="tjam_cjsg.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAM Consulta de Jurisprudencia/CJSG",
            source_url=self.config.tjam_cjsg_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "decision_type"],
            document_types=["acordao", "homologation", "decision"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "origin_county",
                "judging_body",
                "publication_date",
                "summary",
                "document_url",
                "cd_acordao",
                "cd_foro",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "POST /resultadoCompleta.do",
                "GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>",
                "GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page_size=10,
            completeness_contract="reported_window_or_source_page_limit",
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "number",
                "exact_phrase",
                "updated_from",
                "updated_to",
                "types",
                "order_by",
            ],
            limitations=[
                "A fonte compartilha padrao CJSG/e-SAJ e pode mudar sem aviso.",
                "Provider nao tenta contornar captcha, login ou controles de acesso.",
            ],
            responsible_use=[
                "Usar coletas paginadas com rate limit.",
                "Preservar cdAcordao/cdForo e SourceTrace para auditoria.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        self._respect_rate_limit()
        url = urljoin(self.config.tjam_cjsg_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"TJAM/CJSG request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJAM/CJSG returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJAM/CJSG returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJAM/CJSG rejected request with HTTP {response.status_code}"
            )
        text = decode_cjsg_response_text(response)
        content = _response_bytes(response)
        self._last_response_content = content
        headers = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(getattr(response, "url", url) or url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if 200 <= response.status_code < 300 else "http_error",
        }
        diagnostic = diagnose_cjsg_access(text)
        if diagnostic.access_control_required:
            raise AccessControlRequiredError(
                "TJAM/CJSG requires captcha or another access-control step "
                f"({diagnostic.summary()})"
            )
        return text

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()

    @staticmethod
    def _parse_precedent_id(precedent_id: str) -> tuple[str, str]:
        match = re.fullmatch(r"tjam-cjsg-(?P<cd>\d+)(?:-(?P<foro>\d+))?", precedent_id)
        if not match:
            raise ParserContractChangedError(
                "TJAM/CJSG precedent id must look like tjam-cjsg-<cdAcordao>-<cdForo>"
            )
        return match.group("cd"), match.group("foro") or "0"
