from __future__ import annotations

import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import UnsupportedQueryError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.justica_eleitoral_sjur import JusticaEleitoralSjurProvider

ROOT = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.url = "https://sjur-pesquisa-api.tse.jus.br/tse/catalog"
        self.text = json.dumps(payload)
        self.content = self.text.encode("utf-8")

    def json(self) -> object:
        return self._payload


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def post(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def fixture(name: str) -> object:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_catalog_maps_the_four_public_metadata_routes():
    session = FakeSession(
        [
            FakeResponse(fixture("sjur_classes.json")),
            FakeResponse(fixture("sjur_relatorias.json")),
            FakeResponse(fixture("sjur_eleicoes.json")),
            FakeResponse(fixture("sjur_normas.json")),
        ]
    )
    provider = JusticaEleitoralSjurProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    catalog = provider.get_catalog()

    assert [option.code for option in catalog.species] == ["RESPE", "AI"]
    assert catalog.raw["relatorias"][0]["nome"] == "Ministro Relator"
    assert catalog.raw["eleicoes"] == ["2022", "2024"]
    assert all(call["kwargs"]["json"] == ["TSE"] for call in session.calls)
    assert session.calls[0]["url"].endswith(
        "/tse/sjur-pesquisa-backend/rest/public/pesquisa/classes"
    )


def test_catalog_capabilities_are_catalog_only():
    provider = JusticaEleitoralSjurProvider(session=FakeSession([]))
    capabilities = provider.get_capabilities()

    assert capabilities.supports_catalog is True
    assert capabilities.supports_unified_search is False
    assert capabilities.canonical_records == ["ProviderCatalog"]
    assert capabilities.completeness_contract == "catalog_snapshot_only"


def test_decision_search_is_not_promoted_without_result_contract():
    provider = JusticaEleitoralSjurProvider(session=FakeSession([]))

    with pytest.raises(UnsupportedQueryError):
        provider.search(JurisprudenceQuery(text="urna eletrônica"))
