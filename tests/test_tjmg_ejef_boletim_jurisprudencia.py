from __future__ import annotations

import io
import json
from pathlib import Path

from pypdf import PdfWriter
from pytest import raises

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjmg_ejef_boletim_jurisprudencia import (
    TjmgEjefBoletimJurisprudenciaProvider,
)

FIXTURES = Path(__file__).parent / "fixtures"


class _Response:
    status_code = 200
    url = "https://bd.tjmg.jus.br"

    def __init__(self, body: bytes, content_type: str = "application/json") -> None:
        self.content = body
        self.headers = {"Content-Type": content_type}

    def json(self):  # type: ignore[no-untyped-def]
        return json.loads(self.content)


class _Session:
    def __init__(self, responses: list[_Response]) -> None:
        self.responses = responses
        self.calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def request(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append((args, kwargs))
        return self.responses.pop(0)


def _pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_search_normalizes_curated_second_degree_record() -> None:
    session = _Session([_Response((FIXTURES / "tjmg_ejef_boletim_search.json").read_bytes())])
    provider = TjmgEjefBoletimJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=5))

    assert page.total == 1
    assert page.total_known is True
    assert page.results[0].source == "tjmg_ejef_boletim_jurisprudencia"
    assert page.results[0].authority == "TJMG"
    assert page.results[0].degree == "second"
    assert page.results[0].instance == "second"
    assert page.results[0].collection == "CJSG_EJEF_BOLETIM"
    assert page.results[0].document_url.endswith("ecd53b20-ca8b-4e2f-9714-d9db923d06a5")
    assert session.calls[0][1]["params"]["scope"] == "c4bd64ae-089d-446c-966f-2ba332a0cbf5"


def test_empty_result_is_authoritative_when_dspace_reports_zero() -> None:
    session = _Session([_Response((FIXTURES / "tjmg_ejef_boletim_empty.json").read_bytes())])
    provider = TjmgEjefBoletimJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="termo inexistente"))

    assert page.results == []
    assert page.total == 0
    assert page.total_known is True
    assert page.is_complete is True


def test_bulletin_metadata_without_abstract_remains_searchable() -> None:
    payload = json.loads((FIXTURES / "tjmg_ejef_boletim_search.json").read_text())
    metadata = payload["_embedded"]["searchResult"]["_embedded"]["objects"][0]["_embedded"][
        "indexableObject"
    ]["metadata"]
    metadata.pop("dc.description.abstract", None)
    session = _Session([_Response(json.dumps(payload).encode())])
    provider = TjmgEjefBoletimJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="responsabilidade"))

    assert len(page.results) == 1
    assert page.results[0].document_type == "boletim"
    assert page.results[0].summary


def test_invalid_schema_is_not_treated_as_empty() -> None:
    session = _Session([_Response((FIXTURES / "tjmg_ejef_boletim_invalid.json").read_bytes())])
    provider = TjmgEjefBoletimJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    with raises(ParserContractChangedError, match="searchResult"):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_document_uses_official_original_bitstream() -> None:
    bundles = {
        "_embedded": {
            "bundles": [
                {
                    "name": "ORIGINAL",
                    "_links": {
                        "bitstreams": {"href": "https://bd.tjmg.jus.br/server/api/core/streams"}
                    },
                }
            ]
        }
    }
    streams = {
        "_embedded": {
            "bitstreams": [
                {
                    "_links": {
                        "content": {
                            "href": "https://bd.tjmg.jus.br/server/api/core/content/bje-170"
                        }
                    }
                }
            ]
        }
    }
    session = _Session(
        [
            _Response((FIXTURES / "tjmg_ejef_boletim_search.json").read_bytes()),
            _Response(json.dumps(bundles).encode()),
            _Response(json.dumps(streams).encode()),
            _Response(_pdf(), "application/pdf"),
        ]
    )
    provider = TjmgEjefBoletimJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )
    result = provider.search(JurisprudenceQuery(text="responsabilidade")).results[0]

    document = provider.get_document(result.id)

    assert document.access_status.value == "public"
    assert document.content_type == "application/pdf"
    assert document.url.endswith("content/bje-170")
    assert document.source == "tjmg_ejef_boletim_jurisprudencia"


def test_only_second_degree_scope_is_supported() -> None:
    provider = TjmgEjefBoletimJurisprudenciaProvider()

    with raises(Exception, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="x", degree="first"))


def test_capabilities_keep_curated_scope_explicit() -> None:
    capabilities = TjmgEjefBoletimJurisprudenciaProvider().get_capabilities()

    assert capabilities.source == "tjmg_ejef_boletim_jurisprudencia"
    assert capabilities.supports_unified_search is True
    assert capabilities.pagination_mode == "offset"
    assert "text" in capabilities.supported_filters
    assert "Colecao curada" in capabilities.limitations[0]
