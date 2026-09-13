"""TJPE public REST jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime
from html import unescape
from typing import Any, Literal
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
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
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)

TJPE_JSF_RESULTS_PER_PAGE = 5
TJPE_JSF_DEFAULT_SUBMIT_ID = "formPesquisaJurisprudencia:j_id101"
_TJPE_JSF_FIELD_MAP = {
    "processo": "processo",
    "classe cnj": "classe",
    "assunto cnj": "assunto",
    "relator(a)": "relator",
    "órgão julgador": "orgao_julgador",
    "orgao julgador": "orgao_julgador",
    "data de julgamento": "data_julgamento",
    "data da publicação/fonte": "data_publicacao",
    "data da publicacao/fonte": "data_publicacao",
    "ementa": "ementa",
    "acórdão": "acordao",
    "acordao": "acordao",
    "meio de tramitação": "meio_tramitacao",
    "meio de tramitacao": "meio_tramitacao",
}


class TjpeJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for TJPE's REST surface and public JSF compatibility route.

    ``auto`` is the default: it prefers REST and uses the stateful public JSF
    flow used by Juscraper after a transport-level
    failure from REST (never after an HTTP error or an access-control signal).
    """

    name = "tjpe_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
        *,
        transport: Literal["rest", "jsf", "auto"] = "auto",
    ) -> None:
        if transport not in {"rest", "jsf", "auto"}:
            raise ValueError("TJPE transport must be 'rest', 'jsf' or 'auto'")
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        hosts = tuple(
            host
            for host in (
                urlparse(self.config.tjpe_jurisprudencia_url).hostname,
                urlparse(self.config.tjpe_juscraper_url).hostname,
            )
            if host
        )
        self.http = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=hosts,
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                # The REST and JSF surfaces expose access-control responses
                # (429/5xx) that must be classified immediately.  The shared
                # client still enforces timeout, pacing and circuit breaking;
                # retries are deliberately left to an explicit caller retry
                # so an access signal is never hidden by a second request.
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self.transport = transport
        self._results: dict[str, JurisprudenceResult] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjpe_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if self.transport == "jsf":
            page = self._search_jsf(query)
            self._remember_results(page)
            return page
        # The REST endpoint currently exposes only free text, NPU, dates and
        # decision type.  Route richer filters through the public JSF form so
        # they are never silently ignored (the JSF fields mirror Juscraper's
        # observed contract for relator and CNJ class).
        if _requires_jsf_filter(query):
            page = self._search_jsf(query, fallback_reason="filter_requires_jsf")
            self._remember_results(page)
            return page
        try:
            page = self._search_rest(query)
            self._remember_results(page)
            return page
        except SourceUnavailableError as exc:
            if self.transport != "auto" or "request failed" not in str(exc):
                raise
            try:
                page = self._search_jsf(query, fallback_reason="rest_transport_failure")
                self._remember_results(page)
                return page
            except AccessControlRequiredError:
                # Preserve an external access-control signal; it is not a
                # transport failure and must remain visible to callers.
                raise
            except ParserContractChangedError:
                raise
            except SourceUnavailableError as fallback_exc:
                raise SourceUnavailableError(
                    "TJPE REST transport unavailable and JSF fallback did not produce a "
                    "validated result"
                ) from fallback_exc

    def _search_rest(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/api/v1/jurisprudencias"
        page_size = _page_size(query.page_size)
        params = build_tjpe_search_parameters(query, page_size=page_size)
        data, source_url = self._request_json(endpoint, params=params)
        trace_metadata = {
            key: value for key, value in self._last_http_metadata.items() if key != "reported_total"
        }
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /api/v1/jurisprudencias",
            query={"text": query.text, "page": query.page, "page_size": page_size, **params},
            source_url=source_url,
            limitations=[
                "A API usa pagina zero-based no transporte HTTP.",
                "Filtros por ids exigem catalogos oficiais de classes, assuntos ou unidades.",
                "Texto integral depende de textoAcordao ou textoDecisao presente no item.",
            ],
            **trace_metadata,
        )
        return parse_tjpe_search_response(
            data,
            query=query,
            trace=trace,
            reported_total=self._last_http_metadata.get("reported_total"),
        )

    def _search_jsf(
        self,
        query: JurisprudenceQuery,
        *,
        fallback_reason: str | None = None,
    ) -> SearchPage:
        """Execute TJPE's public JSF/RichFaces flow with one session."""

        base_url = self.config.tjpe_juscraper_url.rstrip("/")
        search_html, search_url = self._request_html("GET", "/consulta.xhtml", base_url=base_url)
        viewstate = extract_tjpe_jsf_viewstate(search_html)
        submit_id = extract_tjpe_jsf_submit_id(search_html)
        form = build_tjpe_jsf_form_body(
            query,
            viewstate=viewstate,
            submit_id=submit_id,
        )
        response_html, _ = self._request_html(
            "POST",
            "/consulta.xhtml",
            base_url=base_url,
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        endpoint = "POST /consulta.xhtml"
        if _is_tjpe_jsf_choice(response_html):
            tipo = _tjpe_jsf_type_label_ascii(query.types)
            button_id = extract_tjpe_jsf_choice_button_id(response_html, tipo)
            response_html, _ = self._request_html(
                "POST",
                "/escolhaResultado.xhtml",
                base_url=base_url,
                data={
                    "resultadoForm": "resultadoForm",
                    "javax.faces.ViewState": extract_tjpe_jsf_viewstate(response_html),
                    button_id: button_id,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            endpoint = "POST /escolhaResultado.xhtml"
        if not _is_tjpe_jsf_results(response_html) and not _has_tjpe_jsf_zero_marker(response_html):
            raise ParserContractChangedError(
                "TJPE JSF response is neither a results page nor an explicit empty result"
            )

        source_url = str(self._last_http_metadata.get("final_url") or search_url)
        page_html = response_html
        if query.page > 1:
            form_id, scroller_id = extract_tjpe_jsf_pagination_ids(response_html)
            page_html, source_url = self._request_html(
                "POST",
                "/resultado.xhtml",
                base_url=base_url,
                data={
                    "AJAXREQUEST": "_viewRoot",
                    form_id: form_id,
                    "hiddenPesquisaLivre": query.text or query.exact_phrase or query.number,
                    "javax.faces.ViewState": extract_tjpe_jsf_viewstate(response_html),
                    scroller_id: str(query.page),
                    "AJAX:EVENTS_COUNT": "1",
                },
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                },
            )
            endpoint = "POST /resultado.xhtml"

        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "number": query.number,
                "page": query.page,
                "page_size": query.page_size,
                "transport": "jsf",
                **({"fallback": fallback_reason} if fallback_reason else {}),
            },
            source_url=source_url,
            limitations=[
                "Fluxo JSF/RichFaces publico com ViewState e cookies mantidos em memoria.",
                "A fonte limita o resultado a cinco documentos por pagina.",
                "O provider nao tenta contornar CAPTCHA, login ou controles de acesso.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjpe_jsf_results(page_html, query=query, trace=trace)

    def get_decisions(self, precedent_id: str):
        result = self._results.get(precedent_id)
        if result is None:
            raise ValueError("TJPE precedent_id must be observed in the current search page")
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=result.rapporteur,
            texts=[
                {
                    "type": result.document_type or result.type,
                    "text": result.full_text or result.summary or "",
                }
            ],
            source_trace=result.source_trace,
            raw=dict(result.raw),
        )

    def _remember_results(self, page: SearchPage) -> None:
        self._results.update({result.id: result for result in page.results})

    def get_document(self, document_id: str) -> CanonicalDocument:
        result = self._results.get(document_id)
        if result is None:
            raise ValueError("TJPE document_id must be observed in the current search page")
        text = result.full_text or result.summary or ""
        content = text.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        status = ExtractionStatus.COMPLETE if text.strip() else ExtractionStatus.EMPTY
        return CanonicalDocument(
            id=result.id,
            source=result.source,
            document_type=result.document_type or result.type,
            content_type="text/plain",
            title=f"TJPE {result.number or result.id}",
            text=text or None,
            url=result.document_url,
            sha256=digest,
            byte_size=len(content),
            retrieved_at=result.source_trace.retrieved_at if result.source_trace else None,
            access_status=AccessStatus.PUBLIC,
            extraction_status=status,
            source_trace=result.source_trace,
            extraction_trace=ExtractionTrace(
                parser="tjpe_jurisprudencia.inline_result",
                parser_version="1",
                status=status,
                access_status=AccessStatus.PUBLIC,
                content_sha256=digest,
                content_bytes=len(content),
            ),
            raw_metadata=dict(result.raw),
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJPE Consulta de Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "pagination"],
            document_types=["acordao", "decisao"],
            content_formats=["json", "html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "source_key",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /api/v1/jurisprudencias",
                "GET /api/v1/classes",
                "GET /api/v1/assuntos",
                "GET /api/v1/relatores",
                "GET /api/v1/unidades-judiciais",
                "GET /consultajurisprudenciaweb/xhtml/consulta/consulta.xhtml",
                "POST /consultajurisprudenciaweb/xhtml/consulta/consulta.xhtml",
                "POST /consultajurisprudenciaweb/xhtml/consulta/escolhaResultado.xhtml",
                "POST /consultajurisprudenciaweb/xhtml/consulta/resultado.xhtml",
            ],
            supports_full_text=True,
            supports_cli=True,
            # REST and the documented public JSF fallback both returned
            # textual second-degree records in the bounded 2026-09-06 smoke.
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="offset",
            completeness_contract="x_total_count_and_page_window",
            full_text_access="inline",
            supported_filters=[
                "text",
                "number",
                "rapporteur",
                "case_class",
                "published_from",
                "published_to",
                "judgment_date_from",
                "judgment_date_to",
                "types",
                "order_by",
            ],
            filter_semantics={
                "text": "translated",
                "exact_phrase": "translated",
                "number": "translated",
                "rapporteur": "translated",
                "case_class": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "judgment_date_from": "translated",
                "judgment_date_to": "translated",
                "types": "translated",
                "order_by": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                **{
                    name: "unsupported"
                    for name in (
                        "courts",
                        "all_words",
                        "any_words",
                        "without_words",
                        "judging_body",
                        "updated_from",
                        "updated_to",
                        "degree",
                        "instance",
                        "legal_area",
                        "decision_type",
                        "source_origin",
                        "source_origins",
                        "fetch_details",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "precatory_number",
                        "police_document",
                        "cda",
                    )
                },
            },
            limitations=[
                "A API pode retornar ementa nula e texto de decisao presente.",
                "A cadeia TLS do ambiente precisa ser valida; o provider nunca "
                "desativa verify_ssl.",
                "Filtros de catalogo por codigo ainda nao fazem parte da interface publica comum.",
                "O transporte JSF e uma alternativa explicita/auto para indisponibilidade "
                "de transporte REST.",
            ],
            responsible_use=[
                "Respeitar rate limit e page_size moderado.",
                "Preservar SourceTrace e o JSON bruto de cada item.",
                "Nao confundir a rota auxiliar de processo com consulta processual geral.",
            ],
        )

    def _request_json(self, endpoint: str, **kwargs: Any) -> tuple[list[Any], str]:
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        request = TransportRequest(
            source=self.name,
            operation="tjpe_rest_request",
            method="GET",
            url=url,
            headers={"Accept": "application/json", **kwargs.pop("headers", {})},
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            idempotent=True,
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.http.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPE jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJPE transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJPE transport returned no HTTP status")
        content = bytes(response.body)
        headers = response.headers
        total_header = headers.get("X-Total-Count") or headers.get("x-total-count")
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status_code < 400 else "error",
            "reported_total": _as_int(total_header),
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJPE jurisprudence returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJPE jurisprudence requires access validation")
        if status_code in {400, 422}:
            raise QueryRejectedError(
                f"TJPE jurisprudence rejected the query with HTTP {status_code}"
            )
        if status_code >= 500:
            raise SourceUnavailableError(f"TJPE jurisprudence returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"TJPE jurisprudence rejected request with HTTP {status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJPE jurisprudence response is not JSON") from exc
        if isinstance(data, list):
            return data, str(response.final_url or url)
        if isinstance(data, dict) and isinstance(data.get("content"), list):
            self._last_http_metadata["reported_total"] = _as_int(
                data.get("totalElements"), default=self._last_http_metadata.get("reported_total")
            )
            return data["content"], str(response.final_url or url)
        raise ParserContractChangedError("TJPE jurisprudence JSON root is not a result list")

    def _request_html(
        self,
        method: str,
        endpoint: str,
        *,
        base_url: str,
        **kwargs: Any,
    ) -> tuple[str, str]:
        url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
        request_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        request_headers.update(kwargs.pop("headers", {}) or {})
        request = TransportRequest(
            source=self.name,
            operation="tjpe_jsf_request",
            method=method,
            url=url,
            headers=request_headers,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.http.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPE JSF request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJPE JSF transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJPE JSF transport returned no HTTP status")
        content = bytes(response.body)
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status_code < 400 else "error",
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJPE JSF returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJPE JSF requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJPE JSF returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJPE JSF rejected request with HTTP {status_code}")
        text = response.text
        lowered = text.casefold()
        if any(
            marker in lowered
            for marker in ("captcha", "recaptcha", "g-recaptcha", "acesso negado", "sajcas/login")
        ):
            raise AccessControlRequiredError("TJPE JSF returned an access-control page")
        return text, str(response.final_url or url)


def extract_tjpe_jsf_viewstate(html: str) -> str:
    """Extract the JSF ViewState token without exposing it in traces."""

    soup = BeautifulSoup(html, "html.parser")
    field = soup.find("input", attrs={"name": "javax.faces.ViewState"})
    if field is None:
        raise ParserContractChangedError("TJPE JSF response missing javax.faces.ViewState")
    value = str(field.get("value") or "").strip()
    if not value:
        raise ParserContractChangedError("TJPE JSF ViewState is empty")
    return value


def extract_tjpe_jsf_submit_id(html: str) -> str:
    """Extract the dynamic JSF submit id, with the historical safe fallback."""

    match = re.search(
        r"jsfcljs\([^)]*\{\s*'((?:formPesquisaJurisprudencia:)[^']+)'",
        html,
        re.IGNORECASE,
    )
    return match.group(1) if match else TJPE_JSF_DEFAULT_SUBMIT_ID


def build_tjpe_jsf_form_body(
    query: JurisprudenceQuery,
    *,
    viewstate: str,
    submit_id: str,
) -> dict[str, str]:
    """Build the form body accepted by the public TJPE JSF search."""

    tipo = _tjpe_jsf_type_key(query.types)
    return {
        "formPesquisaJurisprudencia": "formPesquisaJurisprudencia",
        "formPesquisaJurisprudencia:inputBuscaSimples": (
            query.text or query.exact_phrase or query.number
        ),
        "tipo_processo": "NPU",
        "formPesquisaJurisprudencia:j_id46": "",
        "formPesquisaJurisprudencia:j_id48": "",
        "formPesquisaJurisprudencia:numeroAntigoDigito": "",
        "formPesquisaJurisprudencia:numeroAntigoBarramento": "",
        "formPesquisaJurisprudencia:j_id59InputDate": _date_br(
            query.published_from or query.judgment_date_from
        ),
        "formPesquisaJurisprudencia:j_id59InputCurrentDate": "04/2026",
        "formPesquisaJurisprudencia:periodoFimInputDate": _date_br(
            query.published_to or query.judgment_date_to
        ),
        "formPesquisaJurisprudencia:periodoFimInputCurrentDate": "04/2026",
        "formPesquisaJurisprudencia:selectRelator": query.rapporteur,
        "formPesquisaJurisprudencia:selectClasseCNJ": query.case_class,
        "formPesquisaJurisprudencia:selectAssuntoCNJ": "",
        "formPesquisaJurisprudencia:selectMeioTramitacao": "",
        "javax.faces.ViewState": viewstate,
        submit_id: submit_id,
        **_tjpe_jsf_type_fields(tipo),
    }


def extract_tjpe_jsf_choice_button_id(html: str, tipo: str = "Acórdãos") -> str:
    """Extract the JSF action id for an ``escolhaResultado`` type link."""

    soup = BeautifulSoup(html, "html.parser")
    wanted = _fold_text(tipo)
    for link in soup.find_all("a", onclick=True):
        if "documentos encontrados" not in link.get_text(" ", strip=True).casefold():
            continue
        row = link.find_parent("tr")
        label = row.find("label") if row else None
        if label is None or _fold_text(label.get_text(" ", strip=True)) != wanted:
            continue
        match = re.search(r"'([^']+)':'[^']+'", str(link.get("onclick") or ""))
        if match:
            return match.group(1)
    raise ParserContractChangedError(f"TJPE JSF choice button missing for {tipo}")


def extract_tjpe_jsf_pagination_ids(html: str) -> tuple[str, str]:
    """Return the RichFaces form and datascroller ids from a results page."""

    match = re.search(r'class="rich-datascr[^\"]*"\s+id="([^\"]+)"', html)
    if match:
        scroller = match.group(1)
        return scroller.split(":", 1)[0], scroller
    form_match = re.search(r'<form id="([^\"]+)"[^>]*class="form-consulta"', html)
    form_id = form_match.group(1) if form_match else "j_id81"
    return form_id, f"{form_id}:j_id87"


def parse_tjpe_jsf_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
) -> SearchPage:
    """Parse the label/value tables returned by TJPE's JSF application."""

    soup = BeautifulSoup(html, "html.parser")
    if _has_tjpe_jsf_zero_marker(html):
        return SearchPage(
            source="tjpe_jurisprudencia",
            total=0,
            start=0,
            end=0,
            page=query.page,
            page_size=min(_page_size(query.page_size), TJPE_JSF_RESULTS_PER_PAGE),
            results=[],
            source_trace=trace,
            pagination_mode="page",
            is_complete=True,
            completeness_reason="explicit_zero_marker",
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.EMPTY,
            total_known=True,
        )
    tables: list[Any] = []
    for label in soup.find_all("label"):
        if _fold_text(label.get_text(" ", strip=True)) != "processo":
            continue
        table = label.find_parent("table")
        if table is not None and table not in tables:
            tables.append(table)
    if not tables:
        raise ParserContractChangedError("TJPE JSF results contain no Processo result tables")

    result_rows: list[JurisprudenceResult] = []
    for index, table in enumerate(tables):
        fields: dict[str, str] = {}
        rows = table.find_all("tr")
        position = 0
        while position < len(rows):
            label = rows[position].find("label")
            if label is None or position + 1 >= len(rows):
                position += 1
                continue
            key = _TJPE_JSF_FIELD_MAP.get(_fold_text(label.get_text(" ", strip=True)))
            if key:
                value_cell = rows[position + 1].find("td")
                if value_cell is not None:
                    fields[key] = _clean_jsf_value(value_cell.get_text(" ", strip=True))
                position += 2
                continue
            position += 1
        process = fields.get("processo", "")
        links = table.find_all("a", href=re.compile(r"downloadInteiroTeor", re.IGNORECASE))
        detail_url = str(links[0].get("href")) if links else ""
        if detail_url and detail_url.startswith("/"):
            detail_url = "https://www.tjpe.jus.br" + detail_url
        stable_key = _stable_jsf_key(process, fields, index)
        result_rows.append(
            JurisprudenceResult(
                id=f"tjpe-juris-{stable_key}",
                source="tjpe_jurisprudencia",
                court="TJPE",
                type=_infer_jsf_type(fields, query),
                number=process or None,
                summary=fields.get("ementa") or None,
                full_text=fields.get("acordao") or None,
                rapporteur=fields.get("relator") or None,
                judgment_date=_date_iso(fields.get("data_julgamento", "")) or None,
                publication_date=_date_iso(fields.get("data_publicacao", "")) or None,
                updated_at=_date_iso(
                    fields.get("data_publicacao") or fields.get("data_julgamento", "")
                )
                or None,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                degree="second",
                instance="second",
                branch="state",
                authority="TJPE",
                collection="CJSG",
                document_type="acordao",
                source_trace=trace,
                raw={**fields, "source_key": stable_key, "document_url": detail_url or None},
            )
        )
    reported_total = _extract_tjpe_jsf_total(html)
    total = reported_total if reported_total is not None else len(result_rows)
    page_size = min(_page_size(query.page_size), TJPE_JSF_RESULTS_PER_PAGE)
    result_rows = result_rows[:page_size]
    start = ((query.page - 1) * TJPE_JSF_RESULTS_PER_PAGE) + 1 if result_rows else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(result_rows),
        total_is_authoritative=reported_total is not None,
    )
    return SearchPage(
        source="tjpe_jurisprudencia",
        total=total,
        start=start,
        end=start + len(result_rows) - 1 if result_rows else 0,
        page=query.page,
        page_size=page_size,
        results=result_rows,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if result_rows else ExtractionStatus.EMPTY),
        total_known=reported_total is not None,
    )


def _is_tjpe_jsf_results(html: str) -> bool:
    lowered = _fold_text(html)
    return "documentos encontrados:" in lowered and (
        "documento 1" in lowered or "processo" in lowered
    )


def _is_tjpe_jsf_choice(html: str) -> bool:
    lowered = _fold_text(html)
    return "documentos encontrados" in lowered and "documento 1" not in lowered


def _has_tjpe_jsf_zero_marker(html: str) -> bool:
    lowered = _fold_text(html)
    return any(
        marker in lowered for marker in ("nenhum documento encontrado", "0 documentos encontrados")
    )


def _extract_tjpe_jsf_total(html: str) -> int | None:
    for pattern in (r"documentos encontrados:\s*(\d+)", r"(\d+)\s+documentos encontrados"):
        match = re.search(pattern, _fold_text(html), re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _stable_jsf_key(process: str, fields: dict[str, str], index: int) -> str:
    normalized = re.sub(r"\D", "", process)
    if normalized:
        return normalized
    digest = hashlib.sha256(repr(sorted(fields.items())).encode("utf-8")).hexdigest()[:16]
    return f"row-{index + 1}-{digest}"


def _clean_jsf_value(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _fold_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value)
    return "".join(char for char in folded if not unicodedata.combining(char)).casefold()


def _date_br(value: str) -> str:
    if not value:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        year, month, day = value.split("-")
        return f"{day}/{month}/{year}"
    return value


def _tjpe_jsf_type_key(types: list[str]) -> str:
    normalized = {_fold_text(item) for item in types}
    if not normalized or "todos" in normalized or len(normalized) > 1:
        return "todos" if len(normalized) > 1 or "todos" in normalized else "acordaos"
    return (
        "monocraticas"
        if next(iter(normalized)) in {"decisao", "monocratica", "monocraticas"}
        else "acordaos"
    )


def _tjpe_jsf_type_label(types: list[str]) -> str:
    return "Decisões Monocráticas" if _tjpe_jsf_type_key(types) == "monocraticas" else "Acórdãos"


def _tjpe_jsf_type_label_ascii(types: list[str]) -> str:
    """Return an accent-free label that matches folded HTML labels."""

    return "Decisoes Monocraticas" if _tjpe_jsf_type_key(types) == "monocraticas" else "Acordaos"


def _tjpe_jsf_type_fields(tipo: str) -> dict[str, str]:
    if tipo == "monocraticas":
        return {"formPesquisaJurisprudencia:tipoDecisaoMonocratica": "on"}
    if tipo == "todos":
        return {
            "formPesquisaJurisprudencia:tipoAcordao": "on",
            "formPesquisaJurisprudencia:tipoDecisaoMonocratica": "on",
            "formPesquisaJurisprudencia:tipoTodos": "on",
        }
    return {"formPesquisaJurisprudencia:tipoAcordao": "on"}


def _infer_jsf_type(fields: dict[str, str], query: JurisprudenceQuery) -> str:
    text = _fold_text(fields.get("acordao", ""))
    if text or _tjpe_jsf_type_key(query.types) == "acordaos":
        return "acordao"
    return "decisao"


def build_tjpe_search_parameters(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, Any]:
    """Build only parameters observed in the public TJPE application."""

    size = _page_size(page_size or query.page_size)
    params: dict[str, Any] = {"page": max(query.page - 1, 0), "size": size}
    if query.text:
        params["pesquisaLivre.contains"] = query.text
    if query.number:
        params["npuSemFormatacao.equals"] = re.sub(r"\D", "", query.number)
    published_from = query.published_from or query.judgment_date_from
    published_to = query.published_to or query.judgment_date_to
    if published_from:
        params["dataJulgamento.greaterThanOrEqual"] = _date_iso(published_from)
    if published_to:
        params["dataJulgamento.lessThanOrEqual"] = _date_iso(published_to)
    if query.types:
        params["tipoSentenca.in"] = query.types
    if query.order_by and query.order_by.lower() != "text":
        params["sort"] = f"dataJulgamento,{_sort_direction(query.order_by)}"
    return params


def _requires_jsf_filter(query: JurisprudenceQuery) -> bool:
    """Return whether a query needs the richer public JSF contract.

    The REST endpoint has no observed parameters for these fields.  Sending
    them to REST would produce a successful response while ignoring the
    caller's constraint, so ``auto`` deliberately selects JSF instead.
    """

    return bool(query.rapporteur.strip() or query.case_class.strip())


def parse_tjpe_search_response(
    data: list[Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    reported_total: int | None = None,
) -> SearchPage:
    """Parse the public TJPE result list without discarding source fields."""

    if not isinstance(data, list):
        raise ParserContractChangedError("TJPE jurisprudence result root must be a list")
    results = [
        _item_to_result(item, trace=trace)
        for item in data[: _page_size(query.page_size)]
        if isinstance(item, dict)
    ]
    total = reported_total if reported_total is not None else len(results)
    page_size = _page_size(query.page_size)
    start = (max(query.page - 1, 0) * page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=reported_total is not None,
    )
    return SearchPage(
        source="tjpe_jurisprudencia",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        source_trace=trace,
        pagination_mode="offset",
        is_complete=complete,
        completeness_reason=reason,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        total_known=reported_total is not None,
    )


def _item_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    source_key = _first_string(item, "chave", "codigoProcesso", "npuSemFormatacao")
    if not source_key:
        raise ParserContractChangedError("TJPE jurisprudence item missing stable key")
    summary_raw = _first_string(item, "textoEmenta")
    full_text_raw = _first_string(item, "textoAcordao", "textoDecisao")
    summary = _html_to_text(summary_raw)
    full_text = _html_to_text(full_text_raw)
    judgment_raw = _first_string(item, "dataJulgamento", "dataJulgamentoString")
    publication_raw = _first_string(item, "dataPublicacao", "dataPublicacaoString")
    return JurisprudenceResult(
        id=f"tjpe-juris-{source_key}",
        source="tjpe_jurisprudencia",
        court="TJPE",
        type=_first_string(item, "tipoSentenca") or _infer_type(item),
        number=_first_string(item, "npu", "npuSemFormatacao", "numAntigo"),
        summary=summary or None,
        full_text=full_text or None,
        rapporteur=_first_string(item, "relator"),
        judgment_date=_date_iso(judgment_raw) if judgment_raw else None,
        publication_date=_date_iso(publication_raw) if publication_raw else None,
        updated_at=(
            _date_iso(publication_raw or judgment_raw)
            if (publication_raw or judgment_raw)
            else None
        ),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        degree="second",
        instance="second",
        branch="state",
        authority="TJPE",
        collection="CJSG",
        document_type=_infer_type(item),
        source_trace=trace,
        raw={
            **item,
            "source_key": source_key,
            "summary_raw": summary_raw,
            "full_text_raw": full_text_raw,
            "judgment_date": _date_iso(judgment_raw) if judgment_raw else None,
            "publication_date": _date_iso(publication_raw) if publication_raw else None,
            "judging_body": _first_string(item, "nomeOrgaoJulgador", "codOrgaoJulgador"),
            "case_class": _first_string(item, "descrClasseCNJ", "classeCNJ"),
        },
    )


def _html_to_text(value: str) -> str:
    if not value:
        return ""
    text = BeautifulSoup(unescape(value), "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _date_iso(value: str) -> str:
    text = value.strip()
    for pattern in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    for pattern in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return text[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", text) else text


def _first_string(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _infer_type(item: dict[str, Any]) -> str:
    return "acordao" if item.get("textoAcordao") else "decisao"


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 100))


def _as_int(value: object, *, default: int | None = None) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _sort_direction(value: str) -> str:
    return "asc" if value.lower().endswith("asc") else "desc"
