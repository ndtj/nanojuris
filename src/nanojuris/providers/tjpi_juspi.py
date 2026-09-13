"""TJPI/JusPI public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

from nanojuris.adaptive_selectors import resilient_find_all
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
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)

CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


def _looks_like_case_number(value: str) -> bool:
    return bool(CNJ_PATTERN.fullmatch(value.strip()))


class TjpiJuspiProvider(JurisprudenceProvider):
    """Provider for the public TJPI/JusPI jurisprudence search."""

    name = "tjpi_juspi"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjpi_juspi_url).hostname or ""
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
        self._last_response_content = b""
        self._last_response_content_type: str | None = None
        self._last_http_metadata: dict[str, Any] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_degree_scope(query)
        endpoint = "/jurisprudences/search"
        params = self._build_params(query)
        html = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=urljoin(self.config.tjpi_juspi_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=[
                "Fonte HTML publica do TJPI/JusPI sujeita a mudancas de layout.",
                "Busca validada por GET em sessao HTTP limpa.",
                "Inteiro teor e retornado apenas quando a rota "
                "/jurisprudences/<id>/public estiver publica.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjpi_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjpi_juspi_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        public_id = _normalize_public_id(precedent_id)
        endpoint = f"/jurisprudences/{public_id}/public"
        html = self._request_text("GET", endpoint)
        document_text, metadata = extract_tjpi_document_text(html)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/jurisprudences/<id>/public",
            query={"id": public_id},
            source_url=urljoin(self.config.tjpi_juspi_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=[
                "A rota publica retorna HTML; o provider limpa navegacao e scripts sem baixar PDF.",
            ],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=metadata.get("rapporteur"),
            texts=[
                {
                    "content": document_text,
                    "content_type": "text/plain",
                    "source_content_type": "text/html",
                }
            ],
            source_trace=trace,
            raw={
                "public_id": public_id,
                "raw_content_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
                "raw_content_bytes": len(html.encode("utf-8")),
                **metadata,
            },
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        content = str(bundle.texts[0].get("content") if bundle.texts else "")
        raw_content = self._last_response_content or content.encode("utf-8")
        metadata = dict(bundle.raw or {})
        access_status = AccessStatus(
            str(metadata.get("access_status") or AccessStatus.PUBLIC.value)
        )
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type=str(metadata.get("decision_type") or "decisao"),
            content=raw_content,
            content_type=self._last_response_content_type or "text/html",
            title=str(metadata.get("title") or f"TJPI/JusPI jurisprudencia {document_id}"),
            text_override=content,
            url=bundle.source_trace.source_url if bundle.source_trace else None,
            access_status=access_status,
            source_trace=bundle.source_trace,
            raw_metadata=metadata,
            parser="tjpi_juspi.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJPI JusPI Jurisprudencias",
            source_url=self.config.tjpi_juspi_url,
            category="court_jurisprudence",
            search_modes=[
                "full_text",
                "summary",
                "case_number",
                "date_range",
                "decision_type",
                "rapporteur",
                "case_class",
                "judging_body",
            ],
            document_types=["acordao", "decisao_terminativa"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "public_id",
                "case_number",
                "decision_type",
                "subject",
                "case_class",
                "rapporteur",
                "judging_body",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /jurisprudences/search?q=<termo>",
                "GET /jurisprudences/search?page=<n>&q=<termo>",
                "GET /jurisprudences/<id>/public",
            ],
            supports_full_text=True,
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "types",
                "rapporteur",
                "source_origin",
                "updated_from",
                "updated_to",
                "degree",
                "instance",
                "decision_type",
            ],
            unsupported_filters=[
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "source_origins",
                "fetch_details",
                "published_from",
                "published_to",
                "case_class",
                "judging_body",
                "branch",
                "legal_area",
                "authority",
                "collection",
                "document_type",
                "judgment_date_from",
                "judgment_date_to",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "native",
                "types": "native",
                "rapporteur": "native",
                "source_origin": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "degree": "translated",
                "instance": "translated",
                "decision_type": "translated",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "party_name": "unsupported",
                "party_document": "unsupported",
                "lawyer_name": "unsupported",
                "oab": "unsupported",
                "precatory_number": "unsupported",
                "police_document": "unsupported",
                "cda": "unsupported",
                "source_origins": "unsupported",
                "fetch_details": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "branch": "unsupported",
                "legal_area": "unsupported",
                "authority": "unsupported",
                "collection": "unsupported",
                "document_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
            },
            limitations=[
                "Contrato HTML server-side sem API JSON publica observada.",
                "Paginacao por parametro page foi observada em links publicos da propria fonte.",
                "Filtros de classe, relator e orgao dependem dos valores textuais "
                "publicados no formulario.",
            ],
            responsible_use=[
                "Usar coletas paginadas com rate limit.",
                "Nao tentar automatizar login administrativo ou qualquer controle de acesso.",
                "Preservar public_id e SourceTrace para auditoria.",
            ],
        )

    def _build_params(self, query: JurisprudenceQuery) -> dict[str, str | int]:
        text = query.text or query.exact_phrase or query.number
        params: dict[str, str | int] = {"q": text}
        if query.page > 1:
            params["page"] = query.page
        # The CJSG binding is intentionally restricted to acórdãos.  Without
        # this explicit filter the public portal also returns súmulas, which
        # are not a degree-specific decision surface.
        params["tipo"] = _map_decision_type(query.types[0]) if query.types else "Acórdão"
        if params["tipo"] != "Acórdão":
            raise QueryRejectedError("TJPI CJSG accepts only the public acórdão collection")
        if query.rapporteur or query.lawyer_name:
            params["relator"] = query.rapporteur or query.lawyer_name
        if query.source_origin:
            params["orgao"] = query.source_origin
        if query.updated_from:
            params["data_min"] = query.updated_from
        if query.updated_to:
            params["data_max"] = query.updated_to
        return params

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        url = urljoin(self.config.tjpi_juspi_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        params = kwargs.pop("params", {})
        request = TransportRequest(
            source=self.name,
            operation="juspi_request",
            method=method,
            url=url,
            headers=headers,
            params=params,
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPI/JusPI request failed: {exc}") from exc
        # JusPI currently responds with HTTP 500 for a CNJ number combined
        # with the accented ``tipo`` value, although the same public route
        # accepts either parameter independently. Retry once with the type
        # omitted only for a syntactically valid process number. This is a
        # bounded compatibility fallback, not a bypass of access controls.
        params = kwargs.get("params")
        if (
            response.status_code is not None
            and response.status_code >= 500
            and isinstance(params, dict)
            and "tipo" in params
            and _looks_like_case_number(str(params.get("q", "")))
        ):
            for fallback_type in ("Acordao", None):
                fallback = dict(params)
                if fallback_type is None:
                    fallback.pop("tipo", None)
                else:
                    fallback["tipo"] = fallback_type
                fallback_request = TransportRequest(
                    source=self.name,
                    operation="juspi_request_fallback",
                    method=method,
                    url=url,
                    headers=headers,
                    params=fallback,
                    idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
                )
                response = self.transport.request(fallback_request)
                if response.status_code is not None and response.status_code < 500:
                    break
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJPI/JusPI transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJPI/JusPI transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("TJPI/JusPI returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJPI/JusPI requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJPI/JusPI returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJPI/JusPI rejected request with HTTP {status_code}")
        self._last_response_content = bytes(response.body)
        self._last_response_content_type = response.content_type
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or url),
            "content_type": self._last_response_content_type,
            "content_sha256": hashlib.sha256(self._last_response_content).hexdigest(),
            "response_bytes": len(self._last_response_content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status_code < 400 else "error",
        }
        text = response.text
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("TJPI/JusPI returned captcha or access-control HTML")
        return text


def parse_tjpi_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse TJPI/JusPI search HTML into normalized results."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError("TJPI/JusPI returned captcha or access-control HTML")
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    total, start, end = _parse_total(soup)
    # Never let adaptive selector memory relocate stale result cards into an
    # explicitly empty response.  The empty marker is stronger evidence than
    # a previous page's structural fingerprint.
    cards = (
        []
        if _is_explicit_empty(page_text)
        else resilient_find_all(
            soup, "div.callout", name="result_card", source="tjpi_juspi", trace=trace
        )
    )
    if not cards:
        complete: bool | None
        if _is_explicit_empty(page_text):
            complete = True
            completeness_reason = "A fonte declarou explicitamente que nao ha resultados."
        else:
            complete, completeness_reason = page_completeness(
                reported_total=total,
                start=start,
                returned=0,
                total_is_authoritative=total is not None,
            )
        return SearchPage(
            source="tjpi_juspi",
            total=total if total is not None else 0,
            start=0,
            end=0,
            page=query.page,
            page_size=query.page_size,
            results=[],
            source_trace=trace,
            pagination_mode="page",
            is_complete=complete,
            completeness_reason=completeness_reason,
            total_known=total is not None,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.EMPTY,
        )

    results: list[JurisprudenceResult] = []
    for card in cards:
        result = _parse_result_card(card, trace=trace, base_url=base_url)
        if result is not None:
            results.append(result)

    if not results and total is not None and total > 0:
        raise ParserContractChangedError("TJPI/JusPI parser found total results but no cards")

    limited_results = results[: query.page_size]
    complete, completeness_reason = page_completeness(
        reported_total=total,
        start=start or (1 if limited_results else 0),
        returned=len(limited_results),
        total_is_authoritative=total is not None,
    )
    # The portal reports the absolute result range for the server-side page
    # (for example ``26 - 50`` on page two), while the provider intentionally
    # limits the materialized window to ``query.page_size``.  Returning the
    # portal's end value after truncation produced impossible ranges such as
    # ``26 - 3`` and made federated completeness/deduplication unreliable.
    # Keep the one-based start and make ``end`` describe the records actually
    # returned by this SearchPage.
    returned_start = start or (1 if limited_results else 0)
    returned_end = returned_start + len(limited_results) - 1 if limited_results else 0
    return SearchPage(
        source="tjpi_juspi",
        total=total if total is not None else len(results),
        start=returned_start,
        end=returned_end,
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=completeness_reason,
        # The counter is authoritative even when it is zero.  A missing
        # counter remains unknown and is never silently treated as empty.
        total_known=total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if limited_results else ExtractionStatus.EMPTY,
    )


def extract_tjpi_document_text(html: str) -> tuple[str, dict[str, Any]]:
    """Extract readable text and metadata from a public TJPI/JusPI detail page."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError("TJPI/JusPI detail returned captcha/access-control HTML")
    soup = BeautifulSoup(html, "html.parser")
    for element in soup.select("script, style, noscript, nav, footer"):
        element.decompose()
    content = soup.select_one(".card-body") or soup.select_one(".content") or soup.body
    if content is None:
        raise ParserContractChangedError("TJPI/JusPI detail content container not found")
    text = _normalize_text(content.get_text("\n", strip=True))
    if not text:
        raise ParserContractChangedError("TJPI/JusPI detail returned empty public text")
    metadata = _extract_metadata_from_text(text)
    title_parts = [
        metadata.get("decision_type"),
        metadata.get("subject"),
        metadata.get("case_number"),
    ]
    metadata["title"] = " - ".join(str(item) for item in title_parts if item)
    metadata["access_status"] = AccessStatus.PUBLIC.value
    metadata["text_characters"] = len(text)
    return text, metadata


def _parse_result_card(
    card: Any,
    *,
    trace: SourceTrace,
    base_url: str,
) -> JurisprudenceResult | None:
    link = card.select_one('a[href*="/jurisprudences/"][href$="/public"]')
    if link is None:
        return None
    href = str(link.get("href") or "")
    public_id = _extract_public_id(href)
    if not public_id:
        return None
    header = _normalize_text(link.get_text("\n", strip=True))
    subject, case_number = _parse_subject_and_number(header)
    decision_type = _normalize_text((card.select_one(".badge") or link).get_text(" ", strip=True))
    publication_date = _extract_publication_date(card.get_text("\n", strip=True))
    summary_element = card.select_one(".text-justify")
    summary = (
        _normalize_text(summary_element.get_text(" ", strip=True))
        if summary_element is not None
        else None
    )
    hidden_text_element = card.select_one(".mt-3") or card.select_one(".d-none")
    hidden_text = (
        _normalize_text(hidden_text_element.get_text(" ", strip=True))
        if hidden_text_element is not None
        else ""
    )
    metadata = _extract_metadata_from_text(hidden_text)
    document_url = urljoin(base_url.rstrip("/") + "/", href.lstrip("/"))
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint="/jurisprudences/search",
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
    normalized_type = _normalize_decision_type(decision_type)
    if normalized_type not in {"acordao", "decisao_terminativa"}:
        raise ParserContractChangedError(
            f"TJPI CJSG returned unsupported document type: {normalized_type}"
        )
    return JurisprudenceResult(
        id=f"tjpi-juspi-{public_id}",
        source="tjpi_juspi",
        court="TJPI",
        type=normalized_type,
        number=case_number or metadata.get("case_number"),
        summary=summary,
        rapporteur=metadata.get("rapporteur"),
        publication_date=publication_date,
        updated_at=publication_date,
        degree="second",
        instance="second",
        branch="state",
        authority="TJPI",
        collection="CJSG",
        document_type=normalized_type,
        source_origin="JusPI",
        document_url=document_url,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        highlights={},
        source_trace=result_trace,
        raw={
            "public_id": public_id,
            "subject": subject or metadata.get("subject"),
            "assunto": subject or metadata.get("subject"),
            "case_class": metadata.get("case_class"),
            "classe": metadata.get("case_class"),
            "judging_body": metadata.get("judging_body"),
            "orgao_julgador": metadata.get("judging_body"),
            "publication_date": publication_date,
            "data_publicacao": publication_date,
            "document_url": document_url,
            "full_text_url": document_url,
            "source_decision_type": decision_type,
            "degree": "second",
            "instance": "second",
            "branch": "state",
            "authority": "TJPI",
            "collection": "CJSG",
            "document_type": normalized_type,
        },
        field_provenance={
            "degree": {"source": "source_contract:tjpi_juspi_acordao"},
            "instance": {"source": "source_contract:tjpi_juspi_acordao"},
            "branch": {"source": "source_contract:tjpi"},
            "authority": {"source": "source_contract:tjpi"},
            "collection": {"source": "source_contract:tjpi_juspi_acordao"},
        },
    )


def _validate_degree_scope(query: JurisprudenceQuery) -> None:
    """Reject non-CJSG document scopes before contacting the public portal."""

    values = {value.strip().casefold() for value in query.types}
    if values & {"sumula", "súmula", "first", "primeiro", "sentenca", "sentença"}:
        raise QueryRejectedError("TJPI CJSG exposes only second-degree acórdãos")


def _parse_total(soup: BeautifulSoup) -> tuple[int | None, int, int]:
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Exibindo\s+(\d+)\s*-\s*(\d+)\s+de\s+um\s+total\s+de\s+(\d+)", text, re.I)
    if not match:
        return None, 0, 0
    start, end, total = (int(match.group(index)) for index in (1, 2, 3))
    return total, start, end


def _is_explicit_empty(text: str) -> bool:
    """Recognize the portal's empty-result message without relying on a count."""

    normalized = re.sub(r"\s+", " ", text).casefold()
    return any(
        marker in normalized
        for marker in (
            "sem resultados para",
            "nenhum resultado",
            "nenhum registro encontrado",
        )
    )


def _parse_subject_and_number(text: str) -> tuple[str | None, str | None]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    joined = " ".join(lines)
    number_match = CNJ_PATTERN.search(joined)
    case_number = number_match.group(0) if number_match else None
    subject = lines[0] if lines else None
    if subject and case_number and case_number in subject:
        subject = subject.replace(case_number, "").strip()
    return subject, case_number


def _extract_metadata_from_text(text: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    case_number = _first_match(CNJ_PATTERN, text)
    if case_number:
        metadata["case_number"] = case_number
    case_class = _first_match(re.compile(r"CLASSE:\s*([^\[]+?)(?:\s+ASSUNTO\(S\):|$)", re.I), text)
    if case_class:
        metadata["case_class"] = case_class.strip()
    subject = _first_match(re.compile(r"ASSUNTO\(S\):\s*\[([^\]]+)\]", re.I), text)
    if subject:
        metadata["subject"] = subject.strip()
    rapporteur = _first_match(
        re.compile(r"GABINETE(?:\s+DO)?\s+(Desembargador(?:a)?\s+[^\n]+?)(?:\s+PROCESSO|$)", re.I),
        text,
    )
    if rapporteur:
        metadata["rapporteur"] = rapporteur.strip()
    body = _first_match(
        re.compile(r"GABINETE(?:\s+DO)?\s+([^\n]+?)(?:\s+PROCESSO|$)", re.I),
        text,
    )
    if body:
        metadata["judging_body"] = body.strip()
    decision_type = _first_match(
        re.compile(
            r"(Ac[oó]rd[aã]o|Decis[aã]o Terminativa|S[uú]mula)(?:\s+de\s+2[ºo]\s+Grau)?", re.I
        ),
        text,
    )
    if decision_type:
        metadata["decision_type"] = _normalize_decision_type(decision_type)
    return metadata


def _extract_public_id(href: str) -> str:
    match = re.search(r"/jurisprudences/(\d+)/public", href)
    return match.group(1) if match else ""


def _normalize_public_id(document_id: str) -> str:
    match = re.fullmatch(r"(?:tjpi-juspi-)?(?P<id>\d+)", document_id)
    if not match:
        raise ParserContractChangedError(
            "TJPI/JusPI document id must look like tjpi-juspi-<public_id>"
        )
    return match.group("id")


def _extract_publication_date(text: str) -> str | None:
    return _first_match(re.compile(r"Publica[çc][aã]o:\s*(\d{2}/\d{2}/\d{4})", re.I), text)


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1 if pattern.groups else 0).strip() if match else None


def _normalize_decision_type(value: str) -> str:
    normalized = _normalize_text(value).lower()
    if "ac" in normalized and "rd" in normalized:
        return "acordao"
    if "sum" in normalized:
        return "sumula"
    if "terminativa" in normalized:
        return "decisao_terminativa"
    if "decis" in normalized:
        return "decisao"
    return normalized or "decisao"


def _map_decision_type(value: str) -> str:
    normalized = _normalize_text(value).lower()
    mapping = {
        "acordao": "Acórdão",
        "acórdão": "Acórdão",
        "decisao": "Decisão Terminativa",
        "decisão": "Decisão Terminativa",
        "decisao terminativa": "Decisão Terminativa",
        "decisão terminativa": "Decisão Terminativa",
        "sumula": "Súmula",
        "súmula": "Súmula",
    }
    return mapping.get(normalized, value)


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    return "g-recaptcha" in lowered or "captcha" in lowered or "recaptcha" in lowered


def _normalize_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)
