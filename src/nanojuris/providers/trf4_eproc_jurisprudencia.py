"""TRF4 eproc public jurisprudence provider."""

from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    ExtractionStatus,
    ExtractionTrace,
    JurisprudenceQuery,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.tjsp_eproc_jurisprudencia import (
    _extract_document_id,
    _looks_like_access_control,
    fetch_eproc_page,
)
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus


class Trf4EprocJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TRF4 eproc jurisprudence search."""

    name = "trf4_eproc_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = session or requests.Session()
        host = urlparse(self.config.trf4_eproc_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_retries=2,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return fetch_eproc_page(
            self,
            query,
            source=self.name,
            court="TRF4",
            id_prefix="trf4-eproc-jurisprudencia",
            source_label="TRF4/eproc jurisprudence",
            limitations=[
                "Jurisprudencia publica do eproc/TRF4 validada com sessao HTTP limpa.",
                "Resultados podem conter acordaos, despachos e decisoes da Vice-Presidencia.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _extract_document_id(precedent_id)
        endpoint = (
            "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor"
        )
        params = {"id_jurisprudencia": document_id}
        content, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=["Inteiro teor publico da jurisprudencia eproc/TRF4."],
            **self._last_http_metadata,
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": content, "content_type": "text/html"}],
            source_trace=trace,
            raw={"id_jurisprudencia": document_id},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        eproc_id = _extract_document_id(document_id)
        endpoint = (
            "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor"
        )
        params = {"id_jurisprudencia": eproc_id}
        content, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=["Documento publico retornado pela rota de inteiro teor eproc/TRF4."],
            **self._last_http_metadata,
        )
        return CanonicalDocument(
            id=f"trf4-eproc-jurisprudencia-document-{eproc_id}",
            source=self.name,
            document_type="decisao",
            content_type="text/html",
            title="TRF4 eproc inteiro teor",
            text=content,
            url=source_url,
            source_trace=trace,
            extraction_trace=ExtractionTrace(
                parser="trf4_eproc_jurisprudencia.get_document",
                parser_version="1",
                status=ExtractionStatus.COMPLETE,
                access_status=AccessStatus.PUBLIC,
            ),
            raw_metadata={"id_jurisprudencia": eproc_id},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRF4 eproc Jurisprudencia",
            source_url=self.config.trf4_eproc_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range"],
            document_types=["acordao", "decisao", "despacho"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "document_url",
                "full_text_url",
                "id_jurisprudencia",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                (
                    "POST /externo_controlador.php?"
                    "acao=jurisprudencia@jurisprudencia/listar_resultados"
                ),
                (
                    "GET /externo_controlador.php?"
                    "acao=jurisprudencia@jurisprudencia/download_inteiro_teor&"
                    "id_jurisprudencia=<id>"
                ),
            ],
            supports_full_text=True,
            pagination_mode="local_window",
            completeness_contract="observed_window_only",
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number"],
            unsupported_filters=[
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origins",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
            ],
            filter_semantics={
                "text": "native",
                "number": "native",
                "exact_phrase": "native",
                "published_from": "native",
                "published_to": "native",
                "updated_from": "native",
                "updated_to": "native",
                "types": "translated",
                "source_origin": "translated",
                "degree": "local_postfilter",
                "instance": "local_postfilter",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "rapporteur": "unsupported",
                "fetch_details": "unsupported",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "source_origins": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
            },
            limitations=[
                "Rota publica descoberta e validada por requests limpo em 2026-08-03.",
                "O provider parseia os cards HTML da primeira pagina retornada pela fonte.",
                "A fonte pode alterar hashes, layouts e listas de filtros sem aviso.",
                "O provider detecta controles de acesso e nao implementa bypass.",
            ],
            responsible_use=[
                "Usar consultas pequenas e rate limit em coletas exploratorias.",
                "Preservar id_jurisprudencia, URLs e SourceTrace para auditoria.",
                "Nao reutilizar cookies ou sessao de navegador para contornar restricoes.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        url = urljoin(
            self.config.trf4_eproc_jurisprudencia_url.rstrip("/") + "/",
            path.lstrip("/"),
        )
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.transport.request(
                TransportRequest(
                    source=self.name,
                    operation="document_or_search",
                    method=method,
                    url=url,
                    params=dict(kwargs.get("params") or {}),
                    data=kwargs.get("data"),
                    json_body=kwargs.get("json"),
                    headers=headers,
                    idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
                )
            )
        except (requests.RequestException, SourceUnavailableError) as exc:
            raise SourceUnavailableError(f"TRF4/eproc jurisprudence request failed: {exc}") from exc

        response_url = response.final_url or url
        content = response.body
        text = content.decode("iso-8859-1", errors="replace")
        headers = response.headers
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response_url,
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": response.content_sha256 or hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok"
            if response.status_code is not None and 200 <= response.status_code < 300
            else response.status.value,
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TRF4/eproc jurisprudence transport failed: {response.status.value}"
            )
        status_code = response.status_code or 0
        if status_code == 429:
            raise RateLimitDetectedError("TRF4/eproc jurisprudence returned HTTP 429")
        if status_code in {401, 403}:
            raise AccessControlRequiredError("TRF4/eproc jurisprudence requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"TRF4/eproc jurisprudence returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"TRF4/eproc jurisprudence rejected request with HTTP {status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError(
                "TRF4/eproc jurisprudence returned access-control HTML"
            )
        return text, response_url
