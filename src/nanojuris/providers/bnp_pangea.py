"""BNP/Pangea public provider."""

from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import urlparse

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
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
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus


class BnpPangeaProvider(JurisprudenceProvider):
    """Provider for the public Pangea/BNP frontend API."""

    name = "bnp_pangea"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.bnp_api_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=4_000_000,
                # The public API is used by a browser frontend and may expose
                # rate-limit or gateway decisions.  Do not repeat those
                # requests automatically; callers can retry explicitly.
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._catalog_codes: tuple[list[str], list[str]] | None = None
        self._last_http_metadata: dict[str, Any] = {}

    def get_parameters(self) -> dict[str, Any]:
        data = self._request_json("GET", "/parametros")
        if not isinstance(data, dict):
            raise ParserContractChangedError("BNP parametros response is not an object")
        return data

    def get_catalog(self) -> ProviderCatalog:
        endpoint = "/parametros"
        data = self.get_parameters()
        self._validate_parameters_response(data)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            source_url=self.config.bnp_api_url.rstrip("/") + endpoint,
            limitations=[
                "Catalogo publico exposto pela interface Pangea/BNP.",
                "Orgaos marcados como sem precedentes podem aparecer desabilitados.",
            ],
            **self._last_http_metadata,
        )
        return ProviderCatalog(
            source=self.name,
            courts=self._map_options(data.get("orgaos") or [], disabled_key="semPrecedentes"),
            species=self._map_options(data.get("especies") or []),
            species_groups=list(data.get("gruposEspecies") or []),
            source_trace=trace,
            raw=data,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="Banco Nacional de Precedentes/Pangea",
            source_url=self.config.bnp_api_url,
            category="qualified_precedents",
            search_modes=["text", "court", "species", "number", "date_range"],
            document_types=["precedent", "linked_decision_metadata"],
            content_formats=["json"],
            canonical_records=["CanonicalPrecedent"],
            extracted_fields=[
                "court",
                "precedent_type",
                "number",
                "question",
                "thesis",
                "status",
                "updated_at",
                "paradigm_cases",
                "aggregations",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /parametros",
                "GET /sugestoes",
                "POST /precedentes",
                "GET /precedentes/{id}/decisoes",
            ],
            supports_full_text=False,
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            full_text_access="not_available",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=True,
            supports_live_tests=True,
            supported_filters=[
                "text",
                "number",
                "courts",
                "types",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "updated_from",
                "updated_to",
            ],
            filter_semantics={
                name: "native"
                for name in (
                    "text",
                    "number",
                    "courts",
                    "types",
                    "all_words",
                    "any_words",
                    "without_words",
                    "exact_phrase",
                    "updated_from",
                    "updated_to",
                )
            },
            unsupported_filters=[
                "rapporteur",
                "published_from",
                "published_to",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
                "source_origin",
                "source_origins",
                "fetch_details",
                "case_class",
                "judging_body",
                "degree",
                "instance",
                "branch",
                "legal_area",
                "authority",
                "collection",
                "document_type",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "party_name",
                "party_document",
            ],
            limitations=[
                "O endpoint /precedentes exige 'orgaos' e 'tipos' nao vazios; quando a "
                "consulta nao os informa, o provider os preenche com o catalogo publico "
                "completo (todos os orgaos e especies).",
                "Disponibilidade depende da API publica usada pelo frontend Pangea/BNP.",
                "Nem todo precedente possui textos de decisoes no endpoint publico.",
            ],
            responsible_use=[
                "Aplicar timeout e rate limit em consultas em lote.",
                "Preservar SourceTrace e payload de consulta para auditoria.",
            ],
        )

    def list_courts(self, *, include_disabled: bool = False) -> list[ProviderOption]:
        courts = self.get_catalog().courts
        if include_disabled:
            return courts
        return [court for court in courts if not court.disabled]

    def list_species(self) -> list[ProviderOption]:
        return self.get_catalog().species

    def list_suggestions(self, text: str) -> list[str]:
        if not text.strip():
            return []
        try:
            data = self._request_json("GET", "/sugestoes", params={"texto": text})
        except SourceUnavailableError as exc:
            if "HTTP 404" in str(exc):
                return []
            raise
        if isinstance(data, list):
            return [str(item) for item in data]
        raise ParserContractChangedError("BNP suggestions response is not a list")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/precedentes"
        payload = {"filtro": self._build_filter(query)}
        data = self._request_json("POST", endpoint, json=payload)
        self._validate_search_response(data)

        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=payload,
            source_url=self.config.bnp_api_url.rstrip("/") + endpoint,
            limitations=[
                "Fonte publica consumida a partir da API usada pelo frontend Pangea/BNP.",
                "Resultados dependem da disponibilidade e do contrato atual da fonte.",
            ],
            **self._last_http_metadata,
        )

        results = [self._map_result(item, trace) for item in data.get("resultados", [])]
        total = _coerce_total(data.get("total"))
        start = int(data.get("posicao_inicial") or 0)
        end = int(data.get("posicao_final") or 0)
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
            end=end,
            page=query.page,
            page_size=query.page_size,
            results=results,
            aggregations={
                "species": list(data.get("aggsEspecies") or []),
                "courts": list(data.get("aggsOrgaos") or []),
            },
            source_trace=trace,
            pagination_mode="page",
            is_complete=complete,
            completeness_reason=reason,
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=(ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        endpoint = f"/precedentes/{precedent_id}/decisoes"
        data = self._request_json("GET", endpoint)
        if not isinstance(data, dict):
            raise ParserContractChangedError("BNP decisions response is not an object")

        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={"precedent_id": precedent_id},
            source_url=self.config.bnp_api_url.rstrip("/") + endpoint,
            limitations=[
                "Nem todo precedente possui textos de decisoes no endpoint publico.",
            ],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=data.get("relator"),
            procedural_follow_url=data.get("linkAcompanhamentoProcesssual")
            or data.get("linkAcompanhamentoProcessual"),
            texts=list(data.get("textos") or []),
            source_trace=trace,
            raw=data,
        )

    def _build_filter(self, query: JurisprudenceQuery) -> dict[str, Any]:
        courts = list(query.courts or [])
        types = list(query.types or [])
        if not courts or not types:
            # The /precedentes endpoint rejects empty 'orgaos'/'tipos' with
            # HTTP 400; reproduce the old "search everything" behaviour by
            # backfilling from the public catalog.
            catalog_courts, catalog_types = self._catalog_filter_codes()
            courts = courts or catalog_courts
            types = types or catalog_types
        return {
            "buscaGeral": query.text,
            "todasPalavras": query.all_words,
            "quaisquerPalavras": query.any_words,
            "semPalavras": query.without_words,
            "trechoExato": query.exact_phrase,
            "atualizacaoDesde": query.updated_from,
            "atualizacaoAte": query.updated_to,
            "cancelados": query.include_cancelled,
            "ordenacao": query.order_by,
            "nr": query.number,
            "pagina": query.page,
            "tamanhoPagina": query.page_size,
            "orgaos": courts,
            "tipos": types,
        }

    def _catalog_filter_codes(self) -> tuple[list[str], list[str]]:
        if self._catalog_codes is None:
            data = self._request_json("GET", "/parametros")
            if not isinstance(data, dict):
                raise ParserContractChangedError("BNP parametros response is not an object")
            courts = [
                code
                for option in data.get("orgaos") or []
                if isinstance(option, dict) and (code := str(option.get("sigla") or ""))
            ]
            types = [
                code
                for option in data.get("especies") or []
                if isinstance(option, dict) and (code := str(option.get("sigla") or ""))
            ]
            if not courts or not types:
                raise ParserContractChangedError(
                    "BNP catalog has no orgaos/especies to build a default search filter"
                )
            self._catalog_codes = (courts, types)
        return self._catalog_codes

    def _map_result(
        self,
        item: dict[str, Any],
        trace: SourceTrace,
    ) -> JurisprudenceResult:
        precedent_id = str(item.get("id") or "")
        if not precedent_id:
            raise ParserContractChangedError("BNP result without id")

        cases = [
            ParadigmCase(
                number=str(case.get("numero") or ""),
                case_class=case.get("classe"),
                url=case.get("link"),
            )
            for case in item.get("processosParadigma") or []
            if isinstance(case, dict)
        ]

        highlight = item.get("highlight")
        highlights = highlight if isinstance(highlight, dict) else {}

        return JurisprudenceResult(
            id=precedent_id,
            source=self.name,
            court=str(item.get("orgao") or ""),
            type=str(item.get("tipo") or ""),
            number=item.get("nr"),
            question=item.get("questao"),
            thesis=item.get("tese"),
            status=item.get("situacao"),
            updated_at=item.get("ultimaAtualizacao"),
            paradigm_cases=cases,
            highlights={str(k): str(v) for k, v in highlights.items()},
            source_trace=trace,
            raw=item,
        )

    def _request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self.config.bnp_api_url.rstrip("/") + path
        headers = {
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }
        response = self.transport.request(
            TransportRequest(
                source=self.name,
                operation=f"{method.upper()} {path}",
                method=method,
                url=url,
                params=dict(kwargs.get("params") or {}),
                json_body=kwargs.get("json"),
                headers=headers,
                idempotent=method.upper() in {"GET", "HEAD"},
            )
        )
        content = response.body
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response.final_url or url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256 or hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": (
                "ok"
                if response.status is TransportStatus.COMPLETE
                and response.status_code is not None
                and response.status_code < 400
                else "error"
            ),
            "elapsed_ms": response.elapsed_ms,
        }

        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"BNP transport failed: {response.status.value}")

        status_code = response.status_code
        if status_code == 429:
            raise RateLimitDetectedError("BNP returned HTTP 429")
        if status_code is None:
            raise SourceUnavailableError("BNP returned no HTTP status")
        if status_code >= 500:
            raise SourceUnavailableError(f"BNP returned HTTP {status_code}")
        if status_code >= 400:
            detail = " ".join(response.text.split())[:300]
            payload = kwargs.get("json") or kwargs.get("params") or {}
            if status_code == 400:
                raise QueryRejectedError(
                    f"BNP rejected request with HTTP {status_code}"
                    f"; response={detail!r}; payload={payload!r}; "
                    "hint=the /precedentes endpoint requires non-empty 'orgaos' and "
                    "'tipos'; NanoJuris fills them from the public catalog when the "
                    "query does not, so a 400 here signals a further contract change"
                )
            raise SourceUnavailableError(
                f"BNP rejected request with HTTP {status_code}; response={detail!r}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise ParserContractChangedError("BNP response is not valid JSON") from exc

    @staticmethod
    def _map_options(items: list[Any], *, disabled_key: str | None = None) -> list[ProviderOption]:
        options: list[ProviderOption] = []
        for item in items:
            if not isinstance(item, dict):
                raise ParserContractChangedError("BNP catalog option is not an object")
            code = str(item.get("sigla") or "")
            description = str(item.get("descricao") or "")
            if not code or not description:
                raise ParserContractChangedError("BNP catalog option missing sigla/descricao")
            options.append(
                ProviderOption(
                    code=code,
                    description=description,
                    alias=str(item.get("apelido") or "") or None,
                    disabled=bool(item.get(disabled_key)) if disabled_key else False,
                    metadata={
                        key: value
                        for key, value in item.items()
                        if key not in {"sigla", "descricao", "apelido", disabled_key}
                    },
                )
            )
        return options

    @staticmethod
    def _validate_search_response(data: Any) -> None:
        if not isinstance(data, dict):
            raise ParserContractChangedError("BNP search response is not an object")
        for key in ("resultados", "total"):
            if key not in data:
                raise ParserContractChangedError(f"BNP search response missing {key!r}")
        if not isinstance(data.get("resultados"), list):
            raise ParserContractChangedError("BNP search resultados is not a list")

    @staticmethod
    def _validate_parameters_response(data: Any) -> None:
        if not isinstance(data, dict):
            raise ParserContractChangedError("BNP parameters response is not an object")
        for key in ("orgaos", "especies"):
            if key not in data:
                raise ParserContractChangedError(f"BNP parameters response missing {key!r}")
            if not isinstance(data.get(key), list):
                raise ParserContractChangedError(f"BNP parameters {key!r} is not a list")


def _short_response_text(response: requests.Response) -> str:
    text = getattr(response, "text", "") or ""
    return " ".join(text.split())[:300]


def _coerce_total(value: Any) -> int:
    try:
        total = int(value)
    except (TypeError, ValueError) as exc:
        raise ParserContractChangedError("BNP search response total is not an integer") from exc
    if total < 0:
        raise ParserContractChangedError("BNP search response total cannot be negative")
    return total
