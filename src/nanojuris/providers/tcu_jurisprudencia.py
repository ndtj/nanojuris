"""TCU public jurisprudence open-data provider."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from nanojuris.canonical import normalize_date
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
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

MANIFEST_PATH = "/dados-abertos/jurisprudencia/arquivos/jurisprudencia-arquivos.csv"
SUMMARY_PATH = "/dados-abertos/jurisprudencia/arquivos/acordao-completo/acordao-completo-resumo.csv"
DATASET_PATHS = {
    "acordao-completo-resumo": SUMMARY_PATH,
    "jurisprudencia-selecionada": (
        "/dados-abertos/jurisprudencia/arquivos/jurisprudencia-selecionada/"
        "jurisprudencia-selecionada.csv"
    ),
    "boletim-jurisprudencia": (
        "/dados-abertos/jurisprudencia/arquivos/boletim-jurisprudencia/boletim-jurisprudencia.csv"
    ),
    "resposta-consulta": (
        "/dados-abertos/jurisprudencia/arquivos/resposta-consulta/resposta-consulta.csv"
    ),
    "sumula": "/dados-abertos/jurisprudencia/arquivos/sumula/sumula.csv",
}
MAX_SCAN_BYTES = 80_000_000


@dataclass(slots=True)
class _BufferedResponse:
    """Small requests-compatible view over a bounded transport body."""

    content: bytes
    url: str
    status_code: int
    headers: dict[str, str]
    closed: bool = False

    def iter_lines(self, *, decode_unicode: bool = False):
        for line in self.content.splitlines():
            yield line.decode("utf-8", "replace") if decode_unicode else line

    def close(self) -> None:
        self.closed = True


class TcuJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for TCU jurisprudence datasets published as pipe-delimited CSV."""

    name = "tcu_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.base_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_SCAN_BYTES,
                # Dataset downloads are large and non-idempotent from the
                # provider's perspective (a retry would restart the scan).
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def base_url(self) -> str:
        return self.config.tcu_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = (query.text or query.exact_phrase or query.number).strip()
        if not term:
            raise ValueError("TCU jurisprudence search requires a term or number")
        dataset = _dataset_for_query(query)
        endpoint = DATASET_PATHS[dataset]
        response, source_url, elapsed_ms = self._request_stream(endpoint)
        page_size = _page_size(query.page_size)
        trace = self._build_trace(
            response,
            endpoint=endpoint,
            source_url=source_url,
            elapsed_ms=elapsed_ms,
            query={
                "text": term,
                "page": query.page,
                "page_size": page_size,
                "dataset": dataset,
            },
            limitations=[
                "A busca percorre o dataset publico de resumo e pode exigir leitura extensa.",
                "O dataset pode crescer; o provider limita a leitura local a 80 MB por chamada.",
                "Para series grandes, prefira sincronizacao local e pesquisa offline.",
            ],
        )
        rows, truncated = _search_dataset_csv(
            response, dataset=dataset, term=term, query=query, trace=trace
        )
        response.close()
        if truncated:
            trace.limitations.append(
                "A leitura atingiu o limite de 80 MB; o total pode ser parcial."
            )
        return SearchPage(
            source=self.name,
            total=len(rows),
            start=((max(query.page, 1) - 1) * page_size) + 1 if rows else 0,
            end=((max(query.page, 1) - 1) * page_size) + len(rows) if rows else 0,
            page=max(query.page, 1),
            page_size=page_size,
            results=rows,
            source_trace=trace,
            pagination_mode="local_window",
            is_complete=not truncated,
            completeness_reason="bounded_dataset_scan" if not truncated else "scan_byte_limit",
            total_known=False,
            filters_applied={
                "collection": "translated" if query.collection else "default",
                "published_from": "local" if query.published_from else "not_requested",
                "published_to": "local" if query.published_to else "not_requested",
            },
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "O dataset resumido do TCU nao possui uma rota de detalhe promovida neste provider."
        )

    def get_catalog(self) -> ProviderCatalog:
        endpoint = MANIFEST_PATH
        response, source_url, elapsed_ms = self._request_stream(endpoint)
        content = response.content
        response.close()
        try:
            rows = parse_tcu_manifest(content.decode("utf-8-sig", "replace"))
        except (csv.Error, UnicodeError) as exc:
            raise ParserContractChangedError(
                "TCU manifest is not a valid pipe-delimited CSV"
            ) from exc
        trace = self._build_trace(
            response,
            endpoint=endpoint,
            source_url=source_url,
            elapsed_ms=elapsed_ms,
            limitations=["O manifesto publica bases, anos, tamanhos e URLs oficiais."],
        )
        species = [
            ProviderOption(
                code=str(index),
                description=str(row.get("BASE") or ""),
                metadata={
                    "year": row.get("ANO"),
                    "size": row.get("TAMANHO"),
                    "url": row.get("ARQUIVO"),
                },
            )
            for index, row in enumerate(rows)
            if row.get("BASE")
        ]
        return ProviderCatalog(
            source=self.name,
            species=species,
            source_trace=trace,
            raw={"manifest": rows},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TCU Jurisprudencia e Dados Abertos",
            source_url=self.base_url,
            category="administrative_jurisprudence",
            search_modes=["full_text", "summary", "dataset", "catalog"],
            document_types=["acordao", "jurisprudencia_selecionada", "sumula", "boletim"],
            content_formats=["csv", "text/html"],
            canonical_records=["CanonicalDecision", "CanonicalPrecedent"],
            semantic_discriminator="dataset",
            extracted_fields=[
                "dataset_key",
                "id",
                "number",
                "summary",
                "full_text",
                "thesis",
                "legal_references",
                "case_class",
                "judging_body",
                "authority",
                "branch",
                "collection",
                "judgment_date",
                "publication_date",
                "published_at",
                "source_trace",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /dados-abertos/jurisprudencia/arquivos/jurisprudencia-arquivos.csv",
                "GET /dados-abertos/jurisprudencia/arquivos/acordao-completo/"
                "acordao-completo-resumo.csv",
                "GET /dados-abertos/jurisprudencia/arquivos/jurisprudencia-selecionada/"
                "jurisprudencia-selecionada.csv",
                "GET /dados-abertos/jurisprudencia/arquivos/boletim-jurisprudencia/"
                "boletim-jurisprudencia.csv",
                "GET /dados-abertos/jurisprudencia/arquivos/resposta-consulta/"
                "resposta-consulta.csv",
                "GET /dados-abertos/jurisprudencia/arquivos/sumula/sumula.csv",
            ],
            supports_full_text=False,
            pagination_mode="local_window",
            completeness_contract="observed_window_or_source_limit",
            full_text_access="inline_summary",
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_live_tests=True,
            supported_filters=["text", "number", "collection", "published_from", "published_to"],
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "translated",
                "published_from": "local_postfilter",
                "published_to": "local_postfilter",
                "document_type": "validated_scope",
                **{
                    name: "unsupported"
                    for name in (
                        "courts",
                        "types",
                        "all_words",
                        "any_words",
                        "without_words",
                        "rapporteur",
                        "updated_from",
                        "updated_to",
                        "case_class",
                        "judging_body",
                        "degree",
                        "instance",
                        "legal_area",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                        "source_origin",
                        "source_origins",
                        "fetch_details",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "precatory_number",
                        "police_document",
                        "cda",
                    )
                },
            },
            limitations=[
                "A pesquisa interativa do TCU permanece separada e pode retornar firewall HTML.",
                "A busca live no resumo percorre um CSV grande e possui limite de leitura.",
                "Campos ausentes no dataset permanecem nulos; nao sao inferidos.",
            ],
            responsible_use=[
                "Preferir manifesto, Range e sincronizacao incremental.",
                "Respeitar tamanho dos arquivos e evitar varreduras repetidas.",
                "Identificar a fonte como jurisprudencia administrativa do TCU.",
            ],
        )

    def _request_stream(self, endpoint: str) -> tuple[_BufferedResponse, str, float]:
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        request = TransportRequest(
            source=self.name,
            operation="tcu_dataset",
            method="GET",
            url=url,
            headers={
                "Accept": "text/csv,application/octet-stream,*/*",
                "User-Agent": self.config.user_agent,
            },
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TCU jurisprudence request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                "TCU jurisprudence transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TCU jurisprudence transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("TCU jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TCU jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TCU jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TCU jurisprudence returned HTTP {response.status_code}")
        final_url = str(response.final_url or url)
        buffered = _BufferedResponse(
            content=bytes(response.body),
            url=final_url,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
        return buffered, final_url, response.elapsed_ms

    def _build_trace(
        self,
        response: _BufferedResponse,
        *,
        endpoint: str,
        source_url: str,
        elapsed_ms: float,
        query: dict[str, object] | None = None,
        limitations: list[str] | None = None,
    ) -> SourceTrace:
        headers = getattr(response, "headers", {}) or {}
        content_length = headers.get("Content-Length")
        try:
            response_bytes = int(content_length) if content_length else None
        except (TypeError, ValueError):
            response_bytes = None
        return SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=query or {},
            source_url=source_url,
            http_status=getattr(response, "status_code", None),
            final_url=getattr(response, "url", source_url),
            content_type=headers.get("Content-Type"),
            response_bytes=response_bytes,
            elapsed_ms=elapsed_ms,
            retrieval_status="success",
            limitations=limitations or [],
        )


def parse_tcu_manifest(text: str) -> list[dict[str, str]]:
    """Parse the official TCU manifest, ignoring its publication-date line."""

    lines = [line for line in text.splitlines() if line.strip()]
    header_index = next(
        (index for index, line in enumerate(lines) if "BASE" in line and "ARQUIVO" in line),
        None,
    )
    if header_index is None:
        raise ParserContractChangedError("TCU manifest header not found")
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_index:])), delimiter="|")
    rows: list[dict[str, str]] = []
    for row in reader:
        normalized = {
            str(key).strip().strip('"'): (value or "").strip().strip('"')
            for key, value in row.items()
        }
        if normalized.get("ARQUIVO"):
            rows.append(normalized)
    return rows


def _search_dataset_csv(
    response: _BufferedResponse,
    *,
    dataset: str,
    term: str,
    query: JurisprudenceQuery,
    trace: SourceTrace,
) -> tuple[list[JurisprudenceResult], bool]:
    target = term.casefold()
    page_size = _page_size(query.page_size)
    page = max(query.page, 1)
    wanted_start = (page - 1) * page_size
    matched = 0
    results: list[JurisprudenceResult] = []
    consumed = 0
    truncated = False

    def decoded_lines():
        nonlocal consumed, truncated
        for raw_line in response.iter_lines(decode_unicode=False):
            if raw_line is None:
                continue
            line = (
                raw_line.decode("utf-8", "replace")
                if isinstance(raw_line, bytes)
                else str(raw_line)
            )
            consumed += len(line.encode("utf-8", "replace"))
            if consumed > MAX_SCAN_BYTES:
                truncated = True
                return
            yield line

    reader = csv.DictReader(decoded_lines(), delimiter="|")
    for raw_row in reader:
        row = {
            str(key).strip().strip('"'): (value or "").strip().strip('"')
            for key, value in raw_row.items()
            if key
        }
        if not row or target not in " ".join(row.values()).casefold():
            continue
        if not _matches_published_range(row, query):
            continue
        matched += 1
        if matched <= wanted_start or len(results) >= page_size:
            continue
        results.append(_row_to_result(row, dataset=dataset, trace=trace))
    return results, truncated


def _dataset_for_query(query: JurisprudenceQuery) -> str:
    value = (query.collection or "").strip().casefold()
    if not value:
        return "acordao-completo-resumo"
    aliases = {
        "resumo": "acordao-completo-resumo",
        "acordaos": "acordao-completo-resumo",
        "jurisprudencia_selecionada": "jurisprudencia-selecionada",
        "boletim_jurisprudencia": "boletim-jurisprudencia",
        "resposta_consulta": "resposta-consulta",
        "sumulas": "sumula",
    }
    normalized = aliases.get(value, value)
    if normalized not in DATASET_PATHS:
        raise ValueError(f"collection TCU nao suportada: {query.collection}")
    return normalized


def _matches_published_range(row: dict[str, str], query: JurisprudenceQuery) -> bool:
    raw = row.get("DATASESSAOFORMATADA") or row.get("DATAAPROVACAO") or row.get("APROVACAO") or ""
    normalized = normalize_date(raw)
    if not normalized:
        return not (query.published_from or query.published_to)
    if query.published_from:
        start = normalize_date(query.published_from)
        if start and normalized < start:
            return False
    if query.published_to:
        end = normalize_date(query.published_to)
        if end and normalized > end:
            return False
    return True


def _row_to_result(row: dict[str, str], *, dataset: str, trace: SourceTrace) -> JurisprudenceResult:
    key = row.get("KEY") or row.get("ID") or ""
    summary_raw = (
        row.get("ENUNCIADO")
        or row.get("TITULO")
        or row.get("VISAOGERAL")
        or row.get("EXCERTO")
        or ""
    )
    full_text_raw = row.get("TEXTOACORDAO") or ""
    summary = BeautifulSoup(summary_raw, "html.parser").get_text(" ", strip=True) or None
    full_text = BeautifulSoup(full_text_raw, "html.parser").get_text(" ", strip=True) or None
    collection = dataset.replace("-", "_")
    published_raw = (
        row.get("DATASESSAOFORMATADA") or row.get("DATAAPROVACAO") or row.get("APROVACAO") or ""
    )
    decision_number = row.get("NUMACORDAO") or row.get("NUMSUMULA") or row.get("NUMERO")
    id_prefix = "tcu-acordao-resumo" if dataset == "acordao-completo-resumo" else f"tcu-{dataset}"
    return JurisprudenceResult(
        id=f"{id_prefix}-{key}",
        source="tcu_jurisprudencia",
        court="TCU",
        type=dataset,
        number=decision_number or None,
        summary=summary,
        full_text=full_text,
        judgment_date=normalize_date(published_raw),
        publication_date=normalize_date(published_raw),
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        case_class=row.get("TIPOPROCESSO") or None,
        judging_body=row.get("COLEGIADO") or None,
        branch="control",
        authority="TCU",
        collection=collection,
        document_type=dataset,
        source_origin=dataset,
        raw={**row, "dataset": dataset},
        field_provenance={
            "summary": {"source_field": "ENUNCIADO/TITULO/VISAOGERAL/EXCERTO"},
            "full_text": {"source_field": "TEXTOACORDAO"},
            "publication_date": {"source_field": "DATASESSAOFORMATADA/DATAAPROVACAO"},
        },
    )


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 50))
