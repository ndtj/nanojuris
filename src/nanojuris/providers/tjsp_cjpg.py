"""TJSP CJPG (first-instance) public jurisprudence provider.

TJSP's e-SAJ exposes first-instance decisions through the ``cjpg`` HTML
surface.  The collection is distinct from CJSG (second instance), so this
adapter keeps its source identity and first-degree semantics explicit.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from nanojuris.adaptive_selectors import USE_DEFAULT_MEMORY, resilient_find_all
from nanojuris.canonical import normalize_date
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
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
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

TJSP_CJPG_PAGE_SIZE = 10
_PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
_TOTAL_RE = re.compile(
    r"(?:resultados?|registros?)\s+\d+\s+a\s+\d+\s+de\s+([\d.]+)",
    re.IGNORECASE,
)


class TjspCjpgProvider(JurisprudenceProvider):
    """Provider for the public TJSP first-instance (CJPG) search."""

    name = "tjsp_cjpg"
    # The e-SAJ CJPG form is shared by more than one state court.  Keep the
    # parser implementation common, while allowing a court-specific binding
    # to provide its own authority and host without conflating identities.
    authority = "TJSP"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjsp_cjpg_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self._inline_documents: dict[str, tuple[str, SourceTrace]] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjsp_cjpg_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_cjpg_scope(query, authority=self.authority, source_label=f"{self.authority}/CJPG")
        term = query.text or query.exact_phrase or query.number
        if not term:
            raise ValueError("TJSP CJPG search requires text, exact_phrase or number")
        page_size = _page_size(query.page_size)
        initial = query if query.page == 1 else replace(query, page=1)
        params = build_tjsp_cjpg_params(initial)
        content, source_url = self._request_html("GET", "/cjpg/pesquisar.do", params=params)
        endpoint = "GET /cjpg/pesquisar.do"
        trace_query: dict[str, Any] = {
            "params": params,
            "page": query.page,
            "page_size": page_size,
            "collection": "first_degree",
        }
        if query.page > 1:
            pagination_path = f"/cjpg/trocarDePagina.do?pagina={query.page}&conversationId="
            content, source_url = self._request_html("GET", pagination_path)
            endpoint = "GET /cjpg/trocarDePagina.do"
            trace_query["pagina"] = query.page
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=trace_query,
            source_url=source_url,
            limitations=[
                "CJPG e a colecao publica de decisoes de primeiro grau do "
                f"{self.authority}; nao e CJSG.",
                "A fonte HTML e-SAJ pode alterar layout ou exigir sessao publica.",
                "A fonte entrega o texto da decisao oculto no proprio resultado; "
                "nao ha rota de detalhe promovida.",
                "O limite remoto observado e de 10 resultados por pagina.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjsp_cjpg_response(
            content,
            query=query,
            trace=trace,
            base_url=self.base_url,
            page_size=page_size,
            source=self.name,
            authority=self.authority,
        )
        for result in page.results:
            if result.full_text:
                entry = (result.full_text, trace)
                self._inline_documents[result.id] = entry
                self._inline_documents[result.id.removeprefix("tjsp-cjpg-")] = entry
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "text/plain",
                }
            ],
            source_trace=document.source_trace,
            raw=document.raw_metadata,
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        try:
            text, trace = self._inline_documents[document_id]
        except KeyError as exc:
            raise SourceUnavailableError(
                "TJSP CJPG inline document is available only after an observed search"
            ) from exc
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="decisao_1g",
            content=text.encode("utf-8"),
            content_type="text/plain",
            title="TJSP CJPG decisao inline",
            url=trace.source_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"inline": True, "collection": "CJPG"},
            parser=f"{self.name}.inline_document",
            parser_version="1",
            text_override=text,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name=f"{self.authority} CJPG Jurisprudencia (1o grau)",
            source_url=self.base_url,
            category="court_jurisprudence",
            semantic_discriminator="collection=first_degree;route=cjpg",
            search_modes=["full_text", "case_number", "date_range", "pagination"],
            document_types=["decisao_1g", "sentenca"],
            content_formats=["html", "text"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "origin_county",
                "judging_body",
                "availability_date",
                "updated_at",
                "summary",
                "full_text",
                "source_id",
                "cd_processo",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /cjpg/pesquisar.do",
                "GET /cjpg/trocarDePagina.do?pagina=<n>&conversationId=",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page_size=TJSP_CJPG_PAGE_SIZE,
            completeness_contract="reported_total_and_page_window",
            full_text_access="inline",
            supported_filters=["text", "exact_phrase", "number", "updated_from", "updated_to"],
            unsupported_filters=[
                "rapporteur",
                "published_from",
                "published_to",
                "source_origin",
                "types",
                "fetch_details",
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "case_class",
                "judging_body",
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
                "decision_type",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "rapporteur": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "source_origin": "unsupported",
                "types": "unsupported",
                "fetch_details": "unsupported",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
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
                "decision_type": "unsupported",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
            },
            ordering_modes=["source_default"],
            detail_modes=["inline_full_text"],
            limitations=[
                "A rota publica e HTML e depende do layout do e-SAJ.",
                "Data de disponibilizacao nao e tratada como data de julgamento.",
                "Nao ha bypass de captcha, WAF, login ou controle de acesso.",
            ],
            responsible_use=[
                "Usar page_size moderado e respeitar o rate_limit_interval.",
                "Manter CJPG separado de CJSG e de consulta processual.",
                "Tratar bloqueios e mudancas de schema como outcomes, nunca como zero resultados.",
            ],
        )

    def _request_html(self, method: str, path: str, **kwargs: Any) -> tuple[bytes, str]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        request = TransportRequest(
            source=self.name,
            operation="cjpg_request",
            method=method,
            url=url,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            headers=headers,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJSP CJPG request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJSP CJPG transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJSP CJPG transport returned no HTTP status")
        content = response.body
        response_url = str(response.final_url or url)
        content_type = response.content_type
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": response_url,
            "content_type": content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status_code < 400 else "error",
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJSP CJPG returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJSP CJPG requires access validation")
        if status_code in {400, 422}:
            raise QueryRejectedError(f"TJSP CJPG rejected query with HTTP {status_code}")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJSP CJPG returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJSP CJPG rejected request with HTTP {status_code}")
        if "html" not in str(content_type or "").lower() and b"<html" not in content[:4096].lower():
            raise ParserContractChangedError("TJSP CJPG response is not HTML")
        return content, response_url


def _validate_cjpg_scope(query: JurisprudenceQuery, *, authority: str, source_label: str) -> None:
    """Reject cross-authority or second-degree refinements on the CJPG route."""

    aliases = {"first", "primeiro", "primeiro_grau", "1", "1o", "1º"}
    degree = str(query.degree or "").strip().casefold()
    if degree and degree not in aliases:
        raise QueryRejectedError(f"{source_label} only supports degree=first")
    instance = str(query.instance or "").strip().casefold()
    if instance and instance not in aliases:
        raise QueryRejectedError(f"{source_label} only supports instance=first")
    branch = str(query.branch or "").strip().casefold()
    if branch and branch not in {"state", "estadual"}:
        raise QueryRejectedError(f"{source_label} only supports branch=state")
    requested_authority = str(query.authority or "").strip().casefold()
    if requested_authority and requested_authority != authority.casefold():
        raise QueryRejectedError(f"{source_label} cannot query authority={query.authority!r}")
    collection = str(query.collection or "").strip().casefold()
    if collection and collection not in {"cjpg", "first_degree", "jurisprudencia"}:
        raise QueryRejectedError(f"{source_label} only supports the CJPG collection")


def build_tjsp_cjpg_params(query: JurisprudenceQuery) -> dict[str, str]:
    """Build the public TJSP/e-SAJ CJPG query fields observed upstream."""

    number = _clean_process_number(query.number)
    return {
        "conversationId": "",
        "dadosConsulta.pesquisaLivre": query.text or query.exact_phrase or query.number,
        "tipoNumero": "UNIFICADO",
        "numeroDigitoAnoUnificado": number[:15],
        "foroNumeroUnificado": number[-4:],
        "dadosConsulta.nuProcesso": number,
        "classeTreeSelection.values": "",
        "assuntoTreeSelection.values": "",
        "dadosConsulta.dtInicio": query.updated_from,
        "dadosConsulta.dtFim": query.updated_to,
        "varasTreeSelection.values": "",
        "dadosConsulta.ordenacao": "DESC",
    }


def parse_tjsp_cjpg_response(
    content: bytes,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
    page_size: int | None = None,
    memory: Any = USE_DEFAULT_MEMORY,
    source: str = "tjsp_cjpg",
    authority: str = "TJSP",
) -> SearchPage:
    """Parse one public TJSP CJPG result page into canonical result envelopes."""

    html = content.decode("utf-8", errors="replace")
    lowered = html.lower()
    soup = BeautifulSoup(html, "html.parser")
    result_root = soup.select_one("#divDadosResultado")
    if result_root is None and _looks_like_access_control(lowered):
        raise AccessControlRequiredError("TJSP CJPG returned captcha/access-control HTML")
    if result_root is None:
        if _looks_like_empty(lowered):
            return _empty_page(query, trace, page_size, source=source)
        raise ParserContractChangedError(f"{authority} CJPG result container not found")
    page_text = soup.get_text(" ", strip=True)
    explicit_empty = _looks_like_empty(lowered)
    rows = (
        []
        if explicit_empty
        else resilient_find_all(
            result_root,
            "tr.fundocinza1",
            name="cjpg_result_row",
            source="tjsp_cjpg",
            trace=trace,
            memory=memory,
        )
    )
    total = _parse_total(page_text)
    if not rows:
        if _looks_like_access_control(lowered):
            raise AccessControlRequiredError(
                f"{authority} CJPG returned captcha/access-control HTML"
            )
        if total == 0 or explicit_empty:
            return _empty_page(query, trace, page_size, total=total, source=source)
        raise ParserContractChangedError(
            f"{authority} CJPG reported results but no result rows were found"
        )
    results = [
        _row_to_result(row, trace=trace, base_url=base_url, source=source, authority=authority)
        for row in rows
    ]
    total_known = total is not None
    if total is None:
        total = len(results)
    effective_size = _page_size(page_size or query.page_size)
    limited = results[:effective_size]
    start = ((query.page - 1) * TJSP_CJPG_PAGE_SIZE) + 1
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(limited),
        total_is_authoritative=True,
    )
    return SearchPage(
        source=source,
        total=total,
        start=start,
        end=start + len(limited) - 1,
        page=query.page,
        page_size=effective_size,
        results=limited,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
        filters_applied={
            "collection": "first_degree",
            "remote_page_size": str(TJSP_CJPG_PAGE_SIZE),
        },
        total_known=total_known,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if limited else ExtractionStatus.EMPTY,
    )


def _row_to_result(
    row: Any,
    *,
    trace: SourceTrace,
    base_url: str,
    source: str = "tjsp_cjpg",
    authority: str = "TJSP",
) -> JurisprudenceResult:
    table = row.find("table")
    if table is None:
        raise ParserContractChangedError("TJSP CJPG result row has no data table")
    primary = table.find("a", attrs={"style": re.compile("vertical-align")})
    if primary is None:
        primary = table.find("a", attrs={"title": re.compile("Inteiro Teor", re.I)})
    if primary is None:
        raise ParserContractChangedError("TJSP CJPG result row has no stable decision anchor")
    source_id = str(primary.get("name") or "").split("-", 1)[0].strip()
    number_node = primary.find("span", class_="fonteNegrito") or primary
    case_number = _clean_text(number_node.get_text(" ", strip=True))
    if not source_id or not case_number:
        raise ParserContractChangedError("TJSP CJPG result row has no stable id or case number")
    labels: dict[str, str] = {}
    for line in table.find_all("tr", class_="fonte"):
        text = _clean_text(line.get_text(" ", strip=True))
        if ":" not in text:
            continue
        label, value = text.split(":", 1)
        labels[_label_key(label)] = _clean_text(value)
    hidden = table.select_one('div[style*="display: none"]')
    full_text = _clean_text(hidden.get_text(" ", strip=True)) if hidden else ""
    if not full_text:
        raise ParserContractChangedError("TJSP CJPG result row has no inline decision text")
    availability = labels.get("data_de_disponibilizacao")
    summary = _summary_from_text(full_text)
    # There is no independently observed detail endpoint for CJPG.  Keep the
    # actual search URL rather than inventing a deep link to the hidden row.
    document_url = trace.source_url or urljoin(base_url + "/", "cjpg/pesquisar.do")
    raw = {
        "source_id": source_id,
        "cd_processo": source_id,
        "id_processo": case_number,
        "classe": labels.get("classe"),
        "assunto": labels.get("assunto"),
        "magistrado": labels.get("magistrado"),
        "comarca": labels.get("comarca"),
        "foro": labels.get("foro"),
        "vara": labels.get("vara"),
        "data_disponibilizacao": availability,
        "decisao": full_text,
        "full_text": full_text,
        "full_text_url": document_url,
        "labels": labels,
    }
    result_id = (
        f"tjsp-cjpg-{source_id}" if source == "tjsp_cjpg" else f"{source}-record-{source_id}"
    )
    return JurisprudenceResult(
        id=result_id,
        source=source,
        court=authority,
        type="decisao_1g",
        number=case_number,
        summary=summary,
        full_text=full_text,
        rapporteur=labels.get("magistrado") or None,
        updated_at=normalize_date(availability),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw=raw,
        case_class=labels.get("classe") or None,
        judging_body=labels.get("orgao_julgador") or None,
        degree="first",
        instance="first",
        branch="state",
        authority=authority,
        collection="CJPG",
        document_type="decisao_1g",
        source_origin=authority,
        document_url=document_url,
    )


def _empty_page(
    query: JurisprudenceQuery,
    trace: SourceTrace,
    page_size: int | None,
    *,
    total: int | None = None,
    source: str = "tjsp_cjpg",
) -> SearchPage:
    return SearchPage(
        source=source,
        total=total if total is not None else 0,
        start=0,
        end=0,
        page=query.page,
        page_size=_page_size(page_size or query.page_size),
        results=[],
        source_trace=trace,
        pagination_mode="page",
        is_complete=True,
        completeness_reason="A fonte informou explicitamente que nao ha resultados.",
        total_known=total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.EMPTY,
    )


def _parse_total(text: str) -> int | None:
    match = _TOTAL_RE.search(_clean_text(text))
    if not match:
        return None
    try:
        return int(match.group(1).replace(".", ""))
    except ValueError:
        return None


def _looks_like_empty(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "nenhum resultado",
            "não foram encontrados",
            "nao foram encontrados",
            "sem resultados",
        )
    )


def _looks_like_access_control(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "recaptcha",
            "g-recaptcha",
            "uuidcaptcha",
            "captchacontroleacesso",
            "sajcas/verificarlogin",
            "emptysession.jsp",
        )
    )


def _label_key(value: str) -> str:
    normalized = _clean_text(value).lower().replace("-", "_")
    normalized = re.sub(r"[^a-z0-9áéíóúãõç_ ]", "", normalized)
    normalized = re.sub(r"\s+", "_", normalized)
    return {
        "data_de_disponibilização": "data_de_disponibilizacao",
        "órgão_julgador": "orgao_julgador",
    }.get(normalized, normalized)


def _clean_process_number(value: str) -> str:
    return re.sub(r"[^0-9]", "", value) if value and _PROCESS_NUMBER_RE.search(value) else value


def _summary_from_text(value: str, *, limit: int = 1000) -> str:
    return value[:limit].rstrip() + ("..." if len(value) > limit else "")


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), TJSP_CJPG_PAGE_SIZE))
