"""TJTO public Jurisprudencia 4.0 provider."""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from nanojuris.adaptive_selectors import USE_DEFAULT_MEMORY, resilient_find_all
from nanojuris.canonical import normalize_date
from nanojuris.config import NanoJurisConfig
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    NanoJurisError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
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
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
UUID_RE = re.compile(r"uuid=([0-9a-f]{16,})", re.IGNORECASE)
TOTAL_RE = re.compile(r"\(([\d.]+)\s+resultados?\)", re.IGNORECASE)
TJTO_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)


class TjtoJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for TJTO's public HTML search and document routes."""

    name = "tjto_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = session or requests.Session()
        host = urlparse(self.config.tjto_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_retries=2,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self._last_search_method = "POST"

    @property
    def base_url(self) -> str:
        return self.config.tjto_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = query.text or query.exact_phrase or query.number
        if not term:
            raise ValueError("TJTO jurisprudence search requires text, exact_phrase or number")
        degree = _validate_tjto_degree_scope(query)
        page_size = _page_size(query.page_size)
        form = build_tjto_search_parameters(query, page_size=page_size)
        self._last_search_method = "POST"
        try:
            content, source_url = self._request_html("POST", "/consulta.php", data=form)
        except AccessControlRequiredError as exc:
            # The official site also exposes the same public search as a GET
            # route.  When the state-changing form is challenged, try that
            # documented, cacheable representation once.  This is ordinary
            # source navigation, not challenge solving or WAF evasion.
            self._last_search_method = "GET"
            try:
                content, source_url = self._request_html("GET", "/consulta.php", params=form)
            except (AccessControlRequiredError, SourceUnavailableError):
                raise exc from exc
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"{self._last_search_method} /consulta.php",
            query={
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "number": query.number,
                "page": query.page,
                "page_size": page_size,
                "form": {key: value for key, value in form.items() if "fq_" not in key},
            },
            source_url=source_url,
            limitations=[
                "A fonte exige User-Agent de navegador como parte do contrato HTTP publico.",
                "O POST e tentado primeiro; quando a fonte retorna um desafio WAF, "
                "o GET publico equivalente e tentado uma vez, sem gerar ou reutilizar token.",
                "Filtros de classe, assunto e competencia sao expostos pelo formulario, mas "
                "a query comum ainda nao possui campos tipados para esses valores.",
                "O link visualizado como 'Inteiro Teor' redireciona para documento.php e foi "
                "validado como HTML completo, nao como PDF.",
                "A rota tip_criterio_inst="
                f"{1 if degree == 'first' else 2} fixa o grau da consulta.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjto_search_response(content, query=query, trace=trace, source=self.name)
        if query.fetch_details:
            for result in page.results:
                self._enrich_with_detail(result)
        return page

    def _enrich_with_detail(self, result: JurisprudenceResult) -> None:
        """Load one detail lazily without losing the base search result.

        Detail access is an enrichment, not a prerequisite for search.  A
        public-source access error, timeout or schema change is recorded on the
        result and leaves the list item available with an explicit partial
        extraction state.
        """

        document_url = result.raw.get("document_url")
        document_id = result.raw.get("document_uuid")
        if not document_id:
            result.extraction_status = ExtractionStatus.PARTIAL
            result.raw["detail_status"] = "missing_document_id"
            return
        try:
            document = self.get_document(str(document_id))
        except (
            AccessControlRequiredError,
            NanoJurisError,
            ParserContractChangedError,
            QueryRejectedError,
            RateLimitDetectedError,
        ) as exc:
            result.extraction_status = ExtractionStatus.PARTIAL
            result.raw["detail_status"] = "error"
            result.raw["detail_error_type"] = type(exc).__name__
            result.raw["detail_error"] = str(exc)
            return
        result.full_text = document.text
        result.raw["full_text"] = document.text
        result.raw["full_text_status"] = "loaded" if document.text else "empty"
        result.raw["content_sha256"] = document.sha256
        result.raw["response_bytes"] = document.byte_size
        result.raw["document_content_type"] = document.content_type
        result.raw["document_url"] = document.url or document_url
        result.raw["detail_status"] = "loaded"
        result.extraction_status = document.extraction_status

    def get_document(self, document_id: str):
        uuid = document_id.removeprefix("tjto-jurisprudencia-")
        if not re.fullmatch(r"[0-9a-f]{16,}", uuid, re.IGNORECASE):
            raise ValueError("TJTO document_id must contain the public document uuid")
        content, source_url = self._request_html(
            "GET", "/documento.php", params={"uuid": uuid, "options": "#page=1"}
        )
        if b"<html" not in content[:4096].lower() and b"<fieldset" not in content[:4096].lower():
            raise ParserContractChangedError("TJTO document response is not HTML")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /documento.php",
            query={"document_id": uuid},
            source_url=source_url,
            limitations=["Documento publico entregue pela rota oficial documento.php."],
            **self._last_http_metadata,
        )
        return build_canonical_document(
            document_id=f"tjto-jurisprudencia-{uuid}",
            source=self.name,
            document_type="inteiro_teor",
            content=content,
            content_type=self._last_http_metadata.get("content_type"),
            url=source_url,
            title=None,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"document_endpoint": "/documento.php", "uuid": uuid},
            parser="tjto.documento_html",
            parser_version="1",
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        try:
            document = self.get_document(precedent_id)
        except ValueError as exc:
            raise SourceUnavailableError(
                "TJTO detail requires a public document UUID observed from search"
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

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJTO Jurisprudencia 4.0",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "facets", "pagination"],
            document_types=["acordao", "decisao_monocratica", "sentenca"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="degree_scope=tip_criterio_inst;collection=degree_specific",
            extracted_fields=[
                "case_number",
                "case_class",
                "decision_type",
                "subject",
                "competence",
                "rapporteur",
                "judgment_date",
                "filing_date",
                "summary",
                "document_url",
                "document_uuid",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /consulta.php",
                "POST /consulta.php",
                "GET /documento.php?uuid=<uuid>",
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            pagination_mode="offset",
            max_remote_page_size=100,
            completeness_contract="reported_html_total_and_start_rows_window",
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "rapporteur",
                "source_origin",
                "degree",
                "instance",
                "types",
                "order_by",
                "page",
                "fetch_details",
            ],
            unsupported_filters=[
                "courts",
                "all_words",
                "any_words",
                "without_words",
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
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "translated",
                "rapporteur": "translated",
                "source_origin": "translated",
                "degree": "translated",
                "instance": "translated",
                "types": "translated",
                "order_by": "translated",
                "page": "translated",
                "fetch_details": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
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
                "published_from": "unsupported",
                "published_to": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
            },
            limitations=[
                "A busca textual e os metadados sao HTML e dependem do layout publico.",
                "O total remoto e lido do contador textual da pagina quando presente.",
                "O formulario possui filtros adicionais de classe, assunto e competencia; "
                "eles ainda aguardam campos tipados na query unificada.",
            ],
            responsible_use=[
                "Usar User-Agent normal, rate limit e page_size moderado.",
                "Carregar documento sob demanda; nao baixar o corpus inteiro automaticamente.",
                "Nao confundir ementa com o HTML de inteiro teor carregado por documento.php.",
            ],
        )

    def _request_html(self, method: str, path: str, **kwargs: Any) -> tuple[bytes, str]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": TJTO_BROWSER_USER_AGENT,
        }
        request = TransportRequest(
            source=self.name,
            operation="document" if path.lstrip("/") == "documento.php" else "search",
            method=method,
            url=url,
            params=kwargs.pop("params", {}) or {},
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            headers=headers,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport kwargs: {', '.join(sorted(kwargs))}")
        response = self.transport.request(request)
        content = response.body
        response_url = response.final_url or url
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response_url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": response.status.value,
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError("TJTO jurisprudence transport unavailable")
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJTO jurisprudence returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJTO jurisprudence returned HTTP 429")
        if status_code == 202:
            if str(response.headers.get("x-amzn-waf-action", "")).casefold() == "challenge":
                raise AccessControlRequiredError(
                    "TJTO jurisprudence WAF challenge blocked the requested page"
                )
            # The public endpoint occasionally accepts a paginated request for
            # asynchronous processing and returns no body.  It is not an
            # authoritative empty page and must never be exposed as zero
            # results to the federated client.
            raise SourceUnavailableError(
                "TJTO jurisprudence returned HTTP 202 without a completed page"
            )
        if status_code in {401, 403}:
            raise AccessControlRequiredError("TJTO jurisprudence requires access validation")
        if status_code in {400, 422}:
            raise QueryRejectedError(
                f"TJTO jurisprudence rejected the query with HTTP {status_code}"
            )
        if status_code >= 500:
            raise SourceUnavailableError(f"TJTO jurisprudence returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"TJTO jurisprudence rejected request with HTTP {status_code}"
            )
        return content, response_url


def build_tjto_search_parameters(
    query: JurisprudenceQuery, *, page_size: int | None = None
) -> dict[str, str]:
    """Build the form fields observed in the public TJTO search form."""

    size = _page_size(page_size or query.page_size)
    _validate_tjto_degree_scope(query)
    term = query.text or query.exact_phrase or query.number
    form: dict[str, str] = {
        "q": term,
        "start": str(max(query.page - 1, 0) * size),
        "rows": str(size),
        "type_minuta_selected": "1",
    }
    if query.exact_phrase:
        form["soementa"] = "on"
    if query.number:
        form["numero_processo"] = query.number
    # The official form uses ``2`` for second-degree decisions.  Keep this
    # explicit even when the caller did not provide a provider-specific
    # origin, so federation cannot accidentally query the mixed corpus.
    degree = _validate_tjto_degree_scope(query)
    form["tip_criterio_inst"] = "1" if degree == "first" else "2"
    if query.order_by:
        form["tip_criterio_data"] = _order_value(query.order_by)
    selected_types = {item.lower() for item in query.types}
    if not selected_types or "acordao" in selected_types or "acórdão" in selected_types:
        form["tipo_decisao_acordao"] = "true"
    if "sentenca" in selected_types or "sentença" in selected_types:
        if degree != "first":
            raise QueryRejectedError("TJTO CJSG does not accept first-degree sentenca documents")
        form["type_minuta_selected"] = "3"
    if (
        "decisao" in selected_types
        or "decisão" in selected_types
        or "monocratica" in selected_types
    ):
        form["dec_monocrativa_is2G_true"] = "true"
    if query.rapporteur:
        form[f"fq_magistrado[{query.rapporteur}]"] = "on"
    return form


def parse_tjto_search_response(
    content: bytes,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    source: str = "tjto_jurisprudencia",
    memory: Any = USE_DEFAULT_MEMORY,
) -> SearchPage:
    """Parse one public TJTO HTML window without discarding the card HTML."""

    degree = _validate_tjto_degree_scope(query)
    collection = "CJPG" if degree == "first" else "CJSG"
    soup = BeautifulSoup(content, "html.parser")
    page_text = soup.get_text(" ", strip=True)
    total = _parse_total(page_text)
    explicit_empty = _is_explicit_empty(page_text)
    cards = (
        []
        if explicit_empty
        else resilient_find_all(
            soup,
            "div.container.align-self-center.panel.panel-default",
            name="result_card",
            source=source,
            memory=memory,
            trace=trace,
        )
    )
    if explicit_empty:
        return SearchPage(
            source=source,
            total=total if total is not None else 0,
            start=0,
            end=0,
            page=query.page,
            page_size=_page_size(query.page_size),
            results=[],
            source_trace=trace,
            pagination_mode="offset",
            is_complete=True,
            completeness_reason="A fonte declarou explicitamente que nao ha resultados.",
            total_known=total is not None,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.EMPTY,
        )
    if not cards and total:
        raise ParserContractChangedError("TJTO result total exists but result cards were not found")
    results = [
        _card_to_result(
            card,
            trace=trace,
            source=source,
            degree=degree,
            collection=collection,
        )
        for card in cards
    ]
    page_size = _page_size(query.page_size)
    start = (max(query.page - 1, 0) * page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=total is not None,
    )
    return SearchPage(
        source=source,
        total=total if total is not None else len(results),
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        source_trace=trace,
        pagination_mode="offset",
        is_complete=complete,
        completeness_reason=reason,
        total_known=total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
    )


def _card_to_result(
    card: Any,
    *,
    trace: SourceTrace,
    source: str = "tjto_jurisprudencia",
    degree: str = "second",
    collection: str = "CJSG",
) -> JurisprudenceResult:
    heading_node = card.select_one(".panel_doc")
    heading = _clean_text(heading_node.get_text(" ", strip=True)) if heading_node else ""
    body = card.select_one(".panel-body")
    if body is None:
        raise ParserContractChangedError("TJTO result card has no panel-body")
    body_text = _clean_text(body.get_text(" ", strip=True))
    number_match = PROCESS_NUMBER_RE.search(heading)
    number = number_match.group(0) if number_match else None
    document_link = card.select_one("a.button_doc")
    onclick = html.unescape(str(document_link.get("onclick", ""))) if document_link else ""
    uuid_match = UUID_RE.search(onclick)
    stable_id = uuid_match.group(1) if uuid_match else number
    if not stable_id:
        raise ParserContractChangedError("TJTO result card has no stable uuid or process number")
    values = _extract_labeled_fields(body_text)
    summary = values.get("summary") or None
    decision_type = values.get("decision_type") or "jurisprudencia"
    document_type = _canonical_document_type(decision_type)
    document_url = (
        urljoin(trace.source_url or "", f"/documento.php?uuid={uuid_match.group(1)}")
        if uuid_match
        else None
    )
    result = JurisprudenceResult(
        id=f"{source.replace('_', '-')}-{stable_id}",
        source=source,
        court="TJTO",
        type=decision_type,
        number=number,
        summary=summary,
        rapporteur=values.get("rapporteur") or None,
        judgment_date=normalize_date(values.get("judgment_date")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if summary else ExtractionStatus.PARTIAL,
        source_trace=trace,
        case_class=values.get("case_class") or None,
        judging_body=values.get("competence") or None,
        branch="state",
        authority="TJTO",
        degree=degree,
        instance=degree,
        collection=collection,
        document_type=document_type,
        source_origin="1" if degree == "first" else "2",
        document_url=document_url,
        field_provenance={
            "degree": {
                "value": degree,
                "method": "query_scope",
                "source": f"tip_criterio_inst={'1' if degree == 'first' else '2'}",
            },
            "instance": {
                "value": degree,
                "method": "query_scope",
                "source": f"tip_criterio_inst={'1' if degree == 'first' else '2'}",
            },
            "collection": {"value": collection, "method": "query_scope"},
            "document_type": {"value": document_type, "method": "type_filter"},
        },
        raw={
            "card_html": str(card),
            "case_class": values.get("case_class"),
            "subject": values.get("subject"),
            "competence": values.get("competence"),
            "filing_date": values.get("filing_date"),
            "judgment_date": values.get("judgment_date"),
            "document_uuid": uuid_match.group(1) if uuid_match else None,
            "document_url": document_url,
            "authority": "TJTO",
            "branch": "state",
            "collection": collection,
            "document_type": document_type,
            "degree": degree,
            "instance": degree,
            "source_origin": "1" if degree == "first" else "2",
        },
    )
    return result


def _extract_labeled_fields(text: str) -> dict[str, str]:
    labels = {
        "case_class": r"Classe\s+(.*?)\s+Tipo Julgamento",
        "decision_type": r"Tipo Julgamento\s+(.*?)\s+Assunto\(s\)",
        "subject": r"Assunto\(s\)\s+(.*?)\s+Competência",
        "competence": r"Competência\s+(.*?)\s+(?:Relator|Juiz)\s+",
        "rapporteur": r"(?:Relator|Juiz)\s+(.*?)\s+Data Autuação",
        "filing_date": r"Data Autuação\s+(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})",
        # The judgment date must not depend on an EMENTA token following it: some
        # cards carry the date but no published ementa.
        "judgment_date": r"Data Julgamento\s+(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})",
        "summary": r"EMENTA(?:\.|:)\s+(.*?)(?:\s+Referências?|$)",
    }
    return {
        key: _clean_text(match.group(1))
        for key, pattern in labels.items()
        if (match := re.search(pattern, text, re.I | re.S))
    }


def _parse_total(text: str) -> int | None:
    match = TOTAL_RE.search(_clean_text(text))
    if not match:
        return None
    try:
        return int(match.group(1).replace(".", ""))
    except ValueError:
        return None


def _is_explicit_empty(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).casefold()
    return any(
        marker in normalized
        for marker in (
            "nenhum resultado",
            "sem resultados",
            "nenhum registro encontrado",
        )
    )


def _order_value(value: str) -> str:
    normalized = value.lower()
    if "old" in normalized or normalized.endswith("asc"):
        return "ASC"
    if "relev" in normalized:
        return "RELEV"
    return "DESC"


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 100))


def _validate_tjto_degree_scope(query: JurisprudenceQuery) -> str:
    """Validate and return the explicit first/second-degree route scope."""

    degree = query.degree.strip().casefold()
    instance = query.instance.strip().casefold()
    source_origin = query.source_origin.strip().casefold()
    collection = query.collection.strip().casefold()
    second_degree = {"second", "second_degree", "segundo", "segundo grau", "2", "2g", "cjsg"}
    first_degree = {"first", "first_degree", "primeiro", "primeiro grau", "1", "1g", "cjpg"}
    scope_values = {value for value in (degree, instance, source_origin) if value}
    if scope_values & first_degree and scope_values & second_degree:
        raise QueryRejectedError("TJTO query mixes first- and second-degree scope")
    if degree and degree not in first_degree | second_degree:
        raise QueryRejectedError("TJTO jurisprudence accepts only first- or second-degree queries")
    if instance and instance not in first_degree | second_degree:
        raise QueryRejectedError("TJTO jurisprudence accepts only first- or second-degree queries")
    if source_origin and source_origin not in first_degree | second_degree:
        raise QueryRejectedError("TJTO jurisprudence requires a supported degree scope")
    if collection and collection not in {
        "cjpg",
        "cjsg",
        "first_degree",
        "second_degree",
        "jurisprudencia",
    }:
        raise QueryRejectedError("TJTO jurisprudence collection is not supported")
    if collection in {"cjpg", "first_degree"}:
        scope_values.add("first")
    if collection in {"cjsg", "second_degree"}:
        scope_values.add("second")
    result = "first" if scope_values & first_degree or "first" in scope_values else "second"
    selected_types = {item.strip().casefold() for item in query.types}
    if selected_types & {"sentenca", "sentença", "sentence"} and result != "first":
        raise QueryRejectedError("TJTO CJSG does not accept first-degree sentenca documents")
    return result


def _canonical_document_type(value: str) -> str:
    normalized = value.casefold()
    if "senten" in normalized:
        return "sentenca"
    if "monocr" in normalized or "individual" in normalized:
        return "decisao_monocratica"
    return "acordao"
