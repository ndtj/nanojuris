"""TRF4 eproc public jurisprudence provider."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
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
    _build_payload,
    _extract_document_id,
    _looks_like_access_control,
    parse_eproc_jurisprudencia_results,
)


class Trf4EprocJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TRF4 eproc jurisprudence search."""

    name = "trf4_eproc_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados"
        payload = _build_payload(query)
        html, source_url = self._request_text("POST", endpoint, data=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=payload,
            source_url=source_url,
            limitations=[
                "Jurisprudencia publica do eproc/TRF4 validada com sessao HTTP limpa.",
                "Resultados podem conter acordaos, despachos e decisoes da Vice-Presidencia.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )
        results = parse_eproc_jurisprudencia_results(
            html,
            trace=trace,
            source_url=source_url,
            source=self.name,
            court="TRF4",
            id_prefix="trf4-eproc-jurisprudencia",
            source_label="TRF4/eproc jurisprudence",
        )
        limited = results[: query.page_size]
        start = ((query.page - 1) * query.page_size) + 1 if limited else 0
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start,
            end=start + len(limited) - 1 if limited else 0,
            page=query.page,
            page_size=query.page_size,
            results=limited,
            source_trace=trace,
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
        self._respect_rate_limit()
        url = urljoin(
            self.config.trf4_eproc_jurisprudencia_url.rstrip("/") + "/",
            path.lstrip("/"),
        )
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
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TRF4/eproc jurisprudence request failed: {exc}") from exc

        response.encoding = response.encoding or "iso-8859-1"
        text = response.text
        if response.status_code == 429:
            raise RateLimitDetectedError("TRF4/eproc jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TRF4/eproc jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"TRF4/eproc jurisprudence returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TRF4/eproc jurisprudence rejected request with HTTP {response.status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError(
                "TRF4/eproc jurisprudence returned access-control HTML"
            )
        return text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()
