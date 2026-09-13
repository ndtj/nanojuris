"""TJPR public jurisprudence search provider."""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import DocumentReference, fetch_document_reference
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
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.parsing import HtmlNode, parse_html
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
DATE_PATTERN = re.compile(r"\d{2}/\d{2}/\d{4}")
SESSION_ID_PATTERN = re.compile(r";jsessionid=[^?#/]+", re.IGNORECASE)


class TjprJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TJPR jurisprudence HTML search."""

    name = "tjpr_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjpr_jurisprudencia_url).hostname or ""
        self._document_policy = TransportPolicy(
            allowed_hosts=(host,),
            timeout_seconds=self.config.timeout,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self.http = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                # The public form is stateful and reports access-control and
                # server errors explicitly.  Do not hide those signals behind
                # an automatic retry; pacing and circuit breaking remain in the
                # shared boundary.
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_request = 0.0
        self._last_http_metadata: dict[str, Any] = {}
        # Detail slugs are source-issued and may contain accents or session
        # state.  Keep the exact URL observed during search so callers can use
        # the opaque result id without reconstructing a route.
        self._document_urls: dict[str, str] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_degree_scope(query)
        endpoint = "/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true"
        html, final_url = self._search_html(query, endpoint)
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /jurisprudencia/publico/pesquisa.do?actionType=pesquisar",
            query={
                "criterioPesquisa": query.text or query.exact_phrase or query.number,
                "processo": query.number,
                "dataPublicacaoInicio": query.published_from,
                "dataPublicacaoFim": query.published_to,
                "dataJulgamentoInicio": query.updated_from,
                "dataJulgamentoFim": query.updated_to,
                "page": query.page,
                "page_size": query.page_size,
            },
            source_url=final_url,
            limitations=[
                "Fonte HTML publica do TJPR sujeita a mudancas de layout.",
                "A busca publica tambem apresenta uma secao separada da Corte IDH; "
                "ela nao e convertida neste provider em jurisprudencia TJPR.",
                "O resultado pode indicar segredo de justica ou conteudo pendente; "
                "o provider preserva o status sem inferir inteiro teor.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjpr_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjpr_jurisprudencia_url,
        )
        if query.fetch_details:
            self._populate_full_text(page, query)
        for result in page.results:
            if result.document_url:
                self._document_urls[result.id] = result.document_url
        return page

    def _populate_full_text(self, page: SearchPage, query: JurisprudenceQuery) -> None:
        """Expand truncated ementas through TJPR's public XHR endpoint.

        The portal exposes the complete text through a session-bound, read-only
        ``exibirTextoCompleto`` request.  This is deliberately opt-in because
        it costs one bounded request per result and the endpoint may return a
        partial/secret document.  A failed expansion never becomes an empty
        search result: the row remains visible with explicit extraction
        metadata.
        """

        criterion = query.text or query.exact_phrase or query.number
        if not criterion:
            return
        for result in page.results:
            if result.access_status is not AccessStatus.PUBLIC:
                result.raw["full_text_status"] = "not_requested_access_partial"
                continue
            source_id = str(result.raw.get("source_record_id") or "").strip()
            if not source_id:
                continue
            try:
                full_text, metadata = self._fetch_full_text(source_id, criterion)
            except (
                AccessControlRequiredError,
                RateLimitDetectedError,
                SourceUnavailableError,
                ParserContractChangedError,
            ) as exc:
                result.raw["full_text_error"] = str(exc)
                result.raw["full_text_status"] = "unavailable"
                result.extraction_status = ExtractionStatus.PARTIAL
                continue
            if not full_text:
                result.raw["full_text_status"] = "empty"
                result.extraction_status = ExtractionStatus.PARTIAL
                continue
            result.full_text = full_text
            result.extraction_status = ExtractionStatus.COMPLETE
            result.raw["full_text_status"] = "complete"
            result.raw["full_text_sha256"] = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
            result.raw["full_text_http"] = metadata

    def _fetch_full_text(self, source_id: str, criterion: str) -> tuple[str, dict[str, Any]]:
        endpoint = "/jurisprudencia/publico/pesquisa.do?actionType=exibirTextoCompleto"
        url = urljoin(self.config.tjpr_jurisprudencia_url.rstrip("/") + "/", endpoint.lstrip("/"))
        try:
            response = self._request(
                "GET",
                url,
                params={"idProcesso": source_id, "criterio": criterion},
                headers={
                    "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": urljoin(
                        self.config.tjpr_jurisprudencia_url.rstrip("/") + "/",
                        "jurisprudencia/publico/pesquisa.do?actionType=pesquisar",
                    ),
                },
            )
            _raise_for_tjpr_response(response, "TJPR full-text request")
        except (AccessControlRequiredError, RateLimitDetectedError):
            raise
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJPR full-text request failed: {exc}") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPR full-text request failed: {exc}") from exc
        content = bytes(response.body)
        metadata = {
            "http_status": response.status_code,
            "content_type": (getattr(response, "headers", {}) or {}).get("Content-Type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "endpoint": "GET " + endpoint,
        }
        text = _normalize_text(parse_html(content, base_url=url).text())
        if not text or _looks_like_access_control(text) or _looks_like_restricted_detail(text):
            raise ParserContractChangedError("TJPR full-text response had no usable text")
        return text, metadata

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        try:
            document = self.get_document(precedent_id)
        except ValueError as exc:
            raise SourceUnavailableError(
                "TJPR detail is available only from an observed official detail URL"
            ) from exc
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "text/html",
                }
            ],
            source_trace=document.source_trace,
            raw=document.raw_metadata,
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch an explicit TJPR detail URL through the shared document pipeline.

        Search results carry the canonical ``/jurisprudencia/j/<id>/<slug>``
        URL.  Requiring that URL here avoids guessing session-bound slugs from
        an opaque result id while still allowing callers to opt in to the
        public HTML detail page.
        """

        document_url = (
            document_id
            if document_id.startswith("https://")
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "TJPR document_id must be an observed official HTTPS detail URL or "
                "a result id from the current search"
            )
        parsed = urlparse(document_url)
        expected_host = urlparse(self.config.tjpr_jurisprudencia_url).hostname
        if parsed.hostname != expected_host:
            raise ValueError("TJPR document URL is outside the configured allowlist")
        reference = DocumentReference(
            id=document_id,
            source=self.name,
            url=document_url,
            expected_content_types=("text/html", "text/plain"),
        )
        return fetch_document_reference(
            reference,
            policy=self._document_policy,
            session=self.session,
            title=f"TJPR jurisprudência {parsed.path.rsplit('/', 1)[-1]}",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJPR Jurisprudencia",
            source_url=self.config.tjpr_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=["full_text", "case_number", "date_range", "metadata"],
            document_types=["acordao", "decisao_monocratica", "decisao"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "source_record_id",
                "case_number",
                "decision_type",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "summary",
                "document_url",
                "secret_or_pending_content",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true",
                "POST /jurisprudencia/publico/pesquisa.do?actionType=pesquisar",
                "GET /jurisprudencia/publico/pesquisa.do?actionType=exibirTextoCompleto",
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
            completeness_contract="reported_tjpr_window",
            full_text_access="document_link",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
                "judgment_date_from",
                "judgment_date_to",
                "courts",
                "rapporteur",
                "case_class",
                "judging_body",
                "types",
                "fetch_details",
            ],
            unsupported_filters=[
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
                "decision_type",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origin",
                "source_origins",
            ],
            filter_semantics={
                "text": "native",
                "number": "native",
                "published_from": "native",
                "published_to": "native",
                "updated_from": "native",
                "updated_to": "native",
                "fetch_details": "translated",
                "courts": "translated",
                "types": "translated",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "exact_phrase": "unsupported",
                "case_class": "translated",
                "judging_body": "translated",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "decision_type": "unsupported",
                "judgment_date_from": "translated",
                "judgment_date_to": "translated",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "rapporteur": "translated",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
            },
            limitations=[
                "Filtros de classe, relator, comarca, orgao e tipo exigem IDs "
                "obtidos pelos controles publicos da propria pagina; labels nao "
                "sao inferidos nem enviados como se fossem IDs.",
                "O link de detalhe deve ser preservado da resposta; o provider nao monta slug.",
                "O inteiro teor depende do carregamento explicito do link de detalhe publico; "
                "ementa e inteiro teor continuam estados distintos.",
            ],
            responsible_use=[
                "Usar paginas pequenas e respeitar rate limit local.",
                "Nao tentar acessar a area restrita nem contornar captcha ou sessao.",
                "Preservar SourceTrace, URL oficial e campos de acesso parcial.",
            ],
        )

    def _search_html(self, query: JurisprudenceQuery, endpoint: str) -> tuple[str, str]:
        initial_url = urljoin(
            self.config.tjpr_jurisprudencia_url.rstrip("/") + "/", endpoint.lstrip("/")
        )
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            initial = self._request("GET", initial_url, headers=headers)
            _raise_for_tjpr_response(initial, "TJPR initial search")
            initial_final_url = str(initial.final_url or initial.url)
            form = parse_html(initial.body, base_url=initial_final_url).select_one(
                "form#pesquisaForm"
            )
            if form is None or not form.get("action"):
                raise ParserContractChangedError("TJPR search form pesquisaForm not found")
            payload = _form_payload(form)
            payload.update(_query_payload(query))
            action = urljoin(initial_final_url, str(form["action"]))
            response = self._request(
                "POST",
                action,
                data=payload,
                headers={**headers, "Referer": initial_final_url},
            )
            _raise_for_tjpr_response(response, "TJPR search")
        except (ParserContractChangedError, AccessControlRequiredError):
            raise
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJPR search request failed: {exc}") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPR search request failed: {exc}") from exc
        content = bytes(response.body)
        headers_received = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or action),
            "content_type": response.content_type or headers_received.get("Content-Type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        return response.text, _strip_session_id(str(response.final_url or action))

    def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        data: Any = None,
    ) -> Any:
        """Execute one bounded request through the shared transport."""

        request = TransportRequest(
            source=self.name,
            operation=f"tjpr_{method.lower()}",
            method=method,
            url=url,
            headers=headers,
            params=params or {},
            data=data,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        try:
            response = self.http.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPR request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJPR transport failed: {response.error_type or response.status.value}"
            )
        return response

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)


def parse_tjpr_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse TJPR's public result table without including Corte IDH rows."""

    document = parse_html(html, base_url=base_url)
    table = document.select_one("table.resultTable.jurisprudencia")
    if table is None:
        text = _normalize_text(document.text())
        if _is_explicit_empty(text) and not _looks_like_access_control(text):
            return _empty_page(query, trace, "A fonte respondeu sem registros TJPR.")
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("TJPR returned an access-control page")
        raise ParserContractChangedError("TJPR jurisprudence result table not found")

    total = _parse_total(document.text())
    rows = [row for row in table.select("tr") if _is_tjpr_row(row)]
    results: list[JurisprudenceResult] = []
    for index, row in enumerate(rows, start=1):
        result = _parse_tjpr_row(row, trace=trace, base_url=base_url, index=index)
        if result is not None:
            results.append(result)
    if rows and not results:
        raise ParserContractChangedError("TJPR rows found but no decision fields were parsed")

    limited = results[: query.page_size]
    start = ((query.page - 1) * query.page_size) + 1 if limited else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(limited),
        total_is_authoritative=total is not None,
    )
    return SearchPage(
        source="tjpr_jurisprudencia",
        total=total if total is not None else len(results),
        start=start,
        end=start + len(limited) - 1 if limited else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
        filters_applied=_tjpr_filters_applied(query),
        total_known=total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if limited else ExtractionStatus.EMPTY),
    )


def _parse_tjpr_row(
    row: HtmlNode,
    *,
    trace: SourceTrace,
    base_url: str,
    index: int,
) -> JurisprudenceResult | None:
    link = row.select_one("a[href*='/jurisprudencia/j/']")
    if link is None:
        return None
    row_text = _normalize_text(row.get_text(" ", strip=True))
    case_number = _first_match(CNJ_PATTERN, row_text)
    source_id = _input_value(row, "idsSelecionados")
    if not source_id:
        source_id = case_number or hashlib.sha256(row_text.encode("utf-8")).hexdigest()[:16]
    decision_type = _extract_parenthesized_type(link, row_text)
    judgment_raw = _label_value(row_text, "Data Julgamento:")
    judgment_date = _parse_br_date(judgment_raw)
    document_url = urljoin(base_url.rstrip("/") + "/", str(link["href"]))
    document_url = _strip_session_id(document_url)
    summary_cell = row.select_one("td.juris-tabela-ementa")
    summary = _normalize_text(summary_cell.get_text(" ", strip=True)) if summary_cell else ""
    summary = _clean_tjpr_ementa(summary)
    rapporteur: str | None = _label_value(row_text, "Relator:")
    rapporteur = _truncate_at_labels(rapporteur)
    judging_body: str | None = _label_value(row_text, "Órgão Julgador:")
    judging_body = _truncate_at_labels(judging_body)
    secret = "Segredo de Justiça" in row_text
    pending = "Conteúdo pendente de análise e liberação" in row_text
    access_status = AccessStatus.PARTIAL if secret or pending else AccessStatus.PUBLIC
    if decision_type == "sentenca":
        raise ParserContractChangedError("TJPR CJSG returned a first-degree sentence")
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=document_url,
        limitations=trace.limitations,
        http_status=trace.http_status,
        final_url=trace.final_url,
        content_type=trace.content_type,
        content_sha256=trace.content_sha256,
        response_bytes=trace.response_bytes,
        retrieval_status=trace.retrieval_status,
    )
    return JurisprudenceResult(
        id=f"tjpr-{source_id}",
        source="tjpr_jurisprudencia",
        court="TJPR",
        type=decision_type,
        number=case_number,
        summary=summary or None,
        rapporteur=rapporteur,
        judgment_date=judgment_date,
        degree="second",
        instance="second",
        branch="state",
        authority="TJPR",
        collection="CJSG",
        document_type=decision_type,
        source_origin="TJPR",
        document_url=document_url,
        access_status=access_status,
        extraction_status=ExtractionStatus.PARTIAL if pending else ExtractionStatus.COMPLETE,
        source_trace=result_trace,
        raw={
            "source_record_id": source_id,
            "case_number": case_number,
            "decision_type": decision_type,
            "rapporteur": rapporteur,
            "judging_body": judging_body,
            "judgment_date": judgment_date,
            "judgment_date_raw": judgment_raw,
            "document_url": document_url,
            "secret_or_pending_content": secret or pending,
            "secret_of_justice": secret,
            "content_pending_release": pending,
            "row_text": row_text,
            "source_row_index": index,
            "degree": "second",
            "instance": "second",
            "branch": "state",
            "authority": "TJPR",
            "collection": "CJSG",
            "document_type": decision_type,
        },
        field_provenance={
            "degree": {"source": "source_contract:tjpr_jurisprudencia_publica"},
            "instance": {"source": "source_contract:tjpr_jurisprudencia_publica"},
            "branch": {"source": "source_contract:tjpr"},
            "authority": {"source": "source_contract:tjpr"},
            "collection": {"source": "source_contract:tjpr_jurisprudencia_publica"},
        },
    )


def _validate_degree_scope(query: JurisprudenceQuery) -> None:
    """Reject first-degree filters before contacting the appellate portal."""

    values = {value.strip().casefold() for value in query.types}
    if values & {"sentenca", "sentença", "first", "primeiro", "primeiro_grau"}:
        raise QueryRejectedError("TJPR jurisprudencia public exposes only second-degree decisions")


def _form_payload(form: HtmlNode) -> dict[str, str]:
    payload: dict[str, str] = {}
    for field in form.select("input[name]"):
        field_type = str(field.get("type") or "text").lower()
        if field_type in {"button", "submit", "checkbox", "radio"}:
            continue
        name = field.get("name")
        if name:
            payload[name] = str(field.get("value") or "")
    return payload


def _query_payload(query: JurisprudenceQuery) -> dict[str, str]:
    # The public TJPR form represents refinement controls as hidden numeric
    # identifiers.  Accepting labels here would make the portal silently run a
    # broader query, so reject them explicitly instead of dropping filters.
    judgment_from = query.judgment_date_from or query.updated_from
    judgment_to = query.judgment_date_to or query.updated_to
    payload = {
        "criterioPesquisa": query.text or query.exact_phrase or query.number,
        "processo": query.number,
        "dataPublicacaoInicio": query.published_from,
        "dataPublicacaoFim": query.published_to,
        "dataJulgamentoInicio": judgment_from,
        "dataJulgamentoFim": judgment_to,
        "pageSize": str(min(query.page_size, 50)),
        "pageNumber": str(query.page),
        "page": str(query.page),
        "sortColumn": "id",
        "sortOrder": "desc",
    }
    payload.update(
        {
            "idComarca": _numeric_selection(query.courts, "courts"),
            "idRelator": _numeric_selection((query.rapporteur,), "rapporteur"),
            "idOrgaoJulgador": _numeric_selection((query.judging_body,), "judging_body"),
            "idClasseProcessual": _numeric_selection((query.case_class,), "case_class"),
            "idsTipoDecisaoSelecionadosString": _numeric_selection(query.types, "types"),
        }
    )
    return payload


def _numeric_selection(values: Any, field_name: str) -> str:
    """Normalize TJPR's comma-separated numeric selection identifiers."""

    if isinstance(values, str):
        items = [values]
    else:
        items = list(values or [])
    tokens: list[str] = []
    for item in items:
        for token in str(item).replace(";", ",").split(","):
            token = token.strip()
            if not token:
                continue
            if not token.isdecimal():
                raise QueryRejectedError(
                    f"TJPR {field_name} requires official numeric selection IDs; got {item!r}"
                )
            tokens.append(token)
    return ",".join(dict.fromkeys(tokens))


def _is_tjpr_row(row: HtmlNode) -> bool:
    return bool(
        row.select_one("input[name='idsSelecionados']")
        and row.select_one("a[href*='/jurisprudencia/j/']")
    )


def _input_value(row: HtmlNode, name: str) -> str | None:
    field = row.select_one(f"input[name='{name}']")
    return str(field.get("value")) if field and field.get("value") else None


def _extract_parenthesized_type(link: HtmlNode, row_text: str) -> str:
    match = re.search(r"\(([^)]+)\)", link.parent.get_text(" ", strip=True) if link.parent else "")
    value = _normalize_text(match.group(1)) if match else "decisao"
    normalized = value.lower()
    if "acórd" in normalized or "acord" in normalized:
        return "acordao"
    if "monocr" in normalized:
        return "decisao_monocratica"
    if "senten" in normalized:
        return "sentenca"
    return value or "decisao"


def _label_value(text: str, label: str) -> str:
    start = text.find(label)
    if start < 0:
        return ""
    return text[start + len(label) :].strip()


def _truncate_at_labels(value: str | None) -> str | None:
    if not value:
        return None
    for label in ("Processo:", "Órgão Julgador:", "Data Julgamento:", "Segredo de Justiça"):
        value = value.split(label, 1)[0]
    return _normalize_text(value) or None


def _parse_total(text: str) -> int | None:
    match = re.search(r"([\d.]+)\s+registro\(s\) encontrado", text, re.IGNORECASE)
    return int(match.group(1).replace(".", "")) if match else None


def _is_explicit_empty(text: str) -> bool:
    normalized = text.lower()
    return "registro(s) encontrado" in normalized or "nenhum resultado" in normalized


def _parse_br_date(value: str) -> str | None:
    match = DATE_PATTERN.search(value or "")
    if not match:
        return None
    return datetime.strptime(match.group(0), "%d/%m/%Y").date().isoformat()


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _strip_session_id(url: str) -> str:
    return SESSION_ID_PATTERN.sub("", url)


_TJPR_HEADER = re.compile(
    r"^\s*(?:PODER JUDICI[ÁA]RIO\s*)?TRIBUNAL DE JUSTI[ÇC]A DO ESTADO DO PARAN[ÁA].*?"
    r"(?:AC[ÓO]RD[ÃA]O|E\s*M\s*E\s*N\s*T\s*A|EMENTA)\s*[-:.]?\s*",
    re.IGNORECASE | re.DOTALL,
)


def _clean_tjpr_ementa(summary: str) -> str:
    """Drop a leading document-header block from the ementa cell.

    Turma Recursal decisions place the court header, autos and party block in
    the ementa cell. Keep only the text after the ementa marker; if the cell is
    only a header, return an empty string so the card falls back to a
    type/number title instead of an identical header title.
    """

    if not summary:
        return summary
    match = _TJPR_HEADER.match(summary)
    if match:
        summary = summary[match.end() :].lstrip(" :.-").rstrip()
    upper = summary.upper()
    if upper.startswith(("TRIBUNAL DE JUSTI", "PODER JUDICI")):
        return ""
    # A cell that begins mid-sentence (lowercase) is a truncated fragment of the
    # inteiro teor, not an ementa; drop it so the card falls back to a
    # type/number title instead of surfacing a dangling clause.
    first = summary.lstrip("\"'“”‘’ ")[:1]
    if first and first.islower():
        return ""
    return summary


def _normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _looks_like_access_control(text: str) -> bool:
    normalized = text.lower()
    return any(
        marker in normalized
        for marker in (
            "captcha",
            "acesso negado",
            "access denied",
        )
    )


def _looks_like_restricted_detail(text: str) -> bool:
    """Detect TJPR's authenticated/intranet shell returned by the XHR route."""

    normalized = text.lower()
    return "acesso restrito" in normalized and (
        "tjpr intranet" in normalized or "usuários" in normalized or "usu�rios" in normalized
    )


def _empty_page(query: JurisprudenceQuery, trace: SourceTrace, reason: str) -> SearchPage:
    return SearchPage(
        source="tjpr_jurisprudencia",
        total=0,
        start=0,
        end=0,
        page=query.page,
        page_size=query.page_size,
        results=[],
        source_trace=trace,
        pagination_mode="page",
        is_complete=True,
        completeness_reason=reason,
        filters_applied=_tjpr_filters_applied(query),
        total_known=True,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.EMPTY,
    )


def _tjpr_filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    """Expose TJPR's remote, translated, scope and unsupported filters."""

    native = {
        "text",
        "number",
        "published_from",
        "published_to",
        "updated_from",
        "updated_to",
    }
    translated = {
        "courts",
        "rapporteur",
        "case_class",
        "judging_body",
        "types",
        "fetch_details",
        "judgment_date_from",
        "judgment_date_to",
    }
    scope = {"degree", "instance", "branch", "authority", "collection", "document_type"}
    unsupported = {
        "all_words",
        "any_words",
        "without_words",
        "exact_phrase",
        "decision_type",
        "lawyer_name",
        "legal_area",
        "oab",
        "party_document",
        "party_name",
        "police_document",
        "precatory_number",
        "cda",
        "source_origin",
        "source_origins",
    }
    output: dict[str, str] = {}
    for name in native | translated | unsupported:
        value = getattr(query, name)
        output[name] = (
            "native"
            if name in native and value
            else "translated"
            if name in translated and value
            else "unsupported"
            if name in unsupported and value
            else "not_requested"
        )
    output.update({name: "validated_scope" for name in scope})
    return output


def _raise_for_tjpr_response(response: Any, operation: str) -> None:
    status = int(getattr(response, "status_code", 0) or 0)
    text = str(getattr(response, "text", "") or "")
    if status in {401, 403} or _looks_like_access_control(text):
        raise AccessControlRequiredError(f"{operation} returned access-control response")
    if status == 429:
        raise RateLimitDetectedError(f"{operation} returned HTTP 429")
    if status >= 500:
        raise SourceUnavailableError(f"{operation} returned HTTP {status}")
    if status >= 400:
        raise SourceUnavailableError(f"{operation} returned HTTP {status}")
