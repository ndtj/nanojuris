from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError, RateLimitDetectedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjrs_solr import (
    TjrsSolrProvider,
    parse_tjrs_search_response,
)

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, payload, *, status_code: int = 200):
        self.payload = payload
        self.status_code = status_code
        self.url = "https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php"
        self.headers = {"Content-Type": "application/json; charset=utf-8"}
        self.content = json.dumps(payload).encode("utf-8") if isinstance(payload, dict) else b""
        self.text = self.content.decode("utf-8")

    def json(self):
        if not isinstance(self.payload, dict):
            raise ValueError("invalid json")
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def _fixture() -> dict:
    return json.loads(
        (ROOT / "tests" / "fixtures" / "tjrs_solr_results.json").read_text(encoding="utf-8")
    )


def test_tjrs_parser_keeps_identity_and_separates_dates():
    page = parse_tjrs_search_response(
        _fixture(),
        query=JurisprudenceQuery(text="responsabilidade civil", page_size=1),
        trace=SourceTrace(provider="tjrs_solr", endpoint="/buscas/jurisprudencia/ajax.php"),
    )

    result = page.results[0]
    assert result.id == "tjrs-solr-TJRS-0001"
    assert result.judgment_date == "2026-01-10"
    assert result.publication_date == "2026-01-20"
    assert result.updated_at is None
    assert result.access_status.value == "public"
    assert page.is_complete is False


def test_tjrs_search_trace_contains_http_evidence():
    response = FakeResponse(_fixture())
    provider = TjrsSolrProvider(NanoJurisConfig(rate_limit_interval=0), FakeSession([response]))

    page = provider.search(JurisprudenceQuery(text="responsabilidade civil", page_size=1))
    trace = page.source_trace

    assert trace is not None
    assert trace.http_status == 200
    assert trace.content_type == "application/json; charset=utf-8"
    assert trace.response_bytes == len(response.content)
    assert trace.content_sha256 == hashlib.sha256(response.content).hexdigest()
    assert trace.retrieval_status == "ok"


def test_tjrs_parser_rejects_missing_stable_identifier():
    payload = _fixture()
    payload["response"]["docs"][0].pop("cod_ementa")
    payload["response"]["docs"][0].pop("numero_processo")
    payload["response"]["docs"][0].pop("_version_", None)

    with pytest.raises(ParserContractChangedError, match="stable identifier"):
        parse_tjrs_search_response(
            payload,
            query=JurisprudenceQuery(text="termo"),
            trace=SourceTrace(provider="tjrs_solr", endpoint="/buscas/jurisprudencia/ajax.php"),
        )


def test_tjrs_classifies_rate_limit():
    provider = TjrsSolrProvider(
        NanoJurisConfig(rate_limit_interval=0), FakeSession([FakeResponse({}, status_code=429)])
    )

    with pytest.raises(RateLimitDetectedError):
        provider.search(JurisprudenceQuery(text="termo"))
