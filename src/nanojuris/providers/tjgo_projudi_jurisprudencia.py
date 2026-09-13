"""TJGO/Projudi public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests

from nanojuris.adaptive_selectors import resilient_select
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
from nanojuris.parsing import HtmlDocument, HtmlNode, parse_html
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
FILE_ID_PATTERN = re.compile(r"abrirArquivo\(\s*'[^']+'\s*,\s*'(?P<id>\d+)'\s*\)")


class TjgoProjudiJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for public TJGO/Projudi jurisprudence search results."""

    name = "tjgo_projudi_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjgo_projudi_url).hostname or ""
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
        # Result cards carry public text inline. Keep only the bounded pages
        # observed in this provider instance so detail requests never guess
        # undocumented routes.
        self._results: dict[str, JurisprudenceResult] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_fixed_scope(query)
        # The federated/default route is the appellate binding. Callers that
        # explicitly request first degree keep the historical provider
        # behaviour, while an unqualified search is pinned to PROJUDI's
        # ``Id_Instancia=15`` (tribunal/second degree).
        scoped_query = query
        if (
            not query.source_origin
            and not query.degree
            and not query.instance
            and not query.collection
        ):
            scoped_query = replace(query, source_origin="segundo grau")
        endpoint = "/ConsultaJurisprudencia"
        payload = _build_payload(scoped_query)
        html = self._request_text("POST", endpoint, data=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=payload,
            source_url=urljoin(
                self.config.tjgo_projudi_url.rstrip("/") + "/", endpoint.lstrip("/")
            ),
            **self._last_http_metadata,
            limitations=[
                "Fonte HTML publica do PROJUDI/TJGO sujeita a mudancas de layout.",
                "O provider preserva o texto publico retornado pela fonte, "
                "sem redaction automatica.",
                "Download separado por Id_Arquivo permanece pendente ate contrato publico limpo.",
            ],
        )
        page = parse_tjgo_results(
            html,
            query=scoped_query,
            trace=trace,
            base_url=self.config.tjgo_projudi_url,
        )
        self._results.update({result.id: result for result in page.results})
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise ValueError("TJGO precedent_id must be an id observed in the current search page")
        document = tjgo_result_to_document(result)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=result.rapporteur,
            texts=[{"type": result.document_type or result.type, "text": document.text or ""}],
            source_trace=result.source_trace,
            raw={"document": document.raw_metadata},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch the public Projudi document identified by ``Id_Arquivo``.

        The result card exposes this numeric identifier through the official
        ``abrirArquivo`` form.  The browser submits that form back to the same
        HTTPS endpoint; an empty captcha token is intentionally preserved and
        access-control responses remain explicit errors in ``_request_text``.
        """

        cached = self._results.get(document_id)
        if cached is not None and (cached.full_text or cached.summary):
            return tjgo_result_to_document(cached)
        if not re.fullmatch(r"\d+", document_id.strip()):
            raise ValueError("TJGO document_id must be the numeric Id_Arquivo")
        file_id = document_id.strip()
        html = self._request_text(
            "POST",
            "/ConsultaJurisprudencia",
            params={
                "PaginaAtual": "1",
                "Id_Arquivo": file_id,
                "g-recaptcha-response": "",
            },
            data={},
        )
        content = html.encode("utf-8")
        document = parse_html(html, base_url=self.config.tjgo_projudi_url)
        text_node = document.select_one(".conteudoTexto")
        text = _normalize_text(text_node.get_text(" ", strip=True)) if text_node else ""
        if not text:
            raise ParserContractChangedError(
                "TJGO/Projudi documento nao contem o bloco publico .conteudoTexto"
            )
        source_url = urljoin(
            self.config.tjgo_projudi_url.rstrip("/") + "/",
            f"ConsultaJurisprudencia?PaginaAtual=1&Id_Arquivo={file_id}",
        )
        trace = SourceTrace(
            provider=self.name,
            endpoint="/ConsultaJurisprudencia?Id_Arquivo",
            query={"Id_Arquivo": file_id},
            source_url=source_url,
            **self._last_http_metadata,
        )
        digest = hashlib.sha256(content).hexdigest()
        return CanonicalDocument(
            id=f"tjgo-projudi-file-{file_id}",
            source=self.name,
            document_type="inteiro_teor",
            content_type="text/html",
            title=f"TJGO/Projudi documento {file_id}",
            text=text,
            raw_bytes=content,
            url=source_url,
            sha256=digest,
            byte_size=len(content),
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
            source_trace=trace,
            extraction_trace=ExtractionTrace(
                parser=f"{self.name}.document",
                parser_version="1",
                status=ExtractionStatus.COMPLETE,
                access_status=AccessStatus.PUBLIC,
                content_sha256=digest,
                content_bytes=len(content),
                transformations=["html_visible_text"],
                metadata={"file_id": file_id},
            ),
            raw_metadata={"file_id": file_id, "inline": False},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJGO PROJUDI Jurisprudencia",
            source_url=self.config.tjgo_projudi_url,
            category="court_jurisprudence",
            search_modes=[
                "full_text",
                "case_number",
                "date_range",
                "decision_type",
                "judge",
                "unit",
            ],
            document_types=["decisao", "sentenca", "acordao"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "id",
                "case_number",
                "decision_type",
                "rapporteur",
                "judging_body",
                "publication_date",
                "updated_at",
                "summary",
                "full_text",
                "file_id",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /ConsultaJurisprudencia",
                "POST /ConsultaJurisprudencia",
                "POST /ConsultaJurisprudencia?PaginaAtual=1&Id_Arquivo=<id>",
            ],
            # The public result card embeds the decision text in
            # ``.conteudoTexto``.  This is inline full text (not a promoted
            # download/detail route), so callers can rely on it while the
            # separate file endpoint remains unverified.
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            full_text_access="inline_result_text",
            # Keep the capability map aligned with the payload builder.  The
            # Projudi form uses one free-text field (``Texto``), one process
            # number field, an act-type select and a date interval.  Degree
            # and instance are translated to the official ``Id_Instancia``
            # values (15 = appellate, 16 = first degree, 151 = recursal).
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "types",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "degree",
                "instance",
                "source_origin",
                "decision_type",
                "collection",
                "document_type",
                "branch",
                "authority",
            ],
            unsupported_filters=[
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "rapporteur",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "source_origins",
                "fetch_details",
                "case_class",
                "judging_body",
                "legal_area",
                "judgment_date_from",
                "judgment_date_to",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "native",
                "types": "native",
                "updated_from": "translated",
                "updated_to": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "degree": "translated",
                "instance": "translated",
                "source_origin": "translated",
                "decision_type": "translated",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "rapporteur": "unsupported",
                "party_name": "unsupported",
                "party_document": "unsupported",
                "lawyer_name": "unsupported",
                "oab": "unsupported",
                "precatory_number": "unsupported",
                "police_document": "unsupported",
                "cda": "unsupported",
                "source_origins": "unsupported",
                "fetch_details": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "branch": "validated_scope",
                "legal_area": "unsupported",
                "authority": "validated_scope",
                "collection": "translated",
                "document_type": "translated",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
            },
            limitations=[
                "O inteiro teor pode ser extraido do HTML de resultado quando a fonte "
                "o embute no card; "
                "isso nao equivale a get_document por id.",
                "A rota de download por Id_Arquivo voltou ao formulario em probe "
                "sem token e nao e usada.",
                "O HTML contem mencoes globais a captcha em assets, mas resultados "
                "juridicos validos prevalecem.",
            ],
            responsible_use=[
                "Usar coletas paginadas com rate limit.",
                "Nao tentar resolver captcha, token ou area autenticada.",
                "Preservar SourceTrace e raw metadata para auditoria profissional.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        url = urljoin(self.config.tjgo_projudi_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        request = TransportRequest(
            source=self.name,
            operation="projudi_request",
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
            raise SourceUnavailableError(f"TJGO/Projudi request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJGO/Projudi transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJGO/Projudi transport returned no HTTP status")
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
            raise RateLimitDetectedError("TJGO/Projudi returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(
                f"TJGO/Projudi requires access validation (HTTP {status_code})"
            )
        if status_code >= 500:
            raise SourceUnavailableError(f"TJGO/Projudi returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJGO/Projudi rejected request with HTTP {status_code}")
        text = _decode_response_text(content, content_type)
        if _looks_like_blocked_page(text):
            raise AccessControlRequiredError("TJGO/Projudi returned access-control HTML")
        return text


def parse_tjgo_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse TJGO/Projudi result HTML into normalized records."""

    if _looks_like_blocked_page(html):
        raise AccessControlRequiredError("TJGO/Projudi returned access-control HTML")
    document = parse_html(html, base_url=base_url)
    cards = resilient_select(
        document,
        "div.search-result",
        name="result_card",
        source="tjgo_projudi_jurisprudencia",
        trace=trace,
    )
    total = _parse_total(document)
    if not cards:
        complete, completeness_reason = page_completeness(
            reported_total=total,
            start=0,
            returned=0,
            total_is_authoritative=total is not None,
        )
        return SearchPage(
            source="tjgo_projudi_jurisprudencia",
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
            if _is_second_degree_scope(query):
                if not _promote_second_degree_result(result):
                    continue
            elif _is_first_degree_scope(query):
                if not _promote_first_degree_result(result):
                    continue
            results.append(result)

    if not results and total is not None and total > 0:
        raise ParserContractChangedError("TJGO/Projudi parser found total results but no cards")

    limited_results = results[: query.page_size]
    start = ((max(query.page, 1) - 1) * query.page_size) + 1 if limited_results else 0
    complete, completeness_reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(limited_results),
        total_is_authoritative=total is not None,
    )
    return SearchPage(
        source="tjgo_projudi_jurisprudencia",
        total=total if total is not None else len(results),
        start=start,
        end=start + len(limited_results) - 1 if limited_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=completeness_reason,
        total_known=total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if limited_results else ExtractionStatus.EMPTY,
    )


def tjgo_result_to_document(result: JurisprudenceResult) -> CanonicalDocument:
    """Build a canonical document from a TJGO result with embedded full text."""

    raw = dict(result.raw or {})
    text = str(raw.get("full_text") or result.summary or "")
    content_bytes = text.encode("utf-8")
    status = ExtractionStatus.COMPLETE if text.strip() else ExtractionStatus.EMPTY
    return CanonicalDocument(
        id=result.id,
        source=result.source,
        document_type=result.type,
        content_type="text/plain",
        title=f"TJGO/Projudi {result.type} {result.number}",
        text=text,
        url=raw.get("document_url"),
        sha256=hashlib.sha256(content_bytes).hexdigest(),
        byte_size=len(content_bytes),
        retrieved_at=result.source_trace.retrieved_at if result.source_trace else None,
        access_status=AccessStatus.PUBLIC,
        source_trace=result.source_trace,
        extraction_trace=ExtractionTrace(
            parser="tjgo_projudi_jurisprudencia.result_to_document",
            parser_version="1",
            status=status,
            access_status=AccessStatus.PUBLIC,
            content_sha256=hashlib.sha256(content_bytes).hexdigest(),
            content_bytes=len(content_bytes),
            metadata=raw,
        ),
        raw_metadata=raw,
    )


def _parse_result_card(
    card: HtmlNode, *, trace: SourceTrace, base_url: str
) -> JurisprudenceResult | None:
    card_text = _normalize_text(card.get_text("\n", strip=True))
    case_number = _first_match(CNJ_PATTERN, card_text)
    if not case_number:
        return None
    # The embedded full text contains many incidental words such as
    # "sentença".  Restrict act-type detection to metadata paragraphs so a
    # first occurrence in the decision body cannot misclassify the card.
    paragraphs = [
        _normalize_text(p.get_text(" ", strip=True)) for p in card.select("p:not(.conteudoTexto)")
    ]
    paragraphs = [text for text in paragraphs if text]
    judging_body = paragraphs[0] if len(paragraphs) > 0 else None
    rapporteur = paragraphs[1] if len(paragraphs) > 1 else None
    decision_type = _find_decision_type(paragraphs)
    publication_date = _extract_publication_date(card_text)
    full_text_element = card.select_one(".conteudoTexto")
    full_text = (
        _normalize_text(full_text_element.get_text(" ", strip=True))
        if full_text_element is not None
        else ""
    )
    file_id = _extract_file_id(card)
    document_url = (
        f"{base_url.rstrip('/')}/ConsultaJurisprudencia?Id_Arquivo={file_id}"
        if file_id
        else base_url.rstrip() + "/ConsultaJurisprudencia"
    )
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=document_url,
        limitations=trace.limitations,
    )
    return JurisprudenceResult(
        id=f"tjgo-projudi-{case_number}",
        source="tjgo_projudi_jurisprudencia",
        court="TJGO",
        type=decision_type,
        number=case_number,
        summary=full_text,
        full_text=full_text or None,
        rapporteur=rapporteur,
        judging_body=judging_body,
        publication_date=publication_date,
        updated_at=publication_date,
        highlights={},
        source_trace=result_trace,
        branch="state",
        authority="TJGO",
        collection="JURISPRUDENCIA",
        document_type=decision_type,
        document_url=document_url,
        raw={
            "case_number": case_number,
            "judging_body": judging_body,
            "orgao_julgador": judging_body,
            "rapporteur": rapporteur,
            "magistrate": rapporteur,
            "decision_type": decision_type,
            "publication_date": publication_date,
            "data_publicacao": publication_date,
            "full_text": full_text,
            "document_url": document_url,
            "full_text_url": document_url,
            "file_id": file_id,
            "authority": "TJGO",
            "branch": "state",
            "collection": "JURISPRUDENCIA",
            "document_type": decision_type,
        },
    )


def _build_payload(query: JurisprudenceQuery) -> dict[str, str]:
    text = query.text or query.exact_phrase or query.number
    # PROJUDI keeps the jurisprudence screen in ``PaginaAtual=2``.  The
    # actual result page is carried by ``PosicaoPaginaAtual`` (the browser
    # pagination links call ``submitForm(n)`` with zero-based ``n``).  Using
    # ``PaginaAtual=query.page + 1`` appears to work for the first request but
    # silently returns the empty search form for page 2 and beyond.
    return {
        "PaginaAtual": "2",
        "PosicaoPaginaAtual": str(max(query.page - 1, 0)),
        "Viewstate": "",
        "Texto": text,
        "Id_Instancia": _map_instance(query),
        "Id_Area": "0",
        "Id_ServentiaSubTipo": "0",
        "Id_Serventia": "",
        "Id_Usuario": "",
        "Id_ArquivoTipo": _map_decision_type(
            query.types[0] if query.types else (query.document_type or query.decision_type)
        )
        if (query.types or query.document_type or query.decision_type)
        else "",
        "ProcessoNumero": query.number,
        "DataInicial": query.updated_from or query.published_from,
        "DataFinal": query.updated_to or query.published_to,
        "g-recaptcha-response": "",
        "Localizar": "Consultar",
    }


def _validate_fixed_scope(query: JurisprudenceQuery) -> None:
    """Validate filters represented by the provider's fixed TJGO scope.

    Projudi is a TJGO/state-court endpoint, so these fields are not sent as
    form parameters.  They are nevertheless real filters: a request for a
    different authority or branch must be rejected instead of silently
    returning TJGO records while the UI reports the filter as unsupported.
    """

    authority = _normalize_text(query.authority).casefold()
    if authority and authority not in {"tjgo", "tribunal de justica de goias"}:
        raise QueryRejectedError(
            f"a autoridade solicitada nao corresponde ao TJGO Projudi: {query.authority!r}"
        )

    branch = _normalize_text(query.branch).casefold()
    if branch and branch not in {"state", "estadual", "justica estadual"}:
        raise QueryRejectedError(
            f"TJGO Projudi pertence ao ramo estadual; recebido {query.branch!r}"
        )


def _map_instance(query: JurisprudenceQuery) -> str:
    requested_scope = query.source_origin or query.instance or query.degree
    if not requested_scope:
        collection = _normalize_text(query.collection).casefold()
        if collection == "cjpg":
            requested_scope = "first"
        elif collection == "cjsg":
            requested_scope = "second"
    if not requested_scope:
        return "0"
    normalized = _normalize_text(requested_scope).lower()
    mapping = {
        "1": "16",
        "1g": "16",
        "first": "16",
        "first degree": "16",
        "1 grau": "16",
        "primeiro grau": "16",
        "tribunal": "15",
        "second": "15",
        "second degree": "15",
        "appellate": "15",
        "2 grau": "15",
        "segundo grau": "15",
        "turma recursal": "151",
        "turmas recursais": "151",
    }
    return mapping.get(normalized, query.source_origin)


def _is_second_degree_scope(query: JurisprudenceQuery) -> bool:
    values = {
        _normalize_text(query.source_origin).casefold(),
        _normalize_text(query.degree).casefold(),
        _normalize_text(query.instance).casefold(),
        _normalize_text(query.collection).casefold(),
    }
    return bool(
        values
        & {
            "2",
            "2g",
            "2 grau",
            "segundo grau",
            "segundo_grau",
            "second",
            "second degree",
            "cjsg",
            "15",
        }
    )


def _is_first_degree_scope(query: JurisprudenceQuery) -> bool:
    values = {
        _normalize_text(query.source_origin).casefold(),
        _normalize_text(query.degree).casefold(),
        _normalize_text(query.instance).casefold(),
        _normalize_text(query.collection).casefold(),
    }
    return bool(
        values
        & {
            "1",
            "1g",
            "1 grau",
            "primeiro grau",
            "primeiro_grau",
            "first",
            "first degree",
            "16",
            "cjpg",
        }
    )


def _promote_first_degree_result(result: JurisprudenceResult) -> bool:
    """Attach CJPG identity only to an explicit first-degree unit result."""

    body = (result.judging_body or "").casefold()
    rapporteur = (result.rapporteur or "").casefold()
    appellate_marker = any(
        marker in body or marker in rapporteur
        for marker in ("câmara", "camara", "desembargador", "segundo grau")
    )
    first_unit_marker = any(
        marker in body for marker in ("vara", "juizado", "comarca", "ofício", "oficio", "upj")
    )
    if appellate_marker or not first_unit_marker:
        # PROJUDI can return a mixed window for some combinations.  Never
        # infer CJPG from the requested Id_Instancia alone when the card lacks
        # a first-degree unit marker.
        return False
    result.degree = "first"
    result.instance = "first"
    result.collection = "CJPG"
    result.branch = "state"
    result.authority = "TJGO"
    result.source_origin = "16"
    result.document_type = result.type
    result.raw.update(
        {
            "degree": "first",
            "instance": "first",
            "collection": "CJPG",
            "source_origin": "16",
            "document_type": result.document_type,
        }
    )
    result.field_provenance.update(
        {
            "degree": {"value": "first", "method": "query_scope", "source": "Id_Instancia=16"},
            "instance": {
                "value": "first",
                "method": "query_scope",
                "source": "Id_Instancia=16",
            },
            "collection": {"value": "CJPG", "method": "query_scope"},
        }
    )
    return True


def _promote_second_degree_result(result: JurisprudenceResult) -> bool:
    """Attach CJSG identity only after the request selected instance 15."""

    body = (result.judging_body or "").casefold()
    rapporteur = (result.rapporteur or "").casefold()
    rapporteur_is_first = "primeiro grau" in rapporteur or "1º grau" in rapporteur
    appellate_body = "câmara" in body or "camara" in body
    appellate_rapporteur = (
        "desembargador" in rapporteur or "juiz substituto em segundo grau" in rapporteur
    )
    if rapporteur_is_first or not (appellate_body or appellate_rapporteur):
        # PROJUDI has historically returned a mixed window for some filter
        # combinations. Exclude that card rather than attributing it to CJSG.
        return False
    result.degree = "second"
    result.instance = "second"
    result.collection = "CJSG"
    result.branch = "state"
    result.authority = "TJGO"
    result.source_origin = "15"
    result.document_type = "acordao" if result.type in {"decisao", "sentenca"} else result.type
    result.raw.update(
        {
            "degree": "second",
            "instance": "second",
            "collection": "CJSG",
            "source_origin": "15",
            "document_type": result.document_type,
        }
    )
    result.field_provenance.update(
        {
            "degree": {"value": "second", "method": "query_scope", "source": "Id_Instancia=15"},
            "instance": {
                "value": "second",
                "method": "query_scope",
                "source": "Id_Instancia=15",
            },
            "collection": {"value": "CJSG", "method": "query_scope"},
        }
    )
    return True


def _map_decision_type(value: str) -> str:
    normalized = _normalize_text(value).lower()
    mapping = {
        "decisao": "4",
        "decisão": "4",
        "sentenca": "5",
        "sentença": "5",
        "acordao": "1",
        "acórdão": "1",
    }
    return mapping.get(normalized, value)


def _parse_total(document: HtmlDocument) -> int | None:
    text = document.get_text(" ", strip=True) if hasattr(document, "get_text") else document.text()
    match = re.search(r"([\d.]+)\s+resultados encontrados", text, re.I)
    if not match:
        return None
    return int(match.group(1).replace(".", ""))


def _extract_publication_date(text: str) -> str | None:
    return _first_match(
        re.compile(r"Publicado em\s+(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?)", re.I), text
    )


def _extract_file_id(card: Any) -> str | None:
    for link in card.select("a[onclick]"):
        onclick = str(link.get("onclick") or "")
        match = FILE_ID_PATTERN.search(onclick)
        if match:
            return match.group("id")
    return None


def _find_decision_type(values: list[str]) -> str:
    """Find the explicit act label without relying on card paragraph position."""

    for value in values:
        decision_type = _normalize_decision_type(value)
        if decision_type is not None:
            return decision_type
    return "decisao"


def _normalize_decision_type(value: str) -> str | None:
    normalized = _normalize_text(value).lower()
    if "senten" in normalized:
        return "sentenca"
    if "ac" in normalized and "rd" in normalized:
        return "acordao"
    if "decis" in normalized:
        return "decisao"
    return None


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1 if pattern.groups else 0).strip() if match else None


def _decode_response_text(content: bytes, content_type: str | None) -> str:
    match = re.search(r"charset\s*=\s*['\"]?([^;\s'\"]+)", content_type or "", re.I)
    charset = match.group(1) if match else "iso-8859-1"
    try:
        return content.decode(charset, errors="replace")
    except LookupError:
        return content.decode("iso-8859-1", errors="replace")


def _looks_like_blocked_page(html: str) -> bool:
    lowered = html.lower()
    has_results = "search-result" in lowered or "resultados encontrados" in lowered
    if has_results:
        return False
    blocking_markers = [
        "g-recaptcha",
        "token_desafio",
        "tokendesafio",
        "cloudflare ray id",
        "just a moment",
        "verifique que voce nao e um robo",
        "verifique que você não é um robô",
    ]
    return any(marker in lowered for marker in blocking_markers)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
