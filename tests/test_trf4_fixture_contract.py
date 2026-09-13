from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.errors import ParserContractChangedError
from nanojuris.models import SourceTrace
from nanojuris.providers.tjsp_eproc_jurisprudencia import parse_eproc_jurisprudencia_results

FIXTURES = Path(__file__).parent / "fixtures"


def _parse(name: str):
    return parse_eproc_jurisprudencia_results(
        (FIXTURES / name).read_text(encoding="utf-8"),
        trace=SourceTrace(provider="trf4_eproc_jurisprudencia", endpoint="/listar"),
        source_url="https://example.test/resultado",
        source="trf4_eproc_jurisprudencia",
        court="TRF4",
        id_prefix="trf4-eproc-jurisprudencia",
        source_label="TRF4/eproc jurisprudence",
    )


def test_trf4_empty_fixture_is_not_a_parser_failure() -> None:
    assert _parse("trf4_eproc_empty.html") == []


def test_trf4_pagination_fixture_preserves_stable_id_and_summary() -> None:
    results = _parse("trf4_eproc_pagination.html")
    assert len(results) == 1
    assert results[0].id.endswith("12345678901234567890")
    assert results[0].summary == "texto de fixture"


def test_trf4_schema_drift_fixture_is_rejected() -> None:
    with pytest.raises(ParserContractChangedError):
        _parse("trf4_eproc_schema_drift.html")
