"""STJ SCON public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import requests

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
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.parsing import HtmlNode, parse_html
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)


class StjSconProvider(JurisprudenceProvider):
    """Provider for public STJ SCON case-law search."""

    name = "stj_scon"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http_metadata: dict[str, Any] = {}
        host = urlparse(self.config.stj_scon_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=16_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/SCON/pesquisar.jsp"
        params = self._build_params(query)
        html = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=urljoin(self.config.stj_scon_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=[
                "Fonte HTML publica do STJ/SCON sujeita a mudancas de layout.",
                "Operadores de busca pertencem ao STJ e sao repassados sem reinterpretacao.",
                "O provider detecta captcha/controle de acesso e nao implementa bypass.",
            ],
            **self._last_http_metadata,
        )
        return parse_stj_scon_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.stj_scon_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        try:
            document = self.get_document(precedent_id)
        except (ValueError, SourceUnavailableError) as exc:
            raise SourceUnavailableError(
                "STJ/SCON decision detail requires a public registry number observed from search"
            ) from exc
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "application/pdf",
                }
            ],
            source_trace=document.source_trace,
            raw=document.raw_metadata,
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Load the public SCON document referenced by a search result.

        The result id contains the stable SCON registry number.  Callers may
        also pass the exact official document URL captured in ``raw`` when a
        publication date is required by the source.
        """

        if document_id.startswith(("http://", "https://")):
            url = document_id
            endpoint = "/SCON/GetInteiroTeorDoAcordao"
            params: dict[str, str] = {}
            canonical_id = _document_id_from_url(document_id)
        else:
            registry_number = _extract_registry_from_document_id(document_id)
            endpoint = "/SCON/GetInteiroTeorDoAcordao"
            params = {"num_registro": registry_number}
            url = urljoin(self.config.stj_scon_url.rstrip("/") + "/", endpoint.lstrip("/"))
            canonical_id = f"stj-scon-document-{registry_number}"

        response = self._request_response(
            "GET",
            endpoint,
            url=url,
            params=params,
            accept="application/pdf, text/html, */*",
        )
        content = bytes(response.body)
        if not content:
            raise ParserContractChangedError("STJ/SCON document response is empty")
        headers = response.headers
        final_url = str(response.final_url or url)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=final_url,
            final_url=final_url,
            http_status=int(response.status_code or 200),
            content_type=headers.get("Content-Type"),
            limitations=[
                "Documento publico carregado sob demanda pela rota oficial SCON.",
                "O texto e derivado do PDF/HTML, mantendo os bytes originais no documento.",
            ],
        )
        return build_canonical_document(
            document_id=canonical_id,
            source=self.name,
            document_type="acordao",
            content=content,
            content_type=headers.get("Content-Type"),
            url=final_url,
            title="STJ SCON inteiro teor",
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={
                "registry_number": _extract_registry_from_document_id(document_id)
                if not document_id.startswith(("http://", "https://"))
                else None,
                "document_reference": document_id,
            },
            parser="stj_scon.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STJ SCON Acordaos",
            source_url="https://processo.stj.jus.br/SCON/acordaos/",
            category="court_jurisprudence",
            search_modes=["text", "case_number", "stj_query_language"],
            document_types=["acordao"],
            content_formats=["html", "pdf"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "registry_number",
                "decision_type",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /SCON/pesquisar.jsp",
                "GET /SCON/SearchFiltroBRS",
                "GET /SCON/jurisprudencia/pesquisaAjax.jsp",
                "POST /SCON/ActionSelecionaDocumento",
                "GET /SCON/GetInteiroTeorDoAcordao",
            ],
            supports_full_text=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number"],
            unsupported_filters=[
                "courts",
                "types",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "rapporteur",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "fetch_details",
                "case_class",
                "judging_body",
                "degree",
                "instance",
                "legal_area",
                "collection",
                "document_type",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "lawyer_name",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origin",
                "source_origins",
            ],
            filter_semantics={
                "text": "native",
                "number": "native",
                "courts": "unsupported",
                "types": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "exact_phrase": "unsupported",
                "rapporteur": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "fetch_details": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "degree": "unsupported",
                "instance": "unsupported",
                "branch": "validated_scope",
                "legal_area": "unsupported",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "lawyer_name": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
            },
            ordering_modes=["relevance", "publication"],
            detail_modes=["full_text"],
            limitations=[
                "Busca principal mapeada por HAR publico como GET /SCON/pesquisar.jsp.",
                (
                    "HAR complementar observou SearchFiltroBRS, pesquisaAjax.jsp "
                    "e ActionSelecionaDocumento."
                ),
                "A carga documental e feita sob demanda a partir do registro ou URL oficial.",
                "Sessao limpa em ambiente automatizado pode receber verificacao Cloudflare/STJ.",
            ],
            responsible_use=[
                "Nao tentar contornar captcha, login ou controles de acesso.",
                "Usar testes live apenas quando explicitamente habilitados.",
                (
                    "Preservar operadores oficiais do STJ sem reinterpreta-los "
                    "como aconselhamento juridico."
                ),
            ],
        )

    def _build_params(self, query: JurisprudenceQuery) -> dict[str, str | int]:
        params: dict[str, str | int] = {
            "b": "ACOR",
            "p": "true",
            "l": query.page_size,
            "i": query.page,
            "ordenacao": self._map_order_by(query.order_by),
            "thesaurus": "JURIDICO",
            "O": "JT",
        }
        if query.text:
            params["livre"] = query.text
        if query.number:
            params["processo"] = query.number
        return params

    @staticmethod
    def _map_order_by(value: str) -> str:
        normalized = value.strip().lower()
        mapping = {
            "text": "-@DOCN",
            "relevance": "-@DOCN",
            "document": "-@DOCN",
            "date": "-@DTPB",
            "publication": "-@DTPB",
            "dtpublicacao": "-@DTPB",
        }
        return mapping.get(normalized, value or "-@DOCN")

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        url = urljoin(self.config.stj_scon_url.rstrip("/") + "/", path.lstrip("/"))
        response = self._request_response(
            method,
            path,
            url=url,
            accept="text/html, */*",
            **kwargs,
        )
        return response.text

    def _request_response(
        self,
        method: str,
        path: str,
        *,
        url: str | None = None,
        accept: str,
        **kwargs: Any,
    ) -> TransportResponse:
        request_url = url or urljoin(self.config.stj_scon_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {"Accept": accept, "User-Agent": self.config.user_agent}
        request = TransportRequest(
            source=self.name,
            operation=f"{method.lower()}_{path.strip('/').replace('/', '_')}",
            method=method,
            url=request_url,
            params=kwargs.get("params") or {},
            data=kwargs.get("data"),
            headers=headers,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        try:
            response = self.transport.request(request)
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"STJ/SCON request failed: {exc}") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"STJ/SCON request failed: {exc}") from exc

        text = response.text
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or request_url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "retrieval_status": (
                "ok"
                if response.status_code is not None and 200 <= response.status_code < 300
                else "http_error"
            ),
        }
        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.TLS_ERROR:
                raise SourceUnavailableError("STJ/SCON TLS negotiation failed")
            raise SourceUnavailableError(
                f"STJ/SCON transport failed: {response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("STJ/SCON transport returned no HTTP status")
        if response.status_code in {401, 403} and _looks_like_access_control(text):
            raise AccessControlRequiredError("STJ/SCON requires access-control validation")
        if response.status_code == 429:
            raise RateLimitDetectedError("STJ/SCON returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"STJ/SCON returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"STJ/SCON rejected request with HTTP {response.status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("STJ/SCON requires captcha or access control")
        return response


def parse_stj_scon_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    """Parse a representative STJ SCON result page into normalized results."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError("STJ/SCON returned captcha/access-control HTML")

    document = parse_html(html, base_url=base_url)
    real_items = document.select(".documento")
    result_root = document.select_one("#resultados") or document.select_one(".resultados")
    if result_root is None and real_items:
        return _parse_stj_document_items(
            real_items,
            query=query,
            trace=trace,
            base_url=base_url,
        )
    if result_root is None:
        if "resultado" in html.lower() and "nenhum" in html.lower():
            return SearchPage(
                source="stj_scon",
                total=0,
                start=0,
                end=0,
                page=query.page,
                page_size=query.page_size,
                results=[],
                source_trace=trace,
            )
        raise ParserContractChangedError("STJ/SCON result container not found")

    total, start, end = _parse_pagination(result_root.text(" ", strip=True))
    results: list[JurisprudenceResult] = []
    for _index, item in enumerate(result_root.select(".documento, .resultado"), start=1):
        anchor = item.select_one("a.doclink, a[href]")
        registry_number = _text(item, ".registro") or _extract_registry(anchor)
        case_number = _text(item, ".processo") or (anchor.text(" ", strip=True) if anchor else "")
        if not registry_number and not case_number:
            continue
        document_url = (
            urljoin(base_url.rstrip("/") + "/", str(anchor.get("href"))) if anchor else None
        )
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint=trace.endpoint,
            query=trace.query,
            source_url=document_url or trace.source_url,
            limitations=trace.limitations,
        )
        case_class = _text(item, ".classe") or ""
        result = JurisprudenceResult(
            id=_stable_stj_id(registry_number, case_number, item.text(" ", strip=True)),
            source="stj_scon",
            court="STJ",
            type="acordao",
            number=case_number or registry_number,
            summary=_text(item, ".ementa") or None,
            rapporteur=_text(item, ".relator") or None,
            updated_at=_text(item, ".data-publicacao") or _text(item, ".data-julgamento") or None,
            judgment_date=_text(item, ".data-julgamento") or None,
            publication_date=_text(item, ".data-publicacao") or None,
            access_status=AccessStatus.PUBLIC,
            highlights={},
            source_trace=result_trace,
            raw={
                "classe": case_class,
                "registro": registry_number,
                "registry_number": registry_number,
                "orgao_julgador": _text(item, ".orgao-julgador"),
                "data_julgamento": _text(item, ".data-julgamento"),
                "data_publicacao": _text(item, ".data-publicacao"),
                "document_url": document_url,
            },
        )
        results.append(result)

    if not results and total > 0:
        raise ParserContractChangedError("STJ/SCON parser found total results but no items")

    return SearchPage(
        source="stj_scon",
        total=total or len(results),
        start=start or (1 if results else 0),
        end=end or len(results),
        page=query.page,
        page_size=query.page_size,
        results=results,
        source_trace=trace,
    )


def _parse_stj_document_items(
    items: list[HtmlNode],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
) -> SearchPage:
    total = _parse_document_total(items)
    results: list[JurisprudenceResult] = []
    for _index, item in enumerate(items, start=1):
        fields = _extract_stj_document_fields(item)
        identification = _text(item, ".clsIdentificacaoDocumento")
        case_number = fields.get("processo") or identification
        registry_number = _extract_stj_registry(item)
        document_url = _extract_stj_document_url(item, base_url=base_url)
        if not case_number and not registry_number:
            continue
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint=trace.endpoint,
            query=trace.query,
            source_url=document_url or trace.source_url,
            limitations=trace.limitations,
        )
        publication = fields.get("data da publicacao/fonte")
        result = JurisprudenceResult(
            id=_stable_stj_id(registry_number, case_number, item.text(" ", strip=True)),
            source="stj_scon",
            court="STJ",
            type="acordao",
            number=case_number,
            summary=fields.get("ementa"),
            rapporteur=fields.get("relator"),
            updated_at=_extract_date(publication) or fields.get("data do julgamento"),
            judgment_date=_extract_date(fields.get("data do julgamento")),
            publication_date=_extract_date(publication),
            access_status=AccessStatus.PUBLIC,
            highlights={},
            source_trace=result_trace,
            raw={
                "classe": identification,
                "registro": registry_number,
                "registry_number": registry_number,
                "orgao_julgador": fields.get("orgao julgador"),
                "data_julgamento": fields.get("data do julgamento"),
                "data_publicacao": publication,
                "document_url": document_url,
                "fields": fields,
            },
        )
        results.append(result)

    if not results and total > 0:
        raise ParserContractChangedError("STJ/SCON parser found total results but no items")
    limited_results = results[: query.page_size]
    return SearchPage(
        source="stj_scon",
        total=total or len(results),
        start=1 if results else 0,
        end=len(limited_results),
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
    )


def _extract_stj_document_fields(item: HtmlNode) -> dict[str, str]:
    fields: dict[str, str] = {}
    for paragraph in item.select(".paragrafoBRS"):
        title = _normalize_label(_text(paragraph, ".docTitulo"))
        value = _normalize_spaces(_text(paragraph, ".docTexto"))
        if title and value:
            fields[title] = value
    return fields


def _stable_stj_id(registry_number: str, case_number: str, text: str) -> str:
    """Build an identity that remains stable when pagination order changes."""

    primary = registry_number.strip() or _normalize_identifier(case_number)
    if not primary:
        primary = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:20]
    return f"stj-scon-{primary}"


def _normalize_identifier(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "", value).lower()


def _extract_stj_registry(item: HtmlNode) -> str:
    for anchor in item.select("a[href]"):
        href = unquote(str(anchor.get("href") or ""))
        match = re.search(r"num_registro=(\d+)", href)
        if match:
            return match.group(1)
    return ""


def _extract_stj_document_url(item: HtmlNode, *, base_url: str) -> str | None:
    for anchor in item.select("a[href]"):
        href = unquote(str(anchor.get("href") or ""))
        match = re.search(r"inteiro_teor\('([^']+)'\)", href)
        if match:
            return urljoin(base_url.rstrip("/") + "/", match.group(1).lstrip("/"))
        if "GetInteiroTeorDoAcordao" in href:
            return urljoin(base_url.rstrip("/") + "/", href.lstrip("/"))
    return None


def _extract_registry_from_document_id(document_id: str) -> str:
    match = re.search(r"(?:stj-scon-|num_registro=)(\d+)", document_id)
    if not match:
        raise ValueError("STJ SCON document_id must contain a registry number")
    return match.group(1)


def _document_id_from_url(document_url: str) -> str:
    registry = _extract_registry_from_document_id(document_url)
    return f"stj-scon-document-{registry}"


def _parse_document_total(items: list[HtmlNode]) -> int:
    if not items:
        return 0
    text = _normalize_spaces(_text(items[0], ".clsNumDocumento"))
    match = re.search(r"Documento\s+\d+\s+de\s+(\d+)", text, re.I)
    return int(match.group(1)) if match else len(items)


def _extract_date(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"\d{2}/\d{2}/\d{4}", value)
    return match.group(0) if match else value


def _parse_pagination(text: str) -> tuple[int, int, int]:
    match = re.search(r"Resultados\s+(\d+)\s+a\s+(\d+)\s+de\s+(\d+)", text, re.I)
    if not match:
        return 0, 0, 0
    start, end, total = (int(match.group(index)) for index in (1, 2, 3))
    return total, start, end


def _text(item: HtmlNode, selector: str) -> str:
    element = item.select_one(selector)
    return element.text(" ", strip=True) if element else ""


def _normalize_label(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label.replace(":", ""))
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return _normalize_spaces(without_accents).lower()


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_registry(anchor: HtmlNode | None) -> str:
    if anchor is None:
        return ""
    href = str(anchor.get("href") or "")
    match = re.search(r"num_registro=(\d+)", href)
    return match.group(1) if match else ""


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    if 'id="resultados"' in lowered or 'class="documento"' in lowered:
        return False
    if "challenge-error-text" in lowered or "cf-error" in lowered:
        return True
    if "verificação automática" in lowered or "verificacao automatica" in lowered:
        return True
    if "enable javascript and cookies to continue" in lowered:
        return True
    if "g-recaptcha" in lowered or "recaptcha_response_token" in lowered:
        return True
    if "captcha" in lowered and "resultado" not in lowered:
        return True
    return False
