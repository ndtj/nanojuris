"""STJ Informativo public jurisprudence provider."""

from __future__ import annotations

import re
import unicodedata
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.adaptive_selectors import resilient_select
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import DocumentReference, fetch_document_reference
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
from nanojuris.parsing import HtmlDocument, HtmlNode, parse_html
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)


class StjInformativoProvider(JurisprudenceProvider):
    """Provider for STJ Informativo de Jurisprudencia public HTML."""

    name = "stj_informativo"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http_metadata: dict[str, Any] = {}
        host = urlparse(self.config.stj_url).hostname or ""
        self._transport_policy = TransportPolicy(
            allowed_hosts=(host,),
            timeout_seconds=self.config.timeout,
            max_bytes=8_000_000,
            max_retries=0,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._transport = SharedHttpClient(self._transport_policy, session=self.session)
        self._document_policy = TransportPolicy(
            allowed_hosts=(host,),
            timeout_seconds=self.config.timeout,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._document_urls: dict[str, str] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/jurisprudencia/externo/informativo/"
        params = {
            "acao": "pesquisar",
            "livre": query.number or query.text,
            "operador": "E",
            "b": "INFJ",
            "tp": "T",
        }
        html = self._request_text(endpoint, params=params)
        source_url = urljoin(self.config.stj_url.rstrip("/") + "/", endpoint.lstrip("/"))
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {endpoint}",
            query={**params, "page": query.page, "page_size": query.page_size},
            source_url=source_url,
            limitations=[
                "HTML publico do Informativo de Jurisprudencia do STJ.",
                "Fonte curada por notas; nao substitui busca integral de acordaos SCON.",
                "Links para acordaos/inteiro teor podem apontar para rotas protegidas.",
            ],
            **self._last_http_metadata,
        )
        page = parse_stj_informativo_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.stj_url,
        )
        for result in page.results:
            # CNOT is the public informativo note.  An associated SCON
            # acórdão link may be protected, so it is never substituted here.
            note_url = str(result.raw.get("cnot_url") or "")
            if note_url:
                self._document_urls[result.id] = note_url
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        if precedent_id in self._document_urls:
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
                raw={"document": document.raw_metadata},
                raw_bytes=document.raw_bytes,
            )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "stj_informativo exposes public note text and linked case metadata."},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch a public CNOT note URL observed in the current search."""

        document_url = (
            document_id
            if document_id.startswith("https://")
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "STJ Informativo document_id must be an observed CNOT URL or a result id "
                "from the current search"
            )
        parsed = urlparse(document_url)
        expected_host = urlparse(self.config.stj_url).hostname
        if parsed.hostname != expected_host:
            raise ValueError("STJ Informativo document URL is outside the configured allowlist")
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
            title=f"STJ Informativo {parsed.query or parsed.path.rsplit('/', 1)[-1]}",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STJ Informativo",
            source_url="https://processo.stj.jus.br/jurisprudencia/externo/informativo/",
            category="court_jurisprudence",
            search_modes=["text", "case_number", "stj_informativo_query"],
            document_types=["informativo", "nota_jurisprudencia"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "informativo",
                "period",
                "case_number",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "title",
                "summary",
                "document_url",
                "cnot_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /jurisprudencia/externo/informativo/"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="local_window",
            completeness_contract="observed_window_only",
            full_text_access="document_link",
            supported_filters=["text", "number"],
            filter_semantics={
                "text": "native",
                "number": "native",
                **{
                    name: "unsupported"
                    for name in (
                        "all_words",
                        "any_words",
                        "without_words",
                        "exact_phrase",
                        "rapporteur",
                        "updated_from",
                        "updated_to",
                        "published_from",
                        "published_to",
                        "case_class",
                        "judging_body",
                        "degree",
                        "instance",
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
                        "fetch_details",
                        "courts",
                        "types",
                        "document_type",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                    )
                },
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
            },
            limitations=[
                "Retorna notas curadas do Informativo STJ, nao a base integral SCON.",
                "Acordaos referenciados podem depender de rotas SCON sujeitas a verificacao.",
                "Parser HTML depende de blocos .clsInformativoBlocoItem.",
            ],
            responsible_use=[
                "Usar termos especificos e page_size pequeno.",
                "Nao contornar validacao automatica em links de acordaos.",
                "Preservar a nota oficial e a referencia ao informativo na analise.",
            ],
        )

    def _request_text(self, path: str, **kwargs: Any) -> str:
        url = urljoin(self.config.stj_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self._transport.request(
                TransportRequest(
                    source=self.name,
                    operation="search",
                    method="GET",
                    url=url,
                    params=kwargs.pop("params", {}) or {},
                    headers=headers,
                )
            )
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"STJ Informativo request failed: {exc}") from exc
        text = _decode_stj_html(response.body, response.content_type)
        status_code = int(response.status_code or 0)
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": response.final_url or url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok"
            if response.status is TransportStatus.COMPLETE and status_code < 400
            else response.status.value,
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"STJ Informativo request failed: {response.status.value}")
        if status_code in {401, 403}:
            raise AccessControlRequiredError("STJ Informativo requires access-control validation")
        if status_code == 429:
            raise RateLimitDetectedError("STJ Informativo returned HTTP 429")
        if status_code >= 500:
            raise SourceUnavailableError(f"STJ Informativo returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"STJ Informativo rejected request with HTTP {status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("STJ Informativo requires access-control validation")
        return text


def parse_stj_informativo_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse STJ Informativo public HTML into normalized results."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError("STJ Informativo returned access-control HTML")
    document = parse_html(html)
    items = resilient_select(
        document,
        ".clsInformativoBlocoItem",
        name="result_item",
        source="stj_informativo",
        trace=trace,
    )
    if not items:
        text = document.get_text(" ", strip=True).lower()
        if "nenhum item encontrado" in text or "notas encontradas: 0" in text:
            return SearchPage(
                source="stj_informativo",
                total=0,
                start=0,
                end=0,
                page=query.page,
                page_size=query.page_size,
                results=[],
                source_trace=trace,
                pagination_mode="local_window",
                is_complete=True,
                completeness_reason="A fonte informou explicitamente resultado vazio.",
            )
        raise ParserContractChangedError("STJ Informativo result blocks not found")

    results = [
        _item_to_result(item, trace=trace, base_url=base_url, index=index)
        for index, item in enumerate(items, start=1)
    ]
    matches = [item for item in results if _matches_result(item, query)]
    total = _parse_total(document) or len(matches)
    start_index = max(query.page - 1, 0) * query.page_size
    page_results = matches[start_index : start_index + query.page_size]
    start = start_index + 1 if page_results else 0
    complete, completeness_reason = page_completeness(
        reported_total=len(matches),
        start=start,
        returned=len(page_results),
        total_is_authoritative=True,
    )
    return SearchPage(
        source="stj_informativo",
        total=total if len(matches) == len(results) else len(matches),
        start=start,
        end=start + len(page_results) - 1 if page_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=page_results,
        source_trace=trace,
        pagination_mode="local_window",
        is_complete=complete,
        completeness_reason=(
            "A página foi recortada localmente após a fonte retornar o conjunto observado."
            if complete is not False
            else completeness_reason
        ),
    )


def _item_to_result(
    item: HtmlNode,
    *,
    trace: SourceTrace,
    base_url: str,
    index: int,
) -> JurisprudenceResult:
    text = _normalize_spaces(item.text(" ", strip=True))
    title = _extract_title(item, text)
    body = _extract_body(item, title)
    case_number = _extract_case_number(item)
    document_links = _extract_document_links(item, base_url=base_url)
    document_url = document_links["document_url"]
    informativo = _match_group(r"Informativo\s*n[ºo.]?\s*(\d+)", text)
    period = _match_group(r"Per[ií]odo:\s*([^\.]+(?:\d{4})?)", text)
    judging_body = _extract_judging_body(text)
    rapporteur = _match_group(r"Rel\.\s*Min\.\s*([^,]+)", text)
    judgment_date = _match_group(r"julgado em\s*(\d{2}/\d{2}/\d{4})", text)
    source_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=document_url or trace.source_url,
        limitations=trace.limitations,
        http_status=trace.http_status,
        final_url=trace.final_url,
        content_type=trace.content_type,
        content_sha256=trace.content_sha256,
        response_bytes=trace.response_bytes,
        retrieval_status=trace.retrieval_status,
    )
    return JurisprudenceResult(
        id=f"stj-informativo-{informativo or index}-{_slug(case_number or title or str(index))}",
        source="stj_informativo",
        court="STJ",
        type="informativo",
        number=case_number,
        summary=body or title or None,
        rapporteur=rapporteur,
        updated_at=judgment_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=source_trace,
        raw={
            "informativo": informativo,
            "period": period,
            "orgao_julgador": judging_body,
            "judging_body": judging_body,
            "title": title or None,
            "data_julgamento": judgment_date,
            "judgment_date": judgment_date,
            "document_url": document_url,
            "acordao_url": document_links["acordao_url"],
            "cnot_url": document_links["cnot_url"],
            "raw_text": text,
        },
    )


def _extract_title(item: HtmlNode, fallback_text: str) -> str:
    title_candidates = item.select(".clsInformativoTextoBlocoTitulo, .clsInformativoTitulo")
    for candidate in title_candidates:
        text = _normalize_spaces(candidate.text(" ", strip=True))
        if text and not text.lower().startswith("informativo"):
            return text
    match = re.search(r"(DIREITO\s+.+?\.)\s+Compartilhe:", fallback_text, re.I)
    if match:
        return _normalize_spaces(match.group(1))
    match = re.search(r"(DIREITO\s+[A-ZÁ-Ú\s]+?\.\s*[^\.]+\.)", fallback_text)
    return _normalize_spaces(match.group(1)) if match else ""


def _extract_body(item: HtmlNode, title: str) -> str:
    body = item.select_one(".clsInformativoTexto")
    if body:
        return _normalize_spaces(body.text(" ", strip=True))
    text = _normalize_spaces(item.text(" ", strip=True))
    if title and title in text:
        return _normalize_spaces(text.split(title, 1)[-1])
    return text


def _extract_case_number(item: HtmlNode) -> str | None:
    for anchor in item.select("a[href]"):
        text = _normalize_spaces(anchor.text(" ", strip=True))
        if re.search(r"\b[A-Z]{1,8}\s+\d", text):
            return text
    text = _normalize_spaces(item.text(" ", strip=True))
    match = re.search(r"\b([A-Z]{1,8}\s+\d[\d\.\-]*/?[A-Z]{0,2})\b", text)
    return match.group(1) if match else None


def _extract_document_url(item: HtmlNode, *, base_url: str) -> str | None:
    return _extract_document_links(item, base_url=base_url)["document_url"]


def _extract_document_links(item: HtmlNode, *, base_url: str) -> dict[str, str | None]:
    """Return the separate STJ CNOT and acórdão links from an informativo item.

    The public informativo page commonly exposes both a ``@CNOT`` note link and
    one or more links to the underlying decision.  Keeping both links prevents
    consumers from losing the note when the first anchor happens to be the
    CNOT navigation link.
    """
    acordao_url: str | None = None
    cnot_url: str | None = None
    for anchor in item.select("a[href]"):
        text = _normalize_spaces(anchor.text(" ", strip=True))
        href = str(anchor.get("href") or "")
        resolved = urljoin(base_url.rstrip("/") + "/", href.lstrip("/"))
        if acordao_url is None and re.search(r"\b[A-Z]{1,8}\s+\d", text):
            acordao_url = resolved
        if "@CNOT" in href and cnot_url is None:
            cnot_url = resolved
    if cnot_url is None:
        # The current STJ response sometimes renders the CNOT target as plain
        # text (or through a script) instead of an anchor.  Recover only the
        # official route; do not synthesize an SCON URL from the case number.
        plain_text = _normalize_spaces(item.text(" ", strip=True))
        match = re.search(
            r"((?:https?://[^\s/]+)?/jurisprudencia/externo/informativo/\?livre=@CNOT=[^\s<\"']+)",
            plain_text,
            flags=re.I,
        )
        if match:
            cnot_url = urljoin(base_url.rstrip("/") + "/", match.group(1).rstrip(".,;"))
    return {
        "document_url": acordao_url or cnot_url,
        "acordao_url": acordao_url,
        "cnot_url": cnot_url,
    }


def _extract_judging_body(text: str) -> str | None:
    bodies = [
        "CORTE ESPECIAL",
        "PRIMEIRA SEÇÃO",
        "SEGUNDA SEÇÃO",
        "TERCEIRA SEÇÃO",
        "PRIMEIRA TURMA",
        "SEGUNDA TURMA",
        "TERCEIRA TURMA",
        "QUARTA TURMA",
        "QUINTA TURMA",
        "SEXTA TURMA",
        "PLENÁRIO",
    ]
    normalized = text.upper()
    for body in bodies:
        if body in normalized:
            return body.title()
    return None


def _matches_result(result: JurisprudenceResult, query: JurisprudenceQuery) -> bool:
    haystack = _normalize_search(
        " ".join(
            [
                str(result.number or ""),
                result.summary or "",
                result.rapporteur or "",
                " ".join(str(value or "") for value in result.raw.values()),
            ]
        )
    )
    text = _normalize_search(query.text)
    number = _normalize_search(query.number)
    if text and text not in haystack:
        return False
    if number and number not in _normalize_search(str(result.number or "")):
        return False
    return True


def _parse_total(document: HtmlDocument) -> int:
    text = _normalize_spaces(document.get_text(" ", strip=True))
    match = re.search(r"Notas encontradas:\s*(\d+)", text, re.I)
    return int(match.group(1)) if match else 0


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    if "clsinformativoblocoitem" in lowered or "nenhum item encontrado" in lowered:
        return False
    return (
        "challenge-error-text" in lowered
        or "enable javascript and cookies to continue" in lowered
        or ("captcha" in lowered and "informativo" not in lowered)
    )


def _match_group(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return _normalize_spaces(match.group(1)) if match else None


def _normalize_spaces(value: str) -> str:
    without_private_glyphs = re.sub(r"[\ue000-\uf8ff]", " ", value)
    normalized = re.sub(r"\s+", " ", without_private_glyphs).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", normalized)


def _decode_stj_html(body: bytes, content_type: str | None = None) -> str:
    """Decode STJ Informativo pages according to their declared charset."""

    declared = re.search(
        r"charset\s*=\s*['\"]?([\w.-]+)", str(content_type or ""), flags=re.IGNORECASE
    )
    candidates = [declared.group(1)] if declared else []
    candidates.extend(["utf-8", "cp1252", "iso-8859-1"])
    seen: set[str] = set()
    for encoding in candidates:
        normalized = encoding.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return bytes(body).decode(encoding, errors="strict")
        except (LookupError, UnicodeDecodeError):
            continue
    return bytes(body).decode("iso-8859-1", errors="replace")


def _normalize_search(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", _normalize_spaces(value).casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower() or "registro"
