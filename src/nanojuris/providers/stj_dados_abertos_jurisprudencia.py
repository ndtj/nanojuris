"""STJ public open-data catalog provider.

This provider exposes CKAN metadata and synchronization plans. It deliberately
does not download large legal datasets or opt into remote unified search.
"""

from __future__ import annotations

import hashlib
import time
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

PACKAGE_SEARCH_PATH = "/api/3/action/package_search"
PACKAGE_SHOW_PATH = "/api/3/action/package_show"
DEFAULT_QUERY = "jurisprudencia"
MAX_ROWS = 100
MAX_PLAN_RESOURCES = 100


class StjDadosAbertosProvider(JurisprudenceProvider):
    """Provider for the STJ CKAN open-data catalog."""

    name = "stj_dados_abertos_jurisprudencia"

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
        return self.config.stj_dados_abertos_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        """Reject remote search because CKAN publishes files, not an index."""

        raise UnsupportedQueryError(
            "STJ dados abertos nao oferece busca jurisprudencial online; "
            "sincronize um recurso e pesquise o indice local"
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise UnsupportedQueryError(
            "STJ dados abertos nao possui detalhe remoto; use o recurso sincronizado"
        )

    def get_catalog(self) -> ProviderCatalog:
        datasets, response = self._list_source_datasets()
        trace = self._trace(
            PACKAGE_SEARCH_PATH,
            query={"q": DEFAULT_QUERY, "rows": MAX_ROWS},
            response=response,
            limitations=[
                "O catalogo descreve arquivos; nao representa uma busca online de jurisprudencia.",
                "Contagens e recursos devem ser atualizados antes de cada sincronizacao.",
            ],
        )
        species = [
            ProviderOption(
                code=dataset["name"],
                description=dataset["title"],
                metadata={
                    "license": dataset.get("license"),
                    "resource_count": dataset.get("resource_count", 0),
                    "formats": dataset.get("formats", []),
                    "url": dataset.get("url"),
                },
            )
            for dataset in datasets
            if dataset.get("name") and dataset.get("title")
        ]
        return ProviderCatalog(
            source=self.name,
            courts=[ProviderOption(code="STJ", description="Superior Tribunal de Justica")],
            species=species,
            source_trace=trace,
            raw={"datasets": datasets, "mode": "catalog_only"},
        )

    def list_source_datasets(
        self,
        *,
        query: str = DEFAULT_QUERY,
        rows: int = MAX_ROWS,
    ) -> list[dict[str, Any]]:
        """List compact dataset metadata from the official CKAN catalog."""

        datasets, _ = self._list_source_datasets(query=query, rows=rows)
        return datasets

    def _list_source_datasets(
        self,
        *,
        query: str = DEFAULT_QUERY,
        rows: int = MAX_ROWS,
    ) -> tuple[list[dict[str, Any]], requests.Response]:
        """Return dataset metadata and the response used for its trace."""

        normalized_query = query.strip() or DEFAULT_QUERY
        normalized_rows = max(1, min(int(rows), MAX_ROWS))
        body, response = self._request_json(
            PACKAGE_SEARCH_PATH,
            params={"q": normalized_query, "rows": normalized_rows},
        )
        result = body.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("results"), list):
            raise ParserContractChangedError("STJ CKAN package_search missing result.results")
        datasets = [
            _dataset_summary(item)
            for item in result["results"]
            if isinstance(item, dict) and _dataset_summary(item).get("name")
        ]
        return datasets, response

    def describe_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Return dataset metadata and resource descriptors without downloading files."""

        identifier = _require_dataset_id(dataset_id)
        body, response = self._request_json(PACKAGE_SHOW_PATH, params={"id": identifier})
        result = body.get("result")
        if not isinstance(result, dict):
            raise ParserContractChangedError("STJ CKAN package_show missing result")
        return {
            "source": self.name,
            "dataset": _dataset_summary(result),
            "resources": [
                _resource_summary(item) for item in _as_dict_list(result.get("resources"))
            ],
            "source_trace": self._trace(
                PACKAGE_SHOW_PATH,
                query={"id": identifier},
                response=response,
                limitations=["Metadados CKAN consultados; nenhum recurso foi baixado."],
            ).to_dict(),
        }

    def plan_source_sync(
        self,
        dataset_id: str,
        *,
        format: str = "JSON",
        max_resources: int = MAX_PLAN_RESOURCES,
    ) -> dict[str, Any]:
        """Select resources for a future local sync without performing downloads."""

        normalized_format = format.strip().upper()
        if normalized_format not in {"JSON", "CSV", "ZIP"}:
            raise QueryRejectedError("format deve ser JSON, CSV ou ZIP")
        limit = max(1, min(int(max_resources), MAX_PLAN_RESOURCES))
        description = self.describe_dataset(dataset_id)
        resources = [
            resource
            for resource in description["resources"]
            if str(resource.get("format") or "").upper() == normalized_format
        ][:limit]
        return {
            "source": self.name,
            "dataset_id": dataset_id,
            "format": normalized_format,
            "download": False,
            "resource_count": len(resources),
            "resources": resources,
            "instructions": [
                "Baixar em streaming com limite configurado.",
                "Validar checksum quando a fonte publicar checksum.",
                "Registrar dataset, recurso, URL e data da sincronizacao.",
                "Deduplicar registros por id antes de indexar localmente.",
            ],
        }

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STJ Dados Abertos de Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence_dataset",
            search_modes=["dataset", "catalog", "sync_plan"],
            document_types=["acordao_espelho", "integra_decisao", "acordao_dje"],
            content_formats=["json", "csv", "zip"],
            canonical_records=["ProviderCatalog"],
            extracted_fields=[
                "dataset_id",
                "dataset_title",
                "resource_id",
                "resource_url",
                "format",
                "checksum",
                "size",
                "last_modified",
                "license",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /api/3/action/package_search",
                "GET /api/3/action/package_show",
            ],
            supports_full_text=False,
            supports_catalog=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=False,
            supports_mcp=True,
            supports_studio=False,
            pagination_mode="catalog_offset",
            completeness_contract="CKAN_result_count_and_resource_metadata",
            supported_filters=["catalog_query", "rows", "dataset_id", "format"],
            limitations=[
                "Nao oferece busca jurisprudencial online neste adapter.",
                "Recursos podem ser grandes e nao sao baixados automaticamente.",
                "Espelhos de acordaos nao equivalem a cobertura integral do STJ.",
            ],
            responsible_use=[
                "Preferir sincronizacao incremental e respeitar o tamanho publicado.",
                "Preservar licenca, checksum e metadados do dataset.",
                "Nao apresentar o catalogo como cobertura integral da jurisprudencia do STJ.",
            ],
        )

    def _request_json(
        self,
        endpoint: str,
        *,
        params: dict[str, Any],
    ) -> tuple[dict[str, Any], requests.Response]:
        response = self._request(endpoint, params=params)
        try:
            body = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("STJ CKAN response is not JSON") from exc
        if not isinstance(body, dict) or body.get("success") is not True:
            raise ParserContractChangedError("STJ CKAN response did not report success=true")
        return body, response

    def _request(self, endpoint: str, *, params: dict[str, Any]) -> requests.Response:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        try:
            response = self.session.get(
                url,
                params=params,
                headers={
                    "Accept": "application/json",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"STJ CKAN request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("STJ CKAN returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("STJ CKAN requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"STJ CKAN returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"STJ CKAN returned HTTP {response.status_code}")
        return response

    def _trace(
        self,
        endpoint: str,
        *,
        query: dict[str, Any],
        response: requests.Response,
        limitations: list[str],
    ) -> SourceTrace:
        content = bytes(getattr(response, "content", b"") or b"")
        return SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=query,
            source_url=str(getattr(response, "url", "") or "") or None,
            final_url=str(getattr(response, "url", "") or "") or None,
            limitations=limitations,
            http_status=response.status_code,
            content_type=response.headers.get("Content-Type") if response.headers else None,
            content_sha256=hashlib.sha256(content).hexdigest(),
            response_bytes=len(content),
            retrieval_status="ok",
        )

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def _dataset_summary(dataset: dict[str, Any]) -> dict[str, Any]:
    resources = _as_dict_list(dataset.get("resources"))
    formats = sorted(
        {
            str(resource.get("format") or "").strip().upper()
            for resource in resources
            if str(resource.get("format") or "").strip()
        }
    )
    return {
        "id": dataset.get("id"),
        "name": dataset.get("name"),
        "title": dataset.get("title") or dataset.get("name"),
        "notes": dataset.get("notes"),
        "license": dataset.get("license_id") or dataset.get("license_title"),
        "organization": _organization_name(dataset.get("organization")),
        "url": dataset.get("url"),
        "resource_count": len(resources),
        "formats": formats,
        "metadata_modified": dataset.get("metadata_modified"),
    }


def _resource_summary(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": resource.get("id"),
        "name": resource.get("name"),
        "format": str(resource.get("format") or "").strip().upper() or None,
        "mimetype": resource.get("mimetype"),
        "url": resource.get("url"),
        "size": resource.get("size"),
        "hash": resource.get("hash"),
        "last_modified": resource.get("last_modified"),
        "created": resource.get("created"),
    }


def _organization_name(value: object) -> str | None:
    if isinstance(value, dict):
        name = value.get("title") or value.get("name")
        return str(name).strip() if name else None
    return None


def _require_dataset_id(value: str) -> str:
    normalized = value.strip()
    if not normalized or len(normalized) > 200 or any(char in normalized for char in "\r\n"):
        raise QueryRejectedError("dataset_id invalido")
    return normalized


def _as_dict_list(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
