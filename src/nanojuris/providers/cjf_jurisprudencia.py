"""CJF/TRF1 public JSF jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
import unicodedata
from typing import Any
from urllib.parse import urljoin

import requests
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
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
from nanojuris.parsing import HtmlDocument, HtmlNode, parse_html

SEARCH_PATH = "/trf1/index.xhtml"
PROCESS_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
TOTAL_RE = re.compile(r"Exibindo\s+\d+\s*-\s*\d+\s+de\s+(\d+)", re.I)


class CjfJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TRF1 surface hosted by the CJF."""

    name = "cjf_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0
        self._last_http_metadata: dict[str, Any] = {}

    @property
    def base_url(self) -> str:
        return self.config.cjf_trf1_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = (query.text or query.exact_phrase or query.number).strip()
        if not term:
            raise ValueError("CJF/TRF1 jurisprudence search requires a term or number")
        initial_html, initial_url = self._request("GET", SEARCH_PATH)
        payload = _build_jsf_payload(initial_html, query)
        html, source_url = self._request("POST", SEARCH_PATH, data=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=SEARCH_PATH,
            query={**payload, "javax.faces.ViewState": "<session-view-state>"},
            source_url=source_url or initial_url,
            limitations=[
                "O ViewState e dinamico e obtido somente da sessao atual.",
                "A superficie implementada e TRF1; a busca unificada permanece separada.",
                "Links PJe/arquivo sao preservados, mas detalhe individual ainda nao foi "
                "promovido.",
            ],
            **self._last_http_metadata,
        )
        results, total = parse_cjf_results(html, trace=trace)
        page_size = _page_size(query.page_size)
        limited = results[:page_size]
        return SearchPage(
            source=self.name,
            total=total or len(results),
            start=1 if limited else 0,
            end=len(limited) if limited else 0,
            page=1,
            page_size=page_size,
            results=limited,
            source_trace=trace,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "CJF/TRF1 retorna ementa e links externos, mas a rota de detalhe individual "
            "ainda nao possui contrato promovido."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="CJF Jurisprudencia TRF1",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "document_type"],
            document_types=["acordao", "sumula", "arguicao", "decisao_monocratica"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "origin",
                "judging_body",
                "judgment_date",
                "publication_date",
                "publication_source",
                "summary",
                "decision",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET /trf1/index.xhtml", "POST /trf1/index.xhtml"],
            supports_full_text=False,
            pagination_mode="local_window",
            completeness_contract="reported_total_and_source_page_window",
            full_text_access="link_only",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            supported_filters=["text", "number", "types"],
            limitations=[
                "O provider implementa a superficie TRF1, nao a busca unificada do CJF.",
                "A fonte retorna uma pagina volumosa e o provider limita os resultados locais.",
                "Inteiro teor externo nao e inferido nem baixado sem contrato individual.",
            ],
            responsible_use=[
                "Usar page_size pequeno e intervalo entre chamadas.",
                "Preservar origem TRF1, URLs externas e SourceTrace.",
                "Nao persistir cookies, jsessionid ou ViewState.",
            ],
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        try:
            response = self.session.request(
                method,
                url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
                verify=self.config.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"CJF/TRF1 jurisprudence request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("CJF/TRF1 jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("CJF/TRF1 jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"CJF/TRF1 jurisprudence returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(f"CJF/TRF1 rejected HTTP {response.status_code}")
        response.encoding = response.encoding or "utf-8"
        content = bytes(getattr(response, "content", b"") or b"")
        if not content:
            content = response.text.encode(response.encoding or "utf-8", errors="replace")
        headers = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(getattr(response, "url", url) or url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if 200 <= response.status_code < 300 else "http_error",
        }
        if _looks_like_access_control(response.text):
            raise AccessControlRequiredError("CJF/TRF1 jurisprudence returned access-control HTML")
        return response.text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_cjf_results(html: str, *, trace: SourceTrace) -> tuple[list[JurisprudenceResult], int]:
    """Parse TRF1 semantic result tables and their total count."""

    document = parse_html(html)
    tables = document.select("table.table_resultado")
    if not tables:
        text = document.get_text(" ", strip=True)
        if "Nenhum resultado" in text:
            return [], 0
        raise ParserContractChangedError("CJF/TRF1 result tables not found")
    results: list[JurisprudenceResult] = []
    for table in tables:
        fields = _table_fields(table)
        number = _first_process_number(fields.get("numero", ""))
        if not number:
            continue
        publication_date = fields.get("data_da_publicacao") or fields.get("data da publicacao")
        document_url = _first_href(table, "Acesse Aqui")
        results.append(
            JurisprudenceResult(
                id=_stable_cjf_id(number, fields, document_url),
                source="cjf_jurisprudencia",
                court="TRF1",
                type=_normalize_type(fields.get("tipo")),
                number=number,
                summary=fields.get("ementa"),
                rapporteur=fields.get("relator(a)"),
                updated_at=publication_date or fields.get("data"),
                judgment_date=fields.get("data"),
                publication_date=publication_date,
                access_status=AccessStatus.PUBLIC,
                source_trace=trace,
                raw={
                    **fields,
                    "case_class": fields.get("classe"),
                    "judging_body": fields.get("orgao_julgador"),
                    "publication_date": publication_date,
                    "judgment_date": fields.get("data"),
                    "document_url": document_url,
                    "source_court": fields.get("origem") or "TRF1",
                },
            )
        )
    if not results:
        raise ParserContractChangedError("CJF/TRF1 result tables contain no decisions")
    match = TOTAL_RE.search(document.get_text(" ", strip=True))
    return results, int(match.group(1)) if match else len(results)


def _build_jsf_payload(html: str, query: JurisprudenceQuery) -> dict[str, Any]:
    document = parse_html(html)
    form = document.select_one("form#formulario") or document.select_one("form")
    payload: dict[str, Any] = {}
    if form:
        for node in form.css("input, select, textarea"):
            name = str(node.get("name") or "")
            if not name or node.get("type") in {"submit", "button"}:
                continue
            if node.tag.casefold() == "select":
                selected = [
                    item.get("value", "")
                    for item in node.css("option[selected]")
                    if item.get("value") is not None
                ]
                if selected:
                    payload[name] = selected
            else:
                payload[name] = node.get("value", "")
    payload["formulario:textoLivre"] = query.text or query.exact_phrase or query.number
    payload["formulario:actPesquisar"] = "Pesquisar"
    payload["formulario:selectTiposDocumento"] = query.types or ["ACORDAO"]
    return payload


def _table_fields(table: HtmlNode) -> dict[str, str]:
    fields: dict[str, str] = {}
    for label in table.css("span.label_pontilhada"):
        key = _normalize_key(label.text(" ", strip=True))
        wrapper = label.find_parent("div")
        rows = wrapper.css("tr") if wrapper else []
        if key and len(rows) >= 2:
            fields[key] = _clean_text(rows[-1].text(" ", strip=True))
    return fields


def _first_href(table: HtmlNode, text: str) -> str | None:
    for link in table.css("a[href]"):
        if text.lower() in link.text(" ", strip=True).lower():
            href = link.get("href")
            if href:
                return href
    return None


def _first_process_number(value: str) -> str | None:
    match = PROCESS_RE.search(value)
    return match.group(0) if match else None


def _normalize_type(value: str | None) -> str:
    normalized = _clean_text(value or "").lower()
    return {
        "acórdão": "acordao",
        "acordao": "acordao",
        "decisão monocrática": "decisao_monocratica",
    }.get(normalized, normalized or "jurisprudencia")


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9()]+", "_", normalized).strip("_")


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 50))


def _stable_cjf_id(number: str, fields: dict[str, str], document_url: str | None) -> str:
    """Build an identity independent of result-table ordering."""

    identity = "|".join(
        [
            number,
            fields.get("tipo", ""),
            fields.get("data", ""),
            fields.get("data_da_publicacao", fields.get("data da publicacao", "")),
            document_url or "",
        ]
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"cjf-trf1-{digest}"


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    markers = (
        "captcha",
        "recaptcha",
        "acesso negado",
        "verificacao automatica",
        "enable javascript and cookies",
    )
    return any(marker in lowered for marker in markers) and "table_resultado" not in lowered
