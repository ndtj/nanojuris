from __future__ import annotations

from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjpa_jurisprudencia_bff import build_tjpa_search_payload


def test_tjpa_maps_canonical_document_types_to_catalog_values() -> None:
    payload = build_tjpa_search_payload(
        JurisprudenceQuery(text="dano moral", types=["acordao", "decisao_monocratica"])
    )

    assert payload["tipo"] == ["acórdão", "decisão monocrática"]


def test_tjpa_preserves_official_catalog_type_values() -> None:
    payload = build_tjpa_search_payload(JurisprudenceQuery(text="dano moral", types=["acórdão"]))

    assert payload["tipo"] == ["acórdão"]
