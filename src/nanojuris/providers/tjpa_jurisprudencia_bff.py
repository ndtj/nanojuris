"""TJPA public jurisprudence BFF provider."""

from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import urljoin, urlsplit

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
    CanonicalDocument,
    DecisionBundle,
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus


class TjpaJurisprudenciaBffProvider(JurisprudenceProvider):
    """Provider for the public TJPA JSON BFF."""

    name = "tjpa_jurisprudencia_bff"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjpa_jurisprudencia_url).hostname or ""
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
        self._last_http_metadata: dict[str, Any] = {}
        self._inline_documents: dict[str, tuple[str, str, SourceTrace]] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjpa_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_degree_scope(query)
        endpoint = "/bff/api/decisoes/buscar"
        page_size = _page_size(query.page_size)
        payload = build_tjpa_search_payload(query)
        payload.update({"page": max(query.page - 1, 0), "size": page_size})
        data, source_url = self._request_json("POST", endpoint, json=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={
                "text": query.text,
                "page": query.page,
                "page_size": page_size,
                "body_contract": "tjpa_bff_decisoes_buscar_v1",
            },
            source_url=source_url,
            limitations=[
                "A fonte aplica limite tecnico de resultados informado no envelope.",
                "A pagina da API e baseada em zero.",
                "Filtros de classe e assunto exigem ids vindos de /filtros.",
            ],
            **self._last_http_metadata,
        )
        page = parse_tjpa_search_response(data, query=query, trace=trace)
        for result in page.results:
            if result.full_text:
                self._inline_documents[result.id] = (result.full_text, result.full_text, trace)
                self._inline_documents[result.id.removeprefix("tjpa-bff-")] = (
                    result.full_text,
                    result.full_text,
                    trace,
                )
        return page

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Return the full text embedded in a public BFF search result."""

        entry = self._inline_documents.get(document_id)
        if entry is None:
            raise KeyError("TJPA inline document is available only after search")
        content, text, trace = entry
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="inteiro_teor",
            content=content.encode("utf-8"),
            content_type="text/plain",
            url=trace.source_url,
            title="TJPA jurisprudência — documento inline",
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"inline": True, "document_id": document_id},
            parser=f"{self.name}.inline_document",
            parser_version="1",
            text_override=text,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        try:
            document = self.get_document(precedent_id)
        except KeyError as exc:
            raise SourceUnavailableError(
                "TJPA inline document is available only after an observed search"
            ) from exc
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document.text or "",
                    "content_type": document.content_type or "text/plain",
                }
            ],
            source_trace=document.source_trace,
            raw=document.raw_metadata,
            raw_bytes=document.raw_bytes,
        )

    def get_catalog(self) -> ProviderCatalog:
        endpoint = "/bff/api/decisoes/filtros"
        data, source_url = self._request_json("GET", endpoint)
        envelope = data.get("data")
        if not isinstance(envelope, dict):
            raise ParserContractChangedError("TJPA filters response missing data object")
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            source_url=source_url,
            limitations=["Catalogos devem ser usados como fonte dos ids de filtro."],
        )
        species: list[ProviderOption] = []
        for key in ("tipos", "classes", "assuntos"):
            for item in _as_list(envelope.get(key)):
                if not isinstance(item, dict):
                    continue
                code = _first_string(item, "id", "codigo", "value", "descricao")
                description = _first_string(item, "descricao", "nome", "label", "value")
                if code and description:
                    species.append(
                        ProviderOption(code=code, description=description, metadata={"group": key})
                    )
        courts = [
            ProviderOption(
                code=code,
                description=description,
                metadata={"group": "orgaosJulgadoresColegiados"},
            )
            for item in _as_list(envelope.get("orgaosJulgadoresColegiados"))
            if isinstance(item, dict)
            for code, description in [
                (
                    _first_string(item, "id", "codigo", "descricao"),
                    _first_string(item, "descricao", "nome", "label"),
                )
            ]
            if code and description
        ]
        return ProviderCatalog(
            source=self.name,
            courts=courts,
            species=species,
            source_trace=trace,
            raw=data,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJPA Jurisprudencia BFF",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "date_range", "catalog", "recent"],
            document_types=["acordao", "decisao_monocratica"],
            content_formats=["json"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "POST /bff/api/decisoes/buscar",
                "GET /bff/api/decisoes/filtros",
                "GET /bff/api/decisoes/recentes",
                "POST /bff/api/decisoes/pesquisar-por-classe-assunto",
            ],
            supports_full_text=True,
            full_text_access="inline",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            supported_filters=[
                "text",
                "types",
                "source_origins",
                "published_from",
                "published_to",
                "case_class",
                "subject",
                "rapporteur",
            ],
            filter_semantics={
                "text": "translated",
                "exact_phrase": "translated",
                "all_words": "translated",
                "types": "translated",
                "source_origins": "translated",
                "source_origin": "translated",
                "published_from": "translated",
                "published_to": "translated",
                # The BFF payload observed in the public frontend exposes no
                # separate class/rapporteur/number fields; do not advertise
                # filters that the backend would silently ignore.
                "case_class": "unsupported",
                "rapporteur": "unsupported",
                "number": "unsupported",
                "judging_body": "unsupported",
                "lawyer_name": "unsupported",
                "courts": "unsupported",
                "decision_type": "translated",
                "document_type": "translated",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "fetch_details": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
            },
            limitations=[
                "Limite tecnico de resultados e informado pelo backend.",
                "Detalhes por id/processo/documento ainda nao estao validados.",
                "Nao inferir ids de classe ou assunto fora do catalogo oficial.",
            ],
            responsible_use=[
                "Usar page_size pequeno e rate limit.",
                "Preservar o envelope JSON bruto e o limite informado.",
                "Nao apresentar a fonte como consulta processual completa.",
            ],
        )

    def _request_json(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> tuple[dict[str, Any], str]:
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        request = TransportRequest(
            source=self.name,
            operation="bff_request",
            method=method,
            url=url,
            params=kwargs.pop("params", {}),
            data=kwargs.pop("data", None),
            json_body=kwargs.pop("json", None),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": self.config.user_agent,
                **kwargs.pop("headers", {}),
            },
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPA jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                "TJPA jurisprudence transport failed: "
                f"{response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJPA jurisprudence transport returned no HTTP status")
        content = response.body
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if status_code < 400 else "error",
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJPA jurisprudence returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError("TJPA jurisprudence requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJPA jurisprudence returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"TJPA jurisprudence rejected request with HTTP {status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJPA jurisprudence response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJPA jurisprudence JSON root is not an object")
        return data, str(response.final_url or url)


def build_tjpa_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the confirmed textual TJPA BFF payload."""

    payload: dict[str, Any] = {
        "query": query.text or query.exact_phrase or query.all_words,
        "queryType": "anywords" if query.any_words else "free",
        "queryScope": "inteiroTeor" if query.all_words else "ementa",
        "sortBy": "relevancia",
        "sortOrder": "desc",
    }
    optional = {
        "origens": query.source_origins or ([query.source_origin] if query.source_origin else []),
        "tipo": query.types,
        "dataPublicacaoInicio": _date_br(query.published_from),
        "dataPublicacaoFim": _date_br(query.published_to),
    }
    payload.update({key: value for key, value in optional.items() if value})
    return payload


def parse_tjpa_search_response(
    data: dict[str, Any], *, query: JurisprudenceQuery, trace: SourceTrace
) -> SearchPage:
    """Parse the TJPA BFF envelope into normalized results."""

    envelope = data.get("data")
    if not isinstance(envelope, dict):
        raise ParserContractChangedError("TJPA search response missing data object")
    content = envelope.get("content")
    if not isinstance(content, list):
        raise ParserContractChangedError("TJPA search response missing content list")
    page_size = _page_size(query.page_size)
    results = [
        _decision_to_result(item, trace=trace)
        for item in content[:page_size]
        if isinstance(item, dict)
    ]
    total_field_present = "totalElements" in envelope
    total = _as_int(envelope.get("totalElements"), default=len(results))
    page = max(query.page, 1)
    start = ((page - 1) * page_size) + 1 if results else 0
    complete, completeness_reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(results),
        total_is_authoritative="totalElements" in envelope,
    )
    return SearchPage(
        source="tjpa_jurisprudencia_bff",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=page,
        page_size=page_size,
        results=results,
        aggregations={"facets": _as_list(envelope.get("facets"))},
        source_trace=trace,
        pagination_mode="page",
        is_complete=complete,
        completeness_reason=completeness_reason,
        # ``totalElements`` is authoritative only when the backend actually
        # sends the field.  Omitting this flag used to turn a known empty
        # response into an ambiguous ``total=0`` and prevented federation from
        # making a safe pagination decision.
        total_known=total_field_present,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        filters_applied=_tjpa_filters_applied(query),
    )


def _tjpa_filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    """Describe filters translated into the TJPA BFF payload."""

    applied: dict[str, str] = {}
    for name, value in (
        ("text", query.text or query.exact_phrase),
        ("exact_phrase", query.exact_phrase),
        ("all_words", query.all_words),
        ("types", query.types),
        ("source_origins", query.source_origins or query.source_origin),
        ("published_from", query.published_from),
        ("published_to", query.published_to),
    ):
        if value:
            applied[name] = "translated"
    for name, value in (
        ("case_class", query.case_class),
        ("rapporteur", query.rapporteur),
        ("number", query.number),
        ("judging_body", query.judging_body),
        ("lawyer_name", query.lawyer_name),
    ):
        if value:
            applied[name] = "unsupported"
    for name, value in (
        ("degree", query.degree),
        ("instance", query.instance),
        ("branch", query.branch),
        ("authority", query.authority),
        ("collection", query.collection),
    ):
        if value:
            applied[name] = "validated_scope"
    return applied


def _decision_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    external_id = _first_string(item, "id", "hashstorage", "numeroprocesso")
    if not external_id:
        raise ParserContractChangedError("TJPA result missing stable id")
    summary = _first_string(item, "ementatextopuro", "textoementa", "textopuro")
    full_text = _first_string(item, "textopuro", "textooriginal", "full_text", "conteudo")
    judgment_date = _first_string(item, "datajulgamento", "data_julgamento")
    publication_date = _first_string(item, "datapublicacao", "data_publicacao")
    normalized_judgment_date = normalize_date(judgment_date)
    normalized_publication_date = normalize_date(publication_date)
    extraction_status = (
        ExtractionStatus.COMPLETE if summary or full_text else ExtractionStatus.PARTIAL
    )
    decision_type = _first_string(item, "tipo", "especie") or "jurisprudencia"
    _validate_decision_type(decision_type)
    return JurisprudenceResult(
        id=f"tjpa-bff-{external_id}",
        source="tjpa_jurisprudencia_bff",
        court="TJPA",
        type=decision_type,
        number=_first_string(item, "numeroprocesso"),
        summary=summary,
        full_text=full_text or None,
        rapporteur=_nested_name(item.get("relator")),
        judgment_date=normalized_judgment_date,
        publication_date=normalized_publication_date,
        updated_at=normalized_publication_date
        or normalized_judgment_date
        or normalize_date(_first_string(item, "datadocumento")),
        source_trace=trace,
        access_status=AccessStatus.PUBLIC,
        extraction_status=extraction_status,
        raw={
            **item,
            "full_text": full_text,
            "judgment_date_raw": judgment_date,
            "publication_date_raw": publication_date,
            "orgao_julgador": _first_string(item, "orgaojulgadorcolegiado", "orgaojulgador"),
            "case_class": _first_string(item, "classe"),
            "subject": _first_string(item, "indexacao"),
            "degree": "second",
            "instance": "second",
            "branch": "state",
            "authority": "TJPA",
            "collection": "CJSG",
            "document_type": _document_type(decision_type),
        },
        degree="second",
        instance="second",
        branch="state",
        authority="TJPA",
        collection="CJSG",
        document_type=_document_type(decision_type),
        source_origin="TJPA",
    )


def _validate_degree_scope(query: JurisprudenceQuery) -> None:
    """Reject first-degree or unrelated collection filters for the TJPA portal."""

    accepted = {"second", "segundo", "segundo grau", "2", "2º"}
    degree = query.degree.strip().casefold()
    instance = query.instance.strip().casefold()
    collection = query.collection.strip().casefold()
    if degree and degree not in accepted:
        raise QueryRejectedError("TJPA jurisprudencia e exclusiva para segundo grau")
    if instance and instance not in accepted:
        raise QueryRejectedError("TJPA jurisprudencia e exclusiva para instancia de segundo grau")
    if collection and collection not in {"cjsg", "jurisprudencia"}:
        raise QueryRejectedError("TJPA nao suporta a colecao solicitada")
    branch = query.branch.strip().casefold()
    if branch and branch not in {"state", "estadual"}:
        raise QueryRejectedError("TJPA jurisprudencia pertence ao ramo estadual")
    authority = query.authority.strip().casefold()
    if authority and authority not in {"tjpa", "tribunal de justica do para"}:
        raise QueryRejectedError("TJPA nao suporta a autoridade solicitada")


def _validate_decision_type(value: str) -> None:
    normalized = value.casefold()
    if "sentenc" in normalized or "primeiro grau" in normalized:
        raise ParserContractChangedError(
            f"TJPA retornou item fora do contrato de segundo grau: {value!r}"
        )


def _document_type(value: str) -> str:
    return "decisao_monocratica" if "monocrat" in value.casefold() else "acordao"


def _date_br(value: str) -> str:
    parts = value.split("-")
    return "/".join(reversed(parts)) if len(parts) == 3 else value


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _first_string(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        normalized = _string_value(value)
        if normalized:
            return normalized
    return ""


def _string_value(value: object) -> str:
    if isinstance(value, dict):
        for key in ("descricao", "nome", "name", "label", "sigla", "codigo", "id"):
            nested = value.get(key)
            if nested is not None and str(nested).strip():
                return str(nested).strip()
        return ""
    if isinstance(value, list):
        return "; ".join(item for item in (_string_value(entry) for entry in value) if item)
    return str(value).strip() if value is not None else ""


def _nested_name(value: object) -> str | None:
    if isinstance(value, dict):
        return _first_string(value, "nome", "name") or None
    return str(value).strip() if value else None


def _as_int(value: object, *, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 50))
