"""STJ public open-data catalog provider.

This provider exposes CKAN metadata and synchronization plans. It deliberately
does not download large legal datasets or opt into remote unified search.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import time
import zipfile
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.canonical import normalize_date
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
    CanonicalDecision,
    DecisionBundle,
    ExtractionStatus,
    ExtractionTrace,
    JurisprudenceQuery,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.store import SQLiteStore

PACKAGE_SEARCH_PATH = "/api/3/action/package_search"
PACKAGE_SHOW_PATH = "/api/3/action/package_show"
DEFAULT_QUERY = "jurisprudencia"
MAX_ROWS = 100
MAX_PLAN_RESOURCES = 100
DEFAULT_MAX_SYNC_BYTES = 50_000_000
MAX_ARCHIVE_MEMBERS = 1_000


@dataclass(slots=True)
class StjSyncResult:
    """Audit summary for one explicit local resource synchronization."""

    source: str
    dataset_id: str
    resource_id: str
    format: str
    bytes_read: int
    content_sha256: str
    records_seen: int
    records_saved: int
    duplicate_records: int
    invalid_records: int
    run_id: str
    source_hash: str | None = None
    source_fingerprint: str | None = None
    skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StjIntegralPairSyncResult:
    """Audit summary for a metadata plus integral-text resource pair."""

    source: str
    dataset_id: str
    metadata_resource_id: str
    text_resource_id: str
    metadata_records: int
    text_records: int
    records_saved: int
    unmatched_metadata: int
    unmatched_text: int
    content_sha256: str
    run_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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

    def sync_resource(
        self,
        dataset_id: str,
        resource_id: str,
        *,
        store: SQLiteStore,
        max_bytes: int = DEFAULT_MAX_SYNC_BYTES,
        label: str | None = None,
        force: bool = False,
    ) -> StjSyncResult:
        """Download, parse and persist one JSON/CSV resource explicitly."""

        if max_bytes <= 0:
            raise QueryRejectedError("max_bytes deve ser maior que zero")
        description = self.describe_dataset(dataset_id)
        resource = next(
            (item for item in description["resources"] if item.get("id") == resource_id),
            None,
        )
        if resource is None:
            raise QueryRejectedError("resource_id nao pertence ao dataset informado")
        resource_format = str(resource.get("format") or "").upper()
        if resource_format not in {"JSON", "CSV", "ZIP"}:
            raise UnsupportedQueryError(
                "A sincronizacao aceita recursos JSON, CSV ou ZIP contendo "
                "cargas JSON/CSV; outros formatos permanecem bloqueados"
            )
        resource_url = _require_official_resource_url(str(resource.get("url") or ""), self.base_url)
        source_hash = _text_value(resource, "hash") or None
        source_fingerprint = _resource_fingerprint(resource, source_hash=source_hash)
        manifest = store.get_sync_manifest(
            source=self.name,
            dataset_id=dataset_id,
            resource_id=resource_id,
        )
        if (
            not force
            and source_fingerprint
            and manifest is not None
            and manifest.get("status") == "complete"
            and manifest.get("source_fingerprint") == source_fingerprint
        ):
            return StjSyncResult(
                source=self.name,
                dataset_id=dataset_id,
                resource_id=resource_id,
                format=resource_format,
                bytes_read=int(manifest["response_bytes"]),
                content_sha256=str(manifest["content_sha256"]),
                records_seen=int(manifest["records_seen"]),
                records_saved=0,
                duplicate_records=int(manifest["duplicate_records"]),
                invalid_records=int(manifest["invalid_records"]),
                run_id=str(manifest["run_id"]),
                source_hash=source_hash,
                source_fingerprint=source_fingerprint,
                skipped=True,
            )
        content, response = self._download_resource(resource_url, max_bytes=max_bytes)
        content_sha256 = hashlib.sha256(content).hexdigest()
        trace = self._trace(
            f"GET resource/{resource_id}",
            query={"dataset_id": dataset_id, "resource_id": resource_id},
            response=response,
            content=content,
            limitations=[
                f"Recurso limitado a {max_bytes} bytes.",
                "ZIP e aceito somente com membros JSON/CSV, limite de membros e "
                "tamanho total extraido controlados.",
            ],
        )
        trace.content_sha256 = content_sha256
        trace.response_bytes = len(content)
        trace.transformations = ["download_stream", "parse_rows", "deduplicate_by_id"]
        rows = _parse_resource(content, resource_format, max_bytes=max_bytes)
        _validate_resource_schema(rows)
        unique_rows, duplicate_records, invalid_records = _deduplicate_rows(rows)
        records = [
            _row_to_decision(
                row,
                dataset_id=dataset_id,
                resource_id=resource_id,
                trace=trace,
                content_sha256=content_sha256,
                content_bytes=len(content),
            )
            for row in unique_rows
        ]
        run = store.save_research_run(
            source=self.name,
            text=f"dataset:{dataset_id} resource:{resource_id}",
            query={
                "dataset_id": dataset_id,
                "resource_id": resource_id,
                "format": resource_format,
                "source_hash": source_hash,
                "source_fingerprint": source_fingerprint,
                "content_sha256": content_sha256,
            },
            records=records,
            label=label or f"STJ sync {dataset_id}/{resource_id}",
            sync_manifest={
                "source": self.name,
                "dataset_id": dataset_id,
                "resource_id": resource_id,
                "format": resource_format,
                "source_url": resource_url,
                "source_hash": source_hash,
                "source_fingerprint": source_fingerprint,
                "content_sha256": content_sha256,
                "response_bytes": len(content),
                "records_seen": len(rows),
                "records_saved": len(records),
                "duplicate_records": duplicate_records,
                "invalid_records": invalid_records,
                "status": "complete",
            },
        )
        return StjSyncResult(
            source=self.name,
            dataset_id=dataset_id,
            resource_id=resource_id,
            format=resource_format,
            bytes_read=len(content),
            content_sha256=content_sha256,
            records_seen=len(rows),
            records_saved=len(records),
            duplicate_records=duplicate_records,
            invalid_records=invalid_records,
            run_id=run.id,
            source_hash=source_hash,
            source_fingerprint=source_fingerprint,
        )

    def sync_integral_pair(
        self,
        dataset_id: str,
        metadata_resource_id: str,
        text_resource_id: str,
        *,
        store: SQLiteStore,
        max_bytes: int = DEFAULT_MAX_SYNC_BYTES,
        label: str | None = None,
    ) -> StjIntegralPairSyncResult:
        """Join one official STJ metadata JSON resource to its text ZIP.

        The STJ publishes daily integral decisions as two resources: a JSON
        metadata file keyed by ``SeqDocumento`` and a ZIP whose UTF-8/HTML
        text filenames use that same identifier.  They are intentionally
        synchronized together so a metadata-only resource can never be
        mistaken for full text, and an unmatched text member is reported
        instead of silently becoming a record.
        """

        if max_bytes <= 0:
            raise QueryRejectedError("max_bytes deve ser maior que zero")
        description = self.describe_dataset(dataset_id)
        resources = {item.get("id"): item for item in description["resources"]}
        metadata = resources.get(metadata_resource_id)
        text_resource = resources.get(text_resource_id)
        if metadata is None or text_resource is None:
            raise QueryRejectedError("os dois resource_id devem pertencer ao dataset informado")
        if str(metadata.get("format") or "").upper() != "JSON":
            raise QueryRejectedError("metadata_resource_id deve apontar para um JSON")
        if str(text_resource.get("format") or "").upper() != "ZIP":
            raise QueryRejectedError("text_resource_id deve apontar para um ZIP")
        metadata_url = _require_official_resource_url(str(metadata.get("url") or ""), self.base_url)
        text_url = _require_official_resource_url(
            str(text_resource.get("url") or ""), self.base_url
        )
        metadata_content, metadata_response = self._download_resource(
            metadata_url, max_bytes=max_bytes
        )
        text_content, text_response = self._download_resource(text_url, max_bytes=max_bytes)
        metadata_rows = _parse_resource(metadata_content, "JSON", max_bytes=max_bytes)
        normalized_rows: list[dict[str, Any]] = []
        for row in metadata_rows:
            item = dict(row)
            identifier = _text_value(item, "id", "SeqDocumento", "seqDocumento")
            if identifier:
                item["id"] = identifier
            normalized_rows.append(item)
        _validate_resource_schema(normalized_rows)
        text_rows = _parse_text_archive(text_content, max_bytes=max_bytes)
        metadata_by_id = {
            _text_value(row, "id"): row for row in normalized_rows if _text_value(row, "id")
        }
        merged: list[dict[str, Any]] = []
        for identifier, row in metadata_by_id.items():
            text = text_rows.get(identifier)
            if text is None:
                continue
            item = dict(row)
            item["decisao_html"] = text
            item["decisao"] = _html_to_text(text)
            item["integral_text_resource_id"] = text_resource_id
            merged.append(item)
        if not merged:
            raise ParserContractChangedError(
                "STJ metadata e ZIP de inteiro teor nao possuem identificadores correspondentes"
            )
        combined_hash = hashlib.sha256(metadata_content + text_content).hexdigest()
        trace = self._trace(
            "GET metadata+integral-text resources",
            query={
                "dataset_id": dataset_id,
                "metadata_resource_id": metadata_resource_id,
                "text_resource_id": text_resource_id,
            },
            response=metadata_response,
            content=metadata_content + text_content,
            limitations=[
                f"Cada recurso limitado a {max_bytes} bytes.",
                "O inteiro teor e associado por SeqDocumento e preservado em texto "
                "normalizado e raw HTML.",
            ],
        )
        trace.final_url = f"{metadata_response.url} | {text_response.url}"
        trace.transformations = [
            "json_metadata",
            "bounded_zip_text",
            "join_by_seq_documento",
            "html_to_text",
        ]
        records = []
        for row in merged:
            decision = _row_to_decision(
                row,
                dataset_id=dataset_id,
                resource_id=metadata_resource_id,
                trace=trace,
                content_sha256=combined_hash,
                content_bytes=len(metadata_content) + len(text_content),
            )
            decision.degree = "superior"
            decision.instance = "superior"
            decision.branch = "superior"
            decision.authority = "STJ"
            decision.collection = "JURISPRUDENCIA"
            records.append(decision)
        run = store.save_research_run(
            source=self.name,
            text=f"dataset:{dataset_id} metadata:{metadata_resource_id} text:{text_resource_id}",
            query={
                "dataset_id": dataset_id,
                "metadata_resource_id": metadata_resource_id,
                "text_resource_id": text_resource_id,
                "content_sha256": combined_hash,
            },
            records=records,
            label=label or f"STJ integral pair {dataset_id}/{metadata_resource_id}",
        )
        return StjIntegralPairSyncResult(
            source=self.name,
            dataset_id=dataset_id,
            metadata_resource_id=metadata_resource_id,
            text_resource_id=text_resource_id,
            metadata_records=len(metadata_rows),
            text_records=len(text_rows),
            records_saved=len(records),
            unmatched_metadata=max(0, len(metadata_by_id) - len(records)),
            unmatched_text=len(set(text_rows) - set(metadata_by_id)),
            content_sha256=combined_hash,
            run_id=run.id,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STJ Dados Abertos de Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence_dataset",
            search_modes=["dataset", "catalog", "sync_plan", "local_sync", "integral_pair_sync"],
            document_types=["acordao_espelho", "integra_decisao", "acordao_dje"],
            content_formats=["json", "csv", "zip"],
            canonical_records=["ProviderCatalog", "CanonicalDecision", "ResearchRun"],
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
                "records_seen",
                "records_saved",
                "duplicate_records",
                "invalid_records",
                "content_sha256",
                "source_hash",
                "run_id",
                "skipped",
                "integral_text_resource_id",
                "document_url",
                "case_number",
                "summary",
                "full_text",
                "judgment_date",
                "publication_date",
                "source_updated_at",
                "document_type",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "source_trace",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /api/3/action/package_search",
                "GET /api/3/action/package_show",
                "GET /resource/{resource_id} (explicit local sync)",
                "GET /resource/{metadata_resource_id} + "
                "/resource/{text_resource_id} (integral pair)",
            ],
            # The daily STJ integral dataset publishes metadata JSON and a
            # matching text ZIP.  Full text is available only through the
            # explicit pair-sync operation, never through remote unified
            # search or an assumed single-resource download.
            supports_full_text=True,
            # The capability contract uses ``detail_call`` for any lazy
            # document retrieval. The metadata/text pair is the source-level
            # implementation detail of that call.
            full_text_access="detail_call",
            supports_catalog=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=False,
            supports_mcp=True,
            supports_studio=False,
            pagination_mode="catalog_offset",
            completeness_contract="CKAN_result_count_and_resource_metadata",
            supported_filters=[
                "catalog_query",
                "rows",
                "dataset_id",
                "resource_id",
                "metadata_resource_id",
                "text_resource_id",
                "format",
                "max_bytes",
                "force",
            ],
            filter_semantics={
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                **{
                    name: "unsupported"
                    for name in (
                        "text",
                        "courts",
                        "types",
                        "all_words",
                        "any_words",
                        "without_words",
                        "exact_phrase",
                        "rapporteur",
                        "updated_from",
                        "updated_to",
                        "published_from",
                        "published_to",
                        "number",
                        "party_name",
                        "party_document",
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
                        "legal_area",
                        "document_type",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                    )
                },
            },
            limitations=[
                "Nao oferece busca jurisprudencial online neste adapter.",
                "Recursos podem ser grandes e nao sao baixados automaticamente.",
                "Espelhos de acordaos nao equivalem a cobertura integral do STJ.",
                "O inteiro teor exige o pareamento explicito de JSON de metadados "
                "com ZIP de textos.",
                "A sincronizacao local aceita JSON/CSV e ZIP seguro contendo "
                "cargas JSON/CSV; outros formatos permanecem bloqueados.",
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

    def _download_resource(
        self,
        url: str,
        *,
        max_bytes: int,
    ) -> tuple[bytes, requests.Response]:
        self._respect_rate_limit()
        try:
            response = self.session.get(
                url,
                headers={
                    "Accept": "application/json, text/csv, application/octet-stream",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                stream=True,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"STJ resource request failed: {exc}") from exc
        if response.status_code == 429:
            response.close()
            raise RateLimitDetectedError("STJ resource returned HTTP 429")
        if response.status_code in {401, 403}:
            response.close()
            raise AccessControlRequiredError("STJ resource requires access validation")
        if response.status_code >= 400:
            response.close()
            raise SourceUnavailableError(f"STJ resource returned HTTP {response.status_code}")
        declared_size = _content_length(response)
        if declared_size is not None and declared_size > max_bytes:
            response.close()
            raise QueryRejectedError("recurso excede max_bytes antes do download")
        chunks: list[bytes] = []
        total = 0
        try:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    raise QueryRejectedError("recurso excede max_bytes durante o download")
                chunks.append(bytes(chunk))
        finally:
            response.close()
        return b"".join(chunks), response

    def _trace(
        self,
        endpoint: str,
        *,
        query: dict[str, Any],
        response: requests.Response,
        content: bytes | None = None,
        limitations: list[str],
    ) -> SourceTrace:
        if content is None:
            try:
                content = bytes(getattr(response, "content", b"") or b"")
            except RuntimeError:
                content = b""
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


def _require_official_resource_url(value: str, base_url: str) -> str:
    parsed = urlparse(value)
    expected = urlparse(base_url)
    if parsed.scheme != "https" or parsed.hostname != expected.hostname:
        raise QueryRejectedError("resource_url deve pertencer ao dominio oficial do STJ")
    return value


def _content_length(response: requests.Response) -> int | None:
    value = response.headers.get("Content-Length") if response.headers else None
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _resource_fingerprint(resource: dict[str, Any], *, source_hash: str | None) -> str | None:
    """Prefer a publisher hash and otherwise fingerprint stable catalog metadata."""

    if source_hash:
        return f"hash:{source_hash}"
    metadata = {
        "url": resource.get("url"),
        "size": resource.get("size"),
        "last_modified": resource.get("last_modified"),
    }
    if not metadata["url"] or not metadata["size"] and not metadata["last_modified"]:
        return None
    encoded = json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return f"metadata:{hashlib.sha256(encoded).hexdigest()}"


def _parse_resource(
    content: bytes,
    resource_format: str,
    *,
    max_bytes: int = DEFAULT_MAX_SYNC_BYTES,
) -> list[dict[str, Any]]:
    if resource_format == "JSON":
        try:
            payload = json.loads(content.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ParserContractChangedError("STJ JSON resource is invalid") from exc
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = next(
                (
                    payload[key]
                    for key in ("records", "data", "items", "result")
                    if isinstance(payload.get(key), list)
                ),
                [payload],
            )
        else:
            raise ParserContractChangedError("STJ JSON resource must contain records")
        return [row for row in rows if isinstance(row, dict)]
    if resource_format == "ZIP":
        return _parse_zip_resource(content, max_bytes=max_bytes)
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=";,|\t")
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        return [
            {str(key).strip(): (value or "").strip() for key, value in row.items() if key}
            for row in reader
        ]
    except (csv.Error, UnicodeError) as exc:
        raise ParserContractChangedError("STJ CSV resource is invalid") from exc


def _validate_resource_schema(rows: list[dict[str, Any]]) -> None:
    """Reject a non-empty resource that no longer exposes its stable id.

    Individual malformed rows are still counted as invalid by the existing
    deduplication gate.  A payload with no ``id`` field anywhere, however,
    indicates a source-level schema change and must not be accepted as a
    successful empty synchronization.
    """

    if rows and not any(_text_value(row, "id") for row in rows):
        raise ParserContractChangedError("STJ resource schema missing id")


def _parse_zip_resource(content: bytes, *, max_bytes: int) -> list[dict[str, Any]]:
    """Parse a bounded STJ archive without allowing unsafe extraction.

    CKAN publishes historical loads as ZIP files.  The archive itself is
    downloaded under the normal response limit; each member is then checked
    for path traversal, encryption, expansion size and an allowed JSON/CSV
    suffix before parsing.  We never extract to disk and reject archives that
    contain no structured data instead of silently returning an empty list.
    """

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except (zipfile.BadZipFile, OSError) as exc:
        raise ParserContractChangedError("STJ ZIP resource is invalid") from exc

    rows: list[dict[str, Any]] = []
    extracted_bytes = 0
    members = archive.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ParserContractChangedError("STJ ZIP resource has too many members")
    try:
        for info in members:
            name = info.filename
            if info.is_dir():
                continue
            if info.flag_bits & 0x1:
                raise ParserContractChangedError("STJ ZIP resource contains encrypted data")
            normalized = name.replace("\\", "/")
            if normalized.startswith("/") or any(part == ".." for part in normalized.split("/")):
                raise ParserContractChangedError("STJ ZIP resource contains unsafe path")
            suffix = normalized.rsplit("/", 1)[-1].lower()
            if suffix.endswith(".json"):
                member_format = "JSON"
            elif suffix.endswith(".csv"):
                member_format = "CSV"
            else:
                # Archives may include licensing/readme files.  They are not
                # data and are ignored, while an archive with only such files
                # is rejected below.
                continue
            extracted_bytes += int(info.file_size)
            if extracted_bytes > max_bytes:
                raise ParserContractChangedError(
                    "STJ ZIP resource exceeds max_bytes after extraction"
                )
            compressed = max(1, int(info.compress_size))
            if info.file_size > compressed * 1_000:
                raise ParserContractChangedError("STJ ZIP resource has an unsafe compression ratio")
            try:
                member_content = archive.read(info)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                raise ParserContractChangedError("STJ ZIP member could not be read") from exc
            rows.extend(_parse_resource(member_content, member_format, max_bytes=max_bytes))
    finally:
        archive.close()
    if not rows:
        raise ParserContractChangedError("STJ ZIP resource has no JSON/CSV records")
    return rows


def _parse_text_archive(content: bytes, *, max_bytes: int) -> dict[str, str]:
    """Read the STJ integral-text ZIP into ``SeqDocumento -> HTML text``."""

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except (zipfile.BadZipFile, OSError) as exc:
        raise ParserContractChangedError("STJ integral ZIP resource is invalid") from exc
    texts: dict[str, str] = {}
    extracted_bytes = 0
    members = archive.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ParserContractChangedError("STJ integral ZIP resource has too many members")
    try:
        for info in members:
            if info.is_dir():
                continue
            if info.flag_bits & 0x1:
                raise ParserContractChangedError(
                    "STJ integral ZIP resource contains encrypted data"
                )
            normalized = info.filename.replace("\\", "/")
            if normalized.startswith("/") or any(part == ".." for part in normalized.split("/")):
                raise ParserContractChangedError("STJ integral ZIP resource contains unsafe path")
            if not normalized.lower().endswith((".txt", ".html", ".htm")):
                continue
            extracted_bytes += int(info.file_size)
            if extracted_bytes > max_bytes:
                raise QueryRejectedError("STJ integral ZIP excede max_bytes apos extracao")
            compressed = max(1, int(info.compress_size))
            if info.file_size > compressed * 1_000:
                raise ParserContractChangedError("STJ integral ZIP has unsafe compression ratio")
            try:
                raw = archive.read(info)
            except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                raise ParserContractChangedError(
                    "STJ integral ZIP member could not be read"
                ) from exc
            identifier = normalized.rsplit("/", 1)[-1].rsplit(".", 1)[0].strip()
            if not identifier:
                continue
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
            texts[identifier] = text
    finally:
        archive.close()
    if not texts:
        raise ParserContractChangedError("STJ integral ZIP has no text members")
    return texts


def _html_to_text(value: str) -> str:
    """Convert source HTML fragments to deterministic searchable plain text."""

    text = re.sub(r"<\s*br\s*/?\s*>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\f\r]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _deduplicate_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    unique: dict[str, dict[str, Any]] = {}
    invalid = 0
    duplicates = 0
    for row in rows:
        identifier = _text_value(row, "id", "SeqDocumento", "seqDocumento")
        if identifier and not _text_value(row, "id"):
            row["id"] = identifier
        if not identifier:
            invalid += 1
            continue
        if identifier in unique:
            duplicates += 1
        unique[identifier] = row
    return list(unique.values()), duplicates, invalid


def _row_to_decision(
    row: dict[str, Any],
    *,
    dataset_id: str,
    resource_id: str,
    trace: SourceTrace,
    content_sha256: str,
    content_bytes: int,
) -> CanonicalDecision:
    external_id = _text_value(row, "id")
    canonical_id = hashlib.sha256(f"{dataset_id}:{external_id}".encode()).hexdigest()[:24]
    full_text = _text_value(row, "decisao") or None
    summary = _text_value(row, "ementa") or None
    extraction_status = (
        ExtractionStatus.COMPLETE if full_text or summary else ExtractionStatus.PARTIAL
    )
    return CanonicalDecision(
        id=f"stj-dados-{canonical_id}",
        source="stj_dados_abertos_jurisprudencia",
        court="STJ",
        case_number=_text_value(row, "numeroProcesso", "processo") or None,
        registry_number=_text_value(row, "numeroRegistro") or None,
        decision_type=_text_value(row, "tipoDeDecisao", "tipoDocumento") or "acordao_espelho",
        case_class=_text_value(row, "descricaoClasse", "siglaClasse") or None,
        subject=_text_value(row, "tema", "termosAuxiliares") or None,
        rapporteur=_text_value(row, "ministroRelator", "NM_MINISTRO") or None,
        judging_body=_text_value(row, "nomeOrgaoJulgador") or None,
        judgment_date=normalize_date(_text_value(row, "dataDecisao")),
        publication_date=normalize_date(_text_value(row, "dataPublicacao")),
        judgment_date_raw=_text_value(row, "dataDecisao") or None,
        publication_date_raw=_text_value(row, "dataPublicacao") or None,
        source_updated_at=normalize_date(_text_value(row, "dataAtualizacao")),
        retrieved_at=trace.retrieved_at,
        access_status=AccessStatus.PUBLIC,
        extraction_status=extraction_status,
        summary=summary,
        full_text=full_text,
        document_type=_text_value(row, "tipoDocumento") or "acordao_espelho",
        source_trace=trace,
        extraction_trace=ExtractionTrace(
            parser="stj_dados_abertos_jurisprudencia.sync_resource",
            parser_version="1",
            status=extraction_status,
            access_status=AccessStatus.PUBLIC,
            content_sha256=content_sha256,
            content_bytes=content_bytes,
            transformations=["json_or_csv_to_canonical_decision"],
            metadata={"dataset_id": dataset_id, "resource_id": resource_id},
        ),
        raw={**row, "dataset_id": dataset_id, "resource_id": resource_id},
    )


def _text_value(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""
