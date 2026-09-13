from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfWriter

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjmg_dspace_jurisprudencia import (
    TjmgDspaceJurisprudenciaProvider,
)


class _Response:
    status_code = 200
    url = "https://bd.tjmg.jus.br"
    headers = {"Content-Type": "application/json"}

    def __init__(self, body: bytes, content_type: str = "application/json") -> None:
        self.content = body
        self.headers = {"Content-Type": content_type}

    def json(self):  # type: ignore[no-untyped-def]
        return json.loads(self.content)


class _Session:
    def __init__(self) -> None:
        root = Path(__file__).parent / "fixtures"
        search = (root / "tjmg_dspace_search.json").read_bytes()
        empty = (
            b'{"_embedded":{"searchResult":{"page":{"totalElements":0},'
            b'"_embedded":{"objects":[]}}}}'
        )
        bundles = b'{"_embedded":{"bundles":[{"name":"ORIGINAL","_links":{"bitstreams":{"href":"https://bd.tjmg.jus.br/streams"}}}]}}'
        streams = b'{"_embedded":{"bitstreams":[{"_links":{"content":{"href":"https://bd.tjmg.jus.br/content/item-001"}}}]}}'
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        import io

        buffer = io.BytesIO()
        writer.write(buffer)
        self.responses = [
            _Response(search),
            _Response(empty),
            _Response(empty),
            _Response(bundles),
            _Response(streams),
            _Response(buffer.getvalue(), "application/pdf"),
        ]

    def request(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self.responses.pop(0)


def test_tjmg_dspace_search_normalizes_second_degree_record() -> None:
    provider = TjmgDspaceJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=_Session(),  # type: ignore[arg-type]
    )
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=10))
    assert page.total == 1
    assert page.total_known is True
    result = page.results[0]
    assert result.authority == "TJMG"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.branch == "state"
    assert result.collection == "CJSG_CIVEL"
    document = provider.get_document(result.id)
    assert document.access_status.value == "public"
    assert document.content_type == "application/pdf"


def test_tjmg_dspace_rejects_first_degree() -> None:
    provider = TjmgDspaceJurisprudenciaProvider()
    from pytest import raises

    from nanojuris.errors import QueryRejectedError

    with raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="x", degree="first"))
