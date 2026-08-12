"""TJAC e-SAJ first-instance public case lookup provider."""

from __future__ import annotations

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
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.tjsp_esaj_cpopg import parse_esaj_cpopg_document

PROCESS_NUMBER_RE = re.compile(r"^(\d{7}-\d{2}\.\d{4})\.\d\.\d{2}\.(\d{4})$")
ANY_PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


class TjacEsajCpopgProvider(JurisprudenceProvider):
    """Provider for public TJAC e-SAJ CPOPg first-instance case pages."""

    name = "tjac_esaj_cpopg"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        process_number = _normalize_process_number(query.number or query.text)
        document = self.get_document(process_number)
        result = JurisprudenceResult(
            id=document.id,
            source=self.name,
            court="TJAC",
            type="processo",
            number=process_number,
            summary=document.title,
            status=document.raw_metadata.get("status"),
            updated_at=document.raw_metadata.get("last_movement_date"),
            source_trace=document.source_trace,
            raw={
                **document.raw_metadata,
                "document_url": document.url,
                "record_kind": "case_lookup",
            },
        )
        return SearchPage(
            source=self.name,
            total=1,
            start=1,
            end=1,
            page=query.page,
            page_size=query.page_size,
            results=[result],
            source_trace=document.source_trace,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "tjac_esaj_cpopg is a public case lookup provider"},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        process_number = _normalize_process_number(document_id)
        endpoint = "/cpopg/search.do"
        params = _build_search_params(process_number)
        html, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=[
                "Consulta processual publica de primeiro grau no e-SAJ/TJAC.",
                "Autos, anexos e partes sob segredo podem exigir login ou senha.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )
        return parse_esaj_cpopg_document(
            html,
            process_number=process_number,
            trace=trace,
            source_url=source_url,
            source=self.name,
            id_prefix="tjac-esaj-cpopg",
            parser_name="tjac_esaj_cpopg.parse_esaj_cpopg_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAC e-SAJ Consulta Processual 1o Grau",
            source_url=self.config.tjac_esaj_url,
            category="case_lookup",
            search_modes=["case_number"],
            document_types=["processo_1g"],
            content_formats=["html"],
            canonical_records=["CanonicalDocument", "JurisprudenceResult"],
            extracted_fields=[
                "case_number",
                "status",
                "case_class",
                "subject",
                "origin_county",
                "court_unit",
                "distribution",
                "control_number",
                "area",
                "parties_text",
                "movements_text",
                "document_url",
                "parties",
                "movements",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.LOGIN_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /cpopg/search.do", "GET /cpopg/show.do"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            limitations=[
                "Busca por numero CNJ validada com redirect oficial search.do -> show.do.",
                "Busca por nome/OAB ainda nao foi promovida para TJAC.",
                "Dados processuais sao objetivos; autos e documentos podem ser restritos.",
            ],
            responsible_use=[
                "Consultar apenas dados publicos e respeitar limites da fonte.",
                "Nao reutilizar cookies, sessoes ou tokens de navegador para bypass.",
                "Preservar SourceTrace e URL final para auditoria.",
            ],
        )

    def _request_text(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.config.tjac_esaj_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"TJAC/e-SAJ CPOPg request failed: {exc}") from exc

        response.encoding = response.encoding or "utf-8"
        text = response.text
        if response.status_code == 429:
            raise RateLimitDetectedError("TJAC/e-SAJ CPOPg returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJAC/e-SAJ CPOPg requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJAC/e-SAJ CPOPg returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJAC/e-SAJ CPOPg rejected request with HTTP {response.status_code}"
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


def _build_search_params(process_number: str) -> dict[str, str]:
    match = PROCESS_NUMBER_RE.match(process_number)
    if match is None:
        raise ParserContractChangedError("TJAC/e-SAJ CPOPg requires a valid CNJ case number")
    unified_prefix, forum_code = match.groups()
    return {
        "conversationId": "",
        "cbPesquisa": "NUMPROC",
        "numeroDigitoAnoUnificado": unified_prefix,
        "foroNumeroUnificado": forum_code,
        "dadosConsulta.valorConsultaNuUnificado": process_number,
        "dadosConsulta.valorConsulta": process_number,
        "dadosConsulta.tipoNuProcesso": "UNIFICADO",
    }


def _normalize_process_number(value: str) -> str:
    number = value.strip()
    match = ANY_PROCESS_NUMBER_RE.search(number)
    if match is None:
        raise ParserContractChangedError("TJAC/e-SAJ CPOPg requires a CNJ case number")
    return match.group(0)
