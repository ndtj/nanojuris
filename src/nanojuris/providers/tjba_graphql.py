"""TJBA public GraphQL jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urljoin, urlsplit

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
    ProviderCatalog,
    ProviderOption,
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

TJBA_GRAPHQL_QUERY = """query filter(
  $decisaoFilter: DecisaoFilter!
  $pageNumber: Int!
  $itemsPerPage: Int!
) {
  filter(decisaoFilter: $decisaoFilter, pageNumber: $pageNumber, itemsPerPage: $itemsPerPage) {
    decisoes {
      id sourceId numeroProcesso codigoProcesso
      orgaoJulgador { id nome }
      relator { id nome }
      classe { id descricao }
      source instancia tipoDecisao dataPublicacao dataJulgamento dataAtualizacao
      conteudo ementa contentType hash score
    }
    relatores { key value }
    orgaos { key value }
    classes { key value }
    pageCount itemCount
  }
}"""

TJBA_CATALOG_QUERY = """query catalogs {
  findAllClasses { id codPai descricao segundoGrau }
  findAllOrgaosJulgadoresGroupByInstancia {
    todos { id nome instancia }
  }
  findAllRelatoresGroupByInstancia {
    todos { id nome instancia }
  }
}"""

UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
    re.IGNORECASE,
)


class TjbaGraphqlProvider(JurisprudenceProvider):
    """Provider for TJBA's public GraphQL jurisprudence portal."""

    name = "tjba_graphql"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjba_graphql_url).hostname or ""
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

    @property
    def graphql_url(self) -> str:
        return self.config.tjba_graphql_url.rstrip("/") + "/graphql"

    @property
    def detail_url(self) -> str:
        return self.config.tjba_graphql_url.rstrip("/") + "/inteiroTeor/"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_degree_scope(query)
        if not (
            query.text.strip()
            or query.number.strip()
            or query.exact_phrase.strip()
            or query.all_words.strip()
            or query.any_words.strip()
            or query.without_words.strip()
        ):
            raise QueryRejectedError(
                "TJBA exige assunto, numero, frase exata ou filtros booleanos de palavras"
            )
        page_size = max(1, min(query.page_size, 50))
        variables: dict[str, Any] = {
            "decisaoFilter": build_tjba_filter(query),
            "pageNumber": query.page - 1,
            "itemsPerPage": page_size,
        }
        payload = {
            "query": TJBA_GRAPHQL_QUERY,
            "variables": variables,
        }
        data, response = self._request_json(payload)
        envelope = data.get("filter")
        if not isinstance(envelope, dict):
            raise ParserContractChangedError("TJBA GraphQL response missing filter object")
        trace = _source_trace(
            self.name,
            endpoint="/graphql",
            query=variables,
            response=response,
            limitations=[
                "A fonte exige os flags publicos de instancia e tipo enviados pelo frontend.",
                "pageNumber e baseado em zero no contrato GraphQL.",
                "Catalogos devem ser obtidos da propria fonte; ids nao devem ser inventados.",
            ],
        )
        decisions = envelope.get("decisoes")
        if not isinstance(decisions, list):
            raise ParserContractChangedError("TJBA GraphQL response missing decisoes list")
        results = [
            _decision_to_result(item, trace=trace, base_url=self.config.tjba_graphql_url)
            for item in decisions[:page_size]
            if isinstance(item, dict)
        ]
        total = _as_int(envelope.get("itemCount"), default=len(results))
        start = ((query.page - 1) * page_size) + 1 if results else 0
        complete, reason = page_completeness(
            reported_total=total,
            start=start,
            returned=len(results),
            total_is_authoritative="itemCount" in envelope,
        )
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=page_size,
            results=results,
            aggregations={
                "page_count": envelope.get("pageCount"),
                "relatores": envelope.get("relatores", []),
                "orgaos": envelope.get("orgaos", []),
                "classes": envelope.get("classes", []),
            },
            source_trace=trace,
            pagination_mode="page",
            is_complete=complete,
            completeness_reason=reason,
            ordering="dataPublicacao",
            filters_applied={
                "degree": "remote",
                "instance": "remote",
                "text": "remote"
                if query.text or query.exact_phrase or query.all_words
                else "not_requested",
                "number": "remote" if query.number else "not_requested",
            },
            total_known="itemCount" in envelope,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        identifier = _parse_tjba_identifier(precedent_id)
        endpoint = f"/inteiroTeor/{identifier}"
        response = self._request("GET", endpoint, headers={"Accept": "text/html,*/*"})
        text, metadata = _extract_document_text(response.text)
        trace = _source_trace(
            self.name,
            endpoint=endpoint,
            query={"id": identifier},
            response=response,
            limitations=["Inteiro teor publico consultado por identificador observado."],
        )
        raw_bytes = bytes(response.body)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": text,
                    "content_type": "text/html",
                    "source_content_type": response.headers.get("Content-Type", "text/html"),
                }
            ],
            source_trace=trace,
            raw={
                "identifier": identifier,
                "raw_content_sha256": hashlib.sha256(raw_bytes).hexdigest(),
                "raw_content_bytes": len(raw_bytes),
                **metadata,
            },
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        identifier = _parse_tjba_identifier(document_id)
        endpoint = f"/inteiroTeor/{identifier}"
        response = self._request("GET", endpoint, headers={"Accept": "text/html,*/*"})
        content = bytes(response.body)
        trace = _source_trace(
            self.name,
            endpoint=endpoint,
            query={"id": identifier},
            response=response,
            limitations=["Inteiro teor publico consultado por identificador observado."],
        )
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao",
            content=content,
            content_type=response.headers.get("Content-Type"),
            title=f"TJBA inteiro teor {document_id}",
            url=trace.source_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"identifier": identifier},
            parser="tjba_graphql.get_document",
        )

    def get_catalog(self) -> ProviderCatalog:
        data, response = self._request_json({"query": TJBA_CATALOG_QUERY})
        trace = _source_trace(
            self.name,
            endpoint="/graphql",
            query={"operation": "catalogs"},
            response=response,
            limitations=["Catalogos sao valores oficiais para filtros GraphQL."],
        )
        classes = _as_list(data.get("findAllClasses"))
        grouped_organs = data.get("findAllOrgaosJulgadoresGroupByInstancia") or {}
        grouped_rapporteurs = data.get("findAllRelatoresGroupByInstancia") or {}
        court_options = _catalog_options(grouped_organs.get("todos"), "nome", "instancia")
        species = _catalog_options(classes, "descricao", "segundoGrau")
        rapporteurs = _catalog_options(grouped_rapporteurs.get("todos"), "nome", "instancia")
        return ProviderCatalog(
            source=self.name,
            courts=court_options,
            species=species,
            source_trace=trace,
            raw={"relatores": [item.to_dict() for item in rapporteurs], **data},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJBA Jurisprudencia GraphQL",
            source_url=self.config.tjba_graphql_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "catalog"],
            document_types=["acordao", "decisao_monocratica"],
            content_formats=["json", "html", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "registry_number",
                "judging_body",
                "rapporteur",
                "case_class",
                "decision_type",
                "judgment_date",
                "publication_date",
                "source_updated_at",
                "summary",
                "full_text",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "POST /graphql (filter)",
                "POST /graphql (catalogs)",
                "GET /inteiroTeor/<uuid>",
            ],
            supports_full_text=True,
            full_text_access="detail_call",
            supports_catalog=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="page",
            completeness_contract="itemCount_and_page_window",
            supported_filters=[
                "text",
                "exact_phrase",
                "all_words",
                "any_words",
                "without_words",
                "number",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "order_by",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "fetch_details",
                "case_class",
                "judging_body",
                "rapporteur",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origin",
                "source_origins",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "all_words": "translated",
                "any_words": "translated",
                "without_words": "translated",
                "number": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "order_by": "native",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "types": "unsupported",
                "fetch_details": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "rapporteur": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
            },
            limitations=[
                "A busca depende dos defaults publicos de instancia e tipo do frontend.",
                "PageCount e preservado como metadado; itemCount e o total de decisoes.",
                "Filtros por orgao, relator e classe exigem ids do catalogo oficial.",
            ],
            responsible_use=[
                "Usar baixa frequencia e respeitar limites da fonte.",
                "Nao realizar introspection em cada consulta de producao.",
                "Nao contornar captcha, login, WAF ou controle de acesso.",
            ],
        )

    def _request_json(self, payload: dict[str, Any]) -> tuple[dict[str, Any], TransportResponse]:
        response = self._request("POST", "/graphql", json=payload)
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJBA GraphQL response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJBA GraphQL root is not an object")
        errors = data.get("errors")
        if errors:
            raise ParserContractChangedError(
                "TJBA GraphQL returned errors in a successful response"
            )
        body = data.get("data")
        if not isinstance(body, dict):
            raise ParserContractChangedError("TJBA GraphQL response missing data object")
        return body, response

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> TransportResponse:
        url = urljoin(self.config.tjba_graphql_url.rstrip("/") + "/", endpoint.lstrip("/"))
        headers = {
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        if method == "POST":
            headers.setdefault("Content-Type", "application/json")
        request = TransportRequest(
            source=self.name,
            operation="graphql_request",
            method=method,
            url=url,
            headers=headers,
            json_body=kwargs.pop("json", None),
            data=kwargs.pop("data", None),
            params=kwargs.pop("params", {}),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJBA request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJBA transport failed: {response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TJBA transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("TJBA returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJBA returned access-control response")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJBA returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TJBA rejected request with HTTP {response.status_code}")
        return response


def build_tjba_filter(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the public frontend-compatible DecisaoFilter payload."""

    payload: dict[str, Any] = {
        "assunto": _graphql_text(_build_tjba_search_expression(query)),
        "orgaos": [],
        "relatores": [],
        "classes": [],
        "segundoGrau": True,
        "turmasRecursais": True,
        "tipoAcordaos": True,
        "tipoDecisoesMonocraticas": True,
        "ordenadoPor": _order_by(query.order_by),
    }
    optional = {
        "numeroRecurso": query.number,
        "dataInicial": _date_iso(query.updated_from or query.published_from),
        "dataFinal": _date_iso(query.updated_to or query.published_to),
    }
    payload.update({key: value for key, value in optional.items() if value})
    return payload


def _build_tjba_search_expression(query: JurisprudenceQuery) -> str:
    """Translate the canonical word filters to TJBA's GraphQL expression.

    The public endpoint accepts one boolean expression in ``assunto`` rather
    than separate fields.  Keeping the translation here means federation can
    report the three word filters as translated without silently dropping
    them, while preserving the caller's explicit ``text`` expression.
    """

    if query.text.strip():
        return query.text.strip()
    if query.exact_phrase.strip():
        return f'"{query.exact_phrase.strip()}"'
    clauses: list[str] = []
    if query.all_words.strip():
        words = [part for part in query.all_words.split() if part]
        if words:
            clauses.append(" AND ".join(words))
    if query.any_words.strip():
        words = [part for part in query.any_words.split() if part]
        if words:
            clauses.append("(" + " OR ".join(words) + ")")
    if query.without_words.strip():
        words = [part for part in query.without_words.split() if part]
        if words:
            clauses.extend(f"NOT {word}" for word in words)
    return " AND ".join(clauses)


def _decision_to_result(
    item: dict[str, Any], *, trace: SourceTrace, base_url: str = ""
) -> JurisprudenceResult:
    _validate_decision_degree(item)
    external_id = _first_uuid(item, "hash", "id") or _first_string(
        item, "id", "sourceId", "numeroProcesso"
    )
    if not external_id:
        raise ParserContractChangedError("TJBA decision missing stable identifier")
    return JurisprudenceResult(
        id=f"tjba-graphql-{external_id}",
        source="tjba_graphql",
        court="TJBA",
        type=_first_string(item, "tipoDecisao") or "jurisprudencia",
        number=_first_string(item, "numeroProcesso", "codigoProcesso") or None,
        summary=_ementa_from_blob(_first_string(item, "ementa")) or None,
        full_text=_first_string(item, "conteudo") or None,
        rapporteur=_nested_string(item.get("relator"), "nome"),
        judgment_date=_date_iso(_first_string(item, "dataJulgamento")) or None,
        publication_date=_date_iso(_first_string(item, "dataPublicacao")) or None,
        source_updated_at=_date_iso(_first_string(item, "dataAtualizacao")) or None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(
            ExtractionStatus.COMPLETE
            if _first_string(item, "conteudo", "ementa")
            else ExtractionStatus.PARTIAL
        ),
        source_trace=trace,
        case_class=_nested_string(item.get("classe"), "descricao"),
        judging_body=_nested_string(item.get("orgaoJulgador"), "nome"),
        degree="second",
        instance="second",
        branch="state",
        authority="TJBA",
        collection="CJSG",
        document_type=_decision_type_to_document_type(_first_string(item, "tipoDecisao")),
        source_origin="TJBA",
        document_url=(
            urljoin(base_url.rstrip("/") + "/", f"inteiroTeor/{external_id}")
            if base_url and UUID_PATTERN.fullmatch(external_id)
            else None
        ),
        raw={
            **item,
            "case_class": _nested_string(item.get("classe"), "descricao"),
            "judging_body": _nested_string(item.get("orgaoJulgador"), "nome"),
            "document_id": _first_uuid(item, "hash", "id"),
            "document_url": (
                urljoin(base_url.rstrip("/") + "/", f"inteiroTeor/{external_id}")
                if base_url and UUID_PATTERN.fullmatch(external_id)
                else f"/inteiroTeor/{external_id}"
                if UUID_PATTERN.fullmatch(external_id)
                else None
            ),
            "degree": "second",
            "instance": "second",
            "branch": "state",
            "authority": "TJBA",
            "collection": "CJSG",
            "document_type": _decision_type_to_document_type(_first_string(item, "tipoDecisao")),
        },
    )


def _validate_degree_scope(query: JurisprudenceQuery) -> None:
    """Reject filters that cannot be satisfied by the TJBA/CJSG endpoint."""

    degree = query.degree.strip().casefold()
    instance = query.instance.strip().casefold()
    collection = query.collection.strip().casefold()
    if degree and degree not in {"second", "segundo", "segundo grau", "2", "2º"}:
        raise QueryRejectedError("TJBA GraphQL e exclusivo para jurisprudencia de segundo grau")
    if instance and instance not in {"second", "segundo", "segundo grau", "2", "2º"}:
        raise QueryRejectedError("TJBA GraphQL e exclusivo para instancia de segundo grau")
    if collection and collection not in {"cjsg", "jurisprudencia"}:
        raise QueryRejectedError("TJBA GraphQL nao suporta a colecao solicitada")


def _validate_decision_degree(item: dict[str, Any]) -> None:
    """Reject response items that contradict the second-degree contract."""

    raw_instance = _first_string(item, "instancia", "instance", "grau", "degree")
    if not raw_instance:
        # The source query is explicitly restricted to segundo grau; when the
        # source omits the field, preserve that contract in the canonical row.
        return
    normalized = (
        raw_instance.casefold()
        .replace("º", "")
        .replace("°", "")
        .replace("_", " ")
        .replace("-", " ")
    )
    if normalized not in {"segundo grau", "segundo", "2", "2 grau", "second"}:
        raise ParserContractChangedError(
            f"TJBA retornou item fora do contrato de segundo grau: {raw_instance!r}"
        )


def _decision_type_to_document_type(value: str) -> str:
    normalized = value.casefold().replace("_", " ")
    if "monocrat" in normalized:
        return "decisao_monocratica"
    return "acordao"


def _extract_document_text(html: str) -> tuple[str, dict[str, Any]]:
    if any(value in html.casefold() for value in ("captcha", "recaptcha", "acesso negado")):
        return "", {
            "access_status": AccessStatus.ACCESS_CONTROL_REQUIRED.value,
            "warnings": ["TJBA document response contains access-control text."],
        }
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("script, style, noscript"):
        node.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    return text, {
        "access_status": AccessStatus.PUBLIC.value if text else AccessStatus.PARTIAL.value,
        "text_characters": len(text),
    }


def _source_trace(
    provider: str,
    *,
    endpoint: str,
    query: dict[str, Any],
    response: TransportResponse,
    limitations: list[str],
) -> SourceTrace:
    content = bytes(response.body)
    status_code = response.status_code
    return SourceTrace(
        provider=provider,
        endpoint=endpoint,
        query=query,
        source_url=str(getattr(response, "url", "") or "") or None,
        final_url=str(getattr(response, "url", "") or "") or None,
        limitations=limitations,
        http_status=status_code,
        content_type=response.headers.get("Content-Type") if response.headers else None,
        content_sha256=hashlib.sha256(content).hexdigest(),
        response_bytes=len(content),
        retrieval_status=(
            "ok"
            if status_code is not None and 200 <= status_code < 300
            else "transport_error"
            if status_code is None
            else "http_error"
        ),
    )


def _parse_tjba_identifier(value: str) -> str:
    candidate = value.removeprefix("tjba-graphql-")
    if not UUID_PATTERN.fullmatch(candidate):
        raise ParserContractChangedError("TJBA id deve usar tjba-graphql-<uuid>")
    return candidate


def _catalog_options(items: object, description_key: str, group_key: str) -> list[ProviderOption]:
    options: list[ProviderOption] = []
    for item in _as_list(items):
        if not isinstance(item, dict):
            continue
        code = _first_string(item, "id", "key")
        description = _first_string(item, description_key, "nome", "value")
        if code and description:
            options.append(
                ProviderOption(
                    code=code,
                    description=description,
                    metadata={"group": item.get(group_key)},
                )
            )
    return options


def _date_iso(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T.*)?", value):
        return value[:10]
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", value)
    return f"{match.group(3)}-{match.group(2)}-{match.group(1)}" if match else value


def _graphql_text(value: str) -> str:
    value = re.sub(r"\s+E\s+", " AND ", value.strip(), flags=re.IGNORECASE)
    value = re.sub(r"\s+OU\s+", " OR ", value, flags=re.IGNORECASE)
    return re.sub(r"\s+NAO\s+", " NOT ", value, flags=re.IGNORECASE)


def _order_by(value: str) -> str:
    normalized = value.casefold().replace("_", "")
    return (
        "dataPublicacao" if normalized in {"text", "relevancia", "publication", "date"} else value
    )


_ACORDAO_MARKER = re.compile(
    r"AC[ÓO]RD[ÃA]O\s*[-:.]?\s*(?:ementa\s*[-:.]?\s*)?(.+)",
    re.IGNORECASE | re.DOTALL,
)


def _ementa_from_blob(text: str) -> str:
    """Return the ementa from the TJBA ``ementa`` field.

    That field carries the whole document (court header, parties, lawyers, then
    the ementa). Everything before the ``ACORDAO`` marker is boilerplate that is
    identical across decisions and produces useless synthesised titles.
    """

    clean = " ".join(text.replace("\xa0", " ").split())
    if not clean:
        return ""
    match = _ACORDAO_MARKER.search(clean)
    body = (match.group(1) if match else clean).lstrip(" :.-").rstrip()
    return body[:6000]


def _first_string(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _first_uuid(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = _first_string(item, key)
        if value and UUID_PATTERN.fullmatch(value):
            return value
    return None


def _nested_string(value: object, key: str) -> str | None:
    if isinstance(value, dict):
        result = value.get(key)
        return str(result).strip() if result else None
    return None


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_int(value: object, *, default: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default
