"""Catalog adapter for the public SJUR/TSE jurisprudence metadata API.

The public catalog routes are useful for discovering electoral classes,
rapporteurs, elections and norms. The decision-search routes are intentionally
not promoted here because the local evidence does not contain a reproducible
result contract.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any
from urllib.parse import urljoin

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedQueryError,
)
from nanojuris.models import (
    AccessStatus,
    DecisionBundle,
    JurisprudenceQuery,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider


CATALOG_ROUTES = ("classes", "relatorias", "eleicoes", "normas")


class JusticaEleitoralSjurProvider(JurisprudenceProvider):
    """Expose only the officially reproduced SJUR/TSE catalog surface."""

    name = "justica_eleitoral_sjur"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    @property
    def api_base_url(self) -> str:
        return self.config.tse_sjur_api_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        raise UnsupportedQueryError(
            "SJUR/TSE possui somente catalogo promovido; a busca decisoria "
            "aguarda contrato de resultados reproduzivel"
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise UnsupportedQueryError(
            "SJUR/TSE ainda nao possui detalhe decisorio promovido no NanoJuris"
        )

    def get_catalog(self, *, tribunal: str = "TSE") -> ProviderCatalog:
        normalized_tribunal = tribunal.strip().upper() or "TSE"
        catalogs = {
            route: self._request_catalog(route, tribunal=normalized_tribunal)
            for route in CATALOG_ROUTES
        }
        classes = self._options(catalogs["classes"], category="class")
        trace = SourceTrace(
            provider=self.name,
            endpoint="POST /{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa/{route}",
            source_url=self.config.tse_sjur_url,
            query={"tribunal": normalized_tribunal, "routes": list(CATALOG_ROUTES)},
            limitations=[
                "Catalogo publico de metadados; nao representa busca de decisoes.",
                "A forma dos objetos de catalogo e preservada em raw para mudancas de schema.",
            ],
        )
        return ProviderCatalog(
            source=self.name,
            courts=[
                ProviderOption(
                    code=normalized_tribunal,
                    description=f"Justica Eleitoral - {normalized_tribunal}",
                )
            ],
            species=classes,
            source_trace=trace,
            raw={"tribunal": normalized_tribunal, **catalogs},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="SJUR - Justica Eleitoral",
            source_url=self.config.tse_sjur_url,
            category="electoral_jurisprudence",
            search_modes=["catalog"],
            document_types=["catalog_metadata"],
            content_formats=["json"],
            canonical_records=["ProviderCatalog"],
            extracted_fields=["classes", "relatorias", "eleicoes", "normas"],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "POST /{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa/classes",
                "POST /{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa/relatorias",
                "POST /{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa/eleicoes",
                "POST /{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa/normas",
            ],
            supports_full_text=False,
            supports_catalog=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            pagination_mode="none",
            completeness_contract="catalog_snapshot_only",
            full_text_access="not_available",
            limitations=[
                "A busca de decisoes permanece fora do contrato runtime.",
                "O endpoint principal pode exigir validacao antirrobo/token.",
                "Catalogos devem ser tratados como snapshot da fonte no instante da consulta.",
            ],
            responsible_use=[
                "Usar apenas as rotas publicas de catalogo reproduzidas.",
                "Nao contornar tokens, antirrobo ou validacao humana.",
                "Preservar SourceTrace e o payload do tribunal consultado.",
            ],
        )

    def _request_catalog(self, route: str, *, tribunal: str) -> list[Any]:
        if route not in CATALOG_ROUTES:
            raise ValueError(f"Rota de catalogo SJUR desconhecida: {route}")
        self._respect_rate_limit()
        endpoint = f"/{tribunal.lower()}/sjur-pesquisa-backend/rest/public/pesquisa/{route}"
        url = urljoin(self.api_base_url + "/", endpoint.lstrip("/"))
        try:
            response = self.session.post(
                url,
                json=[tribunal],
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError("SJUR/TSE catalog TLS validation failed") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"SJUR/TSE catalog request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError(f"SJUR/TSE catalog returned HTTP 429 for {route}")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError(
                f"SJUR/TSE catalog requires access validation for {route}"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"SJUR/TSE catalog returned HTTP {response.status_code} for {route}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"SJUR/TSE catalog rejected HTTP {response.status_code} for {route}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ParserContractChangedError(
                f"SJUR/TSE catalog {route} did not return JSON"
            ) from exc
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("content", "data", "items", "result", "results"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        raise ParserContractChangedError(f"SJUR/TSE catalog {route} schema changed")

    @staticmethod
    def _options(items: Iterable[Any], *, category: str) -> list[ProviderOption]:
        options: list[ProviderOption] = []
        for index, item in enumerate(items):
            if isinstance(item, dict):
                code = _first_value(item, "id", "codigo", "code", "sigla", "numero", "valor")
                description = _first_value(
                    item, "descricao", "description", "nome", "name", "label", "valor"
                )
                metadata = dict(item)
            else:
                code = str(item)
                description = str(item)
                metadata = {"value": item}
            options.append(
                ProviderOption(
                    code=code or f"{category}-{index}",
                    description=description or code or f"{category}-{index}",
                    metadata=metadata,
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


def _first_value(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""
