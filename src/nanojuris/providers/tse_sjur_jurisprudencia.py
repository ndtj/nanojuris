"""Runtime opt-in adapter for the public TSE SJUR decision-search API.

This adapter implements the public ``/simples`` route observed on the official
TSE jurisprudence portal. It is available at runtime for explicit callers,
but is outside the default unified federation because remote pagination is not
proven. It does not use tokens, sessions, CAPTCHA solving, proxies or
challenge bypasses.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import (
    DocumentReference,
    build_canonical_document,
    fetch_document_reference,
)
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
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

SEARCH_PATH = "/tse/sjur-pesquisa-backend/rest/public/pesquisa/simples"
# The public SJUR route returns a bounded 1,000-record JSON window even when
# ``tamanho`` is small.  Most TREs fit below 8 MB, while TRE-GO/TRE-PB were
# observed above that threshold.  Keep a hard in-memory cap, aligned with
# other official JSON providers, rather than silently dropping those courts.
MAX_REMOTE_BYTES = 16_000_000
MAX_REQUEST_PAGE_SIZE = 20
# The service has returned a bounded window of up to 1,000 records while
# ignoring ``pagina``.  Date partitioning may request that window explicitly,
# but only through the opt-in method below and only for a finite range.
MAX_PARTITION_REMOTE_SIZE = 1_000
MAX_DATE_PARTITIONS = 36
MAX_AUTHORITY_BATCH = 27
MAX_DOCUMENT_BYTES = 12_000_000

# Canonical immutable registry for all 27 regional electoral courts. Keeping
# it beside the adapter contract prevents the client and diagnostic tools from
# drifting (for example by omitting a UF or using a different ordering).
TRE_STATES = (
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
)
TRE_AUTHORITIES = tuple(f"TRE-{state}" for state in TRE_STATES)
TRE_FIRST_DEGREE_LABEL = "Sentença"

# The official SJUR/TRE SPA sends its free-text query over these indexed
# fields. Keeping the list explicit makes the translated contract auditable
# and aligns the adapter with the public UI instead of using an opaque
# provider-local catch-all.
SJUR_TEXT_FIELDS = (
    "indexacoes",
    "textoEmenta",
    "textoDecisao",
    "descricaoClasse",
    "descricaoTipoDecisao",
    "numeroProcesso",
    "numeroDecisao",
    "numeroUnico",
    "numeroUnicoFormatado",
    "partes.nomeParte",
    "relatores.nome",
    "referenciasLegislativas.legislacao",
    "referenciasLegislativas.dispositivos.dispositivo",
    "textoObservacaoGeral",
    "textoObservacaoLegado",
)

# Additional fields exposed by the official TRE SPA.  Keep these separate
# from the general free-text fields so the generated query remains auditable
# and does not broaden a structured refinement accidentally.
SJUR_OBSERVATION_FIELDS = (
    "anoEleicao",
    "casos",
    "anexos",
    "decisoesOutrosTribunais",
    "textoObservacaoGeral",
    "textoObservacaoLegado",
)


TRE_SECOND_DEGREE_LABELS = (
    "Ac\u00f3rd\u00e3o",
    "Decis\u00e3o monocr\u00e1tica",
    "Resolu\u00e7\u00e3o",
    "Decis\u00e3o sem resolu\u00e7\u00e3o",
)


def _normalize_tre_type_filter(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


_TRE_SECOND_DEGREE_TYPE_FILTERS: dict[str, tuple[str, ...]] = {
    "acordao": (TRE_SECOND_DEGREE_LABELS[0],),
    "decisao": (TRE_SECOND_DEGREE_LABELS[1], TRE_SECOND_DEGREE_LABELS[3]),
    "decisao_monocratica": (TRE_SECOND_DEGREE_LABELS[1],),
    "decisao_sem_resolucao": (TRE_SECOND_DEGREE_LABELS[3],),
    "resolucao": (TRE_SECOND_DEGREE_LABELS[2],),
}


class TseSjurJurisprudenciaProvider(JurisprudenceProvider):
    """Public TSE SJUR textual decisions, available as a runtime opt-in."""

    name = "tse_sjur_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tse_sjur_api_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_REMOTE_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        document_host = urlparse(self.config.tse_sjur_document_url).hostname or ""
        self._document_policy = TransportPolicy(
            allowed_hosts=(document_host,),
            timeout_seconds=self.config.timeout,
            max_bytes=MAX_DOCUMENT_BYTES,
            max_retries=0,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._document_urls: dict[str, str] = {}

    @property
    def base_url(self) -> str:
        return self.config.tse_sjur_api_url.rstrip("/")

    def search(
        self,
        query: JurisprudenceQuery,
        *,
        _remote_page_size: int | None = None,
        _date_partition: bool = False,
    ) -> SearchPage:
        if not (query.text or query.exact_phrase or query.number):
            raise ValueError("TSE SJUR exige texto, expressao exata ou identificador")
        self._validate_scope(query)
        self._validate_supported_filters(query)
        dsl = build_tse_query(query)
        page_size = min(
            _remote_page_size if _remote_page_size is not None else query.page_size,
            MAX_PARTITION_REMOTE_SIZE if _date_partition else MAX_REQUEST_PAGE_SIZE,
        )
        payload = {
            # The official UI sends the Elasticsearch-like query as a JSON
            # string; sending a native object produces an invalid request.
            "termoPesquisa": json.dumps(dsl, ensure_ascii=False, separators=(",", ":")),
            "pagina": max(query.page - 1, 0),
            "tamanho": page_size,
            "tribunais": ["tse"],
        }
        response = self._request(
            payload,
            decision_type_labels=self._remote_decision_type_labels(query),
        )
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"POST {SEARCH_PATH}",
            query={
                "page": query.page,
                "page_size": page_size,
                "text": query.text,
                "exact_phrase": query.exact_phrase,
                "number": query.number,
                "scope": "TSE",
            },
            source_url=response.final_url or f"{self.base_url}{SEARCH_PATH}",
            limitations=[
                "A rota publica /simples foi reproduzida sem token ou bypass.",
                (
                    "A fonte ignorou pagina e tamanho; a resposta e uma janela unica "
                    "sem paginacao remota."
                ),
                (
                    "temInteiroTeorPDF indica disponibilidade, mas URL de documento "
                    "e validada somente para identificadores observados na busca."
                ),
            ],
            http_status=response.status_code,
            final_url=response.final_url,
            content_type=response.content_type,
            content_sha256=response.content_sha256,
            response_bytes=response.byte_size,
            elapsed_ms=response.elapsed_ms,
            retrieval_status="ok",
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TSE SJUR nao retornou JSON valido") from exc
        page = parse_tse_response(
            data,
            query=query,
            trace=trace,
            page_size=page_size,
            document_base=self.config.tse_sjur_document_url,
        )
        self._document_urls.update(
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
                    "content_type": document.content_type or "application/pdf",
                }
            ],
            source_trace=document.source_trace,
            raw={"document_url": document.url, "access_status": document.access_status.value},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str):
        document_url = self._document_urls.get(document_id)
        if document_url is None:
            raise SourceUnavailableError(
                "TSE SJUR documento somente esta disponivel para um resultado observado"
            )
        return fetch_document_reference(
            DocumentReference(
                id=document_id,
                source=self.name,
                url=document_url,
                document_type="inteiro_teor",
                expected_content_types=("application/pdf", "application/octet-stream"),
                decision_id=document_id,
            ),
            policy=self._document_policy,
            session=self.session,
            title=f"TSE SJUR {document_id}",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        unsupported = [
            "courts",
            "types",
            "rapporteur",
            "updated_from",
            "updated_to",
            "published_from",
            "published_to",
            "case_class",
            "judging_body",
            "document_type",
            "decision_type",
            "fetch_details",
            "party_name",
            "party_document",
            "lawyer_name",
            "oab",
            "precatory_number",
            "police_document",
            "cda",
            "source_origin",
            "source_origins",
            "legal_area",
            "judgment_date_from",
            "judgment_date_to",
            "election_year",
            "observations",
            "tags",
            "municipality",
            "publication_source",
            "publication_number",
            "publication_volume",
            "uf",
        ]
        semantics = {item: "unsupported" for item in unsupported}
        semantics.update(
            {
                "text": "translated",
                "exact_phrase": "translated",
                "number": "translated",
                "all_words": "translated",
                "any_words": "translated",
                "without_words": "translated",
                "page": "unsupported",
                "page_size": "unsupported",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
            }
        )
        supported_filters = [
            "text",
            "exact_phrase",
            "number",
            "all_words",
            "any_words",
            "without_words",
            "authority",
            "branch",
            "degree",
            "instance",
            "collection",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TSE SJUR jurisprudencia textual (janela unica opt-in)",
            source_url=self.config.tse_sjur_url,
            category="electoral_jurisprudence",
            search_modes=["full_text", "summary", "case_number"],
            document_types=["acordao", "decisao"],
            content_formats=["json", "html"],
            canonical_records=["JurisprudenceResult"],
            semantic_discriminator="authority=TSE;branch=electoral;collection=SJUR",
            extracted_fields=[
                "id",
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
                "temInteiroTeorPDF",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                f"POST {SEARCH_PATH}",
                "GET /sjur-servicos/rest/download/pdf/<codigoDecisao>",
            ],
            supports_full_text=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            pagination_mode="none",
            max_remote_page_size=MAX_REQUEST_PAGE_SIZE,
            completeness_contract="reported_total_but_remote_window_unverified",
            # The result contains the decision text inline; the observed PDF
            # route is an additional on-demand document capability exposed via
            # ``get_document``.
            full_text_access="inline",
            supported_filters=supported_filters,
            unsupported_filters=unsupported,
            filter_semantics=semantics,
            ordering_modes=["source_default"],
            detail_modes=["inline_decision_field"],
            limitations=[
                "Provider runtime opt-in e fora da federacao padrao.",
                "A API publica observada devolve uma resposta unica e ignora pagina/tamanho.",
                "O PDF e acessado somente para um identificador observado na busca.",
                "TSE nao representa automaticamente as superficies dos TREs.",
            ],
            responsible_use=[
                "Consultar somente a rota publica oficial e em baixa frequencia.",
                "Nao contornar CAPTCHA, WAF, login, rate limit ou tokens.",
                "Manter bloqueios e schema drift como estados explicitos.",
            ],
        )

    def _validate_supported_filters(self, query: JurisprudenceQuery) -> None:
        """Reject explicit filters that the public SJUR contract cannot apply.

        A federated caller must never mistake an ignored refinement for a
        successful remote filter.  TRE subclasses widen this allowlist after
        proving the corresponding field in the official SPA contract.
        """

        supported = set(self.get_capabilities().supported_filters)
        if query.courts and "courts" not in supported:
            raise QueryRejectedError("TSE SJUR nao suporta o filtro courts nesta superficie")
        if query.types and "types" not in supported:
            raise QueryRejectedError("TSE SJUR nao suporta o filtro types nesta superficie")
        if query.fetch_details and "fetch_details" not in supported:
            raise QueryRejectedError("TSE SJUR nao suporta fetch_details nesta superficie")
        if query.order_by.casefold() != "text":
            raise QueryRejectedError(f"TSE SJUR nao suporta ordenacao order_by={query.order_by!r}")
        query_fields = (
            "updated_from",
            "updated_to",
            "published_from",
            "published_to",
            "rapporteur",
            "party_name",
            "party_document",
            "lawyer_name",
            "oab",
            "precatory_number",
            "police_document",
            "cda",
            "source_origin",
            "source_origins",
            "case_class",
            "judging_body",
            "decision_type",
            "legal_area",
            "judgment_date_from",
            "judgment_date_to",
            "election_year",
            "observations",
            "tags",
            "municipality",
            "publication_source",
            "publication_number",
            "publication_volume",
            "uf",
        )
        for field_name in query_fields:
            value = getattr(query, field_name)
            if value and field_name not in supported:
                raise QueryRejectedError(
                    f"TSE SJUR nao suporta o filtro {field_name} nesta superficie"
                )

    def _validate_scope(self, query: JurisprudenceQuery) -> None:
        """Reject scope filters that cannot match the fixed TSE surface.

        The route is permanently scoped to TSE electoral decisions of the
        superior instance.  Silently ignoring an explicit scope filter would
        make a federated query look successful while returning the wrong
        authority or degree, so incompatible values are rejected before the
        network call.
        """

        def normalized(value: str) -> str:
            return _normalize_tre_type_filter(value).replace("-", "_").replace(" ", "_")

        scope_checks = (
            ("authority", query.authority, {"tse"}),
            ("branch", query.branch, {"electoral", "justica_eleitoral"}),
            ("degree", query.degree, {"second", "superior", "2", "2o", "2grau"}),
            ("instance", query.instance, {"second", "superior", "2", "2o", "2grau"}),
            ("collection", query.collection, {"sjur"}),
        )
        for field_name, value, accepted in scope_checks:
            if value and normalized(value) not in accepted:
                raise QueryRejectedError(
                    f"TSE SJUR nao aceita {field_name}={value!r}; "
                    f"a superficie e fixa em TSE/electoral/second/SJUR"
                )

    def _remote_decision_type_labels(self, query: JurisprudenceQuery) -> tuple[str, ...] | None:
        del query
        return None

    def _request(
        self,
        payload: dict[str, Any],
        *,
        decision_type_labels: tuple[str, ...] | None = None,
    ):
        del decision_type_labels
        request = TransportRequest(
            source=self.name,
            operation="search",
            method="POST",
            url=f"{self.base_url}{SEARCH_PATH}",
            json_body=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            idempotent=False,
        )
        response = self.transport.request(request)
        if response.status in {
            TransportStatus.TIMEOUT,
            TransportStatus.TLS_ERROR,
            TransportStatus.SOURCE_UNAVAILABLE,
            TransportStatus.RESPONSE_TOO_LARGE,
            TransportStatus.CIRCUIT_OPEN,
        }:
            raise SourceUnavailableError("TSE SJUR transporte indisponivel")
        if response.status_code == 429:
            raise RateLimitDetectedError("TSE SJUR retornou HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TSE SJUR exige validacao de acesso")
        if response.status_code in {400, 422}:
            raise QueryRejectedError("TSE SJUR rejeitou a consulta")
        if response.status_code is None or response.status_code >= 500:
            raise SourceUnavailableError("TSE SJUR retornou resposta indisponivel")
        if response.status_code >= 400:
            raise SourceUnavailableError("TSE SJUR rejeitou a requisicao")
        return response


def build_tse_query(query: JurisprudenceQuery) -> dict[str, Any]:
    """Build the DSL fields proven by the official TSE/TRE public SPA.

    Text refinements use the same ``query_string`` field paths as the UI;
    exact metadata and date refinements are emitted as Elasticsearch-style
    ``filter`` clauses.  The returned dictionary is still only a request
    plan: TRE subclasses add their concrete authority and decision-type
    clauses immediately before transport.
    """

    must_not: list[dict[str, Any]] = []
    if query.number:
        digits = "".join(character for character in query.number if character.isdigit())
        identifier: int | str = int(digits) if digits and len(digits) <= 18 else query.number
        must: list[dict[str, Any]] = [
            {"terms": {"codigoDecisao": [identifier]}},
        ]
    else:
        text_parts: list[str] = []
        if query.text:
            text_parts.append(query.text)
        if query.exact_phrase:
            escaped_term = query.exact_phrase.replace('"', '\\"')
            text_parts.append(f'"{escaped_term}"')
        if query.all_words:
            text_parts.append(" AND ".join(_query_terms(query.all_words)))
        if query.any_words:
            any_terms = _query_terms(query.any_words)
            if any_terms:
                text_parts.append("(" + " OR ".join(any_terms) + ")")
        term = " AND ".join(part for part in text_parts if part)
        if not term:
            term = "*"
        must = [_query_string_clause(term)]
        if query.without_words:
            for excluded in _query_terms(query.without_words):
                must_not.append(_query_string_clause(excluded))
    filters: list[dict[str, Any]] = [
        {"terms": {"siglaTribunalJE.keyword": ["TSE"]}},
    ]
    if query.case_class:
        filters.append({"terms": {"siglaClasse.keyword": _comma_values(query.case_class)}})
    if query.judgment_date_from or query.judgment_date_to:
        filters.append(
            {
                "range": {
                    "dataDecisao": _date_range(
                        query.judgment_date_from,
                        query.judgment_date_to,
                    )
                }
            }
        )
    if query.published_from or query.published_to:
        filters.append(
            {
                "range": {
                    "publicacoes.dataPublicacao": _date_range(
                        query.published_from,
                        query.published_to,
                    )
                }
            }
        )
    if query.election_year:
        filters.append(
            {"terms": {"anoEleicao": _numeric_values(query.election_year, "election_year")}}
        )
    if query.tags:
        filters.append({"terms": {"etiquetas.etiqueta.keyword": _comma_values(query.tags)}})
    if query.municipality:
        filters.append({"terms": {"nomeMunicipio.keyword": _comma_values(query.municipality)}})
    if query.publication_source:
        filters.append(
            {
                "terms": {
                    "publicacoes.siglaFontePublicacao.keyword": _comma_values(
                        query.publication_source
                    )
                }
            }
        )
    if query.publication_number:
        filters.append(
            {"terms": {"publicacoes.numeroPublicacao": _comma_values(query.publication_number)}}
        )
    if query.publication_volume:
        filters.append(
            {"terms": {"publicacoes.numeroVolume": _comma_values(query.publication_volume)}}
        )
    if query.uf:
        filters.append({"terms": {"siglaUF.keyword": _comma_values(query.uf)}})
    for value, fields in (
        (query.rapporteur, ["relatores.nome"]),
        (query.party_name, ["partes.nomeParte"]),
        (query.observations, list(SJUR_OBSERVATION_FIELDS)),
    ):
        if value:
            must.append(
                {
                    "query_string": {
                        "query": value,
                        "fields": fields,
                        "default_operator": "AND",
                    }
                }
            )
    return {
        "bool": {
            "must": must,
            "filter": filters,
            "must_not": must_not,
            "should": [],
        }
    }


def _query_terms(value: str) -> list[str]:
    """Split a UI free-text refinement without destroying quoted phrases."""

    return [item for item in re.findall(r'"[^"]+"|\S+', value.strip()) if item]


def _comma_values(value: str) -> list[str]:
    """Translate the SPA's comma-separated multi-select values."""

    return [item.strip() for item in value.split(",") if item.strip()]


def _numeric_values(value: str, field_name: str) -> list[int]:
    """Parse numeric multi-select values without sending malformed DSL."""

    values = _comma_values(value)
    try:
        numbers = [int(item) for item in values]
    except ValueError as exc:
        raise QueryRejectedError(f"{field_name} deve conter apenas numeros") from exc
    if any(number < 1800 or number > 2200 for number in numbers):
        raise QueryRejectedError(f"{field_name} contem ano fora do intervalo suportado")
    return numbers


def _query_string_clause(term: str) -> dict[str, Any]:
    return {
        "query_string": {
            "query": term,
            "fields": list(SJUR_TEXT_FIELDS),
            "default_operator": "AND",
        }
    }


def _date_range(start: str, end: str) -> dict[str, str]:
    """Translate a public query date to the SPA's ``dd/MM/yyyy`` format."""

    range_query: dict[str, str] = {}
    if start:
        range_query["gte"] = _query_date_for_sjur(start)
    if end:
        range_query["lte"] = _query_date_for_sjur(end)
    return range_query


def _query_date_for_sjur(value: str) -> str:
    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).strftime("%d/%m/%Y")
        except ValueError:
            continue
    raise QueryRejectedError(f"data invalida para SJUR: {value!r}")


def _parse_partition_date(value: str) -> date:
    """Parse a public query date for deterministic month partitioning."""

    for pattern in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    raise QueryRejectedError(f"data invalida para particao SJUR: {value!r}")


def _is_sjur_scope_clause(clause: object) -> bool:
    """Identify authority/type clauses replaced by a concrete TRE binding."""

    if not isinstance(clause, dict):
        return False
    for key in ("terms", "term"):
        value = clause.get(key)
        if isinstance(value, dict) and (
            "siglaTribunalJE.keyword" in value or "descricaoTipoDecisao.keyword" in value
        ):
            return True
    return False


def _tre_filters_applied(query: JurisprudenceQuery, *, degree: str) -> dict[str, str]:
    """Expose only refinements actually translated into the SJUR request."""

    applied = {"degree": degree}
    for field_name in (
        "case_class",
        "rapporteur",
        "party_name",
        "judgment_date_from",
        "judgment_date_to",
        "published_from",
        "published_to",
        "election_year",
        "observations",
        "tags",
        "municipality",
        "publication_source",
        "publication_number",
        "publication_volume",
        "uf",
    ):
        if getattr(query, field_name):
            applied[field_name] = "remote"
    if query.document_type:
        applied["document_type"] = "remote"
    if query.decision_type:
        applied["decision_type"] = "remote"
    if query.types:
        applied["types"] = "remote"
    return applied


def parse_tse_response(
    data: Any,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    page_size: int,
    document_base: str = "https://sjur-servicos.tse.jus.br/sjur-servicos/rest",
) -> SearchPage:
    if not isinstance(data, dict):
        raise ParserContractChangedError("TSE SJUR resposta nao e um objeto")
    message = data.get("mensagem")
    if message:
        lowered = str(message).casefold()
        if any(token in lowered for token in ("captcha", "antirrob", "acesso", "token")):
            raise AccessControlRequiredError("TSE SJUR exige validacao de acesso")
        raise QueryRejectedError("TSE SJUR rejeitou a sintaxe da consulta")
    content = data.get("content")
    total = data.get("totalRegistros")
    if not isinstance(content, list) or not isinstance(total, int) or total < 0:
        raise ParserContractChangedError("TSE SJUR schema de resultados mudou")
    # The public route has been observed to ignore ``pagina`` and ``tamanho``
    # and return a single bounded window.  Enforce the caller's candidate
    # budget locally even when a future response contains more records than
    # requested; never claim that truncation is remote pagination.
    bounded_content = content[: max(page_size, 0)]
    results = [_parse_result(item, trace, document_base=document_base) for item in bounded_content]
    complete, reason = page_completeness(
        reported_total=total,
        start=1 if results else 0,
        returned=len(results),
        total_is_authoritative=True,
    )
    if results and len(results) == total:
        reason = (
            "A fonte retornou o total declarado em uma resposta unica; "
            "janela remota nao comprovada."
        )
        complete = True
    elif total == 0 and not results:
        reason = "A fonte informou total zero e mensagem nula."
        complete = True
    elif results and len(results) < total:
        complete = False
        reason = (
            "A fonte informou total maior que a resposta; pagina/tamanho permanecem nao validados."
        )
    if results and not query.number:
        # For thematic text queries the public route was observed to ignore
        # page/size and repeat one bounded window.  Keep the source count as a
        # lower-bound diagnostic only; an exact process-number lookup can
        # still be complete when its single identifier is returned.
        total_known = False
        complete = False
        reason = (
            "A fonte retornou uma janela textual sem paginaÃ§ao remota comprovada; "
            "o total observado nao e exaustivo."
        )
    else:
        total_known = True
    return SearchPage(
        source="tse_sjur_jurisprudencia",
        total=total,
        total_known=total_known,
        start=1 if results else 0,
        end=len(results) if results else 0,
        page=query.page,
        page_size=page_size,
        results=results,
        source_trace=trace,
        pagination_mode="none",
        is_complete=complete,
        completeness_reason=reason,
        ordering="source_default",
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
    )


def _parse_result(
    item: Any,
    trace: SourceTrace,
    *,
    document_base: str = "https://sjur-servicos.tse.jus.br/sjur-servicos/rest",
) -> JurisprudenceResult:
    if not isinstance(item, dict):
        raise ParserContractChangedError("TSE SJUR conteudo contem registro invalido")
    code = item.get("codigoDecisao") or item.get("id")
    if code is None:
        raise ParserContractChangedError("TSE SJUR registro sem identificador estavel")
    summary = _html_text(item.get("textoEmenta"))
    full_text = _html_text(item.get("textoDecisao"))
    rapporteur = _first_nested(item.get("relatores"), "nome")
    case_number = (
        item.get("numeroUnicoFormatado") or item.get("numeroUnico") or item.get("numeroProcesso")
    )
    raw = dict(item)
    return JurisprudenceResult(
        id=f"tse-sjur-{code}",
        source="tse_sjur_jurisprudencia",
        court="TSE",
        type=_decision_type(item.get("descricaoTipoDecisao")) or "decisao",
        number=str(case_number) if case_number is not None else None,
        summary=summary,
        full_text=full_text,
        rapporteur=rapporteur,
        judgment_date=_date(item.get("dataDecisao")),
        publication_date=_date(_first_nested(item.get("publicacoes"), "dataPublicacao")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw=raw,
        case_class=item.get("descricaoClasse") or item.get("siglaClasse"),
        degree="superior",
        instance="superior",
        branch="electoral",
        authority="TSE",
        collection="SJUR",
        document_type=_decision_type(item.get("descricaoTipoDecisao")),
        document_url=_document_url(item, document_base=document_base, code=code),
    )


def _html_text(value: Any) -> str | None:
    if value is None:
        return None
    text = BeautifulSoup(str(value), "html.parser").get_text(" ", strip=True)
    return " ".join(text.split()) or None


def _first_nested(value: Any, key: str) -> str | None:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item.get(key):
                return str(item[key]).strip()
    elif isinstance(value, dict) and value.get(key):
        return str(value[key]).strip()
    return None


def _date(value: Any) -> str | None:
    from nanojuris.normalization import normalize_date_value

    return normalize_date_value(value)


def _decision_type(value: Any) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text.lower().replace("ã", "a") or None


def _document_url(item: dict[str, Any], *, document_base: str, code: Any) -> str | None:
    base_host = urlparse(document_base).hostname
    for key in ("documentUrl", "document_url", "urlPdf", "urlPDF", "linkInteiroTeor"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith("https://"):
            parsed = urlparse(value)
            if parsed.hostname != base_host or not parsed.path:
                continue
            return value
    code_text = str(code).strip()
    if code_text.isdecimal() and str(item.get("temInteiroTeorPDF") or "").casefold() in {
        "true",
        "1",
        "sim",
    }:
        return f"{document_base.rstrip('/')}/download/pdf/{code_text}"
    return None


class TreSjurJurisprudenciaProvider(TseSjurJurisprudenciaProvider):
    """Opt-in adapter for one official TRE SJUR route (``TRE-XX``).

    ``degree_scope`` keeps first- and second-degree surfaces separate while
    sharing the public route, transport and parser.
    """

    def __init__(
        self,
        *args: Any,
        tribunal: str = "TRE-SP",
        degree_scope: str = "second",
        **kwargs: Any,
    ) -> None:
        normalized = _normalize_tre(tribunal)
        if degree_scope not in {"first", "second"}:
            raise ValueError("SJUR/TRE degree_scope deve ser first ou second")
        super().__init__(*args, **kwargs)
        self.tribunal = normalized
        self.degree_scope = degree_scope
        suffix = "jurisprudencia" if degree_scope == "second" else "first_degree"
        self.name = f"tre_{normalized.removeprefix('TRE-').casefold()}_sjur_{suffix}"
        self._route_slug = normalized.casefold()
        # The SJUR search payload includes the decision text even when the
        # advertised PDF endpoint returns an HTML error shell. Keep the
        # observed canonical result in memory so the official inline text can
        # be used as a transparent fallback for the same search session.
        self._inline_results: dict[str, JurisprudenceResult] = {}

    def _validate_scope(self, query: JurisprudenceQuery) -> None:
        """Validate the concrete TRE binding instead of the fixed TSE scope."""

        def normalized(value: str) -> str:
            return _normalize_tre_type_filter(value).replace("-", "_").replace(" ", "_")

        accepted_degree = (
            {"second", "superior", "2", "2o", "2grau", "2_grau"}
            if self.degree_scope == "second"
            else {"first", "1", "1o", "1grau", "1_grau"}
        )
        scope_checks = (
            ("authority", query.authority, {normalized(self.tribunal)}),
            ("branch", query.branch, {"electoral", "justica_eleitoral"}),
            ("degree", query.degree, accepted_degree),
            ("instance", query.instance, accepted_degree),
            ("collection", query.collection, {"sjur"}),
        )
        for field_name, value, accepted in scope_checks:
            if value and normalized(value) not in accepted:
                raise QueryRejectedError(
                    f"SJUR/{self.tribunal} nao aceita {field_name}={value!r}; "
                    f"a superficie e fixa em {self.tribunal}/electoral/"
                    f"{self.degree_scope}/SJUR"
                )

    def _remote_decision_type_labels(self, query: JurisprudenceQuery) -> tuple[str, ...]:
        document_type = query.document_type.strip()
        decision_type = query.decision_type.strip()
        requested_types = [item.strip() for item in query.types if str(item).strip()]
        if document_type and decision_type:
            normalized_document = (
                _normalize_tre_type_filter(document_type).replace("-", "_").replace(" ", "_")
            )
            normalized_decision = (
                _normalize_tre_type_filter(decision_type).replace("-", "_").replace(" ", "_")
            )
            if normalized_document != normalized_decision:
                raise QueryRejectedError(
                    "SJUR/TRE document_type e decision_type precisam representar o mesmo tipo"
                )
        scalar_type = document_type or decision_type
        if scalar_type and requested_types:
            normalized_scalar = (
                _normalize_tre_type_filter(scalar_type).replace("-", "_").replace(" ", "_")
            )
            normalized_types = {
                _normalize_tre_type_filter(value).replace("-", "_").replace(" ", "_")
                for value in requested_types
            }
            if normalized_types != {normalized_scalar}:
                raise QueryRejectedError(
                    "SJUR/TRE document_type, decision_type e types precisam representar "
                    "o mesmo tipo"
                )
            requested_values = [scalar_type]
        else:
            requested_values = [scalar_type] if scalar_type else requested_types
        if not requested_values:
            if self.degree_scope == "first":
                return (TRE_FIRST_DEGREE_LABEL,)
            return TRE_SECOND_DEGREE_LABELS
        if self.degree_scope == "first":
            normalized_values = {
                _normalize_tre_type_filter(value).replace("-", "_").replace(" ", "_")
                for value in requested_values
            }
            if normalized_values != {"sentenca"}:
                raise QueryRejectedError(
                    "SJUR/TRE primeiro grau aceita somente document_type=sentenca"
                )
            return (TRE_FIRST_DEGREE_LABEL,)
        labels: list[str] = []
        for value in requested_values:
            normalized = _normalize_tre_type_filter(value).replace("-", "_").replace(" ", "_")
            if normalized == "sentenca":
                raise QueryRejectedError("SJUR/TRE segundo grau nao aceita document_type=sentenca")
            try:
                mapped = _TRE_SECOND_DEGREE_TYPE_FILTERS[normalized]
            except KeyError as exc:
                raise QueryRejectedError(
                    "SJUR/TRE document_type deve ser acordao, decisao ou resolucao"
                ) from exc
            for label in mapped:
                if label not in labels:
                    labels.append(label)
        return tuple(labels)

    @property
    def search_path(self) -> str:
        return f"/{self._route_slug}/sjur-pesquisa-backend/rest/public/pesquisa/simples"

    def search_partitioned(
        self,
        query: JurisprudenceQuery,
        *,
        max_partitions: int = MAX_DATE_PARTITIONS,
    ) -> SearchPage:
        """Collect a bounded explicit date range in monthly partitions.

        The public SJUR endpoint repeats the same window when ``pagina`` is
        changed, so regular ``search`` intentionally exposes no pagination.
        The endpoint does, however, honor the date range filter.  This opt-in
        collector uses non-overlapping calendar-month requests and trusts a
        partition only when ``totalRegistros`` equals the returned records and
        remains below the observed 1,000-record window.  It never retries a
        blocked request and never turns an incomplete partition into an empty
        result.
        """

        if not query.judgment_date_from or not query.judgment_date_to:
            raise QueryRejectedError(
                "SJUR/TRE coleta particionada exige judgment_date_from e judgment_date_to"
            )
        if query.page != 1:
            raise QueryRejectedError("SJUR/TRE coleta particionada aceita somente page=1")
        if max_partitions < 1 or max_partitions > MAX_DATE_PARTITIONS:
            raise QueryRejectedError(f"max_partitions deve estar entre 1 e {MAX_DATE_PARTITIONS}")
        start = _parse_partition_date(query.judgment_date_from)
        end = _parse_partition_date(query.judgment_date_to)
        if start > end:
            raise QueryRejectedError("intervalo de datas particionado invalido")

        ranges: list[tuple[date, date]] = []
        cursor = start
        while cursor <= end:
            if len(ranges) >= max_partitions:
                raise QueryRejectedError(
                    "intervalo excede o limite de particoes; reduza as datas ou aumente "
                    "o limite explicitamente"
                )
            if cursor.month == 12:
                next_month = date(cursor.year + 1, 1, 1)
            else:
                next_month = date(cursor.year, cursor.month + 1, 1)
            partition_end = min(end, next_month - timedelta(days=1))
            ranges.append((cursor, partition_end))
            cursor = partition_end + timedelta(days=1)

        pages: list[SearchPage] = []
        for partition_start, partition_end in ranges:
            partition_query = replace(
                query,
                judgment_date_from=partition_start.isoformat(),
                judgment_date_to=partition_end.isoformat(),
                page=1,
                page_size=min(query.page_size, 100),
            )
            pages.append(
                self.search(
                    partition_query,
                    _remote_page_size=MAX_PARTITION_REMOTE_SIZE,
                    _date_partition=True,
                )
            )

        unique: dict[str, JurisprudenceResult] = {}
        for page in pages:
            for result in page.results:
                unique.setdefault(result.id, result)
        first_trace = pages[0].source_trace
        if first_trace is not None:
            first_trace = replace(
                first_trace,
                query={
                    **first_trace.query,
                    "date_partition_count": len(ranges),
                    "date_partition_ranges": [
                        {"from": item[0].isoformat(), "to": item[1].isoformat()} for item in ranges
                    ],
                },
                limitations=[
                    *first_trace.limitations,
                    "Coleta opt-in particionada por meses; cada particao foi validada "
                    "contra totalRegistros e o limite da janela remota.",
                ],
            )
        complete = bool(pages) and all(
            page.is_complete is True and page.total_known is True for page in pages
        )
        total = len(unique)
        return SearchPage(
            source=self.name,
            total=total,
            total_known=complete,
            start=1 if unique else 0,
            end=total,
            page=1,
            page_size=query.page_size,
            results=list(unique.values()),
            source_trace=first_trace,
            pagination_mode="date_partition",
            is_complete=complete,
            completeness_reason=(
                f"{len(ranges)} particao(oes) mensais coletadas; "
                "cada janela foi comparada ao total declarado."
                if complete
                else "Uma ou mais particoes excederam a janela ou ficaram incompletas."
            ),
            ordering="source_default",
            filters_applied={
                **pages[0].filters_applied,
                "judgment_date_partition": "remote",
            },
            access_status=AccessStatus.PUBLIC,
            extraction_status=(ExtractionStatus.COMPLETE if complete else ExtractionStatus.PARTIAL),
        )

    def search(
        self,
        query: JurisprudenceQuery,
        *,
        _remote_page_size: int | None = None,
        _date_partition: bool = False,
    ) -> SearchPage:
        # The official TRE route currently returns the same bounded window
        # regardless of the requested page.  Do not expose that duplicate
        # window as a valid second page: callers must explicitly handle the
        # source's unresolved pagination contract instead of seeing repeated
        # records or a false completeness signal.
        if query.page != 1:
            raise QueryRejectedError(
                f"SJUR/{self.tribunal} nao oferece pagina remota comprovada; "
                "use page=1 ou consulte a fonte oficial diretamente"
            )
        page = super().search(
            query,
            _remote_page_size=_remote_page_size,
            _date_partition=_date_partition,
        )
        if page.source_trace is None:
            raise ParserContractChangedError("SJUR/TRE retornou página sem SourceTrace")
        base_trace = page.source_trace
        trace = replace(
            base_trace,
            provider=self.name,
            endpoint=f"POST {self.search_path}",
            source_url=f"{self.base_url}{self.search_path}",
            query={**base_trace.query, "scope": self.tribunal},
        )
        mapped = []
        rejected_other_degree = 0
        rejected_unknown_degree = 0
        for result in page.results:
            result_id = f"{self.name}-{result.id.removeprefix('tse-sjur-')}"
            degree = _infer_tre_degree(result.type)
            if degree is not None and degree != self.degree_scope:
                # Regional SJUR may contain mixed first-/second-instance
                # records. Never leak another degree into this binding.
                rejected_other_degree += 1
                continue
            if degree is None:
                # Unknown labels cannot safely be guessed as appellate.
                rejected_unknown_degree += 1
                continue
            item = replace(
                result,
                id=result_id,
                source=self.name,
                court=self.tribunal,
                authority=self.tribunal,
                degree=degree,
                instance=degree,
                source_trace=trace,
            )
            mapped.append(item)
            self._inline_results[result_id] = item
            if item.document_url:
                self._document_urls[result_id] = item.document_url
        rejected = rejected_other_degree + rejected_unknown_degree
        if rejected:
            # The source total refers to the unfiltered regional corpus, not
            # to the post-filtered appellate subset.
            target_label = "first" if self.degree_scope == "first" else "second"
            other_label = "second" if self.degree_scope == "first" else "first"
            reason = (
                f"SJUR/TRE applied local {target_label}-degree filtering; "
                f"{rejected_other_degree} {other_label}-instance and "
                f"{rejected_unknown_degree} unknown decision type(s) rejected."
            )
            if not mapped:
                reason += (
                    f" No {target_label}-degree record was observed; the remote "
                    f"regional total does not prove an empty {target_label}-degree corpus."
                )
            return replace(
                page,
                source=self.name,
                total=len(mapped),
                total_known=False,
                results=mapped,
                source_trace=trace,
                is_complete=False,
                completeness_reason=reason,
                filters_applied=_tre_filters_applied(
                    query, degree=f"remote+local:{self.degree_scope}"
                ),
            )
        if self.degree_scope in {"first", "second"} and not mapped and page.is_explicit_empty:
            # The first-degree binding sends the official ``Sentença`` filter.
            # A zero returned by that filtered query is authoritative for this
            # surface, unlike a zero produced by a mixed unfiltered window.
            return replace(
                page,
                source=self.name,
                source_trace=trace,
                filters_applied=_tre_filters_applied(query, degree=f"remote:{self.degree_scope}"),
            )
        if mapped:
            if (
                _date_partition
                and page.total < MAX_PARTITION_REMOTE_SIZE
                and len(mapped) == page.total
            ):
                return replace(
                    page,
                    source=self.name,
                    total=len(mapped),
                    total_known=True,
                    results=mapped,
                    source_trace=trace,
                    is_complete=True,
                    pagination_mode="date_partition",
                    completeness_reason=(
                        "A particao temporal retornou todos os registros declarados "
                        "sem atingir a janela maxima observada."
                    ),
                    filters_applied=_tre_filters_applied(
                        query, degree=f"remote+local:{self.degree_scope}"
                    ),
                )
            # A successful response is still only the source's current
            # bounded window: the TRE service returned the same IDs for
            # requested pages 1 and 2 during the 2026-09-09 probe.  Preserve
            # the records, but never advertise that window as exhaustive.
            return replace(
                page,
                source=self.name,
                total=len(mapped),
                total_known=False,
                results=mapped,
                source_trace=trace,
                is_complete=False,
                completeness_reason=(
                    "SJUR/TRE retornou uma janela unica; paginaÃ§ao remota "
                    "nao foi comprovada e o total da janela nao e exaustivo."
                ),
                filters_applied=_tre_filters_applied(
                    query, degree=f"remote+local:{self.degree_scope}"
                ),
            )
        return replace(
            page,
            source=self.name,
            results=mapped,
            total_known=False,
            is_complete=False,
            completeness_reason=(
                "A janela observada nao continha rotulo explicito de primeiro grau; "
                "o total remoto pertence ao corpus regional e nao prova vazio de SJUR."
            ),
            source_trace=trace,
            filters_applied=_tre_filters_applied(query, degree=f"remote+local:{self.degree_scope}"),
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch the official PDF, falling back to observed inline decision text.

        Some SJUR installations advertise ``temInteiroTeorPDF=true`` but the
        public download route responds with an HTML access/error shell while
        the same official search response contains ``textoDecisao`` and
        ``textoEmenta``.  The fallback uses only fields returned by that
        observed query; it does not retry, bypass, or synthesize a document.
        """

        try:
            return super().get_document(document_id)
        except (ParserContractChangedError, SourceUnavailableError) as exc:
            # ``SourceUnavailableError`` also covers a legitimate public
            # result that has no PDF URL (``temInteiroTeorPDF=false``).  If
            # the same official search response carries ``textoDecisao`` or
            # ``textoEmenta``, expose that text instead of making the user
            # lose an otherwise valid decision.  Other source failures are
            # re-raised below when no inline result is available.
            if isinstance(exc, ParserContractChangedError) and "invalid_magic" not in str(exc):
                raise
        result = self._inline_results.get(document_id)
        if result is None:
            raise SourceUnavailableError(
                "SJUR/TRE documento inline somente esta disponivel para um resultado observado"
            )
        text = (result.full_text or result.summary or "").strip()
        if not text:
            raise ParserContractChangedError("SJUR/TRE resultado observado nao possui texto inline")
        base_trace = result.source_trace
        if base_trace is None:
            base_trace = SourceTrace(
                provider=self.name,
                endpoint="POST /pesquisa/simples",
                source_url=f"{self.base_url}{self.search_path}",
            )
        trace = replace(
            base_trace,
            provider=self.name,
            endpoint=base_trace.endpoint if base_trace else "POST /pesquisa/simples",
            query={"document_id": document_id, "extraction": "search_inline"},
            limitations=list(base_trace.limitations if base_trace else [])
            + [
                "O download PDF oficial respondeu shell sem assinatura PDF; "
                "textoDecisao/ textoEmenta da mesma busca foram usados como fallback.",
                "Fallback limitado ao resultado observado na sessao; "
                "nenhum corpo externo foi contornado.",
            ],
            transformations=list(base_trace.transformations if base_trace else [])
            + ["official_search_inline_text"],
            retrieval_status="ok",
        )
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type=result.document_type or result.type or "decisao",
            content=text.encode("utf-8"),
            content_type="text/plain",
            url=result.document_url,
            title=f"{self.tribunal} SJUR inteiro teor (texto oficial)",
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={
                "document_url": result.document_url,
                "fallback": "official_search_inline_text",
                "pdf_download_status": "invalid_magic",
                "source_id": document_id,
            },
            parser=f"{self.name}.inline_document",
            parser_version="1",
            text_override=text,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        base = super().get_capabilities()
        supported = list(base.supported_filters)
        for filter_name in (
            "types",
            "degree",
            "document_type",
            "decision_type",
            "authority",
            "case_class",
            "rapporteur",
            "party_name",
            "judgment_date_from",
            "judgment_date_to",
            "published_from",
            "published_to",
            "election_year",
            "observations",
            "tags",
            "municipality",
            "publication_source",
            "publication_number",
            "publication_volume",
            "uf",
        ):
            if filter_name not in supported:
                supported.append(filter_name)
        semantics = dict(base.filter_semantics)
        semantics.update(
            {
                "degree": "validated_scope",
                "types": "native",
                "document_type": "native",
                "decision_type": "native",
                "authority": "validated_scope",
                "case_class": "native",
                "rapporteur": "native",
                "party_name": "native",
                "judgment_date_from": "native",
                "judgment_date_to": "native",
                "published_from": "native",
                "published_to": "native",
                "election_year": "native",
                "observations": "native",
                "tags": "native",
                "municipality": "native",
                "publication_source": "native",
                "publication_number": "native",
                "publication_volume": "native",
                "uf": "native",
            }
        )
        return replace(
            base,
            document_types=["acordao", "decisao", "resolucao"],
            unsupported_filters=[
                item
                for item in base.unsupported_filters
                if item
                not in {
                    "types",
                    "degree",
                    "document_type",
                    "decision_type",
                    "authority",
                    "case_class",
                    "rapporteur",
                    "party_name",
                    "judgment_date_from",
                    "judgment_date_to",
                    "published_from",
                    "published_to",
                    "election_year",
                    "observations",
                    "tags",
                    "municipality",
                    "publication_source",
                    "publication_number",
                    "publication_volume",
                    "uf",
                }
            ],
            supported_filters=supported,
            filter_semantics=semantics,
            source=self.name,
            display_name=(
                f"{self.tribunal} SJUR jurisprudencia textual "
                f"({self.degree_scope}-degree candidato)"
            ),
            source_url="https://jurisprudencia-tres.tse.jus.br",
            semantic_discriminator=(
                f"authority={self.tribunal};branch=electoral;"
                f"degree={self.degree_scope};instance={self.degree_scope};collection=SJUR"
            ),
            endpoints=[f"POST {self.search_path}", *base.endpoints[1:]],
            limitations=[
                *base.limitations,
                "A instancia e limitada ao TRE configurado; nao representa outros TREs.",
            ],
        )

    def _request(
        self,
        payload: dict[str, Any],
        *,
        decision_type_labels: tuple[str, ...] | None = None,
    ):
        rewritten = dict(payload)
        rewritten["tribunais"] = [self._route_slug]
        try:
            dsl = json.loads(str(rewritten.get("termoPesquisa", "{}")))
            bool_query = dsl.setdefault("bool", {})
            existing_filters = bool_query.get("filter", [])
            if not isinstance(existing_filters, list):
                raise TypeError("filter must be a list")
            # ``build_tse_query`` starts with the TSE authority filter.  Keep
            # all semantic filters (class, party and dates), replacing only
            # the fixed authority/type clauses for the concrete TRE route.
            filters = [clause for clause in existing_filters if not _is_sjur_scope_clause(clause)]
            filters.insert(0, {"terms": {"siglaTribunalJE.keyword": [self.tribunal]}})
            labels = decision_type_labels or self._remote_decision_type_labels(JurisprudenceQuery())
            if labels:
                filters.append({"terms": {"descricaoTipoDecisao.keyword": list(labels)}})
            bool_query["filter"] = filters
            rewritten["termoPesquisa"] = json.dumps(dsl, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise QueryRejectedError("SJUR/TRE recebeu DSL invalida") from exc
        request = TransportRequest(
            source=self.name,
            operation="search",
            method="POST",
            url=f"{self.base_url}{self.search_path}",
            json_body=rewritten,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            idempotent=False,
        )
        response = self.transport.request(request)
        if response.status in {
            TransportStatus.TIMEOUT,
            TransportStatus.TLS_ERROR,
            TransportStatus.SOURCE_UNAVAILABLE,
            TransportStatus.RESPONSE_TOO_LARGE,
            TransportStatus.CIRCUIT_OPEN,
        }:
            raise SourceUnavailableError(f"SJUR/{self.tribunal} transporte indisponivel")
        if response.status_code == 429:
            raise RateLimitDetectedError(f"SJUR/{self.tribunal} retornou HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError(f"SJUR/{self.tribunal} exige validacao de acesso")
        if response.status_code in {400, 422}:
            raise QueryRejectedError(f"SJUR/{self.tribunal} rejeitou a consulta")
        if response.status_code is None or response.status_code >= 500:
            raise SourceUnavailableError(f"SJUR/{self.tribunal} retornou resposta indisponivel")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"SJUR/{self.tribunal} rejeitou a requisicao")
        return response


class TreSjurFirstDegreeProvider(TreSjurJurisprudenciaProvider):
    """Opt-in adapter for explicit first-degree SJUR/TRE decisions."""

    def __init__(self, *args: Any, tribunal: str = "TRE-SP", **kwargs: Any) -> None:
        super().__init__(*args, tribunal=tribunal, degree_scope="first", **kwargs)

    def get_capabilities(self) -> ProviderCapabilities:
        capabilities = super().get_capabilities()
        supported = list(capabilities.supported_filters)
        for filter_name in ("degree", "document_type", "authority"):
            if filter_name not in supported:
                supported.append(filter_name)
        semantics = dict(capabilities.filter_semantics)
        semantics.update(
            {
                "degree": "validated_scope",
                "document_type": "native",
                "authority": "validated_scope",
            }
        )
        return replace(
            capabilities,
            document_types=["sentenca"],
            unsupported_filters=[
                item
                for item in capabilities.unsupported_filters
                if item not in {"degree", "document_type", "authority"}
            ],
            detail_modes=["inline_decision_field"],
            supported_filters=supported,
            filter_semantics=semantics,
            semantic_discriminator=(
                f"authority={self.tribunal};branch=electoral;"
                "degree=first;instance=first;collection=SJUR;document_type=sentenca"
            ),
        )


class TreSjurJurisprudenciaFamilyProvider(JurisprudenceProvider):
    """Dispatch the public SJUR/TRE contract by an explicit TRE authority.

    The source exposes one route per regional electoral court.  Keeping a
    family binding avoids duplicating transport and parser code while still
    requiring callers to name the authority explicitly.  It is intentionally
    opt-in: the per-UF route currently has no proven remote pagination and
    some observed PDF links return a non-PDF error body.
    """

    name = "tre_sjur_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = session or requests.Session()
        self._providers: dict[str, TreSjurJurisprudenciaProvider] = {}

    def _provider_for(self, authority: str) -> TreSjurJurisprudenciaProvider:
        normalized = _normalize_tre_query(authority)
        provider = self._providers.get(normalized)
        if provider is None:
            provider = TreSjurJurisprudenciaProvider(
                self.config,
                session=self.session,
                tribunal=normalized,
            )
            self._providers[normalized] = provider
        return provider

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if not query.authority:
            raise QueryRejectedError("SJUR/TRE exige authority explicita (por exemplo, TRE-SP)")
        # The concrete adapter uses an authority-qualified source name (for
        # example ``tre_sp_sjur_jurisprudencia``).  At the family boundary the
        # page must advertise the registered family source, otherwise the
        # federated envelope can reject it as a misattributed page.  Keep the
        # authority-specific record/source identity in the result itself while
        # normalizing only the page and trace envelope.
        page = self._provider_for(query.authority).search(query)
        trace = page.source_trace
        if trace is not None:
            trace = replace(
                trace,
                provider=self.name,
                transformations=[
                    *trace.transformations,
                    f"family_authority={query.authority.upper()}",
                ],
            )
        return replace(page, source=self.name, source_trace=trace)

    def search_authorities(
        self,
        query: JurisprudenceQuery,
        authorities: Sequence[str],
    ) -> SearchPage:
        """Run an explicit, serial batch across named TRE authorities.

        The family intentionally has no implicit national scope.  This method
        is the opt-in escape hatch for callers that explicitly choose a set of
        UFs (up to all 27), while retaining per-authority outcomes in
        ``SearchPage.aggregations``.  Requests are serial and page 1 only;
        the public service's unverified remote pagination is never hidden.
        """

        if query.authority:
            raise QueryRejectedError(
                "SJUR/TRE lote explicito nao aceita authority dentro da consulta"
            )
        if not authorities:
            raise QueryRejectedError("SJUR/TRE lote explicito exige ao menos uma authority")
        if len(authorities) > MAX_AUTHORITY_BATCH:
            raise QueryRejectedError(
                f"SJUR/TRE lote explicito aceita no maximo {MAX_AUTHORITY_BATCH} authorities"
            )

        normalized: list[str] = []
        for value in authorities:
            authority = _normalize_tre_query(value)
            if authority not in normalized:
                normalized.append(authority)
        if not normalized:
            raise QueryRejectedError("SJUR/TRE lote explicito nao possui authorities validas")

        pages: list[SearchPage] = []
        authority_status: dict[str, dict[str, Any]] = {}
        authority_trace: dict[str, dict[str, Any]] = {}
        for authority in normalized:
            scoped_query = replace(query, authority=authority, page=1)
            try:
                page = self.search(scoped_query)
            except AccessControlRequiredError:
                authority_status[authority] = {"status": "access_blocked"}
                authority_trace[authority] = {
                    "trace_status": "unavailable",
                    "status": "access_blocked",
                }
                continue
            except RateLimitDetectedError:
                authority_status[authority] = {"status": "rate_limited"}
                authority_trace[authority] = {
                    "trace_status": "unavailable",
                    "status": "rate_limited",
                }
                continue
            except SourceUnavailableError:
                authority_status[authority] = {"status": "source_unavailable"}
                authority_trace[authority] = {
                    "trace_status": "unavailable",
                    "status": "source_unavailable",
                }
                continue
            except ParserContractChangedError:
                authority_status[authority] = {"status": "schema_invalid"}
                authority_trace[authority] = {
                    "trace_status": "unavailable",
                    "status": "schema_invalid",
                }
                continue
            pages.append(page)
            authority_status[authority] = {
                "status": (
                    "success_with_results"
                    if page.results
                    else "authoritative_empty"
                    if page.is_explicit_empty
                    else "unconfirmed_empty"
                ),
                "returned": len(page.results),
                "total_known": page.total_known,
                "is_complete": page.is_complete,
            }
            authority_trace[authority] = _authority_trace_summary(page.source_trace)

        unique: dict[str, JurisprudenceResult] = {}
        for page in pages:
            for result in page.results:
                unique.setdefault(result.id, result)
        first_trace = pages[0].source_trace if pages else None
        if first_trace is not None:
            first_trace = replace(
                first_trace,
                query={
                    **first_trace.query,
                    "authority_batch": normalized,
                    "authority_batch_count": len(normalized),
                },
                limitations=[
                    *first_trace.limitations,
                    "Lote explicito serial por autoridade; nao e escopo agregado padrao.",
                ],
            )
        failures = [
            authority
            for authority, outcome in authority_status.items()
            if outcome["status"] not in {"success_with_results", "authoritative_empty"}
        ]
        all_complete = (
            bool(pages) and not failures and all(page.is_complete is True for page in pages)
        )
        all_totals_known = (
            bool(pages) and not failures and all(page.total_known is True for page in pages)
        )
        return SearchPage(
            source=self.name,
            total=len(unique),
            total_known=all_totals_known,
            start=1 if unique else 0,
            end=len(unique),
            page=1,
            page_size=query.page_size,
            results=list(unique.values()),
            aggregations={
                "authority_status": authority_status,
                "authority_batch": normalized,
                "authority_trace": authority_trace,
            },
            source_trace=first_trace,
            pagination_mode="authority_batch",
            is_complete=all_complete,
            completeness_reason=(
                "Todas as authorities selecionadas foram consultadas; "
                "a paginacao remota de cada rota permanece independente."
                if not failures
                else f"Authorities sem resultado confirmado: {', '.join(failures)}."
            ),
            ordering="source_default",
            filters_applied={"authority": "explicit_batch"},
            access_status=AccessStatus.PUBLIC if not failures else AccessStatus.PARTIAL,
            access_reason=(
                None
                if not failures
                else "Falha por autoridade preservada em aggregations.authority_status: "
                + ", ".join(
                    f"{authority}={authority_status[authority]['status']}" for authority in failures
                )
            ),
            extraction_status=(
                ExtractionStatus.COMPLETE if not failures else ExtractionStatus.PARTIAL
            ),
        )

    def search_partitioned(
        self,
        query: JurisprudenceQuery,
        *,
        max_partitions: int = MAX_DATE_PARTITIONS,
    ) -> SearchPage:
        """Expose the bounded date collector at the family boundary.

        The authority remains mandatory: the family is a dispatcher, not an
        implicit national aggregate.  Results keep the authority-qualified
        IDs while the page/trace envelope uses the registered family source.
        """

        if not query.authority:
            raise QueryRejectedError("SJUR/TRE exige authority explicita para coleta particionada")
        page = self._provider_for(query.authority).search_partitioned(
            query, max_partitions=max_partitions
        )
        trace = page.source_trace
        if trace is not None:
            trace = replace(
                trace,
                provider=self.name,
                transformations=[
                    *trace.transformations,
                    f"family_authority={query.authority.upper()}",
                ],
            )
        return replace(page, source=self.name, source_trace=trace)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        prefix, separator, _ = precedent_id.partition("-")
        if not separator or not prefix.startswith("tre_"):
            raise QueryRejectedError("identificador SJUR/TRE deve incluir a UF observada")
        parts = prefix.split("_")
        if len(parts) < 2:
            raise QueryRejectedError("identificador SJUR/TRE deve incluir a UF observada")
        state = parts[1].upper()
        return self._provider_for(f"TRE-{state}").get_decisions(precedent_id)

    def get_document(self, document_id: str):
        prefix, separator, _ = document_id.partition("-")
        if not separator or not prefix.startswith("tre_"):
            raise QueryRejectedError("documento SJUR/TRE deve incluir a UF observada")
        parts = prefix.split("_")
        if len(parts) < 2:
            raise QueryRejectedError("documento SJUR/TRE deve incluir a UF observada")
        state = parts[1].upper()
        return self._provider_for(f"TRE-{state}").get_document(document_id)

    def get_parameters(self) -> dict[str, Any]:
        return {
            "source_url": self.config.tse_sjur_url,
            "api_base_url": self.config.tse_sjur_api_url,
            "authorities": list(TRE_AUTHORITIES),
            "status": "opt_in_family_no_remote_pagination",
        }

    def get_capabilities(self) -> ProviderCapabilities:
        base = self._provider_for("TRE-SP").get_capabilities()
        semantics = dict(base.filter_semantics)
        semantics["authority"] = "required_scope"
        supported = list(base.supported_filters)
        if "authority" not in supported:
            supported.append("authority")
        return replace(
            base,
            source=self.name,
            display_name="SJUR/TRE jurisprudencia textual (família opt-in)",
            source_url="https://jurisprudencia-tres.tse.jus.br",
            semantic_discriminator=(
                "authority=TRE-XX;branch=electoral;degree=second;collection=SJUR"
            ),
            supported_filters=supported,
            filter_semantics=semantics,
            limitations=[
                *base.limitations,
                (
                    "A authority deve ser informada para selecionar uma UF; "
                    "não há escopo agregado implícito."
                ),
                "A paginação por UF e o download PDF permanecem gates pendentes.",
            ],
        )


class TreSjurFirstDegreeFamilyProvider(TreSjurJurisprudenciaFamilyProvider):
    """Dispatcher for first-degree SJUR/TRE records, always opt-in."""

    name = "tre_sjur_first_degree"

    def _provider_for(self, authority: str) -> TreSjurFirstDegreeProvider:
        normalized = _normalize_tre_query(authority)
        provider = self._providers.get(normalized)
        if provider is None:
            provider = TreSjurFirstDegreeProvider(
                self.config,
                session=self.session,
                tribunal=normalized,
            )
            self._providers[normalized] = provider
        return provider  # type: ignore[return-value]

    def get_parameters(self) -> dict[str, Any]:
        parameters = super().get_parameters()
        parameters["status"] = "opt_in_first_degree_family_no_remote_pagination"
        return parameters

    def get_capabilities(self) -> ProviderCapabilities:
        capabilities = super().get_capabilities()
        return replace(
            capabilities,
            source=self.name,
            display_name="SJUR/TRE jurisprudencia de primeiro grau (família opt-in)",
            semantic_discriminator=(
                "authority=TRE-XX;branch=electoral;degree=first;instance=first;collection=SJUR"
            ),
            limitations=[
                *capabilities.limitations,
                "Apenas rótulos explícitos de sentença/primeiro grau são aceitos.",
            ],
        )


def _normalize_tre(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if len(normalized) != 6 or not normalized.startswith("TRE-") or not normalized[-2:].isalpha():
        raise ValueError("SJUR/TRE exige autoridade no formato TRE-XX")
    if normalized.removeprefix("TRE-") not in _TRE_STATES:
        raise ValueError(
            "SJUR/TRE exige uma autoridade eleitoral regional válida (uma das 27 UFs: TRE-XX)"
        )
    return normalized


def _authority_trace_summary(trace: SourceTrace | None) -> dict[str, Any]:
    """Return bounded transport facts for an explicit authority batch.

    The complete ``SourceTrace`` (including the submitted query) remains on
    each page/result.  The family aggregate only needs transport metadata to
    explain partial batches, so it deliberately omits query text and body
    data instead of duplicating them in ``aggregations``.
    """

    if trace is None:
        return {"trace_status": "missing"}
    return {
        "trace_status": "available",
        "retrieved_at": trace.retrieved_at,
        "endpoint": trace.endpoint,
        "source_url": trace.source_url,
        "http_status": trace.http_status,
        "final_url": trace.final_url,
        "content_type": trace.content_type,
        "response_bytes": trace.response_bytes,
        "elapsed_ms": trace.elapsed_ms,
        "retrieval_status": trace.retrieval_status,
    }


# Backwards-compatible private alias for existing probes and integrations.
# New code should consume ``TRE_STATES`` or ``TRE_AUTHORITIES`` instead.
_TRE_STATES = TRE_STATES


def _normalize_tre_query(value: str) -> str:
    normalized = str(value or "").strip().upper().replace(" ", "")
    if normalized.startswith("TRE-"):
        try:
            return _normalize_tre(normalized)
        except ValueError as exc:
            raise QueryRejectedError(str(exc)) from exc
    if normalized.startswith("TRE") and len(normalized) == 5:
        try:
            return _normalize_tre(f"TRE-{normalized[-2:]}")
        except ValueError as exc:
            raise QueryRejectedError(str(exc)) from exc
    raise QueryRejectedError("authority SJUR/TRE deve estar no formato TRE-XX")


def _infer_tre_degree(decision_type: str | None) -> str | None:
    """Classify only explicit SJUR decision labels.

    Regional SJUR may contain first-instance sentences alongside appellate
    decisions. Unknown labels are intentionally rejected instead of being
    guessed as second degree.
    """

    normalized = " ".join(str(decision_type or "").casefold().split())
    normalized_ascii = _normalize_tre_type_filter(normalized)
    if not normalized:
        return None
    if "senten" in normalized_ascii or "primeiro grau" in normalized_ascii:
        return "first"
    appellate_markers = (
        "acord",
        "decisao monocratic",
        "decisão monocrátic",
        "resolu",
        "instrução",
    )
    # A few SJUR responses observed in the wild contain a replacement
    # character in Portuguese labels (for example an encoded ``Acórdão``).
    # Recognize only the affected known fragments; arbitrary unknown text is
    # still rejected rather than guessed as second degree.
    if (
        any(marker in normalized_ascii for marker in appellate_markers)
        or ("ac" in normalized and "rd" in normalized)
        or ("decis" in normalized and "monocr" in normalized)
    ):
        return "second"
    return None


__all__ = [
    "TreSjurFirstDegreeFamilyProvider",
    "TreSjurFirstDegreeProvider",
    "TreSjurJurisprudenciaFamilyProvider",
    "TreSjurJurisprudenciaProvider",
    "TseSjurJurisprudenciaProvider",
    "build_tse_query",
    "parse_tse_response",
]
