"""TJSP eproc public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

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
        self._last_request = 0.0
        self._last_http_metadata: dict[str, Any] = {}
        self._last_response_content = b""

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
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
            ],
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
        self._respect_rate_limit()
        url = urljoin(self.config.tjsp_eproc_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"TJSP/eproc jurisprudence request failed: {exc}") from exc

        response.encoding = response.encoding or "utf-8"
        text = response.text
        content = _response_bytes(response, text)
        headers = getattr(response, "headers", {}) or {}
        self._last_response_content = content
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(getattr(response, "url", url) or url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
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
        return text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_eproc_jurisprudencia_results(
    html: str,
    *,
    trace: SourceTrace,
    source_url: str,
    source: str = "tjsp_eproc_jurisprudencia",
    court: str = "TJSP",
    id_prefix: str = "tjsp-eproc-jurisprudencia",
    source_label: str = "TJSP/eproc jurisprudence",
) -> list[JurisprudenceResult]:
    """Parse public eproc jurisprudence result cards."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError(f"{source_label} returned access-control HTML")

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".resultadoItem")
    if not items and _looks_like_search_page(soup):
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
    initial_payload = _build_payload(query)
    initial_html, initial_url = provider._request_text("POST", list_endpoint, data=initial_payload)
    remote_size = _remote_page_size(query.page_size)
    remote_page, local_offset = _remote_window(query.page, query.page_size, remote_size)
    html = initial_html
    source_url = initial_url
    endpoint = list_endpoint
    request_payload: dict[str, Any] = initial_payload
    total = _hidden_int(initial_html, "hdnTotalResultado")
    total_is_authoritative = total is not None
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
        total_is_authoritative=total_is_authoritative,
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
    )


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
) -> JurisprudenceResult:
    labels = _extract_label_values(item)
    process_link = item.select_one("a.numero-processo") or item.select_one(
        "a[data-link*='processo_']"
    )
    process_text = _clean_text(process_link.get_text(" ", strip=True) if process_link else "")
    process_number = _find_process_number(
        process_text or labels.get("processo", "") or item.get_text(" ", strip=True)
    )

    document_type = _clean_text(_text(item.select_one(".resValueTipoJurisprudencia")))
    if not document_type:
        document_type = _infer_document_type(item.get_text(" ", strip=True))
    document_id = _extract_item_id(item)
    process_url = _absolute_url(process_link.get("href") if process_link else None, source_url)
    document_link = item.select_one(
        "a.inteiroTeor, a[data-link*='download_inteiro_teor'], "
        "a[data-link*='jurisprudenciaInteiroTeor']"
    )
    full_text_url = _data_link(document_link, source_url)
    case_class = _extract_case_class(labels.get("processo", ""), process_number or "")
    publication_date = labels.get("data da publicacao")
    judgment_date = labels.get("data do julgamento")

    return JurisprudenceResult(
        id=f"{id_prefix}-{document_id or _digits(process_number)}",
        source=source,
        court=court,
        type=_normalize_decision_type(document_type),
        number=process_number,
        summary=labels.get("decisao") or labels.get("ementa") or _extract_marked_text(item),
        rapporteur=labels.get("magistrado") or labels.get("relator"),
        updated_at=publication_date,
        judgment_date=judgment_date,
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={
            "id_jurisprudencia": document_id,
            "decision_type_label": document_type,
            "case_class": case_class,
            "judging_body": labels.get("orgao julgador"),
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "state": labels.get("uf"),
            "document_url": process_url,
            "full_text_url": full_text_url,
            "source_url": source_url,
            "process_number_missing": process_number is None,
        },
    )


def _build_payload(query: JurisprudenceQuery) -> dict[str, str | list[str]]:
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
    source_origins = _map_source_origins(query.source_origins or [query.source_origin])
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


def _map_source_origins(values: list[str]) -> list[str]:
    mapping = {
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
    return [
        mapped for value in values if value and (mapped := mapping.get(_normalize_label(value)))
    ]


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


def _response_bytes(response: requests.Response, text: str) -> bytes:
    content = getattr(response, "content", None)
    if isinstance(content, bytes):
        return content
    encoding = getattr(response, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace")


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
