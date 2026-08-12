"""TCU public jurisprudence open-data provider."""

from __future__ import annotations

import csv
import io
import time
from urllib.parse import urljoin

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
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider

MANIFEST_PATH = "/dados-abertos/jurisprudencia/arquivos/jurisprudencia-arquivos.csv"
SUMMARY_PATH = "/dados-abertos/jurisprudencia/arquivos/acordao-completo/acordao-completo-resumo.csv"
MAX_SCAN_BYTES = 80_000_000


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
        self._last_request = 0.0

    @property
    def base_url(self) -> str:
        return self.config.tcu_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        term = (query.text or query.exact_phrase or query.number).strip()
        if not term:
            raise ValueError("TCU jurisprudence search requires a term or number")
        endpoint = SUMMARY_PATH
        response, source_url = self._request_stream(endpoint)
        page_size = _page_size(query.page_size)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query={
                "text": term,
                "page": query.page,
                "page_size": page_size,
                "dataset": "acordao-completo-resumo",
            },
            source_url=source_url,
            limitations=[
                "A busca percorre o dataset publico de resumo e pode exigir leitura extensa.",
                "O dataset pode crescer; o provider limita a leitura local a 80 MB por chamada.",
                "Para series grandes, prefira sincronizacao local e pesquisa offline.",
            ],
        )
        rows, truncated = _search_summary_csv(response, term=term, query=query, trace=trace)
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
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise NotImplementedError(
            "O dataset resumido do TCU nao possui uma rota de detalhe promovida neste provider."
        )

    def get_catalog(self) -> ProviderCatalog:
        endpoint = MANIFEST_PATH
        response, source_url = self._request_stream(endpoint)
        content = response.content
        response.close()
        try:
            rows = parse_tcu_manifest(content.decode("utf-8-sig", "replace"))
        except (csv.Error, UnicodeError) as exc:
            raise ParserContractChangedError(
                "TCU manifest is not a valid pipe-delimited CSV"
            ) from exc
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            source_url=source_url,
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
            extracted_fields=[
                "dataset_key",
                "summary",
                "thesis",
                "legal_references",
                "published_at",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /dados-abertos/jurisprudencia/arquivos/jurisprudencia-arquivos.csv",
                "GET /dados-abertos/jurisprudencia/arquivos/acordao-completo/"
                "acordao-completo-resumo.csv",
                "GET /dados-abertos/jurisprudencia/arquivos/jurisprudencia-selecionada/"
                "jurisprudencia-selecionada.csv",
            ],
            supports_full_text=False,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_live_tests=True,
            supported_filters=["text", "number"],
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

    def _request_stream(self, endpoint: str) -> tuple[requests.Response, str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        try:
            response = self.session.get(
                url,
                headers={
                    "Accept": "text/csv,application/octet-stream,*/*",
                    "User-Agent": self.config.user_agent,
                },
                timeout=self.config.timeout,
                allow_redirects=True,
                stream=True,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TCU jurisprudence request failed: {exc}") from exc
        if response.status_code == 429:
            response.close()
            raise RateLimitDetectedError("TCU jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            response.close()
            raise AccessControlRequiredError("TCU jurisprudence requires access validation")
        if response.status_code >= 500:
            response.close()
            raise SourceUnavailableError(f"TCU jurisprudence returned HTTP {response.status_code}")
        if response.status_code >= 400:
            response.close()
            raise SourceUnavailableError(f"TCU jurisprudence returned HTTP {response.status_code}")
        return response, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


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


def _search_summary_csv(
    response: requests.Response,
    *,
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
    for line in response.iter_lines(decode_unicode=True):
        if line is None:
            continue
        encoded = str(line).encode("utf-8", "replace")
        consumed += len(encoded)
        if consumed > MAX_SCAN_BYTES:
            truncated = True
            break
        try:
            row = next(csv.reader([str(line)], delimiter="|"))
        except csv.Error:
            continue
        if not row or target not in " ".join(row).casefold():
            continue
        if row[0].strip().upper() == "KEY":
            continue
        matched += 1
        if matched <= wanted_start or len(results) >= page_size:
            continue
        key = row[0].strip().strip('"')
        raw_summary = row[1].strip().strip('"') if len(row) > 1 else ""
        summary = BeautifulSoup(raw_summary, "html.parser").get_text(" ", strip=True)
        results.append(
            JurisprudenceResult(
                id=f"tcu-acordao-resumo-{key}",
                source="tcu_jurisprudencia",
                court="TCU",
                type="acordao_resumo",
                summary=summary or None,
                source_trace=trace,
                raw={
                    "KEY": key,
                    "VISAOGERAL": raw_summary,
                    "dataset": "acordao-completo-resumo",
                },
            )
        )
    return results, truncated


def _page_size(value: int) -> int:
    return max(1, min(int(value or 10), 50))
