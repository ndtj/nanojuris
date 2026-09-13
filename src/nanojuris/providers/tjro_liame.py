"""TJRO LIAME qualified-precedent provider."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

import requests

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
    DecisionBundle,
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ParadigmCase,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider


class TjroLiameProvider(JurisprudenceProvider):
    """Search TJRO qualified precedents, not the general case-law corpus."""

    name = "tjro_liame"

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
        return self.config.tjro_liame_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        payload = build_tjro_search_payload(query)
        data, source_url = self._request_json("POST", "/api/pesquisa/precedentes", json=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /api/pesquisa/precedentes",
            query={**payload, "page": query.page, "page_size": query.page_size},
            source_url=source_url,
            limitations=[
                "LIAME representa precedentes qualificados do TJRO, nao o acervo geral "
                "de acordaos.",
                "Texto integral de documentos vinculados permanece fora do contrato deste adapter.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjro_search_response(data, query=query, trace=trace)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "LIAME publica metadados de precedentes; documentos vinculados mantem rotas externas."
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRO LIAME Precedentes Qualificados",
            source_url=self.base_url,
            category="court_precedents",
            search_modes=["qualified_precedents", "text", "number", "pagination"],
            document_types=["irdr", "iac"],
            content_formats=["json"],
            canonical_records=["CanonicalPrecedent"],
            extracted_fields=[
                "precedent_type",
                "number",
                "status",
                "question",
                "thesis",
                "rapporteur",
                "paradigm_cases",
                "updated_at",
                "admission_date",
                "document_links",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "POST /api/pesquisa/precedentes",
                "GET /pesquisa/precedentes",
            ],
            supports_full_text=False,
            supports_catalog=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page_size=100,
            completeness_contract="reported_total_and_page_window",
            # LIAME exposes qualified-precedent metadata and external
            # references only; this surface does not publish a document body
            # or a supported document-fetch route.
            full_text_access="not_offered_by_source",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "types",
                "page",
            ],
            unsupported_filters=[
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "rapporteur",
                "updated_from",
                "updated_to",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "fetch_details",
                "case_class",
                "judging_body",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "source_origin",
                "source_origins",
            ],
            filter_semantics={
                "text": "native",
                "number": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "types": "translated",
                "page": "native",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "exact_phrase": "unsupported",
                "rapporteur": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "fetch_details": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "degree": "unsupported",
                "instance": "unsupported",
                "branch": "unsupported",
                "authority": "unsupported",
                "collection": "unsupported",
                "document_type": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
            },
            limitations=[
                "A fonte representa precedentes qualificados; nao mede o volume geral "
                "de jurisprudencia do TJRO.",
                "Filtros de situacao, assunto e processo paradigma existem na API, mas ainda "
                "nao possuem campos tipados na query comum.",
            ],
            responsible_use=[
                "Usar como fonte de precedentes qualificados e contexto, nao como corpus geral.",
                "Preservar os links externos de documentos como referencias observadas.",
            ],
        )

    def _request_json(self, method: str, path: str, **kwargs: Any) -> tuple[dict[str, Any], str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        try:
            response = self.session.request(
                method,
                url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Referer": f"{self.base_url}/pesquisa/precedentes",
                },
                timeout=self.config.timeout,
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJRO LIAME request failed: {exc}") from exc
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        response_url = str(getattr(response, "url", url) or url)
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response_url,
            "content_type": (getattr(response, "headers", {}) or {}).get("Content-Type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJRO LIAME returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJRO LIAME requires access validation")
        if response.status_code in {400, 422}:
            raise QueryRejectedError(f"TJRO LIAME rejected query with HTTP {response.status_code}")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJRO LIAME returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TJRO LIAME returned HTTP {response.status_code}")
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJRO LIAME response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJRO LIAME JSON root is not an object")
        return data, response_url

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def build_tjro_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the JSON payload used by LIAME's public frontend."""

    species = [item for item in query.types if item]
    if not species:
        species = ["incidente_assuncao_competencia", "incidente_demanda_repetitiva"]
    return {
        "siglas": ["TJRO"],
        "especies": species,
        "texto": query.text or query.exact_phrase or "",
        "numero": query.number or "",
        "numero_processo_paradigma": [],
        "assuntos": [],
        "data_inicio": _date_payload(query.published_from),
        "data_final": _date_payload(query.published_to),
        "situacao": [],
        "ordenacao": {"dataAtualizacao": "Desc"},
        "page": max(query.page, 1),
        "page_size": max(1, min(query.page_size, 100)),
    }


def parse_tjro_search_response(
    data: dict[str, Any], *, query: JurisprudenceQuery, trace: SourceTrace
) -> SearchPage:
    envelope = data.get("data")
    if not isinstance(envelope, dict) or not isinstance(envelope.get("results"), list):
        raise ParserContractChangedError("TJRO LIAME response missing data.results")
    results = [
        _precedent_to_result(item, trace=trace)
        for item in envelope["results"]
        if isinstance(item, dict)
    ]
    total = _as_int(envelope.get("total"), default=len(results))
    page_size = max(1, min(query.page_size, 100))
    start = ((max(query.page, 1) - 1) * page_size) + 1 if results else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative=True,
    )
    return SearchPage(
        source="tjro_liame",
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
        total_known=True,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
    )


def _precedent_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    registro = item.get("registro")
    if not isinstance(registro, dict):
        raise ParserContractChangedError("TJRO LIAME result missing registro")
    number = _public_value(registro.get("numero"))
    if not number:
        raise ParserContractChangedError("TJRO LIAME precedent missing stable number")
    cases = [
        ParadigmCase(
            number=str(case.get("numero")),
            case_class=case.get("classe"),
            url=_public_url(case.get("link")),
        )
        for case in registro.get("processosParadigma", [])
        if isinstance(case, dict) and _public_value(case.get("numero"))
    ]
    return JurisprudenceResult(
        id=f"tjro-liame-{item.get('sigla', 'TJRO')}-{item.get('especie', 'precedente')}-{number}",
        source="tjro_liame",
        court=str(item.get("sigla") or "TJRO"),
        type=str(item.get("especie") or "precedente"),
        number=number,
        question=_public_value(registro.get("questao")),
        thesis=_public_value(registro.get("tese")),
        status=_public_value(registro.get("situacao")),
        rapporteur=_public_value(registro.get("relator")),
        updated_at=_date_payload(registro.get("dataAtualizacao")),
        judgment_date=_date_payload(registro.get("dataJulgamento")),
        publication_date=_date_payload(registro.get("dataPublicacao")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        collection="LIAME",
        document_type="qualified_precedent",
        source_origin="TJRO LIAME",
        paradigm_cases=cases,
        source_trace=trace,
        raw={"registro": registro, "sigla": item.get("sigla"), "especie": item.get("especie")},
    )


def _public_value(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    if not text or text.lower() in {"não informado(a)", "nao informado(a)", "não definida."}:
        return None
    return text


def _public_url(value: Any) -> str | None:
    text = _public_value(value)
    return text if text and text.startswith(("http://", "https://")) else None


def _date_payload(value: Any) -> str | None:
    text = _public_value(value)
    if not text:
        return None
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return text


def _as_int(value: Any, *, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default
