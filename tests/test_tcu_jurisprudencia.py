"""Offline contract tests for the public TCU open-data adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tcu_jurisprudencia import (
    TcuJurisprudenciaProvider,
    parse_tcu_manifest,
)
from tests.test_initial_json_providers import FakeSession, StreamResponse

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_search_parses_versioned_public_summary_fixture() -> None:
    response = StreamResponse(
        fixture_bytes("tcu_acordao_resumo.csv"),
        url="https://sites.tcu.gov.br/dados-abertos/jurisprudencia/summary.csv",
    )
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.total == 1
    assert page.results[0].id == "tcu-acordao-resumo-AC-1"
    assert page.results[0].summary == "Responsabilidade administrativa e dano moral."
    assert page.results[0].raw["VISAOGERAL"].startswith("<p>")
    assert page.results[0].access_status.value == "public"
    assert page.source_trace is not None
    assert page.source_trace.http_status == 200
    assert page.source_trace.retrieval_status == "success"
    assert response.closed is True


def test_search_distinguishes_empty_fixture_from_contract_change() -> None:
    response = StreamResponse(
        fixture_bytes("tcu_acordao_resumo_empty.csv"),
        url="https://sites.tcu.gov.br/dados-abertos/jurisprudencia/summary.csv",
    )
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=5))

    assert page.results == []
    assert page.total == 0
    assert page.source_trace is not None


def test_search_preserves_multiline_quoted_csv_records() -> None:
    response = StreamResponse(
        b'KEY|VISAOGERAL\n"AC-2"|"<p>Direito administrativo em duas linhas.\nContinua na ementa.</p>"\n',
        url="https://sites.tcu.gov.br/dados-abertos/jurisprudencia/summary.csv",
    )
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    page = provider.search(JurisprudenceQuery(text="direito", page_size=1))

    assert page.results[0].id == "tcu-acordao-resumo-AC-2"
    assert "duas linhas" in (page.results[0].summary or "")


def test_manifest_fixture_preserves_official_dataset_metadata() -> None:
    rows = parse_tcu_manifest(fixture_bytes("tcu_manifest.csv").decode("utf-8"))

    assert [row["BASE"] for row in rows] == ["Acordaos completos", "Acordaos - resumo"]
    assert rows[1]["ARQUIVO"].endswith("acordao-completo-resumo.csv")


def test_manifest_contract_change_fixture_is_explicit() -> None:
    with pytest.raises(ParserContractChangedError, match="header"):
        parse_tcu_manifest(fixture_bytes("tcu_manifest_contract_changed.txt").decode("utf-8"))


def test_search_selected_dataset_maps_canonical_fields() -> None:
    response = StreamResponse(
        fixture_bytes("tcu_jurisprudencia_selecionada.csv"),
        url="https://sites.tcu.gov.br/dados-abertos/jurisprudencia/jurisprudencia-selecionada.csv",
    )
    provider = TcuJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=FakeSession([response])
    )

    page = provider.search(
        JurisprudenceQuery(
            text="prescrição",
            collection="jurisprudencia-selecionada",
            published_from="2026-01-01",
            published_to="2026-12-31",
            page_size=1,
        )
    )

    result = page.results[0]
    assert result.id == "tcu-jurisprudencia-selecionada-SEL-1"
    assert result.number == "2193"
    assert result.summary and "prescrição" in result.summary
    assert result.judgment_date == "2026-09-01"
    assert result.judging_body == "Plenário"
    assert result.branch == "control"
    assert result.collection == "jurisprudencia_selecionada"
    assert page.total_known is False
    assert page.filters_applied["collection"] == "translated"
