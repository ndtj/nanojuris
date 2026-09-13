from __future__ import annotations

import json
from pathlib import Path

from nanojuris.identity import match_legal_identities, resolve_legal_identity
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjes_cjpg import parse_tjes_cjpg_response
from nanojuris.providers.tjsp_cjpg import parse_tjsp_cjpg_response

FIXTURES = Path(__file__).parent / "fixtures"


def _identity(result) -> object:
    return resolve_legal_identity(
        kind="decision",
        source=result.source,
        authority=result.authority,
        degree=result.degree,
        native_id=result.id,
        case_number=result.number or "",
        record_type=result.type,
        event_date=result.judgment_date or result.updated_at or "",
        text=result.full_text or result.summary or "",
    )


def test_two_first_degree_providers_migrate_multiple_decisions_and_republication() -> None:
    """Native IDs keep decisions distinct and make republication idempotent."""

    tjes_payload = json.loads((FIXTURES / "tjes_cjpg_success.json").read_text(encoding="utf-8"))
    tjes_page = parse_tjes_cjpg_response(
        tjes_payload,
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=SourceTrace(provider="tjes_cjpg", endpoint="GET /api/search"),
        page_size=2,
    )
    tjsp_page = parse_tjsp_cjpg_response(
        (FIXTURES / "tjsp_cjpg_success.html").read_bytes(),
        query=JurisprudenceQuery(text="responsabilidade", page_size=2),
        trace=SourceTrace(provider="tjsp_cjpg", endpoint="POST /cjpg/pesquisar.do"),
        base_url="https://esaj.tjsp.jus.br/cjpg",
        page_size=2,
    )

    tjes_ids = [_identity(result) for result in tjes_page.results]
    tjsp_ids = [_identity(result) for result in tjsp_page.results]
    assert len(tjes_ids) == 2
    assert len(tjsp_ids) == 2
    assert match_legal_identities(tjes_ids[0], tjes_ids[1]).relation == "distinct"
    assert match_legal_identities(tjsp_ids[0], tjsp_ids[1]).relation == "distinct"

    republished = resolve_legal_identity(
        kind="decision",
        source=tjes_page.results[0].source,
        authority=tjes_page.results[0].authority,
        degree=tjes_page.results[0].degree,
        native_id=tjes_page.results[0].id,
        case_number=tjes_page.results[0].number or "",
        record_type=tjes_page.results[0].type,
        event_date="2025-04-01",
        text="Versao republicada com correcao editorial",
    )
    assert match_legal_identities(tjes_ids[0], republished).relation == "same"
