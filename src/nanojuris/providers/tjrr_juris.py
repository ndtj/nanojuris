"""TJRR public JSF/PrimeFaces jurisprudence provider."""

from __future__ import annotations

import hashlib
import html as html_lib
import re
import unicodedata
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

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
    ExtractionTrace,
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
    TransportResponse,
    TransportStatus,
)

CNJ_RAW_PATTERN = re.compile(r"(?<!\d)(\d{7})(\d{2})(\d{4})(\d)(\d{2})(\d{4})(?!\d)")
CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
DOCUMENT_ID_PATTERN = re.compile(r"/(?:inteiroTeor|impressao)\.xhtml\?id=(\d+)")
ROW_COUNT_PATTERN = re.compile(r"rowCount\s*:\s*(\d+)")
ROWS_PATTERN = re.compile(r"rows\s*:\s*(\d+)")
PAGE_COUNT_PATTERN = re.compile(r"\((\d+)\s+of\s+(\d+)\)")
PDF_LINK_PATTERN = re.compile(
    r"(?:href|data)\s*=\s*['\"](?P<href>[^'\"]*/pdf\?id=(?P<id>\d+)[^'\"]*)",
    re.IGNORECASE,
)


class TjrrJurisProvider(JurisprudenceProvider):
    """Provider for TJRR's public JSF/PrimeFaces jurisprudence portal."""

    name = "tjrr_juris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjrr_juris_url).hostname or ""
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

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if not (query.text.strip() or query.number.strip() or query.exact_phrase.strip()):
            raise QueryRejectedError("TJRR exige termo livre, numero ou frase exata")
        if query.degree and _normalize(query.degree) not in {"second", "segundo", "2"}:
            raise QueryRejectedError("TJRR/CJSG aceita apenas grau de segundo grau")
        if query.instance and _normalize(query.instance) not in {"second", "segundo", "2"}:
            raise QueryRejectedError("TJRR/CJSG aceita apenas instancia de segundo grau")
        if query.branch and _normalize(query.branch) not in {"state", "estadual"}:
            raise QueryRejectedError("TJRR pertence ao ramo estadual")
        if query.authority and _normalize(query.authority) not in {
            "tjrr",
            "tribunal de justica de roraima",
        }:
            raise QueryRejectedError("A autoridade solicitada nao corresponde ao TJRR")
        if query.collection and _normalize(query.collection) not in {"cjsg", "jurisprudencia"}:
            raise QueryRejectedError("TJRR expoe a colecao CJSG")

        initial = self._request("GET", "/index.xhtml")
        initial_soup = BeautifulSoup(initial.text, "html.parser")
        form = initial_soup.select_one("form#menuinicial")
        if form is None:
            result_form = initial_soup.select_one("form#formPesquisa")
            if query.page > 1 and result_form is not None and _has_result_markup(initial.text):
                fields: dict[str, str | list[str]] = _hidden_fields(result_form)
                response = self._request_page(
                    initial.text,
                    query,
                    fallback_fields=fields,
                )
                trace = _source_trace(
                    self.name,
                    endpoint=_endpoint_from_response(response, "/index.xhtml"),
                    query={"text": query.text, "number": query.number, "page": query.page},
                    response=response,
                    limitations=[
                        "A fonte usa JSF/PrimeFaces com ViewState e cookies dinamicos por sessao.",
                        (
                            "A pagina foi solicitada a partir da forma publica de resultados "
                            "da sessao."
                        ),
                        (
                            "O provider nao reutiliza cookies, ViewState ou identificadores "
                            "de outra sessao."
                        ),
                    ],
                )
                return parse_tjrr_results(
                    response.text,
                    query=query,
                    trace=trace,
                    base_url=self.config.tjrr_juris_url,
                )
            raise ParserContractChangedError("TJRR nao retornou o formulario publico menuinicial")
        fields = _build_search_fields(form, query)
        action = str(form.get("action") or "/index.xhtml")
        response = self._request("POST", action, data=fields)
        markup = response.text
        if query.page > 1:
            markup = self._request_page(response.text, query, fallback_fields=fields).text
        trace = _source_trace(
            self.name,
            endpoint=_endpoint_from_response(response, "/index.xhtml"),
            query={"text": query.text, "number": query.number, "page": query.page},
            response=response,
            limitations=[
                "A fonte usa JSF/PrimeFaces com ViewState e cookies dinamicos por sessao.",
                "IDs de apresentacao do formulario podem mudar entre versoes do portal.",
                "O provider nao reutiliza cookies, ViewState ou identificadores de outra sessao.",
            ],
        )
        return parse_tjrr_results(
            markup,
            query=query,
            trace=trace,
            base_url=self.config.tjrr_juris_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _parse_document_id(precedent_id)
        endpoint = f"/inteiroTeor.xhtml?id={document_id}"
        response = self._request("GET", endpoint)
        text, metadata = extract_tjrr_document_text(response.text)
        pdf_url = _extract_pdf_url(response.text, document_id)
        trace = _source_trace(
            self.name,
            endpoint="/inteiroTeor.xhtml",
            query={"id": document_id},
            response=response,
            limitations=[
                "O inteiro teor e uma superficie HTML publica separada da busca.",
                "O documento deve ser consultado somente com id observado na fonte.",
            ],
        )
        content_bytes = response.body
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": text,
                    "content_type": "text/plain",
                    "source_content_type": response.headers.get("Content-Type", "text/html"),
                }
            ],
            source_trace=trace,
            raw={
                "document_id": document_id,
                "raw_content_sha256": hashlib.sha256(content_bytes).hexdigest(),
                "raw_content_bytes": len(content_bytes),
                "raw_content_type": response.headers.get("Content-Type", "text/html"),
                "pdf_url": pdf_url,
                **metadata,
            },
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        content = str(bundle.texts[0].get("content") if bundle.texts else "")
        raw = dict(bundle.raw or {})
        access_status = AccessStatus(str(raw.get("access_status") or AccessStatus.PUBLIC.value))
        # TJRR's public detail route is a PDF viewer shell.  The shell itself
        # contains an official ``/pdf?id=...`` link; following that explicit
        # link is part of the documented browser flow and is not an access
        # control bypass.  Older versions returned the shell as an empty
        # document, losing the available full text.
        pdf_url = raw.get("pdf_url")
        if not content.strip() and access_status is AccessStatus.SOURCE_UNAVAILABLE:
            if isinstance(pdf_url, str) and pdf_url:
                pdf_response = self._request("GET", pdf_url)
                if not pdf_response.body.startswith(b"%PDF-"):
                    raise ParserContractChangedError("TJRR PDF link returned a non-PDF response")
                pdf_trace = _source_trace(
                    self.name,
                    endpoint=_endpoint_from_response(pdf_response, "/pdf"),
                    query={"id": _parse_document_id(document_id)},
                    response=pdf_response,
                    limitations=[
                        "PDF oficial obtido pelo link publico exposto no visualizador TJRR.",
                        "O corpo do documento nao e incluido em SourceTrace nem em logs.",
                    ],
                )
                return build_canonical_document(
                    document_id=document_id,
                    source=self.name,
                    document_type="acordao",
                    content=pdf_response.body,
                    content_type=pdf_response.headers.get("Content-Type", "application/pdf"),
                    url=pdf_url,
                    title=f"TJRR inteiro teor {document_id}",
                    source_trace=pdf_trace,
                    access_status=AccessStatus.PUBLIC,
                    raw_metadata={
                        "viewer_url": bundle.source_trace.source_url
                        if bundle.source_trace
                        else None,
                        "pdf_url": pdf_url,
                        "document_id": _parse_document_id(document_id),
                    },
                    parser="tjrr_juris.get_document_pdf",
                    parser_version="1",
                    max_bytes=8_000_000,
                )
        status = (
            ExtractionStatus.UNSUPPORTED_FORMAT
            if access_status is AccessStatus.SOURCE_UNAVAILABLE
            else ExtractionStatus.COMPLETE
            if content.strip()
            else ExtractionStatus.EMPTY
        )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return CanonicalDocument(
            id=document_id,
            source=self.name,
            document_type="acordao",
            content_type="text/plain",
            title=f"TJRR inteiro teor {document_id}",
            text=content,
            url=bundle.source_trace.source_url if bundle.source_trace else None,
            sha256=digest,
            byte_size=len(content.encode("utf-8")),
            retrieved_at=bundle.source_trace.retrieved_at if bundle.source_trace else None,
            access_status=access_status,
            source_trace=bundle.source_trace,
            extraction_trace=ExtractionTrace(
                parser="tjrr_juris.get_document",
                parser_version="1",
                status=status,
                access_status=access_status,
                content_sha256=digest,
                content_bytes=len(content.encode("utf-8")),
                metadata=raw,
            ),
            raw_metadata=raw,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRR Jurisprudencia",
            source_url=self.config.tjrr_juris_url,
            category="court_jurisprudence",
            search_modes=[
                "full_text",
                "summary",
                "case_number",
                "date_range",
                "rapporteur",
                "judging_body",
            ],
            document_types=["acordao", "monocratic_decision"],
            content_formats=["html", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /index.xhtml",
                "POST /index.xhtml (ViewState da sessao publica)",
                "POST AJAX formPesquisa (paginacao PrimeFaces)",
                "GET /inteiroTeor.xhtml?id=<id>",
                "GET /pdf?id=<id> (link oficial exposto pelo visualizador)",
            ],
            supports_full_text=True,
            full_text_access="detail_call",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page_size=10,
            completeness_contract="reported_total_and_page_window",
            supported_filters=[
                "text",
                "number",
                "exact_phrase",
                "rapporteur",
                "judging_body",
                "judgment_date_from",
                "judgment_date_to",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
            ],
            filter_semantics={
                "text": "native",
                "number": "native",
                "exact_phrase": "native",
                "rapporteur": "native",
                "judging_body": "native",
                "judgment_date_from": "native",
                "judgment_date_to": "native",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "case_class": "unsupported",
                "document_type": "validated_scope",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "cda": "unsupported",
                "courts": "unsupported",
                "decision_type": "unsupported",
                "fetch_details": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "types": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "without_words": "unsupported",
            },
            limitations=[
                "Contrato HTML/JSF sujeito a mudancas de markup e ViewState.",
                "Filtros de catalogo devem ser mapeados a partir do formulario atual.",
                "Inteiro teor depende de id publico e da resposta da fonte.",
            ],
            responsible_use=[
                "Usar baixa frequencia e respeitar limites da fonte.",
                "Nao reutilizar cookies, ViewState ou jsessionid entre sessoes.",
                "Nao tentar contornar captcha, login ou controle de acesso.",
            ],
        )

    def _request_page(
        self,
        html: str,
        query: JurisprudenceQuery,
        *,
        fallback_fields: dict[str, str | list[str]],
    ) -> TransportResponse:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.select_one("form#formPesquisa") or soup.select_one("form")
        fields = (
            _form_defaults(form, prefix="formPesquisa")
            if form is not None
            else dict(fallback_fields)
        )
        table = soup.select_one("div[id$=dataTablePesquisa]")
        table_id = str(
            table.get("id") if table is not None else "formPesquisa:j_idt155:dataTablePesquisa"
        )
        rows = _reported_page_size(html) or min(10, max(1, query.page_size))
        for selector in form.select("select[name]") if form is not None else []:
            name = str(selector.get("name") or "")
            if name.endswith("_rppDD"):
                fields[name] = str(rows)
        fields.update(
            {
                "javax.faces.partial.ajax": "true",
                "javax.faces.source": table_id,
                "javax.faces.partial.execute": table_id,
                "javax.faces.partial.render": table_id,
                "javax.faces.behavior.event": "page",
                "javax.faces.partial.event": "page",
                f"{table_id}_pagination": "true",
                f"{table_id}_first": str((query.page - 1) * rows),
                f"{table_id}_rows": str(rows),
                f"{table_id}_skipChildren": "true",
                f"{table_id}_encodeFeature": "true",
                "formPesquisa": "formPesquisa",
            }
        )
        action = str(form.get("action") if form is not None else "/index.xhtml")
        return self._request(
            "POST",
            action,
            data=fields,
            headers={
                "Faces-Request": "partial/ajax",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/xml, text/xml, */*;q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": self.config.tjrr_juris_url.replace("/index.xhtml", ""),
                "Referer": self.config.tjrr_juris_url,
            },
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> TransportResponse:
        url = urljoin(self.config.tjrr_juris_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        request = TransportRequest(
            source=self.name,
            operation="tjrr_request",
            method=method,
            url=url,
            headers=headers,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJRR request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJRR transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJRR transport returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJRR returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJRR requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJRR returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJRR rejected request with HTTP {status_code}")
        if _looks_like_access_control(response.text) and not _has_result_markup(response.text):
            raise AccessControlRequiredError("TJRR returned captcha or access-control HTML")
        return response


def parse_tjrr_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
    source: str = "tjrr_juris",
    court: str = "TJRR",
) -> SearchPage:
    """Parse a TJRR full or PrimeFaces partial response."""

    markup = _extract_partial_markup(html)
    reported_page = _reported_current_page(markup)
    if reported_page is not None and reported_page != query.page:
        raise ParserContractChangedError(
            f"TJRR retornou a pagina {reported_page}, mas a consulta solicitou {query.page}"
        )
    soup = BeautifulSoup(markup, "html.parser")
    roots = soup.select("div[id^=resultados]")
    if not roots:
        if _looks_like_access_control(markup):
            raise AccessControlRequiredError("TJRR returned captcha or access-control HTML")
        if _looks_like_empty_results(markup):
            total = _reported_total(markup)
            complete, reason = page_completeness(
                reported_total=total,
                start=(query.page - 1) * query.page_size + 1,
                returned=0,
                total_is_authoritative=total is not None,
            )
            return SearchPage(
                source=source,
                total=total or 0,
                start=0,
                end=0,
                page=query.page,
                page_size=query.page_size,
                results=[],
                source_trace=trace,
                pagination_mode="page",
                is_complete=complete,
                completeness_reason=reason,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.EMPTY,
                total_known=total is not None,
            )
        raise ParserContractChangedError("TJRR nao retornou containers de jurisprudencia")

    results: list[JurisprudenceResult] = []
    for index, root in enumerate(roots):
        result = _parse_result(root, query=query, trace=trace, base_url=base_url, index=index)
        if result is not None:
            results.append(result)
    if not results:
        raise ParserContractChangedError("TJRR retornou containers sem campos juridicos")
    reported_total = _reported_total(markup)
    total = reported_total if reported_total is not None else len(results)
    actual_page_size = _reported_page_size(markup) or query.page_size
    # PrimeFaces can include more containers than the declared source window.
    # Keep the source-reported page contract instead of leaking extra rows.
    results = results[:actual_page_size]
    start = (query.page - 1) * actual_page_size + 1
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=reported_total is not None,
    )
    return SearchPage(
        source=source,
        total=total,
        start=start,
        end=start + len(results) - 1,
        page=query.page,
        page_size=actual_page_size,
        results=results,
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=reason,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        total_known=reported_total is not None,
    )


def extract_tjrr_document_text(html: str) -> tuple[str, dict[str, Any]]:
    """Extract visible document text and preserve access diagnostics."""

    if _looks_like_access_control(html):
        return "", {
            "access_status": AccessStatus.ACCESS_CONTROL_REQUIRED.value,
            "warnings": ["TJRR document response contains access-control text."],
        }
    if _looks_like_pdf_viewer_notice(html):
        return "", {
            "access_status": AccessStatus.SOURCE_UNAVAILABLE.value,
            "warnings": [
                "TJRR returned a PDF viewer notice instead of the document bytes; "
                "the public detail is unavailable to this client."
            ],
        }
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script, style, noscript"):
        node.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    return text, {
        "access_status": AccessStatus.PUBLIC.value if text else AccessStatus.PARTIAL.value,
        "text_characters": len(text),
    }


def _looks_like_pdf_viewer_notice(value: str) -> bool:
    """Detect the portal's text fallback when a PDF cannot be displayed.

    The response is not a decision and must never be indexed as full text.
    Matching is accent-insensitive because the portal frequently emits a
    legacy encoding with mojibake.
    """

    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    compact = " ".join(normalized.casefold().split())
    return "seu navegad" in compact and "suporte para visualiza" in compact and "pdf" in compact


def _parse_result(
    root: Tag,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
    index: int,
) -> JurisprudenceResult | None:
    process_text = _field_text(root, "PROCESSO")
    case_number = _first_case_number(process_text)
    case_class = _first_line_without_number(process_text)
    rapporteur = _field_text(root, "RELATOR") or None
    judging_body = _field_text(root, "ORGAO JULGADOR") or None
    judgment_date = _field_text(root, "DATA DO JULGAMENTO") or None
    publication_date = _field_text(root, "DATA DA PUBLICACAO") or None
    summary = _field_text(root, "EMENTA") or None
    full_text = _field_text(root, "INTEIRO TEOR") or None
    detail_url = _button_url(root, "inteiroTeor.xhtml")
    print_url = _button_url(root, "impressao.xhtml")
    process_url = _process_url(root)
    document_id = _first_document_id(root)
    if not case_number and not summary and not full_text:
        return None
    stable = (
        document_id
        or case_number
        or hashlib.sha256(
            f"{case_class}|{rapporteur}|{judgment_date}|{publication_date}|{summary}".encode()
        ).hexdigest()[:16]
    )
    return JurisprudenceResult(
        id=f"tjrr-juris-{stable}",
        source="tjrr_juris",
        court="TJRR",
        type="acordao",
        number=case_number,
        summary=summary,
        full_text=full_text,
        rapporteur=rapporteur,
        judgment_date=judgment_date,
        publication_date=publication_date,
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        degree="second",
        instance="second",
        branch="state",
        authority="TJRR",
        collection="CJSG",
        document_type="acordao",
        source_origin="official_portal",
        document_url=detail_url,
        raw={
            "case_class": case_class,
            "judging_body": judging_body,
            "document_id": document_id,
            "document_url": detail_url,
            "print_url": print_url,
            "process_url": process_url,
            "source_query_page": query.page,
        },
    )


def _build_search_fields(form: Tag, query: JurisprudenceQuery) -> dict[str, str | list[str]]:
    fields = _form_defaults(form, prefix="menuinicial")
    text_input = form.select_one("#consultaAtual") or form.select_one("input[name*=':j_idt']")
    if text_input is None or not text_input.get("name"):
        raise ParserContractChangedError("TJRR nao encontrou o campo de termo livre")
    fields[str(text_input["name"])] = query.text or query.exact_phrase or query.number
    submit = form.select_one("button[type=submit][name]")
    if submit is not None:
        fields[str(submit["name"])] = str(submit.get("value") or "")
    _set_labeled_value(
        form, fields, ["numero SISCOM", "numero PROJUDI", "numero do processo"], query.number
    )
    _set_labeled_value(form, fields, ["ementa/indexacao", "ementa/indexação"], query.exact_phrase)
    _set_relator_value(form, fields, query.rapporteur)
    _set_option_value(form, fields, ["orgao julgador", "orgao julgador"], query.judging_body)
    _set_labeled_value(
        form,
        fields,
        ["data inicial"],
        query.judgment_date_from or query.updated_from or query.published_from,
    )
    _set_labeled_value(
        form,
        fields,
        ["data final"],
        query.judgment_date_to or query.updated_to or query.published_to,
    )
    return fields


def _set_option_value(
    form: Tag, fields: dict[str, str | list[str]], labels: list[str], value: str
) -> None:
    """Resolve a human-readable select label to the source option code."""

    if not value:
        return
    wanted = {_normalize(label) for label in labels}
    for label in form.select("label[for]"):
        if not any(item in _normalize(label.get_text(" ", strip=True)) for item in wanted):
            continue
        control = form.select_one(f"#{_css_escape(str(label['for']))}")
        if control is None:
            continue
        for option in control.select("option"):
            if _normalize(option.get_text(" ", strip=True)) == _normalize(value):
                fields[str(control.get("name") or label["for"])] = str(option.get("value") or "")
                return
        raise QueryRejectedError(f"Orgao julgador desconhecido no TJRR: {value}")


def _set_relator_value(form: Tag, fields: dict[str, str | list[str]], value: str) -> None:
    """Resolve the public relator label to its opaque JSF checkbox value."""

    if not value:
        return
    wanted = _normalize(value)
    for checkbox in form.select("input[type=checkbox][name*='relatorList']"):
        checkbox_id = str(checkbox.get("id") or "")
        label = form.find("label", attrs={"for": checkbox_id})
        if label is None or _normalize(label.get_text(" ", strip=True)) != wanted:
            continue
        fields[str(checkbox["name"])] = str(checkbox.get("value") or "")
        return
    raise QueryRejectedError(f"Relator desconhecido no TJRR: {value}")


def _hidden_fields(form: Tag | None) -> dict[str, str | list[str]]:
    if form is None:
        return {}
    fields: dict[str, str | list[str]] = {}
    for input_tag in form.select("input[type=hidden][name]"):
        fields[str(input_tag["name"])] = str(input_tag.get("value") or "")
    return fields


def _form_defaults(form: Tag | None, *, prefix: str) -> dict[str, str | list[str]]:
    """Collect the public JSF form context required by PrimeFaces.

    Hidden fields alone are insufficient for TJRR: the server uses visible
    defaults (collapsed flags and selected options) to reconstruct the
    component tree. Values remain lists for multi-select controls, matching a
    browser's ``application/x-www-form-urlencoded`` submission.
    """

    if form is None:
        return {}
    values: dict[str, list[str]] = {}
    for control in form.select("input[name], select[name], textarea[name]"):
        name = str(control.get("name") or "")
        # JSF's ViewState is global to the form and does not carry the
        # component prefix; it is nevertheless mandatory for every POST.
        if not name.startswith(prefix) and name != "javax.faces.ViewState":
            continue
        control_type = str(control.get("type") or "").lower()
        if control_type in {"submit", "button", "image", "reset"}:
            continue
        if control_type in {"checkbox", "radio"} and not control.has_attr("checked"):
            continue
        if control.name == "select":
            options = control.select("option[selected]") or control.select("option")[:1]
            selected = [str(option.get("value") or "") for option in options]
        else:
            selected = [str(control.get("value") or "")]
        values.setdefault(name, []).extend(selected)
    return {name: entries[0] if len(entries) == 1 else entries for name, entries in values.items()}


def _set_labeled_value(
    form: Tag, fields: dict[str, str | list[str]], labels: list[str], value: str
) -> None:
    if not value:
        return
    normalized_labels = {_normalize(label) for label in labels}
    for label in form.select("label[for]"):
        label_text = _normalize(label.get_text(" ", strip=True))
        if not any(candidate in label_text for candidate in normalized_labels):
            continue
        control = form.select_one(f"#{_css_escape(str(label['for']))}")
        if control is not None and control.get("name"):
            fields[str(control["name"])] = value
            return


def _field_text(root: Tag, label: str) -> str:
    expected = _normalize(label)
    for paragraph in root.select(".docParagrafo"):
        title = paragraph.select_one(".docTitulo")
        if title is None or _normalize(title.get_text(" ", strip=True)).rstrip(":") != expected:
            continue
        text = paragraph.select_one(".docTexto")
        if text is None:
            return ""
        return " ".join(text.get_text(" ", strip=True).split())
    return ""


def _button_url(root: Tag, path: str) -> str | None:
    for button in root.select("button[onclick]"):
        onclick = str(button.get("onclick") or "")
        match = re.search(
            r"abrirJanela\(['\"]([^'\"]*" + re.escape(path) + r"[^'\"]*)['\"]", onclick
        )
        if match:
            return html_lib.unescape(match.group(1))
    return None


def _process_url(root: Tag) -> str | None:
    for button in root.select("button[onclick]"):
        match = re.search(r"extrato-processo\?p=([0-9]+)", str(button.get("onclick") or ""))
        if match:
            return (
                f"https://estatistica.tjrr.jus.br/estatistica/extrato-processo?p={match.group(1)}"
            )
    return None


def _first_document_id(root: Tag) -> str | None:
    for button in root.select("button[onclick]"):
        match = DOCUMENT_ID_PATTERN.search(html_lib.unescape(str(button.get("onclick") or "")))
        if match:
            return match.group(1)
    return None


def _first_case_number(value: str) -> str | None:
    match = CNJ_PATTERN.search(value)
    if match:
        return match.group(0)
    raw_match = CNJ_RAW_PATTERN.search(value)
    if raw_match:
        groups = raw_match.groups()
        return f"{groups[0]}-{groups[1]}.{groups[2]}.{groups[3]}.{groups[4]}.{groups[5]}"
    return None


def _first_line_without_number(value: str) -> str | None:
    number_match = CNJ_PATTERN.search(value)
    if number_match:
        before = value[: number_match.start()].strip()
        return before or None
    raw_match = CNJ_RAW_PATTERN.search(value)
    if raw_match:
        before = value[: raw_match.start()].strip()
        return before or None
    for line in (part.strip() for part in value.splitlines()):
        if (
            line
            and not CNJ_PATTERN.search(line)
            and not CNJ_RAW_PATTERN.search(re.sub(r"\D", "", line))
        ):
            return line
    return None


def _reported_total(markup: str) -> int | None:
    match = ROW_COUNT_PATTERN.search(markup)
    if match:
        return int(match.group(1))
    return None


def _reported_page_size(markup: str) -> int | None:
    match = ROWS_PATTERN.search(markup)
    if match:
        return int(match.group(1))
    return None


def _reported_current_page(markup: str) -> int | None:
    match = PAGE_COUNT_PATTERN.search(markup)
    return int(match.group(1)) if match else None


def _extract_partial_markup(markup: str) -> str:
    if "<partial-response" not in markup:
        return markup
    updates = re.findall(r"<!\[CDATA\[(.*?)\]\]>", markup, flags=re.DOTALL)
    return "\n".join(update for update in updates if "resultados" in update) or markup


def _looks_like_empty_results(markup: str) -> bool:
    lowered = _normalize(markup)
    return any(
        value in lowered for value in ("nenhum resultado", "nenhum registro", "0 resultados")
    )


def _looks_like_access_control(markup: str) -> bool:
    lowered = _normalize(markup)
    return any(value in lowered for value in ("captcha", "recaptcha", "acesso negado", "login"))


def _has_result_markup(markup: str) -> bool:
    return bool(re.search(r"id\s*=\s*['\"]resultados", markup, flags=re.IGNORECASE))


def _normalize(value: str) -> str:
    without_marks = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    return " ".join(without_marks.casefold().replace("\xa0", " ").split())


def _css_escape(value: str) -> str:
    return value.replace(":", "\\:")


def _parse_document_id(precedent_id: str) -> str:
    match = re.fullmatch(r"tjrr-juris-(\d+)", precedent_id)
    if not match:
        raise ParserContractChangedError("TJRR id deve usar tjrr-juris-<id>")
    return match.group(1)


def _extract_pdf_url(markup: str, document_id: str) -> str | None:
    """Extract the official PDF link from TJRR's viewer shell.

    The viewer can contain unrelated assets, so require both the expected
    ``/pdf`` route and the observed decision id.  Relative links are returned
    as absolute HTTPS URLs and are later checked by the allowlisted transport.
    """

    for match in PDF_LINK_PATTERN.finditer(markup):
        if match.group("id") != document_id:
            continue
        href = html_lib.unescape(match.group("href"))
        parsed = urlparse(href)
        if not parsed.scheme:
            return urljoin("https://jurisprudencia.tjrr.jus.br/", href.lstrip("/"))
        if parsed.scheme == "https" and parsed.hostname == "jurisprudencia.tjrr.jus.br":
            return href
    return None


def _endpoint_from_response(response: TransportResponse, fallback: str) -> str:
    parsed = urlparse(str(response.final_url or response.url or ""))
    return parsed.path or fallback


def _source_trace(
    provider: str,
    *,
    endpoint: str,
    query: dict[str, Any],
    response: TransportResponse,
    limitations: list[str],
) -> SourceTrace:
    content = bytes(response.body or b"")
    if not content:
        content = response.text.encode("utf-8")
    status_code = response.status_code
    return SourceTrace(
        provider=provider,
        endpoint=endpoint,
        query=query,
        source_url=str(response.final_url or response.url or "") or None,
        limitations=limitations,
        http_status=status_code,
        final_url=str(response.final_url or response.url or "") or None,
        content_type=response.headers.get("Content-Type") if response.headers else None,
        content_sha256=hashlib.sha256(content).hexdigest(),
        response_bytes=len(content),
        elapsed_ms=response.elapsed_ms,
        retrieval_status="ok"
        if status_code is not None and 200 <= status_code < 300
        else "http_error",
    )
