"""TJMG public jurisprudence provider.

The current TJMG consultation SPA exposes a documented JSON backend. It is
the preferred route because it supports bounded pagination, first-class
filters and on-demand full-text documents without the CAPTCHA used by the
legacy ``www5`` form. The legacy form remains a diagnostic fallback.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urlparse

import requests
from bs4 import BeautifulSoup

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
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)

BASE_URL = "https://www5.tjmg.jus.br/jurisprudencia/"
FORM_URL = "https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do"
MODERN_API_URL = "https://jurisprudencia-api.tjmg.jus.br"
MODERN_PORTAL_URL = "https://consulta-jurisprudencia.tjmg.jus.br"


class TjmgJurisprudenciaProvider(JurisprudenceProvider):
    """Search TJMG's public SPA API (CJSG) and retrieve its full text."""

    name = "tjmg_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
        *,
        use_modern_api: bool = True,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/135.0.0.0 Safari/537.36"
                )
            }
        )
        self.use_modern_api = use_modern_api
        self._last_http_metadata: dict[str, Any] = {}
        self._document_items: dict[str, tuple[dict[str, Any], SourceTrace]] = {}
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=tuple(
                    host
                    for host in {
                        urlparse(self.config.tjmg_jurisprudencia_api_url).hostname,
                        urlparse(self.config.tjmg_jurisprudencia_portal_url).hostname,
                        urlparse(FORM_URL).hostname,
                    }
                    if host
                ),
                timeout_seconds=self.config.timeout,
                max_bytes=16_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.session.headers.get("User-Agent", self.config.user_agent),
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        # Minimal test sessions and explicit legacy callers may not implement
        # POST. In that case preserve the old, explicit CAPTCHA boundary.
        if self.use_modern_api and callable(getattr(self.session, "post", None)):
            return self._search_modern(query)
        return self._search_legacy(query)

    def _search_modern(self, query: JurisprudenceQuery) -> SearchPage:
        payload = _build_modern_payload(query)
        page_size = min(max(query.page_size, 1), 100)
        sort = _modern_sort(query.order_by)
        endpoint = f"/jurisprudencias/filter?size={page_size}&page={query.page - 1}&sort={sort}"
        response = self._modern_request(endpoint, payload)
        try:
            body = response.json()
        except (ValueError, TypeError, AttributeError) as exc:
            raise ParserContractChangedError("TJMG API retornou JSON inválido") from exc
        rows = body.get("jurisprudencias") if isinstance(body, dict) else None
        total = body.get("totalRecords") if isinstance(body, dict) else None
        if not isinstance(rows, list) or not isinstance(total, int):
            raise ParserContractChangedError(
                "TJMG API não retornou o contrato de jurisprudências esperado"
            )
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"POST {endpoint}",
            query=payload | {"page": query.page, "page_size": page_size, "sort": sort},
            source_url=f"{self.config.tjmg_jurisprudencia_api_url.rstrip('/')}{endpoint}",
            limitations=[
                "API oficial pública do TJMG; tipoTexto=INTEIRO_TEOR pesquisa o conteúdo integral.",
                "O total remoto é limitado a 1000 registros pela consulta pública.",
                "O inteiro teor é obtido sob demanda pela rota /jurisprudencias/document.",
            ],
            **self._last_http_metadata,
        )
        results: list[JurisprudenceResult] = []
        for row in rows[:page_size]:
            if not isinstance(row, dict):
                continue
            result = _parse_modern_row(
                row,
                trace=trace,
                portal_url=self.config.tjmg_jurisprudencia_portal_url,
            )
            if result is not None:
                results.append(result)
                self._document_items[result.id] = (row, trace)
        start = ((query.page - 1) * page_size) + 1 if results else 0
        complete, reason = page_completeness(
            reported_total=total,
            start=start,
            returned=len(results),
            total_is_authoritative=True,
        )
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=page_size,
            results=results,
            source_trace=trace,
            pagination_mode="page",
            is_complete=complete,
            completeness_reason=reason,
            ordering=sort,
            filters_applied=_modern_filters_applied(query),
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        item_trace = self._document_items.get(precedent_id)
        if item_trace is None:
            raise KeyError("TJMG documento disponível após uma busca nesta sessão")
        item, search_trace = item_trace
        response, trace = self._fetch_modern_document(item, search_trace)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=str(item.get("magistrado") or "") or None,
            texts=[{"content": response.text, "content_type": "text/html"}],
            source_trace=trace,
            raw={"documentoId": item.get("documentoId"), "source_id": item.get("id")},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        item_trace = self._document_items.get(document_id)
        if item_trace is None:
            raise KeyError("TJMG documento disponível após uma busca nesta sessão")
        item, search_trace = item_trace
        response, trace = self._fetch_modern_document(item, search_trace)
        return _build_modern_document(
            item,
            response.body,
            trace,
            response.content_type,
        )

    def _fetch_modern_document(
        self, item: dict[str, Any], search_trace: SourceTrace
    ) -> tuple[TransportResponse, SourceTrace]:
        publication = _iso_date(str(item.get("publicacaoData") or ""))
        if not publication or not item.get("documentoId"):
            raise ParserContractChangedError("TJMG documento sem ID ou publicacaoData válida")
        payload = {
            "documentoId": item["documentoId"],
            "ids": [],
            "numerosProcessos": [],
            "tiposDocumento": [],
            "orgaosJulgadores": [],
            "magistrados": [],
            "classes": [],
            "assuntos": [],
            "comarcas": [],
            "datasPublicacao": [{"inicio": publication, "fim": publication}],
            "datasJulgamento": [],
            "texto": None,
            "tipoTexto": None,
            "total": False,
        }
        response = self._modern_request("/jurisprudencias/document", payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /jurisprudencias/document",
            query={"documentoId": item["documentoId"], "publicacaoData": publication},
            source_url=(
                f"{self.config.tjmg_jurisprudencia_api_url.rstrip('/')}/jurisprudencias/document"
            ),
            limitations=search_trace.limitations,
            **self._last_http_metadata,
        )
        return response, trace

    def _search_legacy(self, query: JurisprudenceQuery) -> SearchPage:
        response = self._request()
        markup = response.text.casefold()
        if any(marker in markup for marker in ("captcha", "recaptcha", "txtcaptcha")):
            raise AccessControlRequiredError(
                "TJMG exige CAPTCHA numérico no formulário legado; use a API pública moderna"
            )
        if not BeautifulSoup(response.text, "html.parser").find("form"):
            raise ParserContractChangedError("TJMG não retornou o formulário CJSG esperado")
        raise AccessControlRequiredError("TJMG requer validação humana do CAPTCHA legado")

    def get_capabilities(self) -> ProviderCapabilities:
        filters = [
            "text",
            "number",
            "types",
            "case_class",
            "rapporteur",
            "judging_body",
            "courts",
            "legal_area",
            "document_type",
            "decision_type",
            "exact_phrase",
            "all_words",
            "degree",
            "instance",
            "branch",
            "collection",
            "judgment_date_from",
            "judgment_date_to",
            "published_from",
            "published_to",
            "order_by",
        ]
        # The modern public API exposes the filters above.  The remaining
        # cross-provider names are intentionally declared unsupported until a
        # route and response contract proves otherwise; this prevents the
        # capability ledger from promoting guesses to provider guarantees.
        unsupported_filters = [
            "any_words",
            "without_words",
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
            "fetch_details",
            "authority",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMG Jurisprudência API (CJSG)",
            source_url=MODERN_PORTAL_URL,
            category="court_jurisprudence",
            search_modes=["text", "case_number", "date_range", "full_text", "pagination"],
            document_types=["acordao", "decisao_monocratica", "decisao_turma_recursal"],
            content_formats=["json", "html"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="CJSG/acórdão; API oficial consulta-jurisprudencia TJMG",
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
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "POST /jurisprudencias/filter?size={size}&page={page}&sort={field},{order}",
                "POST /jurisprudencias/document",
                "POST /dominio/{field}",
                "GET /jurisprudencia/formEspelhoAcordao.do (legado, CAPTCHA)",
            ],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_unified_search=True,
            pagination_mode="page",
            max_remote_page=100,
            max_remote_page_size=100,
            completeness_contract="totalRecords_authoritative_public_api_capped_at_1000",
            full_text_access="detail_call",
            supported_filters=filters,
            unsupported_filters=unsupported_filters,
            filter_semantics={
                **{
                    name: ("translated" if name in {"exact_phrase", "all_words"} else "native")
                    for name in filters
                },
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                **{name: "unsupported" for name in unsupported_filters},
            },
            ordering_modes=[
                "relevancia,DESC",
                "julgamento_data,ASC",
                "julgamento_data,DESC",
                "publicacao_data,ASC",
                "publicacao_data,DESC",
            ],
            detail_modes=["document_html", "decision_bundle"],
            limitations=[
                "A API pública limita o total exibido a 1000 por consulta.",
                "O formulário www5 legado exige CAPTCHA e permanece apenas como "
                "fallback diagnóstico.",
            ],
            responsible_use=["Não executar OCR de CAPTCHA nem contornar controles de acesso."],
        )

    def get_parameters(self) -> dict[str, str]:
        return {
            "source_url": MODERN_PORTAL_URL,
            "api_url": self.config.tjmg_jurisprudencia_api_url,
            "search_path": "jurisprudencias/filter",
            "document_path": "jurisprudencias/document",
        }

    def _modern_request(self, endpoint: str, payload: dict[str, Any]) -> TransportResponse:
        url = f"{self.config.tjmg_jurisprudencia_api_url.rstrip('/')}{endpoint}"
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="modern_api",
                method="POST",
                url=url,
                json_body=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": self.config.tjmg_jurisprudencia_portal_url,
                    "Referer": f"{self.config.tjmg_jurisprudencia_portal_url.rstrip('/')}/",
                },
                idempotent=False,
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"TJMG API transport failed: {response.status.value}")
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response.final_url or url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if (response.status_code or 0) < 400 else "error",
        }
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TJMG API returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJMG API returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TJMG API returned HTTP {status}")
        return response

    def _request(self) -> TransportResponse:
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="legacy_form",
                method="GET",
                url=FORM_URL,
                idempotent=True,
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"TJMG transport failed: {response.status.value}")
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TJMG returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJMG returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TJMG returned HTTP {status}")
        return response


def _validate_query(query: JurisprudenceQuery) -> None:
    # The modern public API does not expose an independently documented
    # any/without-word channel. Reject those refinements instead of silently
    # returning a result set that ignored the caller's intent.
    if query.any_words:
        raise QueryRejectedError("TJMG API nao comprova o filtro any_words")
    if query.without_words:
        raise QueryRejectedError("TJMG API nao comprova o filtro without_words")

    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJMG exige termo, número ou frase exata")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJMG/CJSG aceita somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJMG/CJSG aceita somente instância de segundo grau")
    if query.branch and query.branch.casefold() not in {"state", "estadual"}:
        raise QueryRejectedError("TJMG pertence ao ramo estadual")
    if query.authority and query.authority.casefold() not in {
        "tjmg",
        "tribunal de justiça de minas gerais",
    }:
        raise QueryRejectedError("a autoridade solicitada não corresponde ao TJMG")
    if query.collection and query.collection.casefold() not in {"cjsg", "jurisprudencia"}:
        raise QueryRejectedError("TJMG/CJSG aceita somente a coleção CJSG")


def _build_modern_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    text_parts: list[str] = []
    if query.text.strip():
        text_parts.append(query.text.strip())
    if query.exact_phrase.strip():
        escaped = query.exact_phrase.strip().replace('"', '\\"')
        text_parts.append(f'"{escaped}"')
    if query.all_words.strip():
        text_parts.append(query.all_words.strip())
    if not text_parts:
        text_parts.append(query.number.strip())
    text = " ".join(part for part in text_parts if part)
    document_types = list(query.types)
    if query.document_type:
        document_types.append(query.document_type)
    if query.decision_type:
        document_types.append(query.decision_type)
    document_types = list(dict.fromkeys(document_types))
    document_types = [
        _document_type_label(item)
        for item in document_types
        if item.casefold() not in {"full_text", "inteiro_teor", "inteiro teor"}
    ]
    return {
        "ids": [],
        "numerosProcessos": [query.number] if query.number.strip() else [],
        "tiposDocumento": document_types,
        "orgaosJulgadores": [query.judging_body] if query.judging_body else [],
        "magistrados": [query.rapporteur] if query.rapporteur else [],
        "classes": [query.case_class] if query.case_class else [],
        "assuntos": [query.legal_area] if query.legal_area else [],
        "comarcas": [item for item in query.courts if item.strip()],
        "datasPublicacao": _date_range(query.published_from, query.published_to),
        "datasJulgamento": _date_range(query.judgment_date_from, query.judgment_date_to),
        "texto": text or None,
        "tipoTexto": "INTEIRO_TEOR"
        if any(
            item.casefold() in {"full_text", "inteiro_teor", "inteiro teor"} for item in query.types
        )
        else "EMENTA",
        "total": False,
    }


def _document_type_label(value: str) -> str:
    """Translate canonical document aliases to TJMG's native labels.

    The modern endpoint accepts the labels exposed by its ``/dominio``
    endpoint (including accents), while callers commonly use the stable
    NanoJuris aliases.  Unknown values are preserved so newly published
    labels remain usable without a library release.
    """

    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    labels = {
        "acordao": "Acórdão",
        "acórdão": "Acórdão",
        "decisao_monocratica": "Decisão Monocrática",
        "decisão_monocrática": "Decisão Monocrática",
        "decisao_turma_recursal": "Decisão Turma Recursal",
        "decisão_turma_recursal": "Decisão Turma Recursal",
        "decisao_vice_presidencia": "Decisão Vice-Presidência",
        "decisão_vice_presidência": "Decisão Vice-Presidência",
    }
    return labels.get(normalized, value)


def _date_range(start: str, end: str) -> list[dict[str, str | None]]:
    if not start and not end:
        return []
    return [{"inicio": _iso_date(start) if start else None, "fim": _iso_date(end) if end else None}]


def _iso_date(value: str) -> str | None:
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _modern_sort(value: str) -> str:
    normalized = value.casefold().replace(" ", "_")
    mapping = {
        "text": "relevancia,DESC",
        "relevancia": "relevancia,DESC",
        "julgamento_data": "julgamento_data,DESC",
        "judgment_date": "julgamento_data,DESC",
        "publication_date": "publicacao_data,DESC",
        "publicacao_data": "publicacao_data,DESC",
    }
    if "," in normalized:
        field, order = normalized.split(",", 1)
        if field in {"relevancia", "julgamento_data", "publicacao_data"} and order in {
            "asc",
            "desc",
        }:
            return f"{field},{order.upper()}"
    return mapping.get(normalized, "relevancia,DESC")


def _modern_filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    fields = {
        "text": "native",
        "number": "native",
        "case_class": "native",
        "rapporteur": "native",
        "judging_body": "native",
        "courts": "native",
        "published_from": "native",
        "published_to": "native",
        "judgment_date_from": "native",
        "judgment_date_to": "native",
        "document_type": "native",
        "types": "native",
        "degree": "validated_scope",
        "instance": "validated_scope",
        "branch": "validated_scope",
        "collection": "validated_scope",
    }
    return {name: status for name, status in fields.items() if getattr(query, name, None)}


def _parse_modern_row(
    row: dict[str, Any], *, trace: SourceTrace, portal_url: str
) -> JurisprudenceResult | None:
    source_id = str(row.get("id") or row.get("documentoId") or "").strip()
    if not source_id:
        return None
    document_type = str(row.get("tipoDocumento") or "Acórdão").strip()
    publication = str(row.get("publicacaoData") or "").strip() or None
    judgment = str(row.get("julgamentoData") or "").strip() or None
    doc_id = str(row.get("documentoId") or "").strip()
    document_url = None
    if doc_id:
        params = {"documentoId": doc_id}
        if publication and _iso_date(publication):
            params["publicacaoData"] = _iso_date(publication) or ""
        document_url = f"{portal_url.rstrip('/')}/inteiro-teor?{urlencode(params)}"
    ementa = str(row.get("ementa") or "").strip() or None
    return JurisprudenceResult(
        id=source_id,
        source="tjmg_jurisprudencia",
        court="TJMG",
        type=document_type.casefold().replace("ó", "o").replace("ã", "a"),
        number=row.get("numeroProcessoCnj") or row.get("numeroProcessoTj"),
        summary=ementa,
        rapporteur=str(row.get("magistrado") or "").strip() or None,
        judgment_date=judgment,
        publication_date=publication,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if ementa else ExtractionStatus.EMPTY,
        source_trace=trace,
        case_class=str(row.get("classe") or "").strip() or None,
        judging_body=str(row.get("orgaoJulgador") or "").strip() or None,
        degree="second",
        instance="second",
        branch="state",
        authority="TJMG",
        collection="CJSG",
        document_type=document_type,
        source_origin="TJMG consulta-jurisprudencia API",
        document_url=document_url,
        raw=dict(row),
    )


def _build_modern_document(
    item: dict[str, Any], content: bytes, trace: SourceTrace, content_type: str | None
) -> CanonicalDocument:
    doc_id = str(item.get("documentoId") or item.get("id") or "tjmg-document")
    text = BeautifulSoup(content, "html.parser").get_text(" ", strip=True)
    return build_canonical_document(
        document_id=doc_id,
        source="tjmg_jurisprudencia",
        document_type="inteiro_teor",
        content=content,
        content_type=content_type or "text/html",
        url=trace.source_url,
        title=f"TJMG {item.get('numeroProcessoCnj') or item.get('numeroProcessoTj') or doc_id}",
        source_trace=trace,
        access_status=AccessStatus.PUBLIC,
        raw_metadata={"source_id": item.get("id"), "documentoId": item.get("documentoId")},
        parser="tjmg_jurisprudencia.modern_document",
        parser_version="1",
        text_override=text,
    )
