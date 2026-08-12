"""BNP/Pangea public provider."""

from __future__ import annotations

import time
from typing import Any

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
    JurisprudenceQuery,
    JurisprudenceResult,
    ParadigmCase,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider


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
        self._last_request = 0.0

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
            supports_full_text=True,
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
            limitations=[
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
        )

        results = [self._map_result(item, trace) for item in data.get("resultados", [])]
        return SearchPage(
            source=self.name,
            total=int(data.get("total") or 0),
            start=int(data.get("posicao_inicial") or 0),
            end=int(data.get("posicao_final") or 0),
            page=query.page,
            page_size=query.page_size,
            results=results,
            aggregations={
                "species": list(data.get("aggsEspecies") or []),
                "courts": list(data.get("aggsOrgaos") or []),
            },
            source_trace=trace,
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
            "orgaos": query.courts,
            "tipos": query.types,
        }

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
        self._respect_rate_limit()
        url = self.config.bnp_api_url.rstrip("/") + path
        headers = {
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"BNP request failed: {exc}") from exc

        if response.status_code == 429:
            raise RateLimitDetectedError("BNP returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"BNP returned HTTP {response.status_code}")
        if response.status_code >= 400:
            detail = _short_response_text(response)
            payload = kwargs.get("json") or kwargs.get("params") or {}
            if response.status_code == 400:
                raise QueryRejectedError(
                    f"BNP rejected request with HTTP {response.status_code}"
                    f"; response={detail!r}; payload={payload!r}; "
                    "hint=try a longer legal expression, precedent species, court filters, "
                    "or the dedicated suggestions/catalog endpoints"
                )
            raise SourceUnavailableError(
                f"BNP rejected request with HTTP {response.status_code}; response={detail!r}"
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

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()

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
