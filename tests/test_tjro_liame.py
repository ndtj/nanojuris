from __future__ import annotations

import json
from pathlib import Path

from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjro_liame import (
    build_tjro_search_payload,
    parse_tjro_search_response,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjro_liame_results.json"


def fixture_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_tjro_maps_qualified_precedent_to_canonical_search_shape() -> None:
    page = parse_tjro_search_response(
        fixture_data(),
        query=JurisprudenceQuery(text="empreitada", page_size=1),
        trace=SourceTrace(provider="tjro_liame", endpoint="POST /api/pesquisa/precedentes"),
    )
    result = page.results[0]
    assert result.id == "tjro-liame-TJRO-incidente_demanda_repetitiva-18"
    assert result.question == "Questão pública de fixture."
    assert result.thesis == "Tese pública de fixture."
    assert result.paradigm_cases[0].number == "08029144420258220000"
    assert result.updated_at == "2026-08-13"


def test_tjro_builds_public_payload() -> None:
    payload = build_tjro_search_payload(
        JurisprudenceQuery(
            text="dano moral",
            published_from="2026-01-01",
            published_to="2026-02-01",
            page=2,
            page_size=25,
        )
    )
    assert payload["siglas"] == ["TJRO"]
    assert payload["data_inicio"] == "2026-01-01"
    assert payload["page"] == 2
    assert payload["page_size"] == 25
