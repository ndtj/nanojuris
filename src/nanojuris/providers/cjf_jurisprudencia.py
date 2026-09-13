"""CJF/TRF1 public JSF jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

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
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.parsing import HtmlNode, parse_html
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

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
        self._last_http_metadata: dict[str, Any] = {}
        cjf_host = (
            urlparse(self.config.cjf_trf1_jurisprudencia_url).hostname
            or "jurisprudencia.cjf.jus.br"
        )
        self._document_policy = TransportPolicy(
            allowed_hosts=(cjf_host, "pje2g.trf1.jus.br"),
            timeout_seconds=self.config.timeout,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self.transport = SharedHttpClient(self._document_policy, session=self.session)
        self._document_urls: dict[str, str] = {}

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
        for result in results:
            document_url = result.document_url or result.raw.get("document_url")
            if isinstance(document_url, str) and document_url.startswith("https://"):
                self._document_urls[result.id] = document_url
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

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch an observed public TRF1 document through shared transport."""

        document_url = (
            document_id
            if document_id.startswith("https://")
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "CJF/TRF1 document_id must be an observed official HTTPS URL or a result id"
            )
        parsed = urlparse(document_url)
        allowed_hosts = {
            urlparse(self.config.cjf_trf1_jurisprudencia_url).hostname
            or "jurisprudencia.cjf.jus.br",
            "pje2g.trf1.jus.br",
        }
        if parsed.hostname not in allowed_hosts:
            raise ValueError("CJF/TRF1 document URL is outside the official host allowlist")
        reference = DocumentReference(
            id=document_id,
            source=self.name,
            url=document_url,
            document_type="acordao",
            expected_content_types=("application/pdf", "text/html", "text/plain"),
        )
        return fetch_document_reference(
            reference,
            policy=self._document_policy,
            session=self.session,
            title="CJF/TRF1 Acordao",
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        # The result card carries an observed official PJe2G/HTML link.  Use
        # the same allowlisted document path as ``get_document`` so callers
        # receive a complete decision envelope without inventing a detail
        # endpoint or silently downgrading the record to metadata-only.
        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "text/html",
                }
            ],
            procedural_follow_url=document.url,
            source_trace=document.source_trace,
            raw={"document_url": document.url},
            raw_bytes=document.raw_bytes,
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
            canonical_records=["JurisprudenceResult", "CanonicalDocument", "DecisionBundle"],
            extracted_fields=[
                "id",
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
            supports_full_text=True,
            pagination_mode="local_window",
            completeness_contract="reported_total_and_source_page_window",
            full_text_access="detail_call",
            supports_cli=True,
            # The TRF1 surface is blocked and lacks a promoted detail contract;
            # keep it out of the default federation rather than reporting a
            # false empty result.
            supports_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            supported_filters=["text", "number", "types"],
            filter_semantics={
                "text": "translated",
                "exact_phrase": "translated",
                "number": "translated",
                "types": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "translated",
                **{
                    name: "unsupported"
                    for name in (
                        "courts",
                        "all_words",
                        "any_words",
                        "without_words",
                        "rapporteur",
                        "updated_from",
                        "updated_to",
                        "published_from",
                        "published_to",
                        "case_class",
                        "judging_body",
                        "degree",
                        "instance",
                        "legal_area",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                        "source_origin",
                        "source_origins",
                        "fetch_details",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "precatory_number",
                        "police_document",
                        "cda",
                    )
                },
            },
            limitations=[
                "O provider implementa a superficie TRF1, nao a busca unificada do CJF.",
                "A fonte retorna uma pagina volumosa e o provider limita os resultados locais.",
                "O inteiro teor depende do link oficial observado e e baixado sob demanda.",
            ],
            responsible_use=[
                "Usar page_size pequeno e intervalo entre chamadas.",
                "Preservar origem TRF1, URLs externas e SourceTrace.",
                "Nao persistir cookies, jsessionid ou ViewState.",
            ],
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        request = TransportRequest(
            source=self.name,
            operation=f"search_{method.lower()}",
            method=method,
            url=url,
            data=kwargs.get("data"),
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": self.config.user_agent,
            },
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"CJF/TRF1 jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.TLS_ERROR:
                raise SourceUnavailableError("CJF/TRF1 jurisprudence TLS negotiation failed")
            raise SourceUnavailableError(
                "CJF/TRF1 jurisprudence transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("CJF/TRF1 jurisprudence transport returned no HTTP status")
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
        content = bytes(response.body)
        headers = response.headers
        text = response.text
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": response.content_sha256,
            "response_bytes": len(content),
            "retrieval_status": "ok" if 200 <= response.status_code < 300 else "http_error",
        }
        if _looks_like_access_control(text):
            raise AccessControlRequiredError("CJF/TRF1 jurisprudence returned access-control HTML")
        return text, str(response.final_url or url)


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
                # The route is the official TRF1 appellate collection.  The
                # page does not repeat the degree on every card, so preserve
                # the scope proven by the route and the PJe2G document host
                # explicitly instead of leaving identity in ``raw`` only.
                degree="second",
                instance="second",
                branch="federal",
                authority="TRF1",
                collection="JURISPRUDENCIA",
                document_type=_normalize_type(fields.get("tipo")),
                field_provenance={
                    "authority": {"value": "TRF1", "method": "official_route_scope"},
                    "branch": {"value": "federal", "method": "official_route_scope"},
                    "degree": {"value": "second", "method": "official_route_scope"},
                    "instance": {"value": "second", "method": "official_route_scope"},
                    "collection": {
                        "value": "JURISPRUDENCIA",
                        "method": "official_route_scope",
                    },
                    "document_type": {
                        "value": _normalize_type(fields.get("tipo")),
                        "method": "official_result_field",
                    },
                },
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
