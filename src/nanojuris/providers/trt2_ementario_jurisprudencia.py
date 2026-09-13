"""TRT2 public static ementario provider.

The TRT2 publishes official appellate ementas in static topic pages.  This
adapter uses those pages as a bounded, live collection and follows only the
PDF links returned by the same official page.  It is deliberately separate
from the PJe search surface, whose document route may require a challenge.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

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
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy
from nanojuris.transport.models import TransportRequest, TransportStatus

MAX_INDEX_BYTES = 1_500_000
MAX_TOPIC_BYTES = 200_000
MAX_TOPICS_PER_QUERY = 32
_HOST = "trt2.jus.br"
_OFFICIAL_HOSTS = {"trt2.jus.br", "www.trt2.jus.br"}
_ROOTS = {
    "tribunal_pleno": "/geral/tribunal2/Ementario/Tribunal_Pleno.html",
    "corregedoria": "/geral/tribunal2/Ementario/Corregedoria.html",
}
_PDF_RE = re.compile(r"\.pdf(?:$|[?#])", re.I)
_CASE_RE = re.compile(r"\bTRT/?SP\s+([^\n]{0,100}?\s+-\s+Ac\.)", re.I)
_DATE_RE = re.compile(r"\b(?:DOE|DJE)\s+(\d{2}/\d{2}/\d{4})", re.I)
_CHALLENGE_MARKERS = ("cf-chl-", "turnstile", "captcha", "access denied")


class Trt2EmentarioJurisprudenciaProvider(JurisprudenceProvider):
    """Search official TRT2 appellate ementario topic pages."""

    name = "trt2_ementario_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._items: dict[str, dict[str, Any]] = {}
        host = urlparse(self.config.trt2_ementario_url).hostname or _HOST
        self._document_policy = TransportPolicy(
            allowed_hosts=(host,),
            timeout_seconds=self.config.timeout,
            max_retries=1,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=tuple(_OFFICIAL_HOSTS),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_INDEX_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def base_url(self) -> str:
        return self.config.trt2_ementario_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        selected_roots = _selected_roots(query.collection)
        terms = _query_terms(query)
        candidates: list[dict[str, str]] = []
        traces: list[SourceTrace] = []
        for scope, path in selected_roots.items():
            content, url, trace = self._request_text(path, query, scope, MAX_INDEX_BYTES)
            traces.append(trace)
            candidates.extend(_parse_index(content, source_url=url, scope=scope))

        # Prefer topics whose official subject label contains a query term. If
        # no label matches, use a small deterministic prefix window; the
        # result remains partial because the static collection has no total or
        # native full-text endpoint.
        matching = [
            item for item in candidates if any(term in _norm(item["label"]) for term in terms)
        ]
        selected = matching or candidates[:MAX_TOPICS_PER_QUERY]
        selected = _dedupe_links(selected)[:MAX_TOPICS_PER_QUERY]
        results: list[JurisprudenceResult] = []
        for item in selected:
            content, detail_url, trace = self._request_text(
                item["url"], query, item["scope"], MAX_TOPIC_BYTES
            )
            result = _parse_topic(
                content,
                source_url=detail_url,
                topic=item["label"],
                scope=item["scope"],
                trace=trace,
            )
            if result is None or not _matches_query(result, query):
                continue
            results.append(result)
            self._items[result.id] = {
                "document_url": result.document_url,
                "summary": result.summary,
                "trace": trace,
            }

        start = (query.page - 1) * query.page_size
        page_results = results[start : start + query.page_size]
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /geral/tribunal2/Ementario/{Tribunal_Pleno|Corregedoria}.html",
            query=query.to_dict(),
            source_url=self.base_url,
            limitations=[
                "A fonte publica um indice estatico de topicos; nao informa total nacional.",
                "A janela live e limitada a 32 topicos por consulta para proteger a fonte.",
                "O inteiro teor depende do PDF oficialmente ligado pela ementa.",
            ],
            retrieval_status="ok",
            transformations=["topic_index_selection", "bounded_local_filter"],
        )
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start + 1 if page_results else 0,
            end=start + len(page_results) if page_results else 0,
            page=query.page,
            page_size=query.page_size,
            results=page_results,
            source_trace=trace,
            pagination_mode="local_window",
            is_complete=False,
            completeness_reason=(
                "A fonte nao publica total nem busca textual nacional; apenas uma "
                "janela bounded de topicos oficiais foi consultada."
            ),
            total_known=False,
            access_status=AccessStatus.PUBLIC,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        item = self._items.get(precedent_id)
        if item is None:
            raise SourceUnavailableError("TRT2 ementario exige resultado observado na sessao")
        document_url = item.get("document_url")
        if document_url:
            document = self.get_document(precedent_id)
            text = document.text or str(item.get("summary") or "")
            return DecisionBundle(
                precedent_id=precedent_id,
                source=self.name,
                texts=[{"content": text, "content_type": document.content_type or "text/plain"}],
                source_trace=document.source_trace,
                raw={"document_url": document.url},
                raw_bytes=document.raw_bytes,
            )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": str(item.get("summary") or ""), "content_type": "text/html"}],
            source_trace=item.get("trace"),
        )

    def get_document(self, document_id: str):
        item = self._items.get(document_id)
        if item is None or not item.get("document_url"):
            raise SourceUnavailableError("TRT2 ementario nao forneceu PDF para este topico")
        url = str(item["document_url"])
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in _OFFICIAL_HOSTS:
            raise ParserContractChangedError("TRT2 documento fora da allowlist oficial")
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=url,
                expected_content_types=("application/pdf", "application/octet-stream"),
            ),
            policy=self._document_policy,
            session=self.session,
            title="TRT2 ementario",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRT2 Ementario de Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "summary", "full_text"],
            document_types=["acordao_ementa"],
            content_formats=["html", "pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="official TRT2 appellate ementa topic pages",
            extracted_fields=[
                "topic",
                "summary",
                "full_text",
                "case_number",
                "publication_date",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /geral/tribunal2/Ementario/Tribunal_Pleno.html",
                "GET /geral/tribunal2/Ementario/Corregedoria.html",
                "GET /geral/tribunal2/Ementario/{collection}/{topic}.html",
                "GET /geral/tribunal2/Ementario/{collection}/Acordaos/{document}.pdf",
            ],
            supports_full_text=True,
            supports_catalog=True,
            supports_live_tests=True,
            supports_cli=True,
            # The public static collection has now passed two bounded live
            # rechecks (Tribunal Pleno and Corregedoria). It is safe for the
            # default federation as a clearly partial source: total_known is
            # always false and the response advertises the bounded window.
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="local_window",
            max_remote_page_size=MAX_TOPICS_PER_QUERY,
            completeness_contract="bounded_topic_window_total_unknown",
            full_text_access="document_link",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
                "page",
            ],
            unsupported_filters=[
                "all_words",
                "any_words",
                "without_words",
                "courts",
                "case_class",
                "judging_body",
                "rapporteur",
                "judgment_date_from",
                "judgment_date_to",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "fetch_details",
                "types",
                "precatory_number",
                "police_document",
                "cda",
                "source_origin",
                "source_origins",
                "legal_area",
                "decision_type",
            ],
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "translated",
                "document_type": "validated_scope",
                **{
                    name: "unsupported"
                    for name in (
                        "all_words",
                        "any_words",
                        "without_words",
                        "courts",
                        "case_class",
                        "judging_body",
                        "rapporteur",
                        "judgment_date_from",
                        "judgment_date_to",
                        "updated_from",
                        "updated_to",
                        "published_from",
                        "published_to",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "fetch_details",
                        "types",
                        "precatory_number",
                        "police_document",
                        "cda",
                        "source_origin",
                        "source_origins",
                        "legal_area",
                        "decision_type",
                    )
                },
            },
            limitations=[
                "Colecao curada e estatica; nao substitui a busca PJe completa.",
                "Total nacional entre topicos e desconhecido.",
                "A busca consulta no maximo 32 topicos por chamada.",
                "Alguns PDFs publicados podem ser imagem-only; o provider nao executa OCR.",
            ],
            responsible_use=[
                "Usar somente paginas e documentos publicados pelo TRT2.",
                "Respeitar rate limit e nao tentar contornar desafios do PJe.",
            ],
        )

    def _request_text(
        self,
        path_or_url: str,
        query: JurisprudenceQuery,
        scope: str,
        max_bytes: int,
    ) -> tuple[bytes, str, SourceTrace]:
        url = (
            path_or_url
            if path_or_url.startswith("https://")
            else urljoin(self.base_url + "/", path_or_url.lstrip("/"))
        )
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in _OFFICIAL_HOSTS:
            raise ParserContractChangedError("TRT2 URL fora da allowlist oficial")
        request = TransportRequest(
            source=self.name,
            operation=f"get_{parsed.path.lstrip('/').replace('/', '_')}",
            method="GET",
            url=url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
                "User-Agent": self.config.user_agent,
            },
            idempotent=True,
        )
        try:
            response = self._transport.request(request)
        except (requests.RequestException, SourceUnavailableError) as exc:
            raise SourceUnavailableError(f"TRT2 ementario request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.TLS_ERROR:
                raise SourceUnavailableError("TRT2 ementario TLS negotiation failed")
            if response.status is TransportStatus.TIMEOUT:
                raise SourceUnavailableError("TRT2 ementario timeout")
            raise SourceUnavailableError(
                f"TRT2 ementario transport failed: {response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TRT2 ementario transport returned no HTTP status")
        body = response.body
        final_url = str(response.final_url or url)
        final_host = urlparse(final_url).hostname
        if final_host not in _OFFICIAL_HOSTS:
            raise ParserContractChangedError("TRT2 redirectou para host nao oficial")
        if response.status_code == 429:
            raise RateLimitDetectedError("TRT2 ementario returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT2 ementario returned HTTP {response.status_code}")
        if response.status_code < 200 or response.status_code >= 300:
            raise SourceUnavailableError(f"TRT2 ementario returned HTTP {response.status_code}")
        if len(body) > max_bytes:
            raise ParserContractChangedError("TRT2 resposta excedeu o limite de bytes")
        lowered = body[:100_000].decode("iso-8859-1", errors="ignore").casefold()
        if any(marker in lowered for marker in _CHALLENGE_MARKERS):
            raise AccessControlRequiredError("TRT2 ementario retornou pagina de desafio")
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {parsed.path}",
            query={"scope": scope, "query": query.to_dict()},
            source_url=url,
            http_status=response.status_code,
            final_url=final_url,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status="ok",
        )
        return body, final_url, trace


def _selected_roots(collection: str) -> dict[str, str]:
    value = _norm(collection)
    if not value or value in {"ementario", "trt2_ementario", "cjsg"}:
        return _ROOTS
    if "correg" in value:
        return {"corregedoria": _ROOTS["corregedoria"]}
    if "pleno" in value or "tribunal" in value:
        return {"tribunal_pleno": _ROOTS["tribunal_pleno"]}
    raise QueryRejectedError("colecao TRT2 deve ser ementario, tribunal_pleno ou corregedoria")


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TRT2 ementario exige termo, numero ou frase exata")
    if query.degree and _norm(query.degree) not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT2 ementario suporta somente segundo grau")
    if query.instance and _norm(query.instance) not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT2 ementario suporta somente instancia de segundo grau")
    if query.branch and _norm(query.branch) not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT2 ementario pertence ao ramo trabalhista")
    if query.authority and _norm(query.authority) not in {"trt2", "trt02", "trt/sp"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TRT2")
    if query.document_type and _norm(query.document_type) not in {"acordao", "acordao_ementa"}:
        raise QueryRejectedError("TRT2 ementario publica somente ementas de acordaos")


def _query_terms(query: JurisprudenceQuery) -> list[str]:
    raw = query.exact_phrase or query.text or query.number
    return [term for term in (_norm(raw).split()) if len(term) >= 3]


def _parse_index(content: bytes, *, source_url: str, scope: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(content, "html.parser")
    results: list[dict[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "")
        label = " ".join(anchor.get_text(" ", strip=True).split())
        if not href or not label or href.startswith("#") or label.upper() in {"A", "C", "D"}:
            continue
        url = urljoin(source_url, href)
        parsed = urlparse(url)
        if parsed.hostname not in _OFFICIAL_HOSTS or not parsed.path.lower().endswith(".html"):
            continue
        if "/ementario/" not in parsed.path.casefold():
            continue
        results.append({"label": label, "url": url, "scope": scope})
    if not results:
        raise ParserContractChangedError("TRT2 ementario nao retornou topicos oficiais")
    return results


def _dedupe_links(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    output: list[dict[str, str]] = []
    for item in items:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        output.append(item)
    return output


def _parse_topic(
    content: bytes,
    *,
    source_url: str,
    topic: str,
    scope: str,
    trace: SourceTrace,
) -> JurisprudenceResult | None:
    soup = BeautifulSoup(content, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    if len(text) < 80:
        return None
    pdf_url = None
    for anchor in soup.find_all("a", href=True):
        candidate = urljoin(source_url, str(anchor.get("href") or ""))
        parsed = urlparse(candidate)
        if parsed.hostname in _OFFICIAL_HOSTS and _PDF_RE.search(parsed.path):
            pdf_url = candidate
            break
    result_id = "trt2-ementario-" + hashlib.sha256(source_url.encode()).hexdigest()[:20]
    case_match = _CASE_RE.search(text)
    date_match = _DATE_RE.search(text)
    number = case_match.group(1).strip() if case_match else None
    return JurisprudenceResult(
        id=result_id,
        source="trt2_ementario_jurisprudencia",
        court="TRT2",
        type="acordao_ementa",
        number=number,
        summary=text,
        full_text=text,
        publication_date=_br_date_to_iso(date_match.group(1)) if date_match else None,
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        raw={"topic": topic, "scope": scope, "index_url": trace.source_url},
        degree="second",
        instance="second",
        branch="labor",
        authority="TRT2",
        collection="TRT2_EMENTARIO",
        document_type="acordao_ementa",
        source_origin="trt2_ementario_estatico",
        document_url=pdf_url,
    )


def _matches_query(result: JurisprudenceResult, query: JurisprudenceQuery) -> bool:
    haystack = _norm(" ".join(value or "" for value in (result.summary, result.full_text)))
    if query.number and _norm(query.number) not in haystack:
        return False
    phrase = query.exact_phrase.strip() or query.text.strip()
    if phrase and not all(term in haystack for term in _norm(phrase).split()):
        return False
    if query.without_words and any(term in haystack for term in _norm(query.without_words).split()):
        return False
    return True


def _norm(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _br_date_to_iso(value: str) -> str:
    day, month, year = value.split("/")
    return f"{year}-{month}-{day}"


__all__ = ["Trt2EmentarioJurisprudenciaProvider"]
