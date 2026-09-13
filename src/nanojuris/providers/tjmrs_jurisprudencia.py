"""TJMRS public appellate jurisprudence lookup by exact process number.

The Tribunal de Justiça Militar do Rio Grande do Sul exposes a public HTML
route keyed by a CNJ process number.  The route returns the published appellate
opinion inline (including report, vote and ementa) when a document exists.  It
does not expose a reproducible free-text corpus contract, so this adapter is
deliberately exact-process and opt-in rather than a general federated source.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlencode, urlparse

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

PROCESS_DIGITS_RE = re.compile(r"^\d{20}$")
PROCESS_FORMATTED_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
DOCUMENT_RE = re.compile(r"\bDocumento\s*:\s*(\d+)\b", re.IGNORECASE)
CASE_RE = re.compile(
    r"(?P<label>[A-ZÀ-ÖØ-Ý][^\n]{0,140}?)\s+N[º°o.]\s*"
    r"(?P<number>\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})",
    re.IGNORECASE,
)
RELATOR_RE = re.compile(
    r"\bRELATOR\s*:\s*(?P<value>.+?)(?=\s+(?:APELANTE|APELADO|EMBARGANTE|EMBARGADO|"
    r"AGRAVANTE|AGRAVADO|RECORRENTE|RECORRIDO|REQUERENTE|REQUERIDO|PROCURADOR|"
    r"EMENTA|RELAT[ÓO]RIO|AC[ÓO]RD[ÃA]O)\s*:?|$)",
    re.IGNORECASE,
)
EMPTY_MARKERS = (
    "não houve registro de acórdão",
    "nao houve registro de acordao",
)


class TjmrsJurisprudenciaProvider(JurisprudenceProvider):
    """Public TJMRS appellate document lookup restricted to one process."""

    name = "tjmrs_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjmrs_jurisprudencia_url).hostname or ""
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
        return self.config.tjmrs_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        process = _process_digits(query.number or query.text)
        if process is None:
            raise UnsupportedQueryError(
                "TJMRS provider supports only an exact CNJ process number lookup"
            )
        unsupported = (
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
        if any(getattr(query, field) for field in unsupported):
            raise UnsupportedQueryError(
                "TJMRS exact process lookup does not accept additional search filters"
            )
        if query.page != 1:
            raise UnsupportedQueryError("TJMRS exact process lookup has one remote page")
        if query.degree and query.degree.casefold() not in {"second", "2", "segundo"}:
            raise UnsupportedQueryError("TJMRS route is restricted to second degree")
        if query.instance and query.instance.casefold() not in {"second", "2", "segundo"}:
            raise UnsupportedQueryError("TJMRS route is restricted to second instance")
        if query.branch and query.branch.casefold() not in {"military", "militar"}:
            raise UnsupportedQueryError("TJMRS route is restricted to the military branch")
        if query.collection and query.collection.casefold() not in {
            "tjmrs_jurisprudencia",
            "portal",
        }:
            raise UnsupportedQueryError("TJMRS route exposes only its jurisprudence collection")
        if query.document_type and query.document_type.casefold() not in {
            "acordao",
            "acórdão",
        }:
            raise UnsupportedQueryError("TJMRS route returns appellate opinions")
        if query.decision_type and query.decision_type.casefold() not in {
            "acordao",
            "acórdão",
        }:
            raise UnsupportedQueryError("TJMRS route returns appellate opinions")

        html, source_url = self._request_html(process)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/abreJurisprudencia.php",
            query={"processo": process},
            source_url=source_url,
            limitations=[
                "A rota pública é uma consulta exata por processo, não uma busca textual geral.",
                "A resposta é uma janela única; a fonte não expõe total de corpus.",
                "O inteiro teor HTML é preservado somente no fluxo explícito de documento.",
            ],
            **self._last_http_metadata,
        )
        result = parse_tjmrs_process_result(html, trace=trace, source_url=source_url)
        results = [] if result is None else [result]
        if query.fetch_details and result is not None:
            result = _with_full_text(result, html, trace)
            results = [result]
        return SearchPage(
            source=self.name,
            total=len(results),
            start=1 if results else 0,
            end=len(results),
            page=1,
            page_size=max(1, min(int(query.page_size or 10), 10)),
            results=results,
            source_trace=trace,
            pagination_mode="none",
            is_complete=True,
            completeness_reason=(
                "A fonte retornou um documento exato por processo."
                if results
                else "A fonte confirmou que não há registro de acórdão para o processo."
            ),
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        process = _process_digits(precedent_id)
        if process is None:
            raise UnsupportedQueryError("TJMRS document id must contain an exact CNJ process")
        html, source_url = self._request_html(process)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/abreJurisprudencia.php",
            query={"processo": process},
            source_url=source_url,
            limitations=["Inteiro teor HTML público retornado pela rota oficial do TJMRS."],
            **self._last_http_metadata,
        )
        result = parse_tjmrs_process_result(html, trace=trace, source_url=source_url)
        if result is None:
            return DecisionBundle(
                precedent_id=precedent_id,
                source=self.name,
                texts=[],
                source_trace=trace,
                raw={"access_status": AccessStatus.PUBLIC.value, "total": 0},
            )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=result.rapporteur,
            texts=[{"content": result.full_text or "", "content_type": "text/html"}],
            source_trace=trace,
            raw={"document_url": source_url, "source_id": result.id},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        process = _process_digits(document_id)
        if process is None:
            raise UnsupportedQueryError("TJMRS document id must contain an exact CNJ process")
        html, source_url = self._request_html(process)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/abreJurisprudencia.php",
            query={"processo": process},
            source_url=source_url,
            limitations=["Inteiro teor HTML público retornado pela rota oficial do TJMRS."],
            **self._last_http_metadata,
        )
        result = parse_tjmrs_process_result(html, trace=trace, source_url=source_url)
        if result is None:
            raise ParserContractChangedError("TJMRS returned an empty process document")
        return build_canonical_document(
            document_id=result.id,
            source=self.name,
            document_type="acordao",
            content=self._last_response_content,
            content_type=self._last_response_content_type or "text/html",
            title=f"TJMRS Acórdão {result.number or process}",
            text_override=result.full_text,
            url=source_url,
            access_status=AccessStatus.PUBLIC,
            source_trace=trace,
            raw_metadata={
                "authority": "TJMRS",
                "branch": "military",
                "degree": "second",
                "instance": "second",
                "case_number": result.number,
                "document_id": result.raw.get("document_id"),
            },
            parser="tjmrs_jurisprudencia.get_document",
            parser_version="1",
            max_bytes=8_000_000,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMRS Jurisprudência (processo exato)",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["case_number", "detail"],
            document_types=["acordao"],
            content_formats=["html"],
            canonical_records=["JurisprudenceResult", "CanonicalDocument"],
            semantic_discriminator=(
                "degree=second; instance=second; branch=military; route=abreJurisprudencia"
            ),
            extracted_fields=[
                "case_number",
                "case_class",
                "decision_type",
                "rapporteur",
                "summary",
                "full_text",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /abreJurisprudencia.php?processo=<20 dígitos CNJ>"],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="none",
            max_remote_page=1,
            max_remote_page_size=1,
            completeness_contract="one_public_document_for_exact_process",
            full_text_access="inline",
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
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "decision_type": "validated_scope",
            },
            ordering_modes=["source_document"],
            detail_modes=["html_full_text"],
            limitations=[
                "A rota pública não expõe busca textual geral nem paginação remota.",
                "A janela por processo não informa total do corpus.",
                "O conteúdo HTML pode conter aviso de ausência de acórdão junto com "
                "documento publicado; a presença de ementa e relator é o critério de sucesso.",
            ],
            responsible_use=[
                "Consultar somente processos necessários e em baixa frequência.",
                "Não contornar CAPTCHA, WAF, TLS ou qualquer controle de acesso.",
                "Tratar timeout, bloqueio e schema inválido como indisponibilidade, "
                "nunca como vazio.",
            ],
        )

    def _request_html(self, process: str) -> tuple[str, str]:
        url = f"{self.base_url}/abreJurisprudencia.php"
        request = TransportRequest(
            source=self.name,
            operation="tjmrs_jurisprudencia",
            method="GET",
            url=url,
            params={"processo": process},
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJMRS jurisprudence request failed: {exc}") from exc
        body = bytes(response.body)
        self._last_response_content = body
        self._last_response_content_type = response.content_type
        source_url = response.final_url or f"{url}?{urlencode({'processo': process})}"
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": source_url,
            "content_type": response.content_type,
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
                "TJMRS jurisprudence transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TJMRS jurisprudence transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("TJMRS jurisprudence returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJMRS jurisprudence requires access validation")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJMRS jurisprudence returned HTTP {response.status_code}"
            )
        text = _decode_html(body)
        lowered = text.casefold()
        if any(
            marker in lowered
            for marker in ("captcha", "turnstile", "access denied", "acesso negado")
        ):
            raise AccessControlRequiredError("TJMRS jurisprudence returned access-control HTML")
        return text, source_url


def parse_tjmrs_process_result(
    html: str, *, trace: SourceTrace, source_url: str
) -> JurisprudenceResult | None:
    """Parse one exact-process page, or return ``None`` for a proven empty."""

    soup = BeautifulSoup(html, "html.parser")
    visible = _visible_text(soup)
    lowered = visible.casefold()
    process_match = PROCESS_FORMATTED_RE.search(visible)
    document_match = DOCUMENT_RE.search(visible)
    has_opinion = "ementa" in lowered and "relator" in lowered
    if has_opinion and process_match:
        case_match = CASE_RE.search(visible)
        case_class = _clean_label(case_match.group("label")) if case_match else None
        relator_match = RELATOR_RE.search(visible)
        relator = _clean_label(relator_match.group("value")) if relator_match else None
        summary = _extract_section(
            visible, "EMENTA", ("ACÓRDÃO", "ACORDAO", "RELATÓRIO", "RELATORIO")
        )
        return JurisprudenceResult(
            id=(
                "tjmrs-jurisprudencia-"
                f"{document_match.group(1) if document_match else process_match.group(0)}"
            ),
            source="tjmrs_jurisprudencia",
            court="TJMRS",
            type="acordao",
            number=process_match.group(0),
            summary=summary,
            full_text=visible,
            rapporteur=relator,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
            degree="second",
            instance="second",
            branch="military",
            authority="TJMRS",
            collection="TJMRS_JURISPRUDENCIA",
            document_type="acordao",
            document_url=source_url,
            source_trace=trace,
            raw={
                "process_number": process_match.group(0),
                "document_id": document_match.group(1) if document_match else None,
                "case_class": case_class,
                "source_url": source_url,
            },
        )
    if process_match is None and any(marker in lowered for marker in EMPTY_MARKERS):
        return None
    if process_match and any(marker in lowered for marker in EMPTY_MARKERS) and not has_opinion:
        return None
    raise ParserContractChangedError(
        "TJMRS process page did not expose an opinion or authoritative empty"
    )


def _with_full_text(
    result: JurisprudenceResult, html: str, trace: SourceTrace
) -> JurisprudenceResult:
    return JurisprudenceResult(
        **{
            **result.to_dict(),
            "full_text": _visible_text(BeautifulSoup(html, "html.parser")),
            "source_trace": trace,
            "extraction_status": ExtractionStatus.COMPLETE,
        }
    )


def _process_digits(value: str) -> str | None:
    digits = re.sub(r"\D", "", value or "")
    return digits if PROCESS_DIGITS_RE.fullmatch(digits) else None


def _visible_text(soup: BeautifulSoup) -> str:
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _extract_section(text: str, heading: str, endings: tuple[str, ...]) -> str | None:
    match = re.search(rf"\b{re.escape(heading)}\s*:\s*", text, re.IGNORECASE)
    if match is None:
        return None
    remainder = text[match.end() :]
    end_positions = [
        re.search(rf"\b{re.escape(end)}\b", remainder, re.IGNORECASE) for end in endings
    ]
    offsets = [item.start() for item in end_positions if item is not None]
    value = remainder[: min(offsets)] if offsets else remainder
    return _clean_label(value) or None


def _clean_label(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split()).strip(" :;-")


def _decode_html(body: bytes) -> str:
    utf8 = body.decode("utf-8", errors="replace")
    if utf8.count("�") <= 20:
        return utf8
    return body.decode("cp1252", errors="replace")
