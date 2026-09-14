"""TJCE SJURIS public jurisprudence provider."""

from __future__ import annotations

import base64
import hashlib
import html as html_module
import json
import re
from datetime import date
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

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

SJURIS_PORTAL_URL = "https://sjuris.tjce.jus.br/"
SJURIS_DEFAULT_DOCUMENT_TYPES = ["ACÓRDÃO"]
SJURIS_DEFAULT_BASE = ["2º GRAU"]
SJURIS_DEFAULT_ORIGINS = ["PJE"]
SJURIS_MAX_PAGE_SIZE = 20


class TjceSjurisProvider(JurisprudenceProvider):
    """Provider for TJCE's public Angular SJURIS search gateway.

    The result contract was reproduced from the public browser application. The
    gateway returns the ementa, full text and an authenticated PDF payload in
    the search item itself. No independent detail route is assumed here.
    """

    name = "tjce_sjuris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjce_sjuris_url).hostname
        self.http = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,) if host else (),
                timeout_seconds=self.config.timeout,
                max_bytes=24_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self._inline_documents: dict[str, tuple[str, str, bytes | None, SourceTrace]] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjce_sjuris_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        remote_page = max(query.page - 1, 0)
        remote_size = _page_size(query.page_size)
        payload = build_tjce_sjuris_search_payload(query)
        endpoint = "/jurisprudencia/"
        data, source_url = self._request_json(
            endpoint,
            page=remote_page,
            size=remote_size,
            payload=payload,
        )
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /jurisprudencia/",
            query={
                "text": query.text,
                "page": query.page,
                "remote_page": remote_page,
                "requested_page_size": query.page_size,
                "effective_page_size": remote_size,
                "payload": payload,
            },
            source_url=source_url,
            limitations=[
                "O gateway foi observado com size 20; requests com size 50 e 100 "
                "retornaram HTTP 504.",
                "O texto integral e o PDF sao devolvidos inline no item; uma rota "
                "de detalhe independente ainda nao foi validada.",
                "O payload de datas e o filtro de relator ainda nao foram reproduzidos.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjce_sjuris_response(data, query=query, trace=trace)
        for result in page.results:
            if not result.full_text:
                continue
            pdf_bytes = _decode_pdf(result.raw.get("pdfAutenticadoBase64"))
            entry = (result.full_text, result.full_text, pdf_bytes, trace)
            self._inline_documents[result.id] = entry
            self._inline_documents[result.id.removeprefix("tjce-sjuris-")] = entry
        return page

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Return the text/PDF captured in an observed SJURIS result."""

        try:
            text, _, pdf_bytes, trace = self._inline_documents[document_id]
        except KeyError as exc:
            raise SourceUnavailableError(
                "TJCE/SJURIS inline document is available only after an observed search"
            ) from exc
        content = pdf_bytes or text.encode("utf-8")
        content_type = "application/pdf" if pdf_bytes else "text/plain"
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao",
            content=content,
            content_type=content_type,
            title="TJCE SJURIS documento inline",
            url=trace.source_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"inline": True, "pdf_available": pdf_bytes is not None},
            parser=f"{self.name}.inline_document",
            parser_version="1",
            text_override=text,
        )

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

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJCE SJURIS",
            source_url=SJURIS_PORTAL_URL,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "pagination"],
            document_types=["acordao", "decisao_monocratica", "sumula"],
            content_formats=["json", "text", "pdf"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "inline_pdf_base64",
                "pdf_content_sha256",
                "pdf_response_bytes",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "POST /jurisprudencia/?page={zero_based_page}&size={page_size}",
                "GET /jurisprudencia/buscaListaCampos/{field}",
            ],
            supports_full_text=True,
            supports_cli=True,
            # The provider now has a reproducible two-page live check,
            # success/empty/schema fixtures and a complete technical contract;
            # it is therefore eligible for the default federation.  Legal or
            # deployment policy is intentionally not encoded in capabilities.
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page=None,
            max_remote_page_size=SJURIS_MAX_PAGE_SIZE,
            completeness_contract="spring_page_total_elements",
            full_text_access="inline",
            supported_filters=[
                "text",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "types",
                "source_origins",
            ],
            unsupported_filters=[
                "courts",
                "rapporteur",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "number",
                "case_class",
                "judging_body",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
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
                "fetch_details",
            ],
            filter_semantics={
                "text": "translated",
                "all_words": "translated",
                "any_words": "translated",
                "without_words": "translated",
                "exact_phrase": "translated",
                "types": "translated",
                "source_origins": "translated",
                "source_origin": "unsupported",
                "courts": "unsupported",
                "rapporteur": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "number": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
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
                "fetch_details": "unsupported",
            },
            limitations=[
                "A interface observada usa ACÓRDÃO, 2º GRAU e PJE como filtros padrão.",
                "O gateway retornou HTTP 504 para size 50 e size 100 na validação live.",
                "Data de julgamento, relator e base documental ainda nao possuem payload "
                "reproduzido neste provider.",
                "O PDF e entregue em base64 no resultado; nao ha URL publica de detalhe "
                "confirmada.",
            ],
            responsible_use=[
                "Respeitar rate limit e manter page_size efetivo ate 20.",
                "Preservar o JSON bruto, o texto inline e o PDF base64 retornado pela fonte.",
                "Nao apresentar o PDF inline como documento carregado por uma rota independente.",
            ],
        )

    def _request_json(
        self,
        endpoint: str,
        *,
        page: int,
        size: int,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], str]:
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request_url = f"{url}?page={page}&size={size}"
        request = TransportRequest(
            source=self.name,
            operation="tjce_sjuris_search",
            method="POST",
            url=request_url,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": SJURIS_PORTAL_URL.rstrip("/"),
                "Referer": SJURIS_PORTAL_URL,
            },
            data=body,
            idempotent=False,
        )
        try:
            response = self.http.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJCE/SJURIS request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJCE/SJURIS transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJCE/SJURIS transport returned no HTTP status")
        content = bytes(response.body)
        headers = response.headers
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or request_url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status_code < 400 else "error",
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJCE/SJURIS returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJCE/SJURIS requires access validation")
        if status_code in {400, 422}:
            raise QueryRejectedError(f"TJCE/SJURIS rejected the query with HTTP {status_code}")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJCE/SJURIS returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJCE/SJURIS rejected request with HTTP {status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJCE/SJURIS response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJCE/SJURIS JSON root is not an object")
        return data, str(response.final_url or request_url)


def build_tjce_sjuris_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the browser payload reproduced from the public SJURIS UI."""

    return {
        "dataJulgamento": [],
        "busca": _build_search_expression(query),
        "ordenacao": _order_value(query.order_by),
        "nomeDocumento": _document_types(query.types),
        "baseDocumento": SJURIS_DEFAULT_BASE,
        "origem": list(query.source_origins) or SJURIS_DEFAULT_ORIGINS,
    }


def parse_tjce_sjuris_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
) -> SearchPage:
    """Parse the confirmed Spring-style SJURIS page envelope."""

    page_data = data.get("pagina")
    if not isinstance(page_data, dict) or not isinstance(page_data.get("content"), list):
        raise ParserContractChangedError("TJCE/SJURIS response missing pagina.content")
    items = page_data["content"]
    page_size = _page_size(query.page_size)
    results = [_item_to_result(item, trace=trace) for item in items if isinstance(item, dict)]
    reported_total = _as_int(page_data.get("totalElements"), default=len(results))
    start = ((max(query.page - 1, 0) * page_size) + 1) if results else 0
    complete, reason = page_completeness(
        reported_total=reported_total,
        start=start,
        returned=len(results),
        total_is_authoritative="totalElements" in page_data,
    )
    return SearchPage(
        source="tjce_sjuris",
        total=reported_total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        aggregations={
            "filtros": data.get("filtros", {}),
            "root_id": data.get("id"),
            "remote_page": page_data.get("number"),
            "remote_size": page_data.get("size"),
        },
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
        total_known="totalElements" in page_data,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
    )


def _item_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    source_id = _first_value(item, "id", "idDocumento")
    if source_id is None:
        raise ParserContractChangedError("TJCE/SJURIS item missing stable id")
    full_text = _clean_full_text(item.get("conteudo"))
    summary = _clean_snippet(item.get("ementa"))
    pdf_value = _string_value(item.get("pdfAutenticadoBase64"))
    pdf_metadata: dict[str, Any] = {}
    if pdf_value:
        try:
            pdf_bytes = base64.b64decode(pdf_value, validate=True)
        except (ValueError, TypeError):
            pdf_bytes = b""
        if pdf_bytes:
            pdf_metadata = {
                "pdf_content_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
                "pdf_response_bytes": len(pdf_bytes),
            }
    judgment_date = _date_value(item.get("dataJulgamento"))
    publication_date = _date_value(item.get("dataPublicacao"))
    return JurisprudenceResult(
        id=f"tjce-sjuris-{source_id}",
        source="tjce_sjuris",
        court="TJCE",
        type=_decision_type(item.get("nomeDocumento")),
        number=_string_value(item.get("numeroProcesso")) or None,
        summary=summary or None,
        full_text=full_text or None,
        rapporteur=_string_value(item.get("magistrado")) or None,
        judgment_date=judgment_date,
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if full_text else ExtractionStatus.PARTIAL),
        source_trace=trace,
        raw={
            **item,
            "case_class": _string_value(item.get("classe")) or None,
            "judging_body": _string_value(item.get("orgaoJulgador")) or None,
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "full_text_status": "inline" if full_text else "not_returned",
            "pdf_status": "inline_base64" if pdf_value else "not_returned",
            **pdf_metadata,
        },
    )


def _build_search_expression(query: JurisprudenceQuery) -> str:
    parts: list[str] = []
    if query.text.strip():
        parts.append(query.text.strip())
    if query.exact_phrase.strip():
        parts.append(f'"{query.exact_phrase.strip()}"')
    if query.all_words.strip():
        parts.append(" e ".join(query.all_words.split()))
    if query.any_words.strip():
        parts.append(" ou ".join(query.any_words.split()))
    if query.without_words.strip():
        parts.append("não " + " não ".join(query.without_words.split()))
    return " ".join(parts)


def _document_types(values: list[str]) -> list[str]:
    if not values:
        return list(SJURIS_DEFAULT_DOCUMENT_TYPES)
    known = {
        "acordao": "ACÓRDÃO",
        "acórdão": "ACÓRDÃO",
        "decisao_monocratica": "DECISÃO MONOCRÁTICA",
        "decisão monocrática": "DECISÃO MONOCRÁTICA",
        "sumula": "SÚMULA",
        "súmula": "SÚMULA",
    }
    return [known.get(value.strip().lower(), value.strip()) for value in values if value.strip()]


def _order_value(value: str) -> str:
    normalized = (value or "").strip().lower()
    return "order1" if normalized in {"", "text", "relevance", "relevancia"} else value


def _date_value(value: Any) -> str | None:
    if isinstance(value, list | tuple) and len(value) >= 3:
        try:
            return date(int(value[0]), int(value[1]), int(value[2])).isoformat()
        except (TypeError, ValueError):
            return None
    text = _string_value(value)
    if not text or text.lower() in {"n/d", "nd", "null"}:
        return None
    return text[:10]


def _decision_type(value: Any) -> str:
    text = _string_value(value).lower()
    return {
        "acórdão": "acordao",
        "decisão monocrática": "decisao_monocratica",
        "súmula": "sumula",
    }.get(text, text or "jurisprudencia")


def _first_value(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return value
    return None


_HTML_TAG = re.compile(r"<[^>]+>")


def _decode_pdf(value: Any) -> bytes | None:
    encoded = _string_value(value)
    if not encoded:
        return None
    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (TypeError, ValueError):
        return None
    return decoded or None


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_snippet(value: Any) -> str:
    """Drop search-highlight markup and non-breaking spaces from a text field.

    SJURIS returns the ementa with ``<em>`` highlight tags around matched terms
    and ``\xa0`` separators; those must not reach the canonical summary.
    """

    text = _string_value(value)
    if not text:
        return ""
    text = html_module.unescape(text)
    text = _HTML_TAG.sub("", text)
    return " ".join(text.replace("\xa0", " ").split())


def _clean_full_text(value: Any) -> str:
    """Return inline document text without provider HTML markup.

    SJURIS normally returns plain text, but some decisions contain HTML
    fragments (and occasionally embedded presentation markup).  The raw item
    remains available for provenance; the canonical field must stay readable
    and safe for the browser reader.
    """

    text = _string_value(value)
    if not text:
        return ""
    text = html_module.unescape(text)
    text = re.sub(
        r"<\s*(?:script|style|noscript)\b[^>]*>.*?<\s*/\s*(?:script|style|noscript)\s*>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.IGNORECASE)
    text = _HTML_TAG.sub("", text)
    return "\n".join(" ".join(line.split()) for line in text.splitlines()).strip()


def _as_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), SJURIS_MAX_PAGE_SIZE))
