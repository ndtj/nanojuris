"""TJRR public JSF/PrimeFaces jurisprudence provider."""

from __future__ import annotations

import hashlib
import html as html_lib
import re
import time
import unicodedata
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

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
from nanojuris.providers.base import JurisprudenceProvider

CNJ_RAW_PATTERN = re.compile(r"(?<!\d)(\d{7})(\d{2})(\d{4})(\d)(\d{2})(\d{4})(?!\d)")
CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
DOCUMENT_ID_PATTERN = re.compile(r"/(?:inteiroTeor|impressao)\.xhtml\?id=(\d+)")
ROW_COUNT_PATTERN = re.compile(r"rowCount\s*:\s*(\d+)")
ROWS_PATTERN = re.compile(r"rows\s*:\s*(\d+)")
PAGE_COUNT_PATTERN = re.compile(r"\((\d+)\s+of\s+(\d+)\)")


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
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if not (query.text.strip() or query.number.strip() or query.exact_phrase.strip()):
            raise QueryRejectedError("TJRR exige termo livre, numero ou frase exata")

        initial = self._request("GET", "/index.xhtml")
        initial_soup = BeautifulSoup(initial.text, "html.parser")
        form = initial_soup.select_one("form#menuinicial")
        if form is None:
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
        content_bytes = response.content
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
                **metadata,
            },
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        content = str(bundle.texts[0].get("content") if bundle.texts else "")
        raw = dict(bundle.raw or {})
        access_status = AccessStatus(str(raw.get("access_status") or AccessStatus.PUBLIC.value))
        status = ExtractionStatus.COMPLETE if content.strip() else ExtractionStatus.EMPTY
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
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            supported_filters=[
                "text",
                "number",
                "exact_phrase",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
            ],
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
        fallback_fields: dict[str, str],
    ) -> requests.Response:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.select_one("form#formPesquisa") or soup.select_one("form")
        fields = _hidden_fields(form) if form is not None else dict(fallback_fields)
        table = soup.select_one("div[id$=dataTablePesquisa]")
        table_id = str(
            table.get("id") if table is not None else "formPesquisa:j_idt155:dataTablePesquisa"
        )
        rows = min(30, max(1, query.page_size))
        fields.update(
            {
                "javax.faces.partial.ajax": "true",
                "javax.faces.source": table_id,
                "javax.faces.partial.execute": table_id,
                "javax.faces.partial.render": table_id,
                "javax.faces.behavior.event": "page",
                f"{table_id}_pagination": "true",
                f"{table_id}_first": str((query.page - 1) * rows),
                f"{table_id}_rows": str(rows),
            }
        )
        action = str(form.get("action") if form is not None else "/index.xhtml")
        return self._request(
            "POST",
            action,
            data=fields,
            headers={
                "Faces-Request": "partial/ajax",
                "Accept": "application/xml, text/xml, */*;q=0.01",
            },
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        self._respect_rate_limit()
        url = urljoin(self.config.tjrr_juris_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJRR request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJRR returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJRR returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TJRR rejected request with HTTP {response.status_code}")
        if _looks_like_access_control(response.text) and not _has_result_markup(response.text):
            raise AccessControlRequiredError("TJRR returned captcha or access-control HTML")
        return response

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


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
            )
        raise ParserContractChangedError("TJRR nao retornou containers de jurisprudencia")

    results: list[JurisprudenceResult] = []
    for index, root in enumerate(roots):
        result = _parse_result(root, query=query, trace=trace, base_url=base_url, index=index)
        if result is not None:
            results.append(result)
    if not results:
        raise ParserContractChangedError("TJRR retornou containers sem campos juridicos")
    total = _reported_total(markup) or len(results)
    actual_page_size = _reported_page_size(markup) or query.page_size
    start = (query.page - 1) * actual_page_size + 1
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=_reported_total(markup) is not None,
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
    )


def extract_tjrr_document_text(html: str) -> tuple[str, dict[str, Any]]:
    """Extract visible document text and preserve access diagnostics."""

    if _looks_like_access_control(html):
        return "", {
            "access_status": AccessStatus.ACCESS_CONTROL_REQUIRED.value,
            "warnings": ["TJRR document response contains access-control text."],
        }
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script, style, noscript"):
        node.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    return text, {
        "access_status": AccessStatus.PUBLIC.value if text else AccessStatus.PARTIAL.value,
        "text_characters": len(text),
    }


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
            f"{case_class}|{rapporteur}|{judgment_date}|{summary}|{index}".encode()
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


def _build_search_fields(form: Tag, query: JurisprudenceQuery) -> dict[str, str]:
    fields = _hidden_fields(form)
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
    _set_labeled_value(form, fields, ["data inicial"], query.updated_from or query.published_from)
    _set_labeled_value(form, fields, ["data final"], query.updated_to or query.published_to)
    return fields


def _hidden_fields(form: Tag | None) -> dict[str, str]:
    if form is None:
        return {}
    fields: dict[str, str] = {}
    for input_tag in form.select("input[type=hidden][name]"):
        fields[str(input_tag["name"])] = str(input_tag.get("value") or "")
    return fields


def _set_labeled_value(form: Tag, fields: dict[str, str], labels: list[str], value: str) -> None:
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


def _endpoint_from_response(response: requests.Response, fallback: str) -> str:
    parsed = urlparse(str(getattr(response, "url", "") or ""))
    return parsed.path or fallback


def _source_trace(
    provider: str,
    *,
    endpoint: str,
    query: dict[str, Any],
    response: requests.Response,
    limitations: list[str],
) -> SourceTrace:
    content = bytes(getattr(response, "content", b"") or b"")
    if not content:
        content = str(getattr(response, "text", "")).encode("utf-8")
    return SourceTrace(
        provider=provider,
        endpoint=endpoint,
        query=query,
        source_url=str(getattr(response, "url", "") or "") or None,
        limitations=limitations,
        http_status=int(getattr(response, "status_code", 0) or 0) or None,
        final_url=str(getattr(response, "url", "") or "") or None,
        content_type=response.headers.get("Content-Type") if response.headers else None,
        content_sha256=hashlib.sha256(content).hexdigest(),
        response_bytes=len(content),
        retrieval_status="ok" if 200 <= response.status_code < 300 else "http_error",
    )
