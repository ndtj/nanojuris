"""TCE-PR ViaJuris public open-data provider."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.canonical import normalize_date
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import DocumentReference, fetch_document_reference
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedQueryError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    ExtractionStatus,
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
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

DOWNLOAD_PATH = "/DadosAbertos/DadosAbertos/DownloadArquivo"
MAX_DOWNLOAD_BYTES = 80_000_000


class TcePrViaJurisProvider(JurisprudenceProvider):
    """Search the TCE-PR ViaJuris weekly public CSV snapshot."""

    name = "tce_pr_viajuris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tce_pr_viajuris_url).hostname or ""
        self._document_policy = TransportPolicy(
            allowed_hosts=(host,),
            timeout_seconds=self.config.timeout,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_DOWNLOAD_BYTES,
                # The annual snapshot is large; do not transparently replay
                # a failed download.  Callers can retry the bounded operation
                # explicitly and preserve the source failure state.
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._document_urls: dict[str, str] = {}

    @property
    def base_url(self) -> str:
        return self.config.tce_pr_viajuris_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = (query.text or query.exact_phrase or query.number).strip()
        if not term:
            raise UnsupportedQueryError(
                "TCE-PR ViaJuris exige termo, numero de processo ou frase exata"
            )
        year = _query_year(query)
        content, source_url, status, content_type = self._download(year)
        rows = parse_viajuris_csv(content)
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {DOWNLOAD_PATH}?nomeArquivo={year}_acordaos_base_de_dados.csv",
            query={"text": term, "year": year, "page": query.page, "page_size": query.page_size},
            source_url=source_url,
            http_status=status,
            final_url=source_url,
            content_type=content_type,
            content_sha256=hashlib.sha256(content).hexdigest(),
            response_bytes=len(content),
            retrieval_status="success",
            limitations=[
                "A fonte publica um snapshot CSV; o total representa apenas o arquivo baixado.",
                "O ano pode ser selecionado pelos limites de data da consulta.",
                "O provider nao baixa PDF inline; preserva UrlPDF como link oficial.",
            ],
        )
        matches = [row for row in rows if _row_matches(row, term)]
        page_size = _page_size(query.page_size)
        start_index = (query.page - 1) * page_size
        page_rows = matches[start_index : start_index + page_size]
        results = [_row_to_result(row, trace=trace) for row in page_rows]
        complete, reason = page_completeness(
            reported_total=len(matches),
            start=start_index + 1 if results else 0,
            returned=len(results),
            total_is_authoritative=True,
        )
        page = SearchPage(
            source=self.name,
            total=len(matches),
            start=start_index + 1 if results else 0,
            end=start_index + len(results) if results else 0,
            page=query.page,
            page_size=page_size,
            results=results,
            source_trace=trace,
            pagination_mode="local_window",
            is_complete=complete,
            completeness_reason=reason,
        )
        for result in page.results:
            document_url = result.raw.get("document_url")
            if isinstance(document_url, str) and document_url:
                self._document_urls[result.id] = document_url
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise UnsupportedQueryError(
            "ViaJuris publica links de PDF no CSV; use raw.document_url para o documento oficial"
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch the official PDF linked by a ViaJuris CSV row."""

        document_url = (
            document_id
            if document_id.startswith(("https://", "http://"))
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "TCE-PR document_id must be an observed official PDF URL or a result id"
            )
        if _official_pdf_url(document_url) != document_url:
            raise ValueError("TCE-PR document URL is outside the official ViaJuris host")
        reference = DocumentReference(
            id=document_id,
            source=self.name,
            url=document_url,
            expected_content_types=("application/pdf", "text/html", "text/plain"),
        )
        return fetch_document_reference(
            reference,
            policy=self._document_policy,
            session=self.session,
            title=f"TCE-PR ViaJuris {document_id}",
        )

    def get_catalog(self, *, year: int | None = None) -> ProviderCatalog:
        selected_year = year or datetime.now(timezone.utc).year
        url = self._archive_url(selected_year)
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {DOWNLOAD_PATH}?nomeArquivo={selected_year}_acordaos_base_de_dados.csv",
            query={"year": selected_year, "catalog": True},
            source_url=url,
            limitations=[
                "O catalogo descreve o snapshot anual publico do ViaJuris.",
                "A disponibilidade de anos depende da publicacao do TCE-PR.",
            ],
        )
        return ProviderCatalog(
            source=self.name,
            courts=[
                ProviderOption(
                    code="TCE-PR",
                    description="Tribunal de Contas do Estado do Parana",
                )
            ],
            species=[ProviderOption(code="acordao", description="Acordao")],
            source_trace=trace,
            raw={"year": selected_year, "dataset_url": url, "format": "CSV;"},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TCE-PR ViaJuris Dados Abertos",
            source_url=self.base_url,
            category="administrative_jurisprudence",
            search_modes=["text", "case_number", "dataset", "catalog", "pagination"],
            document_types=["acordao"],
            content_formats=["csv", "pdf_link"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "registry_id",
                "case_number",
                "summary",
                "judgment_date",
                "publication_date",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                f"GET {DOWNLOAD_PATH}?nomeArquivo={{year}}_acordaos_base_de_dados.csv",
            ],
            supports_full_text=True,
            supports_catalog=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_live_tests=True,
            pagination_mode="local_window",
            completeness_contract="complete_local_snapshot_window",
            full_text_access="document_link",
            supported_filters=["text", "number", "published_from", "published_to"],
            filter_semantics={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "published_from": "local_postfilter",
                "published_to": "local_postfilter",
                "updated_from": "local_postfilter",
                "updated_to": "local_postfilter",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
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
                "A base e um snapshot anual/semanário e nao substitui a consulta interativa.",
                "Inteiro teor depende de UrlPDF presente e valido na linha.",
                "Campos inexistentes permanecem nulos; nao sao inferidos.",
            ],
            responsible_use=[
                "Baixar somente o ano necessario e respeitar rate limit.",
                "Preservar hash, tamanho, URL e linha CSV para auditoria.",
                "Tratar a fonte como jurisprudencia administrativa do TCE-PR.",
            ],
        )

    def _archive_url(self, year: int) -> str:
        return urljoin(
            self.base_url + "/",
            f"{DOWNLOAD_PATH}?nomeArquivo={year}_acordaos_base_de_dados.csv",
        )

    def _download(self, year: int) -> tuple[bytes, str, int, str | None]:
        url = self._archive_url(year)
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="download_snapshot",
                method="GET",
                url=url,
                headers={"Accept": "text/csv,application/octet-stream,*/*"},
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TCE-PR ViaJuris transport failed: {response.status.value}"
            )
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TCE-PR ViaJuris returned HTTP 429")
        if status in {401, 403}:
            raise AccessControlRequiredError("TCE-PR ViaJuris requires access validation")
        if status >= 500 or status >= 400:
            raise SourceUnavailableError(f"TCE-PR ViaJuris returned HTTP {status}")
        content = response.body
        if not content:
            raise ParserContractChangedError("TCE-PR ViaJuris CSV response is empty")
        return (
            content,
            str(response.final_url or url),
            status,
            response.content_type,
        )


def parse_viajuris_csv(content: bytes) -> list[dict[str, str]]:
    """Parse the semicolon-delimited ViaJuris snapshot conservatively."""

    text = _decode_csv(content)
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        if not reader.fieldnames:
            raise ParserContractChangedError("TCE-PR ViaJuris CSV header is missing")
        fieldnames = {_normalize_key(name) for name in reader.fieldnames if name}
        # Legacy snapshots carried an "id"/"codigo" column; the current schema
        # (DsTipoAto;NrAto;AnoAto;...) identifies an acordao by ato + year.
        legacy_id = fieldnames.intersection({"id", "codigo", "numeroacordao", "acordao"})
        current_id = {"nrato", "anoato"}.issubset(fieldnames) or {
            "nrprocesso",
            "anoprocesso",
        }.issubset(fieldnames)
        if not legacy_id and not current_id:
            raise ParserContractChangedError(
                "TCE-PR ViaJuris CSV stable identifier column is missing"
            )
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(
                {str(key or "").strip(): (value or "").strip() for key, value in row.items()}
            )
        return rows
    except csv.Error as exc:
        raise ParserContractChangedError("TCE-PR ViaJuris CSV is malformed") from exc


def _row_to_result(row: dict[str, str], *, trace: SourceTrace) -> JurisprudenceResult:
    legacy_id = _first(
        row, "ID", "Id", "codigo", "CODIGO", "numero_acordao", "NumeroAcordao", "acordao"
    )
    ato_nr = _first(row, "NrAto", "numero_ato")
    ato_year = _first(row, "AnoAto", "ano_ato")
    process_nr = _first(row, "NrProcesso", "NumeroProcesso", "numero_processo", "Processo")
    process_year = _first(row, "AnoProcesso", "ano_processo")
    if legacy_id:
        source_id = legacy_id
    elif ato_nr and ato_year:
        source_id = f"{ato_year}-{ato_nr}"
    elif process_nr and process_year:
        source_id = f"proc-{process_year}-{process_nr}"
    else:
        raise ParserContractChangedError("TCE-PR ViaJuris row missing stable identifier")

    summary = _first(row, "Ementa", "EMENTA", "ementa", "DsResumo", "Resumo", "resumo") or _first(
        row, "DsTitulo", "titulo"
    )
    if process_nr and process_year:
        number = f"{process_nr}/{process_year}"
    else:
        number = process_nr
    pdf = _first(row, "UrlPDF", "URLPDF", "url_pdf", "LinkPDF", "link_pdf")
    judgment_raw = _first(row, "DtSessao", "DataJulgamento", "data_julgamento")
    publication_raw = _first(row, "DtPublicacaoDOE", "DataPublicacao", "data_publicacao")
    return JurisprudenceResult(
        id=f"tce-pr-viajuris-{source_id}",
        source="tce_pr_viajuris",
        court="TCE-PR",
        type=_first(row, "DsTipoAto", "tipo_ato") or "acordao",
        number=number or None,
        rapporteur=_first(row, "NmRelator", "Relator", "relator") or None,
        summary=summary or None,
        judgment_date=normalize_date(judgment_raw),
        publication_date=normalize_date(publication_raw),
        updated_at=normalize_date(publication_raw),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={
            **row,
            "registry_id": source_id,
            "judging_body": _first(row, "DsColegiado", "colegiado") or None,
            "case_class": _first(row, "DsClasseProcessual", "classe") or None,
            "subject": _first(row, "DsTema", "tema") or None,
            "document_url": _official_pdf_url(pdf),
        },
    )


def _row_matches(row: dict[str, str], term: str) -> bool:
    target = term.casefold()
    return target in " ".join(row.values()).casefold()


def _official_pdf_url(value: str) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.hostname != "viajuris.tce.pr.gov.br":
        return None
    return value


def _decode_csv(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", "replace")


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _first(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value and value.strip():
            return value.strip()
    normalized = {_normalize_key(key): value for key, value in row.items()}
    for key in keys:
        value = normalized.get(_normalize_key(key))
        if value and value.strip():
            return value.strip()
    return ""


def _query_year(query: JurisprudenceQuery) -> int:
    value = query.published_from or query.updated_from
    if value:
        match = re.match(r"(?:\d{2}/\d{2}/|)(\d{4})", value)
        if match:
            return int(match.group(1))
    return datetime.now(timezone.utc).year


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 100))
