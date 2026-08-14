"""TJBA public GraphQL jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

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
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider

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
        self._last_request = 0.0

    @property
    def graphql_url(self) -> str:
        return self.config.tjba_graphql_url.rstrip("/") + "/graphql"

    @property
    def detail_url(self) -> str:
        return self.config.tjba_graphql_url.rstrip("/") + "/inteiroTeor/"

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if not (query.text.strip() or query.number.strip() or query.exact_phrase.strip()):
            raise QueryRejectedError("TJBA exige assunto, numero de recurso ou frase exata")
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
            _decision_to_result(item, trace=trace)
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
        raw_bytes = bytes(response.content)
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
        bundle = self.get_decisions(document_id)
        text = str(bundle.texts[0].get("content") if bundle.texts else "")
        raw = dict(bundle.raw)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        access_status = AccessStatus(str(raw.get("access_status") or AccessStatus.PUBLIC.value))
        return CanonicalDocument(
            id=document_id,
            source=self.name,
            document_type="acordao",
            content_type="text/html",
            title=f"TJBA inteiro teor {document_id}",
            text=text,
            url=bundle.source_trace.source_url if bundle.source_trace else None,
            sha256=digest,
            byte_size=len(text.encode("utf-8")),
            retrieved_at=bundle.source_trace.retrieved_at if bundle.source_trace else None,
            access_status=access_status,
            extraction_status=ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY,
            source_trace=bundle.source_trace,
            extraction_trace=ExtractionTrace(
                parser="tjba_graphql.get_document",
                parser_version="1",
                status=ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY,
                access_status=access_status,
                content_sha256=digest,
                content_bytes=len(text.encode("utf-8")),
                metadata=raw,
            ),
            raw_metadata=raw,
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
                "number",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "order_by",
            ],
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

    def _request_json(self, payload: dict[str, Any]) -> tuple[dict[str, Any], requests.Response]:
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

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> requests.Response:
        self._respect_rate_limit()
        url = urljoin(self.config.tjba_graphql_url.rstrip("/") + "/", endpoint.lstrip("/"))
        headers = {
            "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        if method == "POST":
            headers.setdefault("Content-Type", "application/json")
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
            raise SourceUnavailableError(f"TJBA request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJBA returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJBA returned access-control response")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJBA returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TJBA rejected request with HTTP {response.status_code}")
        return response

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def build_tjba_filter(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the public frontend-compatible DecisaoFilter payload."""

    payload: dict[str, Any] = {
        "assunto": _graphql_text(query.text or query.exact_phrase or query.all_words),
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


def _decision_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
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
        summary=_first_string(item, "ementa") or None,
        full_text=_first_string(item, "conteudo") or None,
        rapporteur=_nested_string(item.get("relator"), "nome"),
        judgment_date=_date_iso(_first_string(item, "dataJulgamento")) or None,
        publication_date=_date_iso(_first_string(item, "dataPublicacao")) or None,
        source_updated_at=_date_iso(_first_string(item, "dataAtualizacao")) or None,
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        raw={
            **item,
            "case_class": _nested_string(item.get("classe"), "descricao"),
            "judging_body": _nested_string(item.get("orgaoJulgador"), "nome"),
            "document_id": _first_uuid(item, "hash", "id"),
            "document_url": (
                f"/inteiroTeor/{external_id}" if UUID_PATTERN.fullmatch(external_id) else None
            ),
        },
    )


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
    response: requests.Response,
    limitations: list[str],
) -> SourceTrace:
    content = bytes(getattr(response, "content", b"") or b"")
    return SourceTrace(
        provider=provider,
        endpoint=endpoint,
        query=query,
        source_url=str(getattr(response, "url", "") or "") or None,
        final_url=str(getattr(response, "url", "") or "") or None,
        limitations=limitations,
        http_status=response.status_code,
        content_type=response.headers.get("Content-Type") if response.headers else None,
        content_sha256=hashlib.sha256(content).hexdigest(),
        response_bytes=len(content),
        retrieval_status="ok" if 200 <= response.status_code < 300 else "http_error",
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
