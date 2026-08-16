"""TJPI/JusPI public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

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

CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


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
        self._last_request = 0.0
        self._last_response_content = b""
        self._last_response_content_type: str | None = None
        self._last_http_metadata: dict[str, Any] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
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
            document_types=["acordao", "decisao_terminativa", "sumula"],
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
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            supported_filters=["text", "number"],
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
        decision_type = _map_decision_type(query.types[0]) if query.types else ""
        if decision_type:
            params["tipo"] = decision_type
        if query.lawyer_name:
            params["relator"] = query.lawyer_name
        if query.source_origin:
            params["orgao"] = query.source_origin
        if query.updated_from:
            params["data_min"] = query.updated_from
        if query.updated_to:
            params["data_max"] = query.updated_to
        return params

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        self._respect_rate_limit()
        url = urljoin(self.config.tjpi_juspi_url.rstrip("/") + "/", path.lstrip("/"))
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
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPI/JusPI request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJPI/JusPI returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJPI/JusPI returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJPI/JusPI rejected request with HTTP {response.status_code}"
            )
        text = response.text
        self._last_response_content = bytes(
            getattr(response, "content", None) or text.encode("utf-8")
        )
        self._last_response_content_type = (getattr(response, "headers", None) or {}).get(
            "Content-Type"
        )
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": getattr(response, "url", url),
            "content_type": self._last_response_content_type,
            "content_sha256": hashlib.sha256(self._last_response_content).hexdigest(),
            "response_bytes": len(self._last_response_content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("TJPI/JusPI returned captcha or access-control HTML")
        return text

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


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
    total, start, end = _parse_total(soup)
    cards = soup.select("div.callout")
    if not cards:
        complete, completeness_reason = page_completeness(
            reported_total=total,
            start=start,
            returned=0,
            total_is_authoritative=total > 0,
        )
        return SearchPage(
            source="tjpi_juspi",
            total=total,
            start=0,
            end=0,
            page=query.page,
            page_size=query.page_size,
            results=[],
            source_trace=trace,
            pagination_mode="page",
            is_complete=complete,
            completeness_reason=completeness_reason,
        )

    results: list[JurisprudenceResult] = []
    for card in cards:
        result = _parse_result_card(card, trace=trace, base_url=base_url)
        if result is not None:
            results.append(result)

    if not results and total > 0:
        raise ParserContractChangedError("TJPI/JusPI parser found total results but no cards")

    limited_results = results[: query.page_size]
    complete, completeness_reason = page_completeness(
        reported_total=total or None,
        start=start or (1 if limited_results else 0),
        returned=len(limited_results),
        total_is_authoritative=total > 0,
    )
    return SearchPage(
        source="tjpi_juspi",
        total=total or len(results),
        start=start or (1 if limited_results else 0),
        end=end if end and end <= query.page_size else len(limited_results),
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=completeness_reason,
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
        },
    )


def _parse_total(soup: BeautifulSoup) -> tuple[int, int, int]:
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Exibindo\s+(\d+)\s*-\s*(\d+)\s+de\s+um\s+total\s+de\s+(\d+)", text, re.I)
    if not match:
        return 0, 0, 0
    start, end, total = (int(match.group(index)) for index in (1, 2, 3))
    return total, start, end


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
