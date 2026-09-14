"""TJAP Banco de Sentenças public first-instance decision bank.

The source is a public Livewire application.  This adapter follows the same
bounded browser protocol (GET snapshot, dispatch a filter event, optionally
dispatch the documented pagination action) without attempting to solve or
evade any challenge.  It is deliberately separate from the blocked Tucujuris
appellate search.
"""

from __future__ import annotations

import hashlib
import html as html_module
import json
import re
import time
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
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

_CARD_SELECTOR = "div.w-full.mx-auto.shadow-lg.bg-white.border.border-gray-200.rounded-lg"
_CNJ_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.8\.03\.\d{4}\b")
_READER_RE = re.compile(
    r"https://bancosentencas\.tjap\.jus\.br/reader/TUCUJURIS/(?P<id>\d+)\?tipo=(?P<type>banco-(?:decisao|sentenca))",
    re.I,
)
_TOTAL_RE = re.compile(
    r"exibindo\s+(?P<start>[\d.]+)\s+at[eé]\s+(?P<end>[\d.]+)\s+de\s+(?P<total>[\d.]+)",
    re.I,
)


class TjapBancoSentencasProvider(JurisprudenceProvider):
    """Public TJAP Banco de Sentenças (CJPG) provider."""

    name = "tjap_banco_sentencas"
    authority = "TJAP"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjap_banco_sentencas_url).hostname or ""
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
        self._last_request: float = 0.0  # legacy fallback retained for compatibility
        self._last_http: dict[str, Any] = {}
        self._observed_documents: dict[str, str] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjap_banco_sentencas_url.rstrip("/")

    @property
    def livewire_url(self) -> str:
        return f"{self.base_url}/livewire-53cc04b2/update"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_scope(query)
        snapshot, csrf = self._initial_component()
        filters = _build_filters(query)
        component = self._call(
            snapshot,
            csrf,
            {
                "path": "",
                "method": "__dispatch",
                "params": ["update-filters", {"filters": filters}],
            },
        )
        if query.page > 1:
            component = self._call(
                component["snapshot"],
                csrf,
                {"path": "", "method": "gotoPage", "params": [query.page, "page"]},
            )
        effects = component.get("effects") or {}
        markup = str(effects.get("html") or "")
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /livewire-53cc04b2/update",
            query={"page": query.page, "page_size": query.page_size, "filters": filters},
            source_url=self.livewire_url,
            **self._last_http,
            limitations=[
                "Banco oficial de sentenças/decisões de primeiro grau; não representa "
                "o acervo CJSG.",
                "Registros sigilosos podem expor apenas a mensagem pública de indisponibilidade.",
                "O total exibido pela fonte pode ser aproximado e é preservado como desconhecido.",
            ],
        )
        page = parse_tjap_banco_sentencas(markup, query=query, trace=trace, base_url=self.base_url)
        self._observed_documents.update(
            {result.id: result.document_url for result in page.results if result.document_url}
        )
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": "text/plain",
                    "source_content_type": document.content_type,
                }
            ],
            procedural_follow_url=document.url,
            source_trace=document.source_trace,
            raw={"document_url": document.url, "access_status": document.access_status.value},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        url = self._observed_documents.get(document_id)
        if url is None:
            if _READER_RE.fullmatch(document_id.strip()):
                url = document_id.strip()
            else:
                raise QueryRejectedError(
                    "TJAP documento deve ser um ID observado ou URL pública do leitor"
                )
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc.lower() != "bancosentencas.tjap.jus.br":
            raise QueryRejectedError("TJAP documento fora do host oficial permitido")
        markup = self._request("GET", url)
        soup = BeautifulSoup(markup, "html.parser")
        for node in soup(["script", "style", "noscript"]):
            node.decompose()
        text = _normalize_text(soup.get_text(" ", strip=True))
        if not text:
            raise ParserContractChangedError("TJAP leitor retornou documento sem texto público")
        content = text.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /reader/TUCUJURIS/<id>",
            query={"document_id": document_id},
            source_url=url,
            **self._last_http,
            transformations=["html_visible_text"],
        )
        return CanonicalDocument(
            id=document_id,
            source=self.name,
            document_type="decisao",
            content_type="text/html",
            title=f"TJAP Banco de Sentenças {document_id}",
            text=text,
            raw_bytes=markup.encode("utf-8"),
            url=url,
            sha256=digest,
            byte_size=len(content),
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
            source_trace=trace,
            extraction_trace=ExtractionTrace(
                parser=f"{self.name}.reader",
                parser_version="1",
                status=ExtractionStatus.COMPLETE,
                access_status=AccessStatus.PUBLIC,
                content_sha256=digest,
                content_bytes=len(content),
                transformations=["html_visible_text"],
            ),
            raw_metadata={"reader_url": url},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        # Keep the cross-provider contract explicit.  These filters are not
        # accepted by the public Banco de Sentenças route; declaring them as
        # unsupported is materially different from silently treating them as
        # native (or leaving them unverified).
        unsupported_filters = [
            "courts",
            "rapporteur",
            "party_name",
            "party_document",
            "lawyer_name",
            "oab",
            "degree",
            "instance",
            "branch",
            "authority",
            "collection",
            "document_type",
            "decision_type",
            "all_words",
            "any_words",
            "without_words",
            "updated_from",
            "updated_to",
            "published_from",
            "published_to",
            "source_origin",
            "source_origins",
            "fetch_details",
            "legal_area",
            "precatory_number",
            "police_document",
            "cda",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAP Banco de Sentenças (CJPG)",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=[
                "text",
                "exact_phrase",
                "case_number",
                "case_class",
                "judging_body",
                "date_range",
            ],
            document_types=["decisao", "sentenca"],
            content_formats=["html", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="official first-degree unit (vara, juizado, comarca or ofício)",
            extracted_fields=[
                "case_number",
                "case_class",
                "subject",
                "judging_body",
                "rapporteur",
                "judgment_date",
                "summary",
                "full_text",
                "document_url",
                "degree",
                "instance",
                "collection",
                "decision_type",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /", "POST /livewire-53cc04b2/update", "GET /reader/TUCUJURIS/<id>"],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            # A rota pública passou os gates técnicos; a limitação de acervo
            # curado permanece explícita no contrato, sem impedir a federação.
            supports_unified_search=True,
            opt_in_unified_search=True,
            pagination_mode="livewire_page",
            max_remote_page=25,
            max_remote_page_size=10,
            completeness_contract="source_window_with_approximate_total",
            full_text_access="inline",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "case_class",
                "judging_body",
                "types",
                "judgment_date_from",
                "judgment_date_to",
                "page",
            ],
            unsupported_filters=unsupported_filters,
            filter_semantics={
                "text": "native",
                "exact_phrase": "native",
                "number": "local_postfilter",
                "case_class": "translated",
                "judging_body": "translated",
                "types": "translated",
                "judgment_date_from": "translated",
                "judgment_date_to": "translated",
                "page": "native",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                **{name: "unsupported" for name in unsupported_filters},
            },
            ordering_modes=["source_order"],
            detail_modes=["reader_html"],
            limitations=[
                "O banco é uma coleção oficial de decisões/sentenças selecionadas, "
                "não garantia de todo o acervo do TJAP.",
                "Texto sigiloso permanece parcial quando a fonte não o publica.",
                "Filtros de classe/órgão dependem dos valores oficiais disponíveis no snapshot.",
            ],
            responsible_use=[
                "Usar chamadas bounded e respeitar limites da fonte.",
                "Não tentar acessar conteúdo sigiloso ou resolver desafios.",
            ],
        )

    def _initial_component(self) -> tuple[str, str]:
        markup = self._request("GET", "/")
        soup = BeautifulSoup(markup, "html.parser")
        component = soup.select_one("[wire\\:snapshot]")
        csrf_node = soup.select_one("[data-csrf]")
        snapshot = component.get("wire:snapshot") if component else None
        csrf = csrf_node.get("data-csrf") if csrf_node else None
        if not snapshot or not csrf:
            raise ParserContractChangedError(
                "TJAP não expôs snapshot Livewire/CSRF público esperado"
            )
        return str(snapshot), str(csrf)

    def _call(self, snapshot: str, csrf: str, call: dict[str, Any]) -> dict[str, Any]:
        payload = {"components": [{"snapshot": snapshot, "updates": {}, "calls": [call]}]}
        markup = self._request("POST", self.livewire_url, json=payload, csrf=csrf)
        try:
            body = json.loads(markup)
            component = body["components"][0]
            if not component.get("snapshot") or "effects" not in component:
                raise KeyError("component contract")
            return component
        except (ValueError, KeyError, TypeError) as exc:
            raise ParserContractChangedError(
                "TJAP resposta Livewire sem componente/effects"
            ) from exc

    def _request(self, method: str, path: str, *, csrf: str | None = None, **kwargs: Any) -> str:
        url = (
            path if path.startswith("https://") else urljoin(self.base_url + "/", path.lstrip("/"))
        )
        headers = {
            "Accept": "application/json" if method == "POST" else "text/html,application/xhtml+xml"
        }
        if csrf:
            headers.update(
                {"X-Livewire": "", "X-CSRF-TOKEN": csrf, "Content-Type": "application/json"}
            )
        request = TransportRequest(
            source=self.name,
            operation="livewire_request",
            method=method,
            url=url,
            headers=headers,
            json_body=kwargs.pop("json", None),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except SourceUnavailableError:
            raise
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJAP Banco de SentenÃ§as request failed") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                "TJAP Banco de SentenÃ§as transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TJAP Banco de SentenÃ§as transport returned no status")
        body = bytes(response.body)
        self._last_http = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "response_bytes": len(body),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJAP Banco de SentenÃ§as returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(
                f"TJAP Banco de SentenÃ§as returned HTTP {response.status_code}"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"TJAP Banco de SentenÃ§as returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJAP Banco de SentenÃ§as returned HTTP {response.status_code}"
            )
        return body.decode("utf-8", errors="replace")

    def _request_legacy(
        self, method: str, path: str, *, csrf: str | None = None, **kwargs: Any
    ) -> str:
        elapsed = time.monotonic() - self._last_request
        if self.config.rate_limit_interval > elapsed:
            time.sleep(self.config.rate_limit_interval - elapsed)
        url = (
            path if path.startswith("https://") else urljoin(self.base_url + "/", path.lstrip("/"))
        )
        headers = {
            "Accept": "application/json" if method == "POST" else "text/html,application/xhtml+xml"
        }
        if csrf:
            headers.update(
                {"X-Livewire": "", "X-CSRF-TOKEN": csrf, "Content-Type": "application/json"}
            )
        try:
            response = self.session.request(
                method, url, headers=headers, timeout=self.config.timeout, **kwargs
            )
        except requests.exceptions.Timeout as exc:
            raise SourceUnavailableError("TJAP Banco de Sentenças timeout") from exc
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError("TJAP Banco de Sentenças TLS failure") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJAP Banco de Sentenças request failed") from exc
        self._last_request = time.monotonic()
        body = bytes(response.content or b"")
        self._last_http = {
            "http_status": response.status_code,
            "final_url": str(response.url or url),
            "content_type": response.headers.get("Content-Type"),
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "response_bytes": len(body),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJAP Banco de Sentenças returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(
                f"TJAP Banco de Sentenças returned HTTP {response.status_code}"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"TJAP Banco de Sentenças returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJAP Banco de Sentenças returned HTTP {response.status_code}"
            )
        return body.decode(response.encoding or "utf-8", errors="replace")


def parse_tjap_banco_sentencas(
    markup: str, *, query: JurisprudenceQuery, trace: SourceTrace, base_url: str
) -> SearchPage:
    """Parse Livewire ``effects.html`` into first-degree canonical results."""

    if not markup.strip():
        raise ParserContractChangedError("TJAP Livewire retornou HTML vazio")
    lowered = markup.casefold()
    if "turnstile" in lowered or "cloudflare ray id" in lowered or "just a moment" in lowered:
        raise AccessControlRequiredError("TJAP Banco de Sentenças retornou página protegida")
    soup = BeautifulSoup(markup, "html.parser")
    cards = soup.select(_CARD_SELECTOR)
    total_match = _TOTAL_RE.search(_normalize_text(soup.get_text(" ", strip=True)))
    total = int(total_match.group("total").replace(".", "")) if total_match else 0
    total_known = bool(
        total_match and "aproxim" not in _normalize_text(soup.get_text(" ", strip=True)).casefold()
    )
    if not cards:
        if total_match and total > 0:
            raise ParserContractChangedError(
                "TJAP informou resultados, mas nenhum cartão foi encontrado"
            )
        return SearchPage(
            source="tjap_banco_sentencas",
            total=0,
            start=0,
            end=0,
            page=query.page,
            page_size=query.page_size,
            results=[],
            source_trace=trace,
            pagination_mode="livewire_page",
            is_complete=True,
            completeness_reason="fonte não informou cartões para a consulta",
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.EMPTY,
        )
    results = [
        r for card in cards if (r := _parse_card(card, trace=trace, base_url=base_url)) is not None
    ]
    if not results:
        raise ParserContractChangedError("TJAP cartões não continham identidade de primeiro grau")
    start = ((query.page - 1) * query.page_size) + 1
    results = results[: query.page_size]
    return SearchPage(
        source="tjap_banco_sentencas",
        total=total or len(results),
        start=start,
        end=start + len(results) - 1,
        page=query.page,
        page_size=query.page_size,
        results=results,
        source_trace=trace,
        pagination_mode="livewire_page",
        is_complete=not total_match or (total_known and start + len(results) - 1 >= total),
        completeness_reason="total da fonte" if total_match else "total remoto não informado",
        ordering="source_order",
        filters_applied=_filters_applied(query),
        total_known=total_known,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
    )


def _parse_card(card: Tag, *, trace: SourceTrace, base_url: str) -> JurisprudenceResult | None:
    values: dict[str, str] = {}
    for dt in card.select("dt"):
        dd = dt.find_next_sibling("dd")
        if dd:
            values[_normalize_text(dt.get_text(" ", strip=True)).casefold()] = _normalize_text(
                dd.get_text(" ", strip=True)
            )
    # HTML may be decoded as UTF-8 or as the legacy mojibake labels emitted by
    # older TJAP templates.  Keep one ASCII lookup key for both variants.
    for alias in ("órgão", "Ã³rgÃ£o"):
        if alias in values:
            values["orgao"] = values[alias]
    for alias in ("nº processo", "nÂº processo"):
        if alias in values:
            values["nÂº processo"] = values[alias]
    body = values.get("órgão") or values.get("orgao") or ""
    if not _is_first_degree_unit(body):
        return None
    number = (
        values.get("nº processo")
        or values.get("no processo")
        or _first_match(_CNJ_RE, card.get_text(" ", strip=True))
    )
    if not number:
        return None
    reader_match = _READER_RE.search(str(card))
    if not reader_match:
        return None
    reader_url = reader_match.group(0)
    identifier = reader_match.group("id")
    title = _normalize_text((card.select_one("h2") or card).get_text(" ", strip=True))
    decision_type = "sentenca" if "senten" in title.casefold() else "decisao"
    # ``textToCopy`` is the source's clean copy and avoids highlight spans
    # inserted into the visible card. Prefer it, then fall back to an
    # expanded block or the labeled field used by older templates.
    full_text = (
        _extract_rtf_text(card) or _extract_visible_teor(card) or values.get("teor do ato", "")
    )
    sigiloso = "sigiloso" in full_text.casefold() and len(full_text) < 300
    extraction = (
        ExtractionStatus.PARTIAL
        if sigiloso
        else (ExtractionStatus.COMPLETE if full_text else ExtractionStatus.EMPTY)
    )
    return JurisprudenceResult(
        id=f"tjap-banco-sentencas-{identifier}",
        source="tjap_banco_sentencas",
        court="TJAP",
        type=decision_type,
        number=number,
        summary=full_text or None,
        full_text=full_text or None,
        rapporteur=values.get("magistrado"),
        judgment_date=values.get("juntada"),
        access_status=AccessStatus.PUBLIC,
        extraction_status=extraction,
        source_trace=trace,
        case_class=values.get("classe"),
        judging_body=body,
        degree="first",
        instance="first",
        branch="state",
        authority="TJAP",
        collection="CJPG",
        document_type=decision_type,
        document_url=reader_url,
        raw={
            "fields": values,
            "reader_url": reader_url,
            "sigiloso": sigiloso,
            "degree": "first",
            "instance": "first",
            "collection": "CJPG",
        },
        field_provenance={
            "degree": {"value": "first", "method": "official_unit_marker", "source": body},
            "instance": {"value": "first", "method": "official_unit_marker", "source": body},
            "collection": {"value": "CJPG", "method": "provider_contract"},
        },
    )


def _build_filters(query: JurisprudenceQuery) -> dict[str, Any]:
    return {
        "array": {
            "classes": [query.case_class] if query.case_class else [],
            "assuntos": [],
            "orgaos": [query.judging_body] if query.judging_body else [],
            "magistrados": [query.rapporteur] if query.rapporteur else [],
            "order": [],
        },
        "anos": [],
        "search": query.text or query.number,
        "tipo": _map_type(query.types or [query.decision_type]),
        "sistema": "",
        "match_phrase": query.exact_phrase,
        "date": {
            "startDate": query.judgment_date_from or query.published_from,
            "endDate": query.judgment_date_to or query.published_to,
        },
        "banco": "",
    }


def _map_type(values: list[str]) -> str:
    value = next((v for v in values if v), "ambos").casefold()
    if "sent" in value:
        return "sentenca"
    if "decis" in value:
        return "decisao"
    return "ambos"


def _filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    return {
        name: "native"
        for name, value in {
            "text": query.text,
            "exact_phrase": query.exact_phrase,
            "number": query.number,
            "case_class": query.case_class,
            "judging_body": query.judging_body,
            "judgment_date_from": query.judgment_date_from,
            "judgment_date_to": query.judgment_date_to,
        }.items()
        if value
    } | {
        "degree": "validated_scope",
        "instance": "validated_scope",
        "branch": "validated_scope",
        "collection": "validated_scope",
    }


def _validate_scope(query: JurisprudenceQuery) -> None:
    values = {
        query.degree.casefold(),
        query.instance.casefold(),
        query.collection.casefold(),
        query.source_origin.casefold(),
    }
    if values & {"second", "2", "2g", "segundo grau", "second degree", "cjsg"}:
        raise QueryRejectedError("TJAP Banco de Sentenças é exclusivamente de primeiro grau")
    if query.branch and query.branch.casefold() not in {
        "state",
        "estadual",
        "justiça estadual",
        "justica estadual",
    }:
        raise QueryRejectedError("TJAP Banco de Sentenças pertence ao ramo estadual")


def _is_first_degree_unit(value: str) -> bool:
    normalized = value.casefold()
    return any(
        marker in normalized for marker in ("vara", "juizado", "comarca", "ofício", "oficio", "upj")
    )


def _extract_rtf_text(card: Tag) -> str:
    data = str(card.get("x-data") or "")
    match = re.search(r"textToCopy:\s*'((?:\\.|[^'])*)'", data, re.S)
    if not match:
        return ""
    raw = html_module.unescape(match.group(1))
    raw = raw.replace("\\'", "'")
    # Only decode standalone escaped line breaks.  RTF control words such as
    # ``\\rtf1`` and ``\\nowidctlpar`` begin with the same characters and must
    # remain intact until the control-word cleanup below.
    raw = re.sub(r"\\n(?![A-Za-z])", "\n", raw)
    raw = re.sub(r"\\r(?![A-Za-z])", "\r", raw)

    def decode_byte(match: re.Match[str]) -> str:
        return bytes.fromhex(match.group(1)).decode("cp1252", errors="replace")

    # Livewire serializes RTF twice. Decode Unicode and RTF hex escapes before
    # stripping control words, otherwise ``\\u00e3`` becomes visible ``e3``.
    raw = re.sub(r"\\+u0027([0-9a-fA-F]{2})", decode_byte, raw)

    def decode_unicode(match: re.Match[str]) -> str:
        codepoint = int(match.group(1), 16)
        # RTF ``\\uN`` values in the C1 range represent Windows-1252
        # punctuation in the TJAP payload (for example ``\\u0093`` is a
        # left curly quote), not literal control characters.
        if 0x80 <= codepoint <= 0xFF:
            return bytes([codepoint]).decode("cp1252", errors="replace")
        return chr(codepoint)

    def decode_inline_unicode(match: re.Match[str]) -> str:
        """Decode an uppercase escape and consume its RTF fallback blank."""

        codepoint = int(match.group(2), 16)
        decoded = (
            bytes([codepoint]).decode("cp1252", errors="replace")
            if 0x80 <= codepoint <= 0xFF
            else chr(codepoint)
        )
        if not decoded.isupper():
            return match.group(0)
        return match.group(1) + decoded + match.group(3)

    # This source occasionally appends one fallback blank after an uppercase
    # Unicode escape (``Ç A`` in the serialized payload means ``ÇA``). Restrict
    # the repair to an uppercase letter followed by another uppercase letter;
    # a normal blank after ``está`` must remain a word separator.
    raw = re.sub(
        r"([A-Za-zÀ-ÿ])\\+u([0-9a-fA-F]{4}) ([A-ZÀ-Þ])",
        decode_inline_unicode,
        raw,
    )
    raw = re.sub(
        r"\\+u([0-9a-fA-F]{4})",
        decode_unicode,
        raw,
    )
    raw = re.sub(r"\\+'([0-9a-fA-F]{2})", decode_byte, raw)
    # Formatting controls do not delimit legal words. Replacing ``\\f1`` or
    # ``\\f0`` with a blank turns ``dilig\\f1\\'eancia`` into ``dilig ência``;
    # remove those controls instead. Paragraph/line controls intentionally
    # create whitespace.
    raw = re.sub(r"\\+(?:pard?|line|sect|row)\d* ?", "\n", raw, flags=re.I)
    raw = re.sub(r"\\+tab\d* ?", "\t", raw, flags=re.I)
    raw = re.sub(r"\\+[a-zA-Z]+\d* ?", "", raw)
    raw = re.sub(r"[{}]", " ", raw)
    raw = re.sub(r"^(?:\s*Futura-Light;\s*)+", "", raw)
    # A few records embed an HTML fragment in ``textToCopy``. Strip markup so
    # it cannot leak into the canonical summary or the browser card.
    if re.search(r"<(?:div|p|span|br|table)\b", raw, re.I):
        fragment = BeautifulSoup(raw, "html.parser")
        for node in fragment(["script", "style", "noscript"]):
            node.decompose()
        raw = fragment.get_text(" ", strip=True)
    return _normalize_text(raw)


def _extract_visible_teor(card: Tag) -> str:
    """Extract the expanded public ``Teor do Ato`` block when present."""

    for heading in card.find_all(["h3", "h4"]):
        if "teor do ato" not in _normalize_text(heading.get_text(" ", strip=True)).casefold():
            continue
        parent = heading.parent
        if parent is None:
            continue
        text = _normalize_text(parent.get_text(" ", strip=True))
        prefix = _normalize_text(heading.get_text(" ", strip=True))
        if text.casefold().startswith(prefix.casefold()):
            text = text[len(prefix) :].strip()
        if text:
            return text
    return ""


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


__all__ = ["TjapBancoSentencasProvider", "parse_tjap_banco_sentencas"]
