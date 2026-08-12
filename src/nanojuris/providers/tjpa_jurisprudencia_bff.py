"""TJPA public jurisprudence BFF provider."""

from __future__ import annotations

import time
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
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider


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
        self._last_request = 0.0

    @property
    def base_url(self) -> str:
        return self.config.tjpa_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
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
        )
        return parse_tjpa_search_response(data, query=query, trace=trace)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "TJPA possui rotas de detalhe observadas, mas ainda nao validadas para um contrato "
            "estavel; use os campos completos retornados pela busca."
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
            supports_full_text=False,
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
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        try:
            response = self.session.request(
                method,
                url,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJPA jurisprudence request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJPA jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJPA jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJPA jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJPA jurisprudence rejected request with HTTP {response.status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJPA jurisprudence response is not JSON") from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("TJPA jurisprudence JSON root is not an object")
        return data, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


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
    )


def _decision_to_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    external_id = _first_string(item, "id", "hashstorage", "numeroprocesso")
    if not external_id:
        raise ParserContractChangedError("TJPA result missing stable id")
    summary = _first_string(item, "ementatextopuro", "textoementa", "textopuro")
    return JurisprudenceResult(
        id=f"tjpa-bff-{external_id}",
        source="tjpa_jurisprudencia_bff",
        court="TJPA",
        type=_first_string(item, "tipo", "especie") or "jurisprudencia",
        number=_first_string(item, "numeroprocesso"),
        summary=summary,
        rapporteur=_nested_name(item.get("relator")),
        updated_at=_first_string(item, "datapublicacao", "datajulgamento", "datadocumento"),
        source_trace=trace,
        raw={
            **item,
            "full_text": _first_string(item, "textopuro", "textooriginal"),
            "orgao_julgador": _first_string(item, "orgaojulgadorcolegiado", "orgaojulgador"),
            "case_class": _first_string(item, "classe"),
            "subject": _first_string(item, "indexacao"),
        },
    )


def _date_br(value: str) -> str:
    parts = value.split("-")
    return "/".join(reversed(parts)) if len(parts) == 3 else value


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _first_string(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


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
