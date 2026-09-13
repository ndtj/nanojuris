"""TRF3 public appellate jurisprudence by exact process number.

The TRF3 portal exposes a stable public route for looking up the appellate
documents associated with one CNJ process.  The broader free-text search is a
separate browser surface whose submission contract is not reproducible in a
clean HTTP client, so this adapter intentionally implements only the exact
process contract.  Keeping that boundary explicit prevents a process lookup
from being advertised as a complete corpus search.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedQueryError,
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
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

PROCESS_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
DATE_RE = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
DETAIL_RE = re.compile(
    r"/acordaos/Acordao/(?:BuscarDocumentoPje|BuscarDocumento)/[A-Za-z0-9_-]+",
    re.IGNORECASE,
)
PROCESS_DIGITS_RE = re.compile(r"^\d{20}$")


class Trf3JurisprudenciaProvider(JurisprudenceProvider):
    """Public TRF3 appellate document lookup, bounded to one CNJ process."""

    name = "trf3_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.trf3_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                max_retries=1,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_response_content = b""
        self._last_response_content_type: str | None = None
        self._last_http_metadata: dict[str, Any] = {}

    @property
    def base_url(self) -> str:
        return self.config.trf3_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        process = _process_digits(query.number or query.text)
        if process is None:
            raise UnsupportedQueryError(
                "TRF3 provider supports only an exact CNJ process number lookup"
            )
        if any(
            getattr(query, field)
            for field in (
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "rapporteur",
                "published_from",
                "published_to",
                "judgment_date_from",
                "judgment_date_to",
                "case_class",
                "judging_body",
                "types",
            )
        ):
            raise UnsupportedQueryError(
                "TRF3 exact process lookup does not accept additional search filters"
            )
        if query.page != 1:
            raise UnsupportedQueryError("TRF3 exact process lookup has one remote page")
        if query.degree and query.degree.casefold() not in {"second", "2", "segundo"}:
            raise UnsupportedQueryError("TRF3 route is restricted to second degree")
        if query.instance and query.instance.casefold() not in {"second", "2", "segundo"}:
            raise UnsupportedQueryError("TRF3 route is restricted to second instance")
        if query.branch and query.branch.casefold() not in {"federal", "justica_federal"}:
            raise UnsupportedQueryError("TRF3 route is restricted to the federal branch")
        if query.collection and query.collection.casefold() not in {
            "trf3_jurisprudencia",
        }:
            raise UnsupportedQueryError("TRF3 route exposes only its jurisprudence collection")
        if query.document_type and query.document_type.casefold() not in {"acordao", "acordão"}:
            raise UnsupportedQueryError("TRF3 process route returns appellate opinions")
        if query.decision_type and query.decision_type.casefold() not in {"acordao", "acordão"}:
            raise UnsupportedQueryError("TRF3 process route returns appellate opinions")

        html, source_url = self._request_html(
            "/acordaos/Acordao/PesquisarDocumento",
            params={"processo": process},
        )
        trace = SourceTrace(
            provider=self.name,
            endpoint="/acordaos/Acordao/PesquisarDocumento",
            query={"processo": process},
            source_url=source_url,
            limitations=[
                "A rota publica e uma consulta exata por processo, nao uma busca textual geral.",
                "Cada data retornada representa um documento de segundo grau separado.",
                "O total e conhecido apenas dentro da lista de documentos do processo.",
            ],
            **self._last_http_metadata,
        )
        results = parse_trf3_process_results(html, trace=trace, base_url=self.base_url)
        page_size = max(1, min(int(query.page_size or 10), 20))
        page = max(1, int(query.page or 1))
        if query.fetch_details:
            results = self._with_details(results, trace=trace)
        limited = results[:page_size]
        is_complete = len(limited) == len(results)
        return SearchPage(
            source=self.name,
            total=len(results),
            start=1 if limited else 0,
            end=len(limited),
            page=page,
            page_size=page_size,
            results=limited,
            source_trace=trace,
            pagination_mode="detail_links",
            is_complete=is_complete,
            completeness_reason=(
                "A fonte retorna todas as datas de acórdãos encontradas para o processo."
                if is_complete
                else "A fonte retornou todas as datas, mas a página foi limitada "
                "localmente ao page_size."
            ),
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        detail_url = _detail_url(precedent_id, self.base_url)
        html, source_url = self._request_html(detail_url)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/acordaos/Acordao/BuscarDocumentoPje/<id>",
            query={"document": _detail_identifier(detail_url)},
            source_url=source_url,
            limitations=["Inteiro teor HTML publico retornado pela rota oficial do TRF3."],
            **self._last_http_metadata,
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": html, "content_type": "text/html"}],
            source_trace=trace,
            raw={"document_url": source_url},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        content = str(bundle.texts[0]["content"])
        text = _visible_text(content)
        source_url = bundle.source_trace.source_url if bundle.source_trace else None
        detail_identifier = _detail_identifier(source_url or document_id)
        return build_canonical_document(
            document_id=f"trf3-jurisprudencia-document-{detail_identifier}",
            source=self.name,
            document_type="acordao",
            content=self._last_response_content or content.encode("utf-8"),
            content_type=self._last_response_content_type or "text/html",
            title="TRF3 Acórdão",
            text_override=text,
            url=source_url,
            access_status=AccessStatus.PUBLIC,
            source_trace=bundle.source_trace,
            raw_metadata={"authority": "TRF3", "degree": "second", "instance": "second"},
            parser="trf3_jurisprudencia.get_document",
            parser_version="1",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRF3 Jurisprudência (processo exato)",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["case_number", "detail"],
            document_types=["acordao"],
            content_formats=["html"],
            canonical_records=["JurisprudenceResult", "CanonicalDocument"],
            semantic_discriminator="degree=second; instance=second; route=acordaos",
            extracted_fields=[
                "case_number",
                "judgment_date",
                "document_url",
                "summary",
                "full_text",
                "degree",
                "instance",
                "branch",
                "collection",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /acordaos/Acordao/PesquisarDocumento?processo=<CNJ>",
                "GET /acordaos/Acordao/BuscarDocumentoPje/<id>",
            ],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="detail_links",
            max_remote_page=1,
            max_remote_page_size=20,
            completeness_contract="all_documents_for_exact_process",
            full_text_access="detail_call",
            supported_filters=[
                "number",
                "fetch_details",
                "degree",
                "instance",
                "branch",
                "collection",
                "document_type",
                "decision_type",
            ],
            unsupported_filters=[
                "text",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "rapporteur",
                "published_from",
                "published_to",
                "judgment_date_from",
                "judgment_date_to",
                "case_class",
                "judging_body",
                "types",
                "courts",
                "updated_from",
                "updated_to",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "source_origin",
                "source_origins",
                "legal_area",
                "authority",
            ],
            filter_semantics={
                "number": "native",
                "fetch_details": "translated",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "text": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "exact_phrase": "unsupported",
                "rapporteur": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "types": "unsupported",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "party_name": "unsupported",
                "party_document": "unsupported",
                "lawyer_name": "unsupported",
                "oab": "unsupported",
                "precatory_number": "unsupported",
                "police_document": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "legal_area": "unsupported",
                "authority": "unsupported",
            },
            ordering_modes=["source_document_date"],
            detail_modes=["html_full_text"],
            limitations=[
                "A pesquisa textual geral do portal permanece fora deste contrato.",
                "A resposta e uma lista de documentos associados a um processo, "
                "sem total de corpus.",
                "A disponibilidade live depende do host web.trf3.jus.br e pode sofrer timeout.",
            ],
            responsible_use=[
                "Consultar apenas processos necessarios, com page_size pequeno.",
                "Nao contornar CAPTCHA, WAF, TLS ou qualquer controle de acesso.",
                "Tratar timeout e bloqueio como indisponibilidade, nunca como vazio.",
            ],
        )

    def _with_details(
        self, results: list[JurisprudenceResult], *, trace: SourceTrace
    ) -> list[JurisprudenceResult]:
        enriched: list[JurisprudenceResult] = []
        for result in results:
            url = str(result.raw.get("document_url") or "")
            if not url:
                enriched.append(result)
                continue
            html, detail_url = self._request_html(url)
            detail_text = _visible_text(html)
            enriched.append(
                replace(
                    result,
                    full_text=detail_text or None,
                    document_url=detail_url,
                    source_trace=trace,
                    extraction_status=ExtractionStatus.COMPLETE,
                )
            )
        return enriched

    def _request_html(self, path_or_url: str, **kwargs: Any) -> tuple[str, str]:
        url = (
            path_or_url
            if path_or_url.startswith("https://")
            else urljoin(self.base_url + "/", path_or_url.lstrip("/"))
        )
        method = str(kwargs.pop("method", "GET"))
        request = TransportRequest(
            source=self.name,
            operation="trf3_jurisprudencia",
            method=method,
            url=url,
            params=kwargs.pop("params", {}),
            headers={
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "User-Agent": self.config.user_agent,
                **kwargs.pop("headers", {}),
            },
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except SourceUnavailableError:
            raise
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TRF3 jurisprudence request failed: {exc}") from exc
        body = bytes(response.body)
        content_type = str(response.content_type or "")
        self._last_response_content = body
        self._last_response_content_type = content_type
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response.final_url or url,
            "content_type": content_type or None,
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "response_bytes": len(body),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": (
                "ok"
                if response.status is TransportStatus.COMPLETE
                and response.status_code is not None
                and 200 <= response.status_code < 400
                else "error"
            ),
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                "TRF3 jurisprudence transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TRF3 jurisprudence transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("TRF3 jurisprudence returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TRF3 jurisprudence requires access validation")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TRF3 jurisprudence returned HTTP {response.status_code}")
        text = response.text
        lowered = text.casefold()
        if any(
            marker in lowered
            for marker in ("captcha", "turnstile", "access denied", "acesso negado")
        ):
            raise AccessControlRequiredError("TRF3 jurisprudence returned access-control HTML")
        return text, str(getattr(response, "url", url))


def parse_trf3_process_results(
    html: str, *, trace: SourceTrace, base_url: str
) -> list[JurisprudenceResult]:
    """Parse the official process lookup into one result per appellate date."""

    soup = BeautifulSoup(html, "html.parser")
    visible = _visible_text(html)
    if not any(
        marker in visible.casefold() for marker in ("resultado da pesquisa", "acórdão", "acordão")
    ):
        raise ParserContractChangedError("TRF3 process lookup result heading not found")
    process_match = PROCESS_RE.search(visible)
    process_number = process_match.group(0) if process_match else None
    rows: list[JurisprudenceResult] = []
    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href") or "")
        if not DETAIL_RE.search(href):
            continue
        absolute = urljoin(base_url + "/", href)
        date_match = DATE_RE.search(anchor.get_text(" ", strip=True))
        document_id = _detail_identifier(absolute)
        rows.append(
            JurisprudenceResult(
                id=f"trf3-jurisprudencia-{document_id}",
                source="trf3_jurisprudencia",
                court="TRF3",
                type="acordao",
                number=process_number,
                summary=None,
                full_text=None,
                judgment_date=date_match.group(0) if date_match else None,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.PARTIAL,
                degree="second",
                instance="second",
                branch="federal",
                authority="TRF3",
                collection="TRF3_JURISPRUDENCIA",
                document_type="acordao",
                document_url=absolute,
                source_trace=trace,
                raw={
                    "process_number": process_number,
                    "document_url": absolute,
                    "document_id": document_id,
                    "date_label": anchor.get_text(" ", strip=True),
                },
            )
        )
    if rows:
        return rows
    if any(
        marker in visible.casefold()
        for marker in ("nenhum acórdão", "nenhum acordão", "não encontrado", "nao encontrado")
    ):
        return []
    raise ParserContractChangedError("TRF3 process lookup did not expose document links")


def _process_digits(value: str) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    return digits if PROCESS_DIGITS_RE.fullmatch(digits) else None


def _detail_identifier(value: str) -> str:
    parsed = urlparse(value)
    match = DETAIL_RE.search(parsed.path)
    if match:
        return match.group(0).rsplit("/", 1)[-1]
    query = parse_qs(parsed.query)
    for key in ("id", "document", "documento"):
        if query.get(key):
            return query[key][0]
    match = re.search(r"([A-Za-z0-9_-]+)$", parsed.path.rstrip("/"))
    if match:
        return match.group(1)
    raise ParserContractChangedError("TRF3 detail URL does not contain a document id")


def _detail_url(value: str, base_url: str) -> str:
    if value.startswith("https://"):
        parsed = urlparse(value)
        if parsed.hostname != urlparse(base_url).hostname:
            raise ValueError("TRF3 document URL must use the official host")
        return value
    identifier = _detail_identifier(value)
    return urljoin(base_url + "/", f"acordaos/Acordao/BuscarDocumentoPje/{identifier}")


def _visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())
