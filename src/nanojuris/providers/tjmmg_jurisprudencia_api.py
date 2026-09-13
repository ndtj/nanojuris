"""Public bounded binding for the TJMMG jurisprudence application.

The official endpoint has no server-side pagination.  Broad text searches can
therefore exceed the transport budget, while an exact process number or a
closed judgment-date interval returns a complete ``collection`` envelope.  The
adapter accepts only those bounded shapes, preserves the source fields and
never turns a transport limit into an empty result.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urljoin, urlparse

import requests

from nanojuris.canonical import normalize_date
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


class TjmmgJurisprudenciaApiProvider(JurisprudenceProvider):
    """Public TJMMG search binding with explicit bounded-query semantics."""

    name = "tjmmg_jurisprudencia_api"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjmmg_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=2_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def api_url(self) -> str:
        return urljoin(
            self.config.tjmmg_jurisprudencia_url.rstrip("/") + "/",
            "jurisprudencia-api/api/",
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        if query.page != 1:
            raise QueryRejectedError("TJMMG search contract has no proven pagination")
        _validate_bounded_query(query)
        ordering = "DESC" if query.order_by.casefold() in {"date_desc", "desc"} else "ASC"
        payload = {
            "ordenacao": ordering,
            "searchFilter": _search_filter(query),
            "materia": "T",
            "tipo_decisao": _decision_filter(query),
            "numeracao_unica": query.number.strip(),
            "numero_antigo": "",
            "nome_classe": query.case_class.strip(),
            "relator": query.rapporteur.strip(),
            "relator_acordao": "",
            "cod_revisor": "",
            "referencia": "",
            "inicio_publicacao": query.published_from,
            "fim_publicacao": query.published_to,
            "inicio_julgamento": query.judgment_date_from,
            "fim_julgamento": query.judgment_date_to,
            "sumulas": False,
        }
        response = self._request("POST", "jurisprudencia/search", json_body=payload)
        if response.status is TransportStatus.RESPONSE_TOO_LARGE:
            raise SourceUnavailableError(
                "TJMMG search response exceeded the safe transport limit; "
                "use an exact number or a closed date interval"
            )
        try:
            document = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJMMG search did not return JSON") from exc
        if not isinstance(document, dict):
            raise ParserContractChangedError("TJMMG search JSON envelope is not an object")
        collection = document.get("collection")
        if not isinstance(collection, list):
            raise ParserContractChangedError("TJMMG search envelope lacks collection list")
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /jurisprudencia/search",
            query={
                "number": query.number,
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "case_class": query.case_class,
                "rapporteur": query.rapporteur,
                "judgment_date_from": query.judgment_date_from,
                "judgment_date_to": query.judgment_date_to,
                "published_from": query.published_from,
                "published_to": query.published_to,
                "page": query.page,
            },
            source_url=self.api_url,
            limitations=[
                "A fonte retorna a coleção integral e não expõe paginação server-side.",
                "Texto sem número exige intervalo de julgamento ou publicação fechado.",
            ],
            http_status=response.status_code,
            final_url=response.final_url,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status=response.status.value,
            transformations=["official_collection_envelope", "bounded_query_guard"],
        )
        results = [_parse_result(item, trace=trace) for item in collection]
        if not results:
            return SearchPage(
                source=self.name,
                total=0,
                start=0,
                end=0,
                page=1,
                page_size=query.page_size,
                results=[],
                source_trace=trace,
                pagination_mode="none",
                is_complete=True,
                completeness_reason="TJMMG devolveu collection vazia para a consulta bounded.",
                ordering=ordering,
                filters_applied=_filters_applied(query),
                total_known=True,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.EMPTY,
            )
        return SearchPage(
            source=self.name,
            total=len(results),
            start=0,
            end=len(results) - 1,
            page=1,
            page_size=len(results),
            results=results,
            source_trace=trace,
            pagination_mode="none",
            is_complete=True,
            completeness_reason=(
                "TJMMG devolveu a collection integral; a fonte não suporta paginação remota."
            ),
            ordering=ordering,
            filters_applied=_filters_applied(query),
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise SourceUnavailableError(
            "TJMMG exposes full text in the search record; no separate "
            "DecisionBundle route was observed"
        )

    def get_document(self, document_id: str):
        """Fetch one PDF named by a result's ``NomeArquivo`` field."""

        filename = document_id.removeprefix("tjmmg-file-")
        if not filename.lower().endswith(".pdf"):
            raise QueryRejectedError("TJMMG document_id must be a public PDF filename")
        response = self._request(
            "GET",
            "jurisprudencia/file",
            params={"filename": filename},
            headers={"Accept": "application/pdf, application/octet-stream"},
        )
        if response.status is TransportStatus.RESPONSE_TOO_LARGE:
            raise SourceUnavailableError("TJMMG PDF exceeded the safe document limit")
        if not response.body.startswith(b"%PDF"):
            raise ParserContractChangedError("TJMMG document route did not return a PDF")
        url = urljoin(self.api_url, "jurisprudencia/file") + "?filename=" + quote(filename, safe="")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /jurisprudencia/file",
            query={"filename": filename},
            source_url=url,
            http_status=response.status_code,
            final_url=response.final_url,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status=response.status.value,
            transformations=["official_pdf_download"],
        )
        return build_canonical_document(
            document_id=f"tjmmg-file-{filename}",
            source=self.name,
            document_type="inteiro_teor",
            content=response.body,
            content_type=response.content_type,
            url=response.final_url or url,
            title=filename,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"filename": filename, "document_endpoint": "/jurisprudencia/file"},
            parser="tjmmg.jurisprudencia_pdf",
            parser_version="1",
            max_bytes=self.transport.policy.max_bytes,
        )

    def get_parameters(self) -> dict[str, Any]:
        response = self._request("GET", "jurisprudencia/get")
        try:
            document = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJMMG metadata did not return JSON") from exc
        if not isinstance(document, dict):
            raise ParserContractChangedError("TJMMG metadata envelope is not an object")
        return {
            "source_url": self.config.tjmmg_jurisprudencia_url,
            "api_base": self.api_url,
            "metadata_keys": sorted(str(key) for key in document),
            "status": "metadata_public_bounded_search",
            "search_fields": [
                "ordenacao",
                "searchFilter",
                "materia",
                "tipo_decisao",
                "numeracao_unica",
                "numero_antigo",
                "nome_classe",
                "relator",
                "relator_acordao",
                "referencia",
                "inicio_publicacao",
                "fim_publicacao",
                "inicio_julgamento",
                "fim_julgamento",
                "sumulas",
            ],
        }

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMMG Jurisprudência",
            source_url=self.config.tjmmg_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=["text", "case_number", "filters"],
            document_types=["acordao", "decisao"],
            content_formats=["json", "pdf"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="authority=TJMMG;branch=military;degree=second",
            extracted_fields=[
                "authority",
                "degree",
                "instance",
                "case_number",
                "case_class",
                "decision_type",
                "rapporteur",
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
                "GET /jurisprudencia-api/api/jurisprudencia/get",
                "POST /jurisprudencia-api/api/jurisprudencia/search",
            ],
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_full_text=True,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="none",
            completeness_contract="complete_collection_for_exact_or_closed_date_query",
            # The search response contains inline full text; the linked PDF
            # is an additional official document representation.
            full_text_access="inline",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "case_class",
                "rapporteur",
                "judgment_date_from",
                "judgment_date_to",
                "published_from",
                "published_to",
                "document_type",
            ],
            unsupported_filters=[
                "page",
                "updated_from",
                "updated_to",
                "courts",
                "types",
                "all_words",
                "any_words",
                "without_words",
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
                "judging_body",
                "degree",
                "instance",
                "branch",
                "legal_area",
                "authority",
                "collection",
                "decision_type",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "native",
                "case_class": "native",
                "rapporteur": "native",
                "judgment_date_from": "native",
                "judgment_date_to": "native",
                "published_from": "native",
                "published_to": "native",
                "document_type": "translated",
                "page": "unsupported",
            },
            limitations=[
                "A fonte devolve a collection integral e não possui paginação remota.",
                "Texto exige número exato ou intervalo fechado de julgamento/publicação "
                "para manter a resposta bounded.",
                "O provider permanece opt-in e fora da federação padrão até validação "
                "live repetida.",
            ],
            responsible_use=[
                "Não consultar texto amplo sem intervalo fechado.",
                "Não enviar tokens reCAPTCHA nem baixar o corpus inteiro.",
            ],
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        request = TransportRequest(
            source=self.name,
            operation=path.rsplit("/", 1)[-1],
            method=method,
            url=urljoin(self.api_url, path.lstrip("/")),
            params=params or {},
            json_body=json_body,
            headers=headers or {"Accept": "application/json", "Content-Type": "application/json"},
            idempotent=method.upper() == "GET",
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJMMG jurisprudence request failed") from exc
        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.RESPONSE_TOO_LARGE:
                return response
            raise SourceUnavailableError(
                f"TJMMG transport failed: {response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TJMMG transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("TJMMG returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJMMG returned HTTP {response.status_code}")
        if response.status_code < 200 or response.status_code >= 300:
            raise SourceUnavailableError(f"TJMMG returned HTTP {response.status_code}")
        return response


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any(
        (
            query.text.strip(),
            query.number.strip(),
            query.exact_phrase.strip(),
            query.case_class.strip(),
            query.rapporteur.strip(),
            query.judgment_date_from,
            query.judgment_date_to,
            query.published_from,
            query.published_to,
        )
    ):
        raise QueryRejectedError("TJMMG exige termo, número, classe, relator ou intervalo")


def _validate_bounded_query(query: JurisprudenceQuery) -> None:
    if query.number.strip():
        return
    judgment_window = bool(query.judgment_date_from and query.judgment_date_to)
    publication_window = bool(query.published_from and query.published_to)
    if not (judgment_window or publication_window):
        raise QueryRejectedError(
            "TJMMG exige número exato ou intervalo fechado de julgamento/publicação"
        )


def _search_filter(query: JurisprudenceQuery) -> str:
    value = query.text.strip() or query.all_words.strip() or query.exact_phrase.strip()
    if query.exact_phrase.strip() and not value.startswith('"'):
        return f'"{value}"'
    return value


def _decision_filter(query: JurisprudenceQuery) -> str:
    types = {item.casefold() for item in query.types}
    if not types or {"acordao", "acórdão"} & types:
        return "T"
    if "decisao" in types or "decisão" in types or "monocratica" in types:
        return "D"
    return "T"


def _filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    applied: dict[str, str] = {}
    for name in (
        "text",
        "exact_phrase",
        "number",
        "case_class",
        "rapporteur",
        "judgment_date_from",
        "judgment_date_to",
        "published_from",
        "published_to",
    ):
        value = str(getattr(query, name) or "").strip()
        if value:
            applied[name] = "native"
    return applied


def _parse_result(item: Any, *, trace: SourceTrace) -> JurisprudenceResult:
    if not isinstance(item, dict):
        raise ParserContractChangedError("TJMMG collection contains a non-object record")
    source_id = str(item.get("Cd_Jurisprudencia") or item.get("id_index") or "").strip()
    if not source_id:
        raise ParserContractChangedError("TJMMG record lacks a stable identifier")
    decision_code = str(item.get("TipoDecisao") or "").strip().upper()
    decision_type = {
        "A": "acordao",
        "D": "decisao_monocratica",
    }.get(decision_code, "jurisprudencia")
    filename = str(item.get("NomeArquivo") or "").strip()
    document_url = (
        urljoin(trace.source_url or "", "jurisprudencia/file")
        + "?filename="
        + quote(filename, safe="")
        if filename
        else None
    )
    raw = dict(item)
    if filename:
        raw["document_filename"] = filename
        raw["document_id"] = f"tjmmg-file-{filename}"
    return JurisprudenceResult(
        id=f"tjmmg-jurisprudencia-{source_id}",
        source="tjmmg_jurisprudencia_api",
        court="TJMMG",
        type=decision_type,
        number=item.get("Numero"),
        summary=_clean_text(item.get("Ementa") or item.get("Sumario")),
        full_text=_clean_text(item.get("Texto")),
        status=_clean_text(item.get("Decisao")),
        rapporteur=_clean_text(item.get("nome_relator") or item.get("Relator")),
        judgment_date=normalize_date(item.get("data_julgamento")),
        publication_date=normalize_date(item.get("data_publicacao")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw=raw,
        case_class=_clean_text(item.get("classe_nome")),
        judging_body=None,
        degree="second",
        instance="second",
        branch="military",
        authority="TJMMG",
        collection="CJSG",
        document_type=decision_type,
        document_url=document_url,
    )


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\\x00", " ").strip()
    return text or None


__all__ = ["TjmmgJurisprudenciaApiProvider"]
