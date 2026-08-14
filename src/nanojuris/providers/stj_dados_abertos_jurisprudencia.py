"""STJ public open-data catalog provider.

This provider exposes CKAN metadata and synchronization plans. It deliberately
does not download large legal datasets or opt into remote unified search.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import time
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
        if resource_format not in {"JSON", "CSV"}:
            raise UnsupportedQueryError(
                "A sincronizacao inicial aceita somente recursos JSON ou CSV; "
                "ZIP permanece bloqueado"
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
                "Somente JSON e CSV sao aceitos nesta fase; ZIP nao e baixado.",
            ],
        )
        trace.content_sha256 = content_sha256
        trace.response_bytes = len(content)
        trace.transformations = ["download_stream", "parse_rows", "deduplicate_by_id"]
        rows = _parse_resource(content, resource_format)
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

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STJ Dados Abertos de Jurisprudencia",
            source_url=self.base_url,
            category="court_jurisprudence_dataset",
            search_modes=["dataset", "catalog", "sync_plan", "local_sync"],
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
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /api/3/action/package_search",
                "GET /api/3/action/package_show",
                "GET /resource/{resource_id} (explicit local sync)",
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
            supported_filters=[
                "catalog_query",
                "rows",
                "dataset_id",
                "resource_id",
                "format",
                "max_bytes",
                "force",
            ],
            limitations=[
                "Nao oferece busca jurisprudencial online neste adapter.",
                "Recursos podem ser grandes e nao sao baixados automaticamente.",
                "Espelhos de acordaos nao equivalem a cobertura integral do STJ.",
                "A sincronizacao local aceita JSON/CSV; ZIP permanece bloqueado.",
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


def _parse_resource(content: bytes, resource_format: str) -> list[dict[str, Any]]:
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


def _deduplicate_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    unique: dict[str, dict[str, Any]] = {}
    invalid = 0
    duplicates = 0
    for row in rows:
        identifier = _text_value(row, "id")
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
        case_number=_text_value(row, "numeroProcesso") or None,
        registry_number=_text_value(row, "numeroRegistro") or None,
        decision_type=_text_value(row, "tipoDeDecisao") or "acordao_espelho",
        case_class=_text_value(row, "descricaoClasse", "siglaClasse") or None,
        subject=_text_value(row, "tema", "termosAuxiliares") or None,
        rapporteur=_text_value(row, "ministroRelator") or None,
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
