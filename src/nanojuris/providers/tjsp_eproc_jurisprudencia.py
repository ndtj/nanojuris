"""TJSP eproc public jurisprudence provider."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.adaptive_selectors import resilient_find_all
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
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
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


class TjspEprocJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TJSP eproc jurisprudence search."""

    name = "tjsp_eproc_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http_metadata: dict[str, Any] = {}
        self._last_response_content = b""
        host = urlparse(self.config.tjsp_eproc_url).hostname or "eproc-consulta.tjsp.jus.br"
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=16_000_000,
                # Preserve one bounded request per eproc operation; access
                # challenges must be surfaced rather than replayed.
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return fetch_eproc_page(
            self,
            query,
            source=self.name,
            court="TJSP",
            id_prefix="tjsp-eproc-jurisprudencia",
            source_label="TJSP/eproc jurisprudence",
            limitations=[
                "Jurisprudencia publica do eproc/TJSP validada com sessao HTTP limpa.",
                "Resultados podem conter sentencas, acordaos e decisoes monocraticas.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        document_id = _extract_document_id(precedent_id)
        content = document.text or ""
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": content,
                    "content_type": document.content_type or "text/plain",
                    "source_content_type": document.raw_metadata.get("source_content_type"),
                }
            ],
            source_trace=document.source_trace,
            raw={"id_jurisprudencia": document_id, **document.raw_metadata},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Load one public eproc document while preserving the original response bytes."""

        eproc_id = _extract_document_id(document_id)
        endpoint = (
            "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor"
        )
        params = {"id_jurisprudencia": eproc_id}
        html, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=[
                "Documento retornado pela rota publica de inteiro teor eproc/TJSP.",
                "Uma resposta de controle de acesso gera erro explicito e nao e tratada "
                "como documento.",
            ],
        )
        trace = _trace_with_http_metadata(trace, self._last_http_metadata)
        content = self._last_response_content or html.encode("utf-8")
        return build_canonical_document(
            document_id=f"tjsp-eproc-jurisprudencia-document-{eproc_id}",
            source=self.name,
            document_type="decisao",
            content=content,
            content_type=self._last_http_metadata.get("content_type") or "text/html",
            title=f"TJSP eproc inteiro teor {eproc_id}",
            url=source_url,
            access_status=AccessStatus.PUBLIC,
            source_trace=trace,
            raw_metadata={"id_jurisprudencia": eproc_id},
            parser="tjsp_eproc_jurisprudencia.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJSP eproc Jurisprudencia",
            source_url=self.config.tjsp_eproc_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range"],
            document_types=["sentenca", "acordao", "decisao_monocratica"],
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
            pagination_mode="page",
            completeness_contract="reported_form_total_and_page_window",
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
                "source_origin",
                "degree",
                "instance",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "rapporteur",
                "fetch_details",
                "case_class",
                "judging_body",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origins",
            ],
            filter_semantics={
                "text": "native",
                "number": "native",
                "published_from": "native",
                "published_to": "native",
                "updated_from": "native",
                "updated_to": "native",
                "source_origin": "translated",
                # eproc exposes origin (4/5) rather than canonical degree;
                # the adapter translates the request and verifies the card
                # locally before returning it.
                "degree": "local_postfilter",
                "instance": "local_postfilter",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "types": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "exact_phrase": "unsupported",
                "rapporteur": "unsupported",
                "fetch_details": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "source_origins": "unsupported",
            },
            limitations=[
                "Rota publica descoberta e validada por requests limpo em 2026-08-02.",
                "O filtro source_origin aceita colegio_recursal, primeiro_grau e segundo_grau.",
                "Cards de resultado trazem texto de decisao; o inteiro teor e carregado "
                "sob demanda e pode redirecionar para controle de acesso.",
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
        url = urljoin(self.config.tjsp_eproc_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        headers.update(kwargs.pop("headers", {}))
        request = TransportRequest(
            source=self.name,
            operation=f"{method.lower()}_{path.lstrip('/').replace('/', '_')}",
            method=method,
            url=url,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            headers=headers,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported TJSP/eproc transport arguments: {sorted(kwargs)}")
        try:
            response = self._transport.request(request)
        except (requests.RequestException, SourceUnavailableError) as exc:
            raise SourceUnavailableError(f"TJSP/eproc jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                "TJSP/eproc jurisprudence transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError(
                "TJSP/eproc jurisprudence transport returned no HTTP status"
            )
        text = response.text
        content = response.body
        headers = getattr(response, "headers", {}) or {}
        self._last_response_content = content
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJSP/eproc jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJSP/eproc jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"TJSP/eproc jurisprudence returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJSP/eproc jurisprudence rejected request with HTTP {response.status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError(
                "TJSP/eproc jurisprudence returned access-control HTML"
            )
        return text, str(response.final_url or url)


def parse_eproc_jurisprudencia_results(
    html: str,
    *,
    trace: SourceTrace,
    source_url: str,
    source: str = "tjsp_eproc_jurisprudencia",
    court: str = "TJSP",
    id_prefix: str = "tjsp-eproc-jurisprudencia",
    source_label: str = "TJSP/eproc jurisprudence",
    degree_hint: str | None = None,
) -> list[JurisprudenceResult]:
    """Parse public eproc jurisprudence result cards."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError(f"{source_label} returned access-control HTML")

    soup = BeautifulSoup(html, "html.parser")
    items = resilient_find_all(
        soup,
        ".resultadoItem",
        name="result_card",
        source=source,
        # An explicit empty result page must not be populated by adaptive
        # relocation from a prior page.  Relocation is useful for layout drift,
        # but reusing a stale card would fabricate a result.
        memory=None,
        trace=trace,
    )
    if not items and (_looks_like_search_page(soup) or _looks_like_empty_result(soup)):
        return []
    if not items:
        raise ParserContractChangedError(f"{source_label} result cards not found")
    return [
        _parse_result_item(
            item,
            trace=trace,
            source_url=source_url,
            source=source,
            court=court,
            id_prefix=id_prefix,
            source_label=source_label,
            degree_hint=degree_hint,
        )
        for item in items
    ]


def fetch_eproc_page(
    provider: Any,
    query: JurisprudenceQuery,
    *,
    source: str,
    court: str,
    id_prefix: str,
    source_label: str,
    limitations: list[str],
) -> SearchPage:
    """Fetch one logical page through eproc's public form/AJAX contract."""

    list_endpoint = "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados"
    initial_payload = _build_payload(query, court=court)
    initial_html, initial_url = provider._request_text("POST", list_endpoint, data=initial_payload)
    remote_size = _remote_page_size(query.page_size)
    remote_page, local_offset = _remote_window(query.page, query.page_size, remote_size)
    html = initial_html
    source_url = initial_url
    endpoint = list_endpoint
    request_payload: dict[str, Any] = initial_payload
    total = _hidden_int(initial_html, "hdnTotalResultado")
    total_is_authoritative = total is not None
    requested_degree = _normalize_requested_degree(query.degree or query.instance)
    degree_hint = (
        requested_degree
        if requested_degree == "second"
        and court in {"TRF2", "TRF4", "TRF6"}
        and "1" in list(initial_payload.get("selOrigem[]", []))
        else None
    )
    if remote_page > 1:
        form_payload = _extract_form_payload(initial_html)
        form_payload["hdnPaginaAtual"] = str(remote_page)
        form_payload["selTamanhoPagina"] = str(remote_size)
        endpoint = _hidden_value(initial_html, "hdnUrlPaginar") or (
            "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado"
        )
        request_payload = form_payload
        html, source_url = provider._request_text("POST", endpoint, data=form_payload)

    trace = _trace_with_http_metadata(
        SourceTrace(
            provider=source,
            endpoint=endpoint,
            query={**request_payload, "logical_page": query.page},
            source_url=source_url,
            limitations=limitations,
        ),
        provider._last_http_metadata,
    )
    results = parse_eproc_jurisprudencia_results(
        html,
        trace=trace,
        source_url=source_url,
        source=source,
        court=court,
        id_prefix=id_prefix,
        source_label=source_label,
        degree_hint=degree_hint,
    )
    # eproc installations expose several judicial instances through the same
    # public form.  When the caller asks for a specific degree, accepting a
    # card without an auditable degree would silently mix first/second
    # instance data.  Treat that as a contract failure, never as an empty
    # result or a best-effort post-filter.
    degree_postfiltered = False
    if requested_degree:
        unknown = [item for item in results if item.degree is None]
        if unknown:
            raise ParserContractChangedError(
                f"{source_label} returned results without an identifiable judicial degree"
            )
        results = [item for item in results if item.degree == requested_degree]
        degree_postfiltered = True
        if not results:
            raise ParserContractChangedError(
                f"{source_label} returned results outside requested degree={requested_degree}"
            )
    if total is None:
        total = _hidden_int(html, "hdnTotalResultado")
        if total is not None:
            total_is_authoritative = True
        else:
            total = len(results)
    limited = results[local_offset : local_offset + query.page_size]
    start = ((query.page - 1) * query.page_size) + 1 if limited else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(limited),
        total_is_authoritative=total_is_authoritative and not degree_postfiltered,
    )
    return SearchPage(
        source=source,
        total=total,
        start=start,
        end=start + len(limited) - 1 if limited else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if limited else ExtractionStatus.EMPTY,
        total_known=total_is_authoritative and not degree_postfiltered,
        filters_applied=_eproc_filters_applied(query, degree_postfiltered=degree_postfiltered),
    )


def _eproc_filters_applied(
    query: JurisprudenceQuery, *, degree_postfiltered: bool = False
) -> dict[str, str]:
    """Describe the canonical filters represented by the eproc form."""

    applied: dict[str, str] = {}
    if query.text and not query.exact_phrase:
        applied["text"] = "native"
    if query.exact_phrase:
        applied["exact_phrase"] = "native"
    if query.number:
        applied["number"] = "native"
    for name, value in (
        ("published_from", query.published_from),
        ("published_to", query.published_to),
        ("updated_from", query.updated_from),
        ("updated_to", query.updated_to),
    ):
        if value:
            applied[name] = "native"
    if query.types:
        applied["types"] = "translated"
    if query.source_origin or query.source_origins:
        applied["source_origin"] = "translated"
    if degree_postfiltered or query.degree:
        applied["degree"] = "local_postfilter"
    if degree_postfiltered or query.instance:
        applied["instance"] = "local_postfilter"
    return applied


def _remote_page_size(requested: int) -> int:
    """Select the smallest public eproc page size that contains the request."""

    return next((size for size in (10, 25, 50, 100) if size >= requested), 100)


def _remote_window(page: int, requested: int, remote_size: int) -> tuple[int, int]:
    """Map a logical NanoJuris page to a public eproc page and local offset."""

    zero_based = (page - 1) * requested
    return zero_based // remote_size + 1, zero_based % remote_size


def _extract_form_payload(html: str) -> dict[str, Any]:
    """Serialize the public result form like the source JavaScript does."""

    soup = BeautifulSoup(html, "html.parser")
    form = soup.select_one("form#frmJurisprudenciaResultado") or soup.select_one("form")
    if form is None:
        raise ParserContractChangedError("eproc result form not found for pagination")
    payload: dict[str, str | list[str]] = {}
    for field in form.select("input[name], select[name], textarea[name]"):
        name = str(field.get("name"))
        value: str | list[str]
        if field.name == "input":
            field_type = str(field.get("type") or "text").lower()
            if field_type in {"checkbox", "radio"} and not field.has_attr("checked"):
                continue
            value = str(field.get("value") or "")
            if field_type in {"checkbox", "radio"} and not value:
                value = "on"
        elif field.name == "select":
            selected = list(field.select("option[selected]"))
            # jQuery's serializeArray omits an unselected multiple select.
            # Picking its first option silently adds a source-side filter to
            # subsequent AJAX pagination requests.
            if not selected and not field.has_attr("multiple"):
                selected = list(field.select("option")[:1])
            value = [str(option.get("value") or "") for option in selected]
        else:
            value = field.get_text()
        if isinstance(value, list):
            if not value:
                continue
            existing = payload.get(name)
            if isinstance(existing, list):
                existing.extend(value)
            else:
                payload[name] = list(value)
        elif name in payload:
            current = payload[name]
            payload[name] = current + [value] if isinstance(current, list) else [current, value]
        else:
            payload[name] = value
    return payload


def _hidden_value(html: str, name: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    field = soup.select_one(f"input[name='{name}'], input#{name}")
    return str(field.get("value") or "") if field else ""


def _hidden_int(html: str, name: str) -> int | None:
    value = _hidden_value(html, name)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_result_item(
    item: Tag,
    *,
    trace: SourceTrace,
    source_url: str,
    source: str,
    court: str,
    id_prefix: str,
    source_label: str,
    degree_hint: str | None = None,
) -> JurisprudenceResult:
    labels = _extract_label_values(item)
    process_link = item.select_one("a.numero-processo") or item.select_one(
        "a[data-link*='processo_']"
    )
    process_text = _clean_text(process_link.get_text(" ", strip=True) if process_link else "")
    process_number = _find_process_number(
        process_text or labels.get("processo", "") or item.get_text(" ", strip=True)
    )

    document_type_label = _clean_text(_text(item.select_one(".resValueTipoJurisprudencia")))
    document_type = document_type_label
    if not document_type:
        document_type = _infer_document_type(item.get_text(" ", strip=True))
    document_id = _extract_item_id(item)
    if not document_id and not process_number:
        raise ParserContractChangedError(
            f"{source_label} result missing stable id and process number"
        )
    process_url = _absolute_url(process_link.get("href") if process_link else None, source_url)
    document_link = item.select_one(
        "a.inteiroTeor, a[data-link*='download_inteiro_teor'], "
        "a[data-link*='jurisprudenciaInteiroTeor']"
    )
    full_text_url = _data_link(document_link, source_url)
    case_class = _extract_case_class(labels.get("processo", ""), process_number or "")
    publication_date = labels.get("data da publicacao")
    judgment_date = labels.get("data do julgamento")
    judging_body = labels.get("orgao julgador")
    source_origin = (
        labels.get("origem")
        or labels.get("origem do documento")
        or labels.get("instancia")
        or labels.get("uf")
    )
    # Keep the original label as a degree signal.  TJSC, for example, emits
    # "Decisoes Monocraticas do Tribunal de Justica" as plain card text and
    # the normalized document type alone would lose the appellate qualifier.
    degree_signal = document_type_label or item.get_text(" ", strip=True)
    degree = _infer_degree(source_origin, judging_body, degree_signal) or degree_hint
    instance = degree

    return JurisprudenceResult(
        id=f"{id_prefix}-{document_id or _digits(process_number)}",
        source=source,
        court=court,
        type=_normalize_decision_type(document_type),
        number=process_number,
        # The ementa is the jurisprudence summary; the "decisao" label carries
        # only the "Vistos e relatados..." dispositive formula, which is
        # identical across acordaos and produces useless synthesised titles.
        summary=labels.get("ementa") or _extract_marked_text(item) or labels.get("decisao"),
        rapporteur=labels.get("magistrado") or labels.get("relator"),
        updated_at=publication_date,
        judgment_date=judgment_date,
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        case_class=case_class,
        judging_body=judging_body,
        degree=degree,
        instance=instance,
        branch="state" if court.startswith("TJ") else "federal",
        authority=court,
        collection="JURISPRUDENCIA",
        document_type=_normalize_decision_type(document_type),
        source_origin=source_origin,
        document_url=full_text_url or process_url,
        raw={
            "id_jurisprudencia": document_id,
            "decision_type_label": document_type,
            "case_class": case_class,
            "judging_body": judging_body,
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "state": labels.get("uf"),
            "document_url": process_url,
            "full_text_url": full_text_url,
            "source_url": source_url,
            "degree": degree,
            "instance": instance,
            "source_origin": source_origin,
            "process_number_missing": process_number is None,
        },
    )


def _build_payload(
    query: JurisprudenceQuery, *, court: str | None = None
) -> dict[str, str | list[str]]:
    search_text = query.text or query.exact_phrase
    payload: dict[str, str | list[str]] = {
        "txtPesquisa": search_text,
        "rdoCampo": "E" if query.exact_phrase else "I",
        "hdnExibirPesquisaAvancada": "",
        "txtProcesso": _digits(query.number),
        "dtDecisaoInicio": query.updated_from,
        "dtDecisaoFim": query.updated_to,
        "hdnDecisaoInicio": query.updated_from,
        "hdnDecisaoFim": query.updated_to,
        "dtPublicacaoInicio": query.published_from,
        "dtPublicacaoFim": query.published_to,
        "hdnPublicacaoInicio": query.published_from,
        "hdnPublicacaoFim": query.published_to,
        "chkAgruparResultados": "on",
        "selTamanhoPagina": str(_remote_page_size(query.page_size)),
    }
    document_types = _map_document_types(query.types)
    if document_types:
        payload["selTipoDocumento[]"] = document_types
    requested_origins = query.source_origins or [query.source_origin]
    if not any(requested_origins) and (query.degree or query.instance):
        # The public eproc vocabulary uses origin values rather than a
        # ``degree`` field.  Keep this translation local and auditable.
        requested_origins = [_origin_for_degree(query.degree or query.instance, court=court)]
    source_origins = _map_source_origins(requested_origins, court=court)
    if source_origins:
        payload["selOrigem[]"] = source_origins
    return payload


def _map_document_types(values: list[str]) -> list[str]:
    mapping = {
        "1": "1",
        "acordao": "1",
        "2": "2",
        "monocratica": "2",
        "decisao_monocratica": "2",
        "3": "3",
        "sumula": "3",
        "4": "4",
        "despacho": "4",
        "despacho_decisao_vice_presidencia": "4",
        "5": "5",
        "sentenca": "5",
    }
    return [mapped for value in values if (mapped := mapping.get(_normalize_label(value)))]


def _map_source_origins(values: list[str], *, court: str | None = None) -> list[str]:
    mapping = {
        "1": "1",
        "3": "3",
        "colegio_recursal": "3",
        "colegio recursal": "3",
        "4": "4",
        "primeiro_grau": "4",
        "primeiro grau": "4",
        "1g": "4",
        "5": "5",
        "segundo_grau": "5",
        "segundo grau": "5",
        "2g": "5",
    }
    mapped_values: list[str] = []
    for value in values:
        if not value:
            continue
        normalized = _normalize_label(value)
        if normalized in {"segundo grau", "2g", "second", "segunda instancia"} and court in {
            "TJRJ",
            "TJSC",
            "TRF2",
            "TRF4",
            "TRF6",
        }:
            mapped_values.append("1")
            continue
        if normalized in {"primeiro grau", "1g", "first", "primeira instancia"} and court in {
            "TJRJ",
            "TJSC",
        }:
            # These public eproc installations expose only their appellate
            # corpus through this form; keep the request explicit and let the
            # parser reject any non-first-degree response.
            mapped_values.append("1")
            continue
        mapped = mapping.get(normalized)
        if mapped:
            mapped_values.append(mapped)
    return mapped_values


def _origin_for_degree(value: str, *, court: str | None = None) -> str:
    """Translate canonical degree/instance values to eproc origin labels."""

    normalized = _normalize_label(value)
    if normalized in {"second", "2", "2g", "segundo grau", "segunda instancia"}:
        return "1" if court in {"TJRJ", "TJSC", "TRF2", "TRF4", "TRF6"} else "segundo_grau"
    if normalized in {"first", "1", "1g", "primeiro grau", "primeira instancia"}:
        return "primeiro_grau"
    return value


def _normalize_requested_degree(value: str) -> str | None:
    """Return the canonical degree requested by a query, when recognized."""

    normalized = _normalize_label(value)
    if normalized in {"second", "2", "2g", "segundo grau", "segunda instancia"}:
        return "second"
    if normalized in {"first", "1", "1g", "primeiro grau", "primeira instancia"}:
        return "first"
    return None


def _infer_degree(origin: str | None, judging_body: str | None, document_type: str) -> str | None:
    """Infer degree only from explicit source labels or strong court clues."""

    haystack = _normalize_label(" ".join(part for part in (origin, judging_body) if part))
    if any(token in haystack for token in ("segundo grau", "2o grau", "2g", "segundo instancia")):
        return "second"
    if any(token in haystack for token in ("primeiro grau", "1o grau", "1g", "primeiro instancia")):
        return "first"
    # A vara/sentenca is a reliable first-instance signal in the eproc result
    # cards.  Câmara, turma and tribunal labels identify appellate material.
    if any(token in haystack for token in ("vara ", "vara de", "juizado especial")):
        return "first"
    if any(token in haystack for token in ("camara", "turma", "tribunal", "orgao especial")):
        return "second"
    normalized_type = _normalize_label(document_type)
    if normalized_type in {"acordao", "sumula"} or any(
        token in normalized_type for token in ("acordao", "sumula")
    ):
        return "second"
    # Some eproc deployments put the appellate scope only in the document
    # label (for example, "Decisoes Monocraticas do Tribunal de Justica") and
    # omit a separate origin/organ field.  Accept that signal only when the
    # label names a tribunal; a generic "decisao monocratica" remains unknown
    # rather than being guessed as second degree.
    if "tribunal" in normalized_type and (
        "decisao monocratica" in normalized_type or "decisoes monocraticas" in normalized_type
    ):
        return "second"
    return None


def _extract_label_values(item: Tag) -> dict[str, str]:
    values: dict[str, str] = {}
    for label_node in item.select(".resLabel"):
        key = _normalize_label(label_node.get_text(" ", strip=True))
        parent = label_node.parent if isinstance(label_node.parent, Tag) else None
        value_node = parent.select_one(".resValue") if parent else None
        value = _clean_text(_text(value_node))
        if key and value:
            values[key] = value
    normalized_text = _normalize_label(item.get_text(" ", strip=True))
    for date_label in ("data do julgamento", "data da publicacao"):
        match = re.search(
            rf"{re.escape(date_label)}\s*:?\s*(\d{{2}}/\d{{2}}/\d{{4}})",
            normalized_text,
        )
        if match:
            values.setdefault(date_label, match.group(1))
    return values


def _extract_item_id(item: Tag) -> str:
    checkbox = item.select_one("input.chkDocumento")
    value = checkbox.get("value") if checkbox else ""
    if value:
        return str(value)
    raw_id = str(item.get("id") or "")
    return raw_id.removeprefix("resultado")


def _extract_document_id(precedent_id: str) -> str:
    match = re.search(r"(\d{12,})$", precedent_id)
    if not match:
        raise ParserContractChangedError(
            "TJSP/eproc jurisprudence id must end with id_jurisprudencia digits"
        )
    return match.group(1)


def _extract_case_class(process_label_value: str, process_number: str) -> str | None:
    value = process_label_value.replace(process_number, "")
    value = re.sub(r"/[A-Z0-9]{2,6}\b", "", value)
    value = _clean_text(value)
    return value or None


def _normalize_decision_type(value: str) -> str:
    normalized = _normalize_label(value)
    mapping = {
        "acordao": "acordao",
        "decisao monocatica": "monocratica",
        "decisao monocratica": "monocratica",
        "sentenca": "sentenca",
        "sumula": "sumula",
    }
    return mapping.get(normalized, normalized or "decisao")


def _data_link(node: Tag | None, base_url: str) -> str | None:
    if node is None:
        return None
    return _absolute_url(node.get("data-link"), base_url)


def _absolute_url(value: object, base_url: str) -> str | None:
    if not value:
        return None
    return urljoin(base_url, str(value).replace("&amp;", "&"))


def _find_process_number(text: str) -> str | None:
    match = PROCESS_NUMBER_RE.search(text)
    if match:
        return match.group(0)
    source_match = re.search(
        r"\bprocesso\s+([0-9A-Za-z][0-9A-Za-z./-]*(?:/[A-Z]{2})?)",
        text,
        re.IGNORECASE,
    )
    return source_match.group(1) if source_match else None


def _infer_document_type(text: str) -> str:
    normalized = _normalize_label(text)
    if "decisoes monocraticas" in normalized or "decisao monocratica" in normalized:
        return "decisao monocratica"
    if "acordaos" in normalized or "acordao" in normalized:
        return "acordao"
    if "sumulas" in normalized or "sumula" in normalized:
        return "sumula"
    return "decisao"


def _extract_marked_text(item: Tag) -> str | None:
    text = _clean_text(item.get_text(" ", strip=True))
    normalized = _normalize_label(text)
    for marker in ("ementa", "decisao"):
        index = normalized.find(marker)
        if index < 0:
            continue
        value = text[index + len(marker) :].strip(" :.-")
        return value or None
    return None


def _looks_like_search_page(soup: BeautifulSoup) -> bool:
    return soup.select_one("#frmJurisprudenciaPesquisa") is not None


def _looks_like_empty_result(soup: BeautifulSoup) -> bool:
    """Recognize eproc's authoritative zero-result result form.

    A filtered query can return the result form without any cards.  The form
    carries an explicit ``0 documentos encontrados`` message, which is a
    legitimate empty result and must not be confused with a parser/schema
    failure.
    """

    if soup.select_one("#frmJurisprudenciaResultado") is None:
        return False
    text = _normalize_label(soup.get_text(" ", strip=True))
    return bool(re.search(r"\b0\s+documentos?\s+encontrad", text))


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    return (
        any(
            signal in lowered
            for signal in [
                "g-recaptcha",
                "cf-turnstile",
                "cloudflare",
                "captcha",
                "login e senha",
                "entrar no sistema",
            ]
        )
        and "resultadoitem" not in lowered
    )


def _digits(value: object) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_label(value: str) -> str:
    normalized = _clean_text(value).casefold()
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for original, replacement in replacements.items():
        normalized = normalized.replace(original, replacement)
    return normalized


def _trace_with_http_metadata(trace: SourceTrace, metadata: dict[str, Any]) -> SourceTrace:
    return SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        retrieved_at=trace.retrieved_at,
        query=trace.query,
        source_url=trace.source_url,
        limitations=trace.limitations,
        http_status=metadata.get("http_status"),
        final_url=metadata.get("final_url"),
        content_type=metadata.get("content_type"),
        content_sha256=metadata.get("content_sha256"),
        response_bytes=metadata.get("response_bytes"),
        retrieval_status="ok" if metadata.get("http_status") == 200 else None,
    )
