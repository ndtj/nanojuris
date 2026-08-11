"""STF public jurisprudence API provider."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import requests
from bs4 import BeautifulSoup

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
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider

STF_SEARCH_FIELDS = [
    "processo_codigo_completo.plural",
    "acordao_ata.plural^3",
    "documental_doutrina_texto.plural",
    "documental_indexacao_texto.plural",
    "documental_jurisprudencia_citada_texto.plural",
    "documental_legislacao_citada_texto.plural",
    "documental_observacao_texto.plural",
    "documental_publicacao_lista_texto.plural",
    "documental_tese_tema_texto.plural^3",
    "documental_tese_texto.plural^3",
    "ementa_texto.plural^3",
    "ministro_facet.plural",
    "orgao_julgador.plural",
    "partes_lista_texto.plural",
    "procedencia_geografica_completo.plural",
    "processo_classe_processual_unificada_extenso.plural",
    "titulo.plural^6",
    "decisao_texto.plural^2",
    "sumula_texto.plural^3",
    "ramo_direito.plural^1",
    "situacao_sumula.plural^1",
]

STF_SOURCE_FIELDS = [
    "base",
    "id",
    "titulo",
    "processo_codigo_completo",
    "processo_numero",
    "processo_classe_processual_unificada_sigla",
    "processo_classe_processual_unificada_extenso",
    "relator_processo_nome",
    "relator_acordao_nome",
    "ministro_facet",
    "orgao_julgador",
    "julgamento_data",
    "publicacao_data",
    "ementa_texto",
    "acordao_ata",
    "decisao_texto",
    "inteiro_teor_url",
    "acompanhamento_processual_url",
    "dje_url",
    "partes_lista_texto",
    "documental_publicacao_lista_texto",
    "documental_legislacao_citada_texto",
    "documental_indexacao_texto",
    "documental_observacao_texto",
    "documental_assunto_texto",
    "documental_tese_texto",
    "documental_tese_tema_texto",
    "is_repercussao_geral",
    "is_repercussao_geral_admissibilidade",
    "is_repercussao_geral_merito",
    "is_iac",
    "dg_atualizado_em",
]


class StfJurisProvider(JurisprudenceProvider):
    """Provider for the public STF jurisprudence search API."""

    name = "stf_juris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/api/search/search"
        payload = build_stf_search_payload(query)
        response_json = self._request_json(endpoint, payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={
                "text": query.text,
                "number": query.number,
                "page": query.page,
                "page_size": query.page_size,
                "body_contract": "stf_search_api_v1",
            },
            source_url=f"{self.config.stf_juris_url.rstrip('/')}{endpoint}",
            limitations=[
                "API publica JSON observada no frontend de jurisprudencia do STF.",
                "Sessao limpa pode receber desafio AWS WAF e deve ser reportada sem bypass.",
                "Inteiro teor fica como URL publica; get_document ainda nao e promovido.",
            ],
        )
        return parse_stf_search_response(
            response_json,
            query=query,
            trace=trace,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "stf_juris exposes result metadata and document URLs only."},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STF Jurisprudencia",
            source_url=self.config.stf_juris_url,
            category="court_jurisprudence",
            search_modes=["text", "case_number", "date_range", "elasticsearch_query"],
            document_types=["acordao"],
            content_formats=["json"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "registry_id",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text_url",
                "process_url",
                "is_repercussao_geral",
                "highlights",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["POST /api/search/search"],
            supports_full_text=False,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
            ],
            limitations=[
                "Endpoint observado por HAR em 06/08/2026.",
                "Chamadas automatizadas limpas podem receber AWS WAF challenge HTTP 202.",
                "Alguns ambientes podem falhar na cadeia SSL do dominio STF.",
                "Documentos de inteiro teor via portal STF podem retornar 403 em sessao limpa.",
            ],
            responsible_use=[
                "Nao contornar AWS WAF, captcha, cookies ou desafios JavaScript.",
                "Usar page_size pequeno e preservar SourceTrace.",
                "Tratar inteiro teor como URL ate validacao publica sem bloqueio.",
            ],
        )

    def _request_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.config.stf_juris_url.rstrip('/')}{endpoint}"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": self.config.stf_juris_url.rstrip("/"),
            "Referer": f"{self.config.stf_juris_url.rstrip('/')}/pages/search",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError(
                "STF jurisprudence API SSL verification failed in this environment."
            ) from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"STF jurisprudence request failed: {exc}") from exc

        if response.status_code == 429:
            raise RateLimitDetectedError("STF jurisprudence API returned HTTP 429")
        if _looks_like_waf_challenge(response):
            raise AccessControlRequiredError(
                "STF jurisprudence API requires AWS WAF/browser validation"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"STF jurisprudence API returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"STF jurisprudence API rejected request with HTTP {response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError(
                "STF jurisprudence API returned non-JSON content"
            ) from exc
        if not isinstance(data, dict):
            raise ParserContractChangedError("STF jurisprudence API JSON root is not an object")
        return data


def build_stf_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the public STF search body observed from the frontend API."""

    text = query.number or query.text
    offset = max(query.page - 1, 0) * query.page_size
    query_string = {
        "query": text or "*",
        "default_operator": "AND",
        "fields": STF_SEARCH_FIELDS,
        "type": "cross_fields",
        "analyzer": "legal_search_analyzer",
        "quote_analyzer": "legal_index_analyzer",
    }
    bool_query: dict[str, Any] = {"filter": [{"query_string": query_string}], "must": []}
    if query.updated_from or query.updated_to or query.published_from or query.published_to:
        bool_query["filter"].append(_date_filter(query))
    return {
        "query": {"bool": bool_query},
        "_source": STF_SOURCE_FIELDS,
        "size": query.page_size,
        "from": offset,
        "sort": [_sort_clause(query.order_by)],
        "highlight": {
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
            "fields": {
                "ementa_texto.plural": {},
                "decisao_texto.plural": {},
                "titulo.plural": {},
            },
        },
        "track_total_hits": True,
    }


def parse_stf_search_response(
    data: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
) -> SearchPage:
    """Parse STF jurisprudence API JSON into normalized NanoJuris results."""

    result = data.get("result")
    if not isinstance(result, dict):
        raise ParserContractChangedError("STF jurisprudence response missing result object")
    hits_root = result.get("hits")
    if not isinstance(hits_root, dict):
        raise ParserContractChangedError("STF jurisprudence response missing hits object")
    hits = hits_root.get("hits", [])
    if not isinstance(hits, list):
        raise ParserContractChangedError("STF jurisprudence response hits is not a list")
    total = _parse_total(hits_root.get("total"))
    results = [_hit_to_result(hit, trace=trace) for hit in hits if isinstance(hit, dict)]
    limited_results = results[: query.page_size]
    start = ((query.page - 1) * query.page_size) + 1 if limited_results else 0
    return SearchPage(
        source="stf_juris",
        total=total,
        start=start,
        end=start + len(limited_results) - 1 if limited_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
        aggregations=_parse_aggregations(result.get("aggregations")),
    )


def _hit_to_result(hit: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult:
    source = hit.get("_source") or {}
    if not isinstance(source, dict):
        raise ParserContractChangedError("STF jurisprudence hit missing _source object")
    source_id = _optional_str(source.get("id") or hit.get("_id")) or "unknown"
    full_text_url = _optional_str(source.get("inteiro_teor_url"))
    source_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=full_text_url or trace.source_url,
        limitations=trace.limitations,
    )
    case_number = _optional_str(source.get("processo_codigo_completo") or source.get("titulo"))
    summary = _optional_str(
        source.get("ementa_texto")
        or source.get("decisao_texto")
        or source.get("documental_tese_texto")
    )
    return JurisprudenceResult(
        id=f"stf-juris-{source_id}",
        source="stf_juris",
        court="STF",
        type=_map_document_type(source.get("base")),
        number=case_number,
        summary=summary,
        rapporteur=_rapporteur(source),
        updated_at=_optional_str(source.get("publicacao_data") or source.get("julgamento_data")),
        highlights=_parse_highlights(hit.get("highlight")),
        source_trace=source_trace,
        raw={
            "registry_id": source_id,
            "classe": _optional_str(source.get("processo_classe_processual_unificada_sigla")),
            "case_class": _optional_str(source.get("processo_classe_processual_unificada_extenso")),
            "assunto": _optional_str(source.get("documental_assunto_texto")),
            "orgao_julgador": _optional_str(source.get("orgao_julgador")),
            "data_julgamento": _optional_str(source.get("julgamento_data")),
            "data_publicacao": _optional_str(source.get("publicacao_data")),
            "document_url": full_text_url,
            "full_text_url": full_text_url,
            "process_url": _optional_str(source.get("acompanhamento_processual_url")),
            "dje_url": _optional_str(source.get("dje_url")),
            "is_repercussao_geral": bool(source.get("is_repercussao_geral")),
            "partes": _optional_str(source.get("partes_lista_texto")),
            "acordao_ata": _optional_str(source.get("acordao_ata")),
            "base": _optional_str(source.get("base")),
            "score": hit.get("_score"),
        },
    )


def _date_filter(query: JurisprudenceQuery) -> dict[str, Any]:
    gte = query.published_from or query.updated_from or None
    lte = query.published_to or query.updated_to or None
    date_range = {key: value for key, value in {"gte": gte, "lte": lte}.items() if value}
    return {"range": {"publicacao_data": date_range}}


def _sort_clause(order_by: str) -> dict[str, Any] | str:
    normalized = order_by.strip().lower()
    if normalized in {"date", "publication", "dtpublicacao"}:
        return {"publicacao_data": {"order": "desc"}}
    return "_score"


def _parse_total(value: Any) -> int:
    if isinstance(value, dict):
        raw_total = value.get("value")
        return int(raw_total) if isinstance(raw_total, int | float) else 0
    return int(value) if isinstance(value, int | float) else 0


def _parse_aggregations(value: Any) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(value, dict):
        return {}
    aggregations: dict[str, list[dict[str, Any]]] = {}
    for key, item in value.items():
        if not isinstance(item, dict):
            continue
        buckets = item.get("buckets")
        if isinstance(buckets, list):
            aggregations[key] = [bucket for bucket in buckets if isinstance(bucket, dict)]
    return aggregations


def _parse_highlights(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    highlights: dict[str, str] = {}
    for key, items in value.items():
        if not isinstance(items, list):
            continue
        text = " ".join(str(item) for item in items)
        highlights[key] = _strip_html(text)
    return highlights


def _map_document_type(value: Any) -> str:
    normalized = _without_accents(str(value or "").strip().lower())
    if normalized in {"acordaos", "acordao"}:
        return "acordao"
    if normalized in {"decisoes", "decisao"}:
        return "decisao"
    if normalized == "sumulas":
        return "sumula"
    return normalized or "documento"


def _rapporteur(source: dict[str, Any]) -> str | None:
    for key in ("relator_processo_nome", "relator_acordao_nome"):
        value = _optional_str(source.get(key))
        if value:
            return value
    ministers = source.get("ministro_facet")
    if isinstance(ministers, list) and ministers:
        return _optional_str(ministers[0])
    return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        text = "\n".join(str(item).strip() for item in value if str(item).strip())
    else:
        text = str(value).strip()
    return text or None


def _strip_html(value: str) -> str:
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def _without_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _looks_like_waf_challenge(response: requests.Response) -> bool:
    action = response.headers.get("x-amzn-waf-action", "").lower()
    if action == "challenge":
        return True
    lowered = (response.text or "").lower()
    if "awswaf" in lowered or "x-amzn-waf-action" in lowered:
        return True
    return response.status_code == 202 and not response.content
