from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
import requests

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, RateLimitDetectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.stf_informativo import (
    StfInformativoProvider,
    parse_stf_informativo_rows,
    parse_stf_informativo_xlsx,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(
        self,
        content: bytes = b"",
        *,
        status_code: int = 200,
    ):
        self.content = content
        self.status_code = status_code


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        if not self.responses:
            raise AssertionError("unexpected request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_parse_stf_informativo_xlsx_maps_official_columns():
    rows = parse_stf_informativo_xlsx(_xlsx_fixture())

    assert rows[0]["Informativo"] == "1223"
    assert rows[0]["Classe Processo"] == "ADI"
    assert rows[0]["Número Processo"] == "5775"
    assert rows[0]["Data Julgamento"] == "46199.125"
    assert "progressão de praças" in rows[0]["Título"]
    assert rows[0]["ODS ONU 2030"] == "16 Paz, Justiça e Instituições Eficazes"


def test_parse_stf_informativo_versioned_fixture() -> None:
    payload = json.loads((FIXTURES / "stf_informativo_rows.json").read_text(encoding="utf-8"))

    page = parse_stf_informativo_rows(
        payload["rows"],
        query=JurisprudenceQuery(text="tese constitucional", page_size=1),
        trace=SourceTrace(
            provider="stf_informativo",
            endpoint="fixture/stf_informativo_rows.json",
            source_url="https://example.invalid/stf-informativo-fixture",
        ),
    )

    assert page.total == 1
    result = page.results[0]
    assert result.id == "stf-informativo-1223-adi-9999-df"
    assert result.number == "ADI 9999/DF"
    assert result.summary == "Resumo de jurisprudencia sintetica para teste."
    assert result.updated_at == "2026-01-02"
    assert result.raw["orgao_julgador"] == "Plenario de Fixture"


def test_parse_stf_informativo_rows_filters_and_maps_results():
    rows = parse_stf_informativo_xlsx(_xlsx_fixture())
    trace = SourceTrace(provider="stf_informativo", endpoint="xlsx")

    page = parse_stf_informativo_rows(
        rows,
        query=JurisprudenceQuery(text="praças", page_size=5),
        trace=trace,
    )

    assert page.source == "stf_informativo"
    assert page.total == 1
    first = page.results[0]
    assert first.id == "stf-informativo-1223-adi-5775-go"
    assert first.court == "STF"
    assert first.type == "informativo"
    assert first.number == "ADI 5775/GO"
    assert first.rapporteur == "MIN. NUNES MARQUES"
    assert first.updated_at == "2026-06-26"
    assert first.raw["orgao_julgador"] == "Plenário"
    assert first.raw["is_repercussao_geral"] is False
    assert first.raw["assunto"] == "Organização do Estado; Polícia Militar"


def test_parse_stf_informativo_rows_filters_by_case_number():
    rows = parse_stf_informativo_xlsx(_xlsx_fixture())

    page = parse_stf_informativo_rows(
        rows,
        query=JurisprudenceQuery(number="ADI 7632", page_size=5),
        trace=SourceTrace(provider="stf_informativo", endpoint="xlsx"),
    )

    assert page.total == 1
    assert page.results[0].number == "ADI 7632/AL"
    assert page.results[0].raw["ramo_direito"] == "Direito Tributário"


def test_provider_search_downloads_xlsx_and_parses_results():
    session = FakeSession([FakeResponse(_xlsx_fixture())])
    provider = StfInformativoProvider(
        config=NanoJurisConfig(verify_ssl=False),
        session=session,
    )

    page = provider.search(JurisprudenceQuery(text="ICMS", page_size=2))

    assert page.total == 1
    assert page.results[0].number == "ADI 7632/AL"
    call = session.calls[0]
    assert call["url"].endswith("Dados_InformativosSTF.xlsx")
    assert "spreadsheetml.sheet" in call["kwargs"]["headers"]["Accept"]
    assert call["kwargs"]["verify"] is False


def test_provider_capabilities_describe_stf_informativo_contract():
    capabilities = StfInformativoProvider(session=FakeSession([])).get_capabilities()

    assert capabilities.source == "stf_informativo"
    assert capabilities.category == "court_jurisprudence"
    assert capabilities.content_formats == ["xlsx"]
    assert capabilities.supports_catalog is True
    assert "id" in capabilities.extracted_fields
    assert "thesis" in capabilities.extracted_fields


def test_provider_get_decisions_reports_curated_row_scope():
    bundle = StfInformativoProvider(session=FakeSession([])).get_decisions("stf-informativo-1")

    assert bundle.source == "stf_informativo"
    assert bundle.texts == []
    assert "curated rows" in bundle.raw["message"]


def test_client_registers_stf_informativo_by_default():
    client = NanoJurisClient()

    sources = {capability.source for capability in client.list_sources()}
    assert "stf_informativo" in sources


def test_provider_reports_invalid_xlsx_contract():
    provider = StfInformativoProvider(session=FakeSession([FakeResponse(b"not xlsx")]))

    with pytest.raises(ParserContractChangedError):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_reports_request_failures():
    provider = StfInformativoProvider(session=FakeSession([requests.exceptions.Timeout("off")]))

    with pytest.raises(Exception, match="request failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_reports_ssl_failure():
    provider = StfInformativoProvider(session=FakeSession([requests.exceptions.SSLError("cert")]))

    with pytest.raises(Exception, match="SSL verification failed"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_provider_reports_rate_limit():
    provider = StfInformativoProvider(session=FakeSession([FakeResponse(b"PK", status_code=429)]))

    with pytest.raises(RateLimitDetectedError):
        provider.search(JurisprudenceQuery(text="teste"))


@pytest.mark.parametrize("status_code", [400, 503])
def test_provider_reports_http_errors(status_code):
    provider = StfInformativoProvider(
        session=FakeSession([FakeResponse(b"PK", status_code=status_code)])
    )

    with pytest.raises(Exception, match=f"HTTP {status_code}"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_parser_rejects_changed_header():
    content = _xlsx_fixture(headers=["Changed"])

    with pytest.raises(ParserContractChangedError, match="header"):
        parse_stf_informativo_xlsx(content)


def test_parser_rejects_bad_zip_and_missing_sheet():
    with pytest.raises(ParserContractChangedError, match="valid ZIP"):
        parse_stf_informativo_xlsx(b"not a zip")

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/other.xml", "<worksheet />")

    with pytest.raises(ParserContractChangedError, match="sheet1"):
        parse_stf_informativo_xlsx(buffer.getvalue())


def test_parse_rows_accepts_empty_page_and_alternate_dates():
    rows = parse_stf_informativo_xlsx(_xlsx_fixture())
    rows[0]["Data Julgamento"] = "2026-01-02"
    rows[1]["Data Julgamento"] = "data textual"
    trace = SourceTrace(provider="stf_informativo", endpoint="xlsx")

    page = parse_stf_informativo_rows(
        rows,
        query=JurisprudenceQuery(text="termo inexistente", page_size=5),
        trace=trace,
    )

    assert page.total == 0
    assert page.start == 0
    iso_page = parse_stf_informativo_rows(
        rows,
        query=JurisprudenceQuery(text="praças", page_size=5),
        trace=trace,
    )
    assert iso_page.results[0].updated_at == "2026-01-02"
    textual_page = parse_stf_informativo_rows(
        rows,
        query=JurisprudenceQuery(text="ICMS", page_size=5),
        trace=trace,
    )
    assert textual_page.results[0].updated_at == "data textual"


def _xlsx_fixture(headers: list[str] | None = None) -> bytes:
    header_row = headers or [
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
    data_rows = [
        [
            "1223",
            "ADI",
            "5775",
            "",
            "GO",
            "",
            "46199.125",
            "MIN. NUNES MARQUES",
            "",
            "Plenário",
            "Virtual",
            "Concluído",
            "Constitucionalidade da progressão de praças ao oficialato",
            "",
            "É constitucional o ingresso de praças em cargos específicos.",
            "A Constituição Federal estabelece competência privativa.",
            "Direito Constitucional",
            "Organização do Estado; Polícia Militar",
            "Não",
            "",
            "CF/1988: art. 22, XXI.",
            "16 Paz, Justiça e Instituições Eficazes",
            "Não",
            "Notícia completa de teste.",
        ],
        [
            "1223",
            "ADI",
            "7632",
            "",
            "AL",
            "",
            "46199.125",
            "MIN. ANDRÉ MENDONÇA",
            "",
            "Plenário",
            "Virtual",
            "Concluído",
            "ICMS sobre serviços de comunicação",
            "",
            "A superveniência da LC 194/2022 suspendeu a eficácia.",
            "No caso, norma impugnada instituiu adicional de ICMS.",
            "Direito Tributário",
            "Impostos; ICMS; Telecomunicação",
            "Não",
            "",
            "ADCT: art. 82.",
            "16 Paz, Justiça e Instituições Eficazes",
            "Não",
            "Notícia completa tributária.",
        ],
    ]
    sheet = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]
    for row_index, row in enumerate([header_row, *data_rows], start=1):
        sheet.append(f'<row r="{row_index}">')
        for col_index, value in enumerate(row, start=1):
            ref = f"{_column_name(col_index)}{row_index}"
            escaped = (
                value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )
            sheet.append(f'<c r="{ref}" t="inlineStr"><is><t>{escaped}</t></is></c>')
        sheet.append("</row>")
    sheet.append("</sheetData></worksheet>")
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", "".join(sheet))
    return buffer.getvalue()


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name
