from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, QueryRejectedError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjse_boletim_jurisprudencia import (
    TjseBoletimJurisprudenciaProvider,
    _secure_public_url,
)


class _Response:
    status_code = 200
    url = "https://diario.tjse.jus.br/revista/internet/pesquisar.wsp"
    encoding = "iso-8859-1"
    headers = {"Content-Type": "text/html"}

    def __init__(self, body: str) -> None:
        self.content = body.encode("iso-8859-1")


class _Session:
    def __init__(self) -> None:
        root = Path(__file__).parent / "fixtures"
        self.responses = [
            _Response((root / "tjse_boletim_search.html").read_text(encoding="utf-8")),
            _Response((root / "tjse_boletim_search.html").read_text(encoding="utf-8")),
            _Response((root / "tjse_boletim_principal.html").read_text(encoding="utf-8")),
            _Response((root / "tjse_boletim_detail.html").read_text(encoding="utf-8")),
        ]

    def request(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self.responses.pop(0)


def test_tjse_boletim_parses_second_degree_ementa() -> None:
    provider = TjseBoletimJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=_Session(),  # type: ignore[arg-type]
    )
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=10))
    assert len(page.results) == 1
    result = page.results[0]
    assert result.authority == "TJSE"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "CJSG"
    assert result.case_class == "Agravo de Instrumento"
    assert result.publication_date == "2026-08-28"
    assert result.document_url and "202600000101" in result.document_url
    decisions = provider.get_decisions(result.id)
    assert decisions.texts
    assert "VOTO" in str(decisions.texts[0]["content"])


def test_tjse_boletim_rejects_first_degree() -> None:
    provider = TjseBoletimJurisprudenciaProvider()
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="x", degree="first"))


def test_tjse_boletim_rejects_schema_without_sections() -> None:
    class Session(_Session):
        def __init__(self) -> None:
            changed = _Response("<html><body>changed</body></html>")
            self.responses = [changed, changed]

    provider = TjseBoletimJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=Session(),  # type: ignore[arg-type]
    )
    with pytest.raises(ParserContractChangedError):
        provider.search(JurisprudenceQuery(text="x"))


def test_tjse_boletim_exposes_bounded_federation_contract() -> None:
    capabilities = TjseBoletimJurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_unified_search is True
    assert capabilities.completeness_contract == "section_rows_total_unknown_across_editions"


def test_tjse_boletim_empty_fixture_is_not_a_schema_success() -> None:
    empty = (Path(__file__).parent / "fixtures" / "tjse_boletim_empty.html").read_text(
        encoding="utf-8"
    )
    assert "<table></table>" in empty


def test_tjse_boletim_document_links_are_upgraded_to_https() -> None:
    assert (
        _secure_public_url("http://www.tjse.jus.br/tjnet/jurisprudencia/relatorio.wsp?tmp.n=1")
        == "https://www.tjse.jus.br/tjnet/jurisprudencia/relatorio.wsp?tmp.n=1"
    )


def test_tjse_boletim_rejects_external_document_links() -> None:
    with pytest.raises(ParserContractChangedError, match="origem oficial"):
        _secure_public_url("https://example.invalid/report")
