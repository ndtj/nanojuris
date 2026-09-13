from __future__ import annotations

from pathlib import Path

from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjms_cjpg import TjmsCjpgProvider
from nanojuris.providers.tjsp_cjpg import parse_tjsp_cjpg_response

FIXTURE = Path(__file__).parent / "fixtures" / "tjms_cjpg_success.html"


def test_tjms_cjpg_parser_keeps_first_degree_identity() -> None:
    query = JurisprudenceQuery(text="responsabilidade", page_size=10)
    page = parse_tjsp_cjpg_response(
        FIXTURE.read_bytes(),
        query=query,
        trace=SourceTrace(
            provider="tjms_cjpg",
            endpoint="GET /cjpg/pesquisar.do",
            source_url="https://esaj.tjms.jus.br/cjpg/pesquisar.do",
        ),
        base_url="https://esaj.tjms.jus.br",
        source="tjms_cjpg",
        authority="TJMS",
    )
    assert page.source == "tjms_cjpg"
    assert page.total == 1
    assert len(page.results) == 1
    result = page.results[0]
    assert result.court == "TJMS"
    assert result.authority == "TJMS"
    assert result.degree == "first"
    assert result.instance == "first"
    assert result.collection == "CJPG"
    assert result.full_text and "primeiro grau" in result.full_text


def test_tjms_cjpg_capability_uses_own_public_host() -> None:
    provider = TjmsCjpgProvider()
    capabilities = provider.get_capabilities()
    assert capabilities.source == "tjms_cjpg"
    assert capabilities.source_url == "https://esaj.tjms.jus.br"
    assert capabilities.supports_full_text is True
    assert capabilities.filter_status("text") == "native"
    assert capabilities.filter_status("degree") == "validated_scope"
    assert provider.transport.policy.allowed_hosts == ("esaj.tjms.jus.br",)


def _trace() -> SourceTrace:
    return SourceTrace(provider="tjms_cjpg", endpoint="GET /cjpg/pesquisar.do")


def test_tjms_cjpg_explicit_empty_is_not_a_parser_failure() -> None:
    page = parse_tjsp_cjpg_response(
        (Path(__file__).parent / "fixtures" / "tjms_cjpg_empty.html").read_bytes(),
        query=JurisprudenceQuery(text="inexistente"),
        trace=_trace(),
        base_url="https://esaj.tjms.jus.br",
        source="tjms_cjpg",
        authority="TJMS",
    )
    assert page.results == []
    assert page.is_complete is True
    assert page.access_status.value == "public"


def test_tjms_cjpg_access_and_schema_states_are_explicit() -> None:
    with __import__("pytest").raises(AccessControlRequiredError):
        parse_tjsp_cjpg_response(
            (Path(__file__).parent / "fixtures" / "tjms_cjpg_access_control.html").read_bytes(),
            query=JurisprudenceQuery(text="responsabilidade"),
            trace=_trace(),
            base_url="https://esaj.tjms.jus.br",
            source="tjms_cjpg",
            authority="TJMS",
        )
    with __import__("pytest").raises(ParserContractChangedError):
        parse_tjsp_cjpg_response(
            (Path(__file__).parent / "fixtures" / "tjms_cjpg_schema_drift.html").read_bytes(),
            query=JurisprudenceQuery(text="responsabilidade"),
            trace=_trace(),
            base_url="https://esaj.tjms.jus.br",
            source="tjms_cjpg",
            authority="TJMS",
        )
