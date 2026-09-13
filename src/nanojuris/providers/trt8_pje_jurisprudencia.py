"""TRT8 public PJe jurisprudence search adapter.

The TRT8 application publishes a JSON search surface below the official
jurisprudence SPA.  The adapter keeps the appellate contract explicit: every
query is constrained to ``2ª Instância`` and ``Acórdão`` and records that
scope in the canonical result and source trace.  No captcha, token, login or
challenge is generated or replayed.
"""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlparse

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
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

BASE_PATH = "/juris-backend/api"
FILTERS_PATH = f"{BASE_PATH}/filtros"
DOCUMENTS_PATH = f"{BASE_PATH}/documentos"
OPTIONS_PATH = f"{BASE_PATH}/opcoes"
OFFICIAL_HOST = "pje.trt8.jus.br"
MAX_RESPONSE_BYTES = 8_000_000
SECOND_DEGREE_LABEL = "2ª Instância"
APPELLATE_DOCUMENT_LABEL = "Acórdão"


class Trt8PjeJurisprudenciaProvider(JurisprudenceProvider):
    """Search TRT8's public PJe jurisprudence API for appellate decisions."""

    name = "trt8_pje_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self.base_url = self.config.trt8_pje_jurisprudencia_url.rstrip("/")
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(OFFICIAL_HOST,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_RESPONSE_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http: dict[str, Any] = {}
        self._items: dict[str, dict[str, Any]] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        payload = _build_search_payload(query)
        response_payload = self._request_json("POST", DOCUMENTS_PATH, payload)
        trace = self._trace("POST", DOCUMENTS_PATH, payload)
        if "tokenDesafio" in response_payload or "imagem" in response_payload:
            raise AccessControlRequiredError(
                "TRT8 retornou desafio de acesso; a resposta nao e uma busca vazia"
            )
        if "erro" in response_payload:
            raise ParserContractChangedError(
                f"TRT8 retornou erro de contrato: {response_payload['erro']}"
            )
        total = _required_total(response_payload)
        raw_documents = response_payload.get("documents")
        if not isinstance(raw_documents, list):
            raise ParserContractChangedError("TRT8 nao retornou a lista documents esperada")
        if any(not isinstance(item, Mapping) for item in raw_documents):
            raise ParserContractChangedError("TRT8 retornou documento fora do formato objeto")
        results: list[JurisprudenceResult] = []
        for item in raw_documents[: query.page_size]:
            result = _parse_result(dict(item), trace)
            results.append(result)
            self._items[result.id] = {"record": dict(item), "trace": trace}
        if total > 0 and not results:
            raise ParserContractChangedError("TRT8 informou hits, mas nao retornou documentos")

        if query.fetch_details:
            enriched: list[JurisprudenceResult] = []
            for result in results:
                detail = self._request_json("POST", f"{DOCUMENTS_PATH}/{result.id}", {})
                detail_trace = self._trace("POST", f"{DOCUMENTS_PATH}/{result.id}", {})
                enriched.append(_merge_detail(result, detail, detail_trace))
            results = enriched

        start = ((query.page - 1) * query.page_size) + 1 if results else 0
        is_complete = start + len(results) - 1 >= total if total else True
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            source_trace=trace,
            pagination_mode="page",
            is_complete=is_complete,
            completeness_reason="TRT8 informou hits autoritativos no contrato JSON",
            ordering=_ordering_label(payload["ordenarPor"]),
            filters_applied=_filters_applied(query),
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _normalize_document_id(precedent_id)
        payload = self._request_json("POST", f"{DOCUMENTS_PATH}/{document_id}", {})
        trace = self._trace("POST", f"{DOCUMENTS_PATH}/{document_id}", {})
        _validate_detail_scope(payload)
        full_text = _as_text(payload.get("inteiroTeorHTML"))
        if not full_text:
            raise ParserContractChangedError("TRT8 detalhe nao contem inteiroTeorHTML")
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=_as_text(payload.get("magistrado")),
            texts=[{"content": full_text, "content_type": "text/html"}],
            source_trace=trace,
            raw={"document_id": document_id, "detail_fields": sorted(payload)},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        normalized_id = _normalize_document_id(document_id)
        payload = self._request_json("POST", f"{DOCUMENTS_PATH}/{normalized_id}", {})
        trace = self._trace("POST", f"{DOCUMENTS_PATH}/{normalized_id}", {})
        _validate_detail_scope(payload)
        html_text = _as_text(payload.get("inteiroTeorHTML"))
        if not html_text:
            raise ParserContractChangedError("TRT8 detalhe nao contem inteiroTeorHTML")
        content = html_text.encode("utf-8")
        return build_canonical_document(
            document_id=f"trt8-{normalized_id}",
            source=self.name,
            document_type="acordao",
            content=content,
            content_type="text/html",
            title=f"TRT8 {payload.get('processo') or normalized_id}",
            text_override=_html_to_text(html_text),
            url=f"{self.base_url}{DOCUMENTS_PATH}/{normalized_id}",
            access_status=AccessStatus.PUBLIC,
            source_trace=trace,
            raw_metadata={
                "processo": payload.get("processo"),
                "tipoDocumento": payload.get("tipoDocumento"),
                "instancia": payload.get("instancia"),
            },
            parser="trt8_pje_jurisprudencia.detail",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRT8 PJe Jurisprudencia",
            source_url=f"{self.base_url}/jurisprudencia/",
            category="court_jurisprudence",
            search_modes=["text", "all_words", "any_words", "without_words", "date_range", "page"],
            document_types=["acordao"],
            content_formats=["json", "html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator=(
                "TRT8 official PJe jurisprudence API; adapter constrains every request "
                "to explicit 2ª Instância and Acórdão values"
            ),
            extracted_fields=[
                "case_number",
                "case_class",
                "judging_body",
                "rapporteur",
                "judgment_date",
                "publication_date",
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
            endpoints=[
                "GET /juris-backend/api/opcoes",
                "POST /juris-backend/api/filtros",
                "POST /juris-backend/api/documentos",
                "POST /juris-backend/api/documentos/{id}",
            ],
            supports_full_text=True,
            full_text_access="detail_call",
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="page",
            max_remote_page_size=100,
            completeness_contract="reported_hits_and_page_window",
            supported_filters=[
                "text",
                "all_words",
                "any_words",
                "without_words",
                "case_class",
                "judging_body",
                "rapporteur",
                "published_from",
                "published_to",
                "document_type",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "page",
                "fetch_details",
            ],
            unsupported_filters=[
                "exact_phrase",
                "number",
                "updated_from",
                "updated_to",
                "judgment_date_from",
                "judgment_date_to",
                "legal_area",
                "decision_type",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "source_origin",
                "source_origins",
                "courts",
                "types",
            ],
            filter_semantics={
                "text": "translated",
                "all_words": "translated",
                "any_words": "translated",
                "without_words": "translated",
                "case_class": "native",
                "judging_body": "native",
                "rapporteur": "native",
                "published_from": "native",
                "published_to": "native",
                "document_type": "native",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "fetch_details": "native",
            },
            limitations=[
                (
                    "A superficie sem filtros de instancia e tipo mistura primeiro e segundo "
                    "grau; o adapter fixa o escopo appellate."
                ),
                (
                    "O endpoint de detalhe pode omitir inteiro teor para documentos sigilosos "
                    "ou indisponiveis."
                ),
                (
                    "O contrato depende do backend oficial publicado pela SPA e deve falhar "
                    "explicitamente em schema drift."
                ),
            ],
            responsible_use=[
                "Usar chamadas publicas bounded e respeitar o intervalo configurado.",
                "Nao gerar, resolver ou persistir desafios de acesso.",
            ],
            ordering_modes=["relevancia", "dataPublicacao"],
            detail_modes=["POST /juris-backend/api/documentos/{id}"],
        )

    def _request_json(
        self, method: str, path: str, payload: dict[str, Any] | None
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != OFFICIAL_HOST:
            raise QueryRejectedError("TRT8 URL fora da allowlist oficial")
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="trt8_pje_api",
                method=method,
                url=url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Origin": self.base_url,
                    "Referer": f"{self.base_url}/jurisprudencia/",
                },
                json_body=payload,
                idempotent=False,
            )
        )
        self._last_http = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if response.status_code == 200 else "http_error",
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"TRT8 transporte falhou: {response.status.value}")
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TRT8 retornou HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT8 requer controle de acesso (HTTP {status})")
        if status in {400, 422}:
            raise UnsupportedQueryError(f"TRT8 rejeitou a consulta (HTTP {status})")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT8 retornou HTTP {status}")
        try:
            value = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TRT8 nao retornou JSON valido") from exc
        if not isinstance(value, dict):
            raise ParserContractChangedError("TRT8 retornou JSON fora do formato objeto")
        return value

    def _trace(self, method: str, path: str, payload: dict[str, Any]) -> SourceTrace:
        return SourceTrace(
            provider=self.name,
            endpoint=f"{method} {path}",
            query=payload,
            source_url=f"{self.base_url}{path}",
            limitations=[
                "Contrato JSON oficial do PJe TRT8; escopo fixado em segundo grau e acordaos.",
                "Desafios de acesso nao sao automatizados nem tratados como vazio.",
            ],
            **self._last_http,
        )


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any(
        (
            query.text.strip(),
            query.all_words.strip(),
            query.any_words.strip(),
            query.exact_phrase.strip(),
            query.number.strip(),
        )
    ):
        raise QueryRejectedError("TRT8 exige termo, frase ou numero")
    if query.authority and query.authority.casefold() not in {"trt8", "trt-8", "trt 8"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TRT8")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT8 pertence ao ramo trabalhista")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2", "2nd"}:
        raise QueryRejectedError("TRT8 suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2", "2nd"}:
        raise QueryRejectedError("TRT8 suporta somente segunda instancia")
    if query.collection and query.collection.casefold() not in {"jurisprudencia", "cjsg"}:
        raise QueryRejectedError("TRT8 suporta somente a colecao JURISPRUDENCIA/CJSG")
    if query.document_type and _normalize_label(query.document_type) not in {
        "acordao",
        "acordaos",
    }:
        raise QueryRejectedError("TRT8 suporta somente acordaos")
    unsupported = {
        "updated_from": query.updated_from,
        "updated_to": query.updated_to,
        "judgment_date_from": query.judgment_date_from,
        "judgment_date_to": query.judgment_date_to,
        "legal_area": query.legal_area,
        "decision_type": query.decision_type,
        "party_name": query.party_name,
        "party_document": query.party_document,
        "lawyer_name": query.lawyer_name,
        "oab": query.oab,
        "precatory_number": query.precatory_number,
        "police_document": query.police_document,
        "cda": query.cda,
        "source_origin": query.source_origin,
        "source_origins": query.source_origins,
        "courts": query.courts,
        "types": query.types,
    }
    if any(value for value in unsupported.values()):
        names = ", ".join(name for name, value in unsupported.items() if value)
        raise QueryRejectedError(f"TRT8 nao suporta filtro(s): {names}")


def _build_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "timestamp": "##timestamp##",
        "browserIpAddress": "##browserIpAddress##",
        "browserVia": "##browserVia##",
        "name": "query parameters",
        "ordenarPor": "dataPublicacao"
        if query.order_by.casefold() in {"date", "data", "data_publicacao"}
        else "relevancia",
        "browserUserAgent": "NanoJuris",
        "browserReferer": "https://pje.trt8.jus.br/jurisprudencia/",
        "paginationSize": query.page_size,
        "paginationPosition": query.page,
        "fragmentSize": 512,
        # The official UI sends these two values for every appellate search.
        "instancia": [SECOND_DEGREE_LABEL],
        "tipoDocumento": [APPELLATE_DOCUMENT_LABEL],
    }
    all_terms = query.all_words.strip() or query.text.strip()
    if query.exact_phrase.strip():
        payload["andField"] = [query.exact_phrase.strip()]
    elif all_terms:
        payload["andField"] = _split_terms(all_terms)
    if query.any_words.strip():
        payload["orField"] = _split_terms(query.any_words)
    if query.without_words.strip():
        payload["notField"] = _split_terms(query.without_words)
    if query.number.strip():
        payload["andField"] = [query.number.strip()]
    if query.case_class.strip():
        payload["classeJudicial"] = [query.case_class.strip()]
    if query.judging_body.strip():
        payload["orgaoJulgador"] = [query.judging_body.strip()]
    if query.rapporteur.strip():
        payload["magistrado"] = [query.rapporteur.strip()]
    if query.published_from.strip():
        payload["dataPublicacaoStart"] = query.published_from
    if query.published_to.strip():
        payload["dataPublicacaoEnd"] = query.published_to
    return payload


def _parse_result(item: dict[str, Any], trace: SourceTrace) -> JurisprudenceResult:
    _validate_record_scope(item)
    source_id = _as_text(item.get("id"))
    if not source_id:
        raise ParserContractChangedError("TRT8 documento sem id")
    highlights = item.get("highlight")
    summary = None
    if isinstance(highlights, Mapping):
        values = highlights.get("inteiroTeorHTML") or highlights.get("ementaHTML")
        if isinstance(values, list) and values:
            summary = _html_to_text(str(values[0]))
    document_type = "acordao"
    return JurisprudenceResult(
        id=f"trt8-{source_id}",
        source="trt8_pje_jurisprudencia",
        court="TRT8",
        type=document_type,
        number=_as_text(item.get("processo")),
        summary=summary,
        rapporteur=_as_text(item.get("magistrado")),
        publication_date=_as_text(item.get("dataPublicacao")),
        updated_at=_as_text(item.get("dataPublicacao")),
        source_updated_at=_as_text(item.get("timesIndexacao")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if summary else ExtractionStatus.PARTIAL,
        source_trace=trace,
        raw=item,
        case_class=_as_text(item.get("classeJudicial")),
        judging_body=_as_text(item.get("orgaoJulgador")),
        degree="second",
        instance="second",
        branch="labor",
        authority="TRT8",
        collection="CJSG",
        document_type=document_type,
        source_origin="trt8_pje",
        document_url=f"{trace.source_url}/{source_id}" if trace.source_url else None,
        field_provenance={
            "degree": {"source": "source_field:instancia", "value": item.get("instancia")},
            "instance": {"source": "source_field:instancia", "value": item.get("instancia")},
            "document_type": {
                "source": "source_field:tipoDocumento",
                "value": item.get("tipoDocumento"),
            },
            "authority": {"source": "source_contract:trt8_pje"},
            "branch": {"source": "source_contract:trt8"},
            "collection": {"source": "source_contract:trt8_pje_jurisprudencia"},
        },
    )


def _merge_detail(
    result: JurisprudenceResult,
    detail: dict[str, Any],
    trace: SourceTrace,
) -> JurisprudenceResult:
    _validate_detail_scope(detail)
    full_text = _as_text(detail.get("inteiroTeorHTML"))
    if not full_text:
        raise ParserContractChangedError("TRT8 detalhe nao contem inteiroTeorHTML")
    result.full_text = _html_to_text(full_text)
    result.summary = (
        _html_to_text(_as_text(detail.get("ementaHTML")) or result.summary or "") or result.summary
    )
    result.source_trace = trace
    result.extraction_status = ExtractionStatus.COMPLETE
    result.raw = {**result.raw, "detail": detail}
    return result


def _validate_record_scope(item: Mapping[str, Any]) -> None:
    if _normalize_label(item.get("instancia")) != _normalize_label(SECOND_DEGREE_LABEL):
        raise ParserContractChangedError(
            "TRT8 retornou registro fora do escopo de segunda instancia"
        )
    if _normalize_label(item.get("tipoDocumento")) != _normalize_label(APPELLATE_DOCUMENT_LABEL):
        raise ParserContractChangedError("TRT8 retornou documento que nao e acordao")


def _validate_detail_scope(item: Mapping[str, Any]) -> None:
    _validate_record_scope(item)


def _required_total(payload: Mapping[str, Any]) -> int:
    total = payload.get("hits")
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ParserContractChangedError("TRT8 retornou hits invalido")
    return total


def _filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    applied = {
        "degree": "validated_scope",
        "instance": "validated_scope",
        "branch": "validated_scope",
        "authority": "validated_scope",
        "collection": "validated_scope",
        "document_type": "native",
        "page": "native",
    }
    for name in (
        "text",
        "all_words",
        "any_words",
        "without_words",
        "case_class",
        "judging_body",
        "rapporteur",
        "published_from",
        "published_to",
    ):
        if getattr(query, name):
            applied[name] = "native"
    if query.fetch_details:
        applied["fetch_details"] = "native"
    return applied


def _split_terms(value: str) -> list[str]:
    return [part for part in re.split(r"\s+", value.strip()) if part]


def _normalize_document_id(value: str) -> str:
    normalized = value.strip()
    if normalized.lower().startswith("trt8-"):
        normalized = normalized[5:]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", normalized):
        raise QueryRejectedError("identificador TRT8 invalido")
    return normalized


def _normalize_label(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def _html_to_text(value: str) -> str:
    soup = BeautifulSoup(html.unescape(value), "html.parser")
    text = soup.get_text(" ", strip=True)
    text = text.replace("@@juris-trt@@", "")
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _ordering_label(value: str) -> str:
    return "publication_date" if value == "dataPublicacao" else "relevance"


__all__ = ["Trt8PjeJurisprudenciaProvider"]
