"""STF Informativo public structured-data provider."""

from __future__ import annotations

import re
import unicodedata
import zipfile
from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
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
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

_XLSX_NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_EXPECTED_HEADERS = [
    "Informativo",
    "Classe Processo",
    "Número Processo",
    "Incidente Julgamento",
    "UF",
    "Observação",
    "Data Julgamento",
    "Relator",
    "Redator Acórdão",
    "Órgão Julgador",
    "Tipo Julgamento",
    "Situação Julgamento",
    "Título",
    "Tese Julgado",
    "Resumo",
    "Notícia",
    "Ramo Direito",
    "Matéria",
    "Repercussão Geral",
    "Tema RG",
    "Legislação",
    "ODS ONU 2030",
    "Covid-19",
    "Notícia completa",
]


class StfInformativoProvider(JurisprudenceProvider):
    """Provider for the official STF Informativo structured XLSX dataset."""

    name = "stf_informativo"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.stf_informativo_data_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=20_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = self.config.stf_informativo_data_url
        content = self._request_xlsx(endpoint)
        rows = parse_stf_informativo_xlsx(content)
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET Informativo_Dados/Dados_InformativosSTF.xlsx",
            query={
                "text": query.text,
                "number": query.number,
                "page": query.page,
                "page_size": query.page_size,
            },
            source_url=endpoint,
            limitations=[
                "Planilha publica oficial do Informativo STF.",
                "Busca filtrada localmente apos download do XLSX estruturado.",
                "Nao baixa PDF nem tenta contornar WAF do portal de inteiro teor.",
            ],
        )
        return parse_stf_informativo_rows(rows, query=query, trace=trace)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "stf_informativo exposes curated rows, summaries and public links."},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="STF Informativo",
            source_url="https://portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF",
            category="court_jurisprudence",
            search_modes=["text", "case_number", "local_xlsx_filter"],
            document_types=["informativo", "acordao_resumido", "tese_informativo"],
            content_formats=["xlsx"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "id",
                "informativo",
                "case_number",
                "case_class",
                "rapporteur",
                "redator_acordao",
                "judging_body",
                "judgment_date",
                "title",
                "thesis",
                "summary",
                "news",
                "law_branch",
                "matter",
                "is_repercussao_geral",
                "tema_rg",
                "legislation",
                "ods",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /arquivo/cms/informativoSTF/anexo/Informativo_Dados/Dados_InformativosSTF.xlsx"
            ],
            supports_full_text=False,
            pagination_mode="local_window",
            completeness_contract="reported_total_and_page_window",
            full_text_access="not_available",
            supports_cli=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number"],
            filter_semantics={
                "text": "native",
                "number": "native",
                **{
                    name: "unsupported"
                    for name in (
                        "all_words",
                        "any_words",
                        "without_words",
                        "exact_phrase",
                        "rapporteur",
                        "updated_from",
                        "updated_to",
                        "published_from",
                        "published_to",
                        "case_class",
                        "judging_body",
                        "degree",
                        "instance",
                        "lawyer_name",
                        "legal_area",
                        "oab",
                        "party_document",
                        "party_name",
                        "police_document",
                        "precatory_number",
                        "cda",
                        "source_origin",
                        "source_origins",
                        "fetch_details",
                        "courts",
                        "types",
                        "document_type",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                    )
                },
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
            },
            limitations=[
                "Dados sao curados pelo Informativo STF, nao a base integral de acordaos.",
                "A data vem em serial Excel no XLSX oficial e e normalizada para ISO date.",
                "Links de inteiro teor do portal STF podem exigir validacao separada.",
                "Alguns ambientes Windows podem precisar configurar verify_ssl=False "
                "por falha local de cadeia SSL.",
            ],
            responsible_use=[
                "Usar como fonte estruturada de teses e resumos oficiais do STF.",
                "Preservar SourceTrace e URL oficial da planilha.",
                "Nao usar como substituto do inteiro teor quando a analise exigir voto completo.",
                "Desabilitar verificacao SSL apenas por decisao explicita do usuario.",
            ],
        )

    def _request_xlsx(self, url: str) -> bytes:
        headers = {
            "Accept": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
                "application/octet-stream,*/*"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        request = TransportRequest(
            source=self.name,
            operation="informativo_xlsx",
            method="GET",
            url=url,
            headers=headers,
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except SourceUnavailableError as exc:
            if "TLS" in str(exc):
                raise SourceUnavailableError(
                    "STF Informativo XLSX SSL verification failed in this environment."
                ) from exc
            raise
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError(
                "STF Informativo XLSX SSL verification failed in this environment."
            ) from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"STF Informativo request failed: {exc}") from exc

        if response.status is not TransportStatus.COMPLETE:
            if response.status is TransportStatus.TLS_ERROR:
                raise SourceUnavailableError(
                    "STF Informativo XLSX SSL verification failed in this environment."
                )
            raise SourceUnavailableError(
                f"STF Informativo transport failed: {response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("STF Informativo transport returned no HTTP status")
        if response.status_code == 429:
            raise RateLimitDetectedError("STF Informativo returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise SourceUnavailableError(
                f"STF Informativo requires access validation (HTTP {response.status_code})"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(f"STF Informativo returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"STF Informativo rejected request with HTTP {response.status_code}"
            )
        content = bytes(response.body)
        if not content.startswith(b"PK"):
            raise ParserContractChangedError("STF Informativo did not return an XLSX ZIP payload")
        return content


def parse_stf_informativo_xlsx(content: bytes) -> list[dict[str, str]]:
    """Parse the official STF Informativo XLSX using only the standard library."""

    try:
        archive = zipfile.ZipFile(BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ParserContractChangedError("STF Informativo XLSX is not a valid ZIP") from exc
    names = set(archive.namelist())
    if "xl/worksheets/sheet1.xml" not in names:
        raise ParserContractChangedError("STF Informativo XLSX missing sheet1.xml")
    shared_strings = _read_shared_strings(archive) if "xl/sharedStrings.xml" in names else []
    root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    sheet_rows = root.findall(".//x:sheetData/x:row", _XLSX_NS)
    raw_rows = [_read_row(row, shared_strings) for row in sheet_rows]
    raw_rows = [row for row in raw_rows if any(row.values())]
    if not raw_rows:
        raise ParserContractChangedError("STF Informativo XLSX has no rows")
    headers = [_normalize_spaces(raw_rows[0].get(index, "")) for index in range(1, 25)]
    if headers[: len(_EXPECTED_HEADERS)] != _EXPECTED_HEADERS:
        raise ParserContractChangedError("STF Informativo XLSX header contract changed")
    parsed_rows: list[dict[str, str]] = []
    for row in raw_rows[1:]:
        item = {
            _EXPECTED_HEADERS[index - 1]: _normalize_spaces(row.get(index, ""))
            for index in range(1, len(_EXPECTED_HEADERS) + 1)
        }
        if item["Informativo"] or item["Número Processo"] or item["Resumo"]:
            parsed_rows.append(item)
    return parsed_rows


def parse_stf_informativo_rows(
    rows: list[dict[str, str]],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
) -> SearchPage:
    """Filter parsed STF Informativo rows and map them to NanoJuris results."""

    matches = [row for row in rows if _matches_query(row, query)]
    total = len(matches)
    start_index = max(query.page - 1, 0) * query.page_size
    page_rows = matches[start_index : start_index + query.page_size]
    results = [
        _row_to_result(row, trace=trace, index=start_index + offset + 1)
        for offset, row in enumerate(page_rows)
    ]
    start = start_index + 1 if results else 0
    return SearchPage(
        source="stf_informativo",
        total=total,
        start=start,
        end=start + len(results) - 1 if results else 0,
        page=query.page,
        page_size=query.page_size,
        results=results,
        source_trace=trace,
    )


def _row_to_result(row: dict[str, str], *, trace: SourceTrace, index: int) -> JurisprudenceResult:
    case_number = _case_number(row)
    informativo = row.get("Informativo", "")
    title = row.get("Título", "")
    summary = row.get("Resumo") or row.get("Tese Julgado") or row.get("Notícia completa")
    source_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=trace.source_url,
        limitations=trace.limitations,
    )
    return JurisprudenceResult(
        id=f"stf-informativo-{informativo}-{_slug(case_number or title or str(index))}",
        source="stf_informativo",
        court="STF",
        type="informativo",
        number=case_number,
        thesis=row.get("Tese Julgado") or None,
        summary=summary or None,
        rapporteur=row.get("Relator") or None,
        updated_at=_excel_date_to_iso(row.get("Data Julgamento", "")),
        highlights={},
        source_trace=source_trace,
        raw={
            "informativo": informativo,
            "case_class": row.get("Classe Processo") or None,
            "classe": row.get("Classe Processo") or None,
            "case_number_only": row.get("Número Processo") or None,
            "uf": row.get("UF") or None,
            "observacao": row.get("Observação") or None,
            "redator_acordao": row.get("Redator Acórdão") or None,
            "orgao_julgador": row.get("Órgão Julgador") or None,
            "judging_body": row.get("Órgão Julgador") or None,
            "data_julgamento": _excel_date_to_iso(row.get("Data Julgamento", "")),
            "judgment_date": _excel_date_to_iso(row.get("Data Julgamento", "")),
            "tipo_julgamento": row.get("Tipo Julgamento") or None,
            "situacao_julgamento": row.get("Situação Julgamento") or None,
            "title": title or None,
            "noticia": row.get("Notícia") or None,
            "noticia_completa": row.get("Notícia completa") or None,
            "ramo_direito": row.get("Ramo Direito") or None,
            "assunto": row.get("Matéria") or None,
            "subject": row.get("Matéria") or None,
            "is_repercussao_geral": _is_yes(row.get("Repercussão Geral", "")),
            "tema_rg": row.get("Tema RG") or None,
            "legislation": row.get("Legislação") or None,
            "ods": row.get("ODS ONU 2030") or None,
            "covid_19": row.get("Covid-19") or None,
        },
    )


def _matches_query(row: dict[str, str], query: JurisprudenceQuery) -> bool:
    haystack = _normalize_for_search(" ".join(row.values()))
    text = _normalize_for_search(query.text)
    number = _normalize_for_search(query.number)
    if text and text not in haystack:
        return False
    if number and number not in _normalize_for_search(_case_number(row)):
        return False
    return True


def _case_number(row: dict[str, str]) -> str:
    case_class = row.get("Classe Processo", "")
    number = row.get("Número Processo", "")
    uf = row.get("UF", "")
    parts = [part for part in [case_class, number] if part]
    value = " ".join(parts)
    return f"{value}/{uf}" if value and uf else value


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(t.text or "" for t in item.findall(".//x:t", _XLSX_NS))
        for item in root.findall("x:si", _XLSX_NS)
    ]


def _read_row(row: ET.Element, shared_strings: list[str]) -> dict[int, str]:
    values: dict[int, str] = {}
    for cell in row.findall("x:c", _XLSX_NS):
        ref = str(cell.attrib.get("r") or "")
        column = _column_number(ref)
        if column:
            values[column] = _cell_value(cell, shared_strings)
    return values


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//x:t", _XLSX_NS))
    value = cell.find("x:v", _XLSX_NS)
    if value is None or value.text is None:
        return ""
    text = value.text
    if cell_type == "s" and shared_strings:
        return shared_strings[int(text)]
    return text


def _column_number(ref: str) -> int:
    total = 0
    for char in re.sub(r"[^A-Z]", "", ref.upper()):
        total = (total * 26) + ord(char) - 64
    return total


def _excel_date_to_iso(value: str) -> str | None:
    text = value.strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    try:
        serial = int(float(text))
    except ValueError:
        return text
    return (datetime(1899, 12, 30) + timedelta(days=serial)).date().isoformat()


def _is_yes(value: str) -> bool:
    return _normalize_for_search(value) in {"sim", "s", "true", "1"}


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_for_search(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", _normalize_spaces(value).casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return normalized or "registro"
