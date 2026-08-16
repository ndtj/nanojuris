from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError
from nanojuris.models import SourceTrace
from nanojuris.providers.tjma_jurisconsult import (
    TjmaJurisconsultProvider,
    parse_tjma_catalog,
)

FIXTURE = Path(__file__).parent / "fixtures" / "tjma_jurisconsult_catalog.json"


class FakeResponse:
    def __init__(self, data: Any, url: str) -> None:
        self.status_code = 200
        self.url = url
        self.headers = {"Content-Type": "application/json"}
        self.content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.text = self.content.decode("utf-8")

    def json(self) -> Any:
        return json.loads(self.content)


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        return self.responses.pop(0)


def payloads() -> dict[str, dict[str, Any]]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_tjma_catalog_parser_preserves_public_vocabularies() -> None:
    catalog = parse_tjma_catalog(
        payloads(),
        trace=SourceTrace(provider="tjma_jurisconsult", endpoint="catalog"),
    )
    assert catalog.source == "tjma_jurisconsult"
    assert catalog.species[0].description == "Acórdãos"
    assert catalog.raw["classes"][0]["str_classe"].startswith("Apelação")
    assert catalog.raw["search_access_status"] == "access_control_required"


def test_tjma_search_remains_explicitly_gated() -> None:
    provider = TjmaJurisconsultProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(AccessControlRequiredError):
        provider.search(None)


def test_tjma_provider_reads_catalog_endpoints() -> None:
    responses = [
        FakeResponse(payloads()[key], f"https://apijuris.tjma.jus.br/v1/{key}")
        for key in (
            "reports",
            "types",
            "classes",
            "magistrates",
            "chambers",
            "counties",
            "precedent_links",
        )
    ]
    provider = TjmaJurisconsultProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession(responses)
    )
    assert provider.get_catalog().species
