"""Federal eproc public jurisprudence providers."""

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


class FederalEprocJurisprudenciaProvider(JurisprudenceProvider):
    """Base provider for public federal eproc jurisprudence instances."""

    name = "federal_eproc_jurisprudencia"
    court = "FEDERAL"
    display_name = "Federal eproc Jurisprudencia"
    config_url_attr = ""
    id_prefix = "federal-eproc-jurisprudencia"
    source_label = "Federal/eproc jurisprudence"
    origins: tuple[str, ...] = ()
    document_types: tuple[str, ...] = (
        "acordao",
        "decisao_monocratica",
        "sumula",
        "despacho",
        "sentenca",
    )

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    @property
    def source_url(self) -> str:
        return str(getattr(self.config, self.config_url_attr))

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
                f"Jurisprudencia publica {self.court}/eproc validada com sessao HTTP limpa.",
                "Resultados podem conter acordaos, decisoes monocraticas, sumulas, "
                "despachos e sentencas conforme a instancia.",
                "O provider preserva o conteudo publico retornado pela fonte e nao "
                "tenta contornar captcha, login ou controle de acesso.",
            ],
        )
        results = parse_eproc_jurisprudencia_results(
            html,
            trace=trace,
            source_url=source_url,
            source=self.name,
            court=self.court,
            id_prefix=self.id_prefix,
            source_label=self.source_label,
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
            limitations=[f"Inteiro teor publico da jurisprudencia eproc/{self.court}."],
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
            limitations=[
                f"Documento publico retornado pela rota de inteiro teor eproc/{self.court}."
            ],
        )
        return CanonicalDocument(
            id=f"{self.id_prefix}-document-{eproc_id}",
            source=self.name,
            document_type="decisao",
            content_type="text/html",
            title=f"{self.court} eproc inteiro teor",
            text=content,
            url=source_url,
            source_trace=trace,
            extraction_trace=ExtractionTrace(
                parser=f"{self.name}.get_document",
                parser_version="1",
                status=ExtractionStatus.COMPLETE,
                access_status=AccessStatus.PUBLIC,
            ),
            raw_metadata={"id_jurisprudencia": eproc_id},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name=self.display_name,
            source_url=self.source_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range"],
            document_types=list(self.document_types),
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
                "source_origin",
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
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number"],
            limitations=[
                "Rota publica validada por requests limpo em 2026-08-07.",
                "O provider parseia os cards HTML da primeira pagina retornada pela fonte.",
                "Origens observadas: "
                f"{', '.join(self.origins) if self.origins else 'variavel por instancia'}.",
                "A fonte pode alterar layout, filtros e labels sem aviso.",
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
        url = urljoin(self.source_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"{self.source_label} request failed: {exc}") from exc

        response.encoding = response.encoding or "iso-8859-1"
        text = response.text
        if response.status_code == 429:
            raise RateLimitDetectedError(f"{self.source_label} returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError(f"{self.source_label} requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"{self.source_label} returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"{self.source_label} rejected request with HTTP {response.status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError(f"{self.source_label} returned access-control HTML")
        return text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


class TnuEprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    name = "tnu_eproc_jurisprudencia"
    court = "TNU"
    display_name = "TNU eproc Jurisprudencia"
    config_url_attr = "tnu_eproc_jurisprudencia_url"
    id_prefix = "tnu-eproc-jurisprudencia"
    source_label = "TNU/eproc jurisprudence"
    origins = ("TNU",)
    document_types = ("acordao", "decisao_monocratica", "decisao_presidente")


class Trf2EprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    name = "trf2_eproc_jurisprudencia"
    court = "TRF2"
    display_name = "TRF2 eproc Jurisprudencia"
    config_url_attr = "trf2_eproc_jurisprudencia_url"
    id_prefix = "trf2-eproc-jurisprudencia"
    source_label = "TRF2/eproc jurisprudence"
    origins = ("TRF2", "TRU2", "Turmas Recursais")


class Trf6EprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    name = "trf6_eproc_jurisprudencia"
    court = "TRF6"
    display_name = "TRF6 eproc Jurisprudencia"
    config_url_attr = "trf6_eproc_jurisprudencia_url"
    id_prefix = "trf6-eproc-jurisprudencia"
    source_label = "TRF6/eproc jurisprudence"
    origins = ("TRF6", "TRU6", "Turmas Recursais", "Varas Federais")
