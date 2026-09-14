from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
)
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.tjal_esmal_banco_sentencas import (
    TjalEsmalBancoSentencasProvider,
    parse_tjal_esmal_html,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _trace() -> SourceTrace:
    return SourceTrace(
        provider="tjal_esmal_banco_sentencas",
        endpoint="GET /indexS.php?pag=ler",
        source_url="https://esmal.tjal.jus.br/indexS.php?pag=ler",
        http_status=200,
        retrieval_status="ok",
    )


def test_parser_preserves_first_degree_identity_and_pdf_links() -> None:
    html = (FIXTURES / "tjal_esmal_success.html").read_bytes()
    records = parse_tjal_esmal_html(
        html,
        query=JurisprudenceQuery(text="responsabilidade civil"),
        trace=_trace(),
    )
    assert len(records) == 2
    assert all(record.authority == "TJAL" for record in records)
    assert all(record.branch == "state" for record in records)
    assert all(record.degree == "first" for record in records)
    assert all(record.instance == "first" for record in records)
    assert all(record.collection == "TJAL_ESMAL_CJPG" for record in records)
    assert all(record.document_type == "sentenca" for record in records)
    assert all("intranetlegado.tjal.jus.br" in (record.document_url or "") for record in records)
    assert all(record.raw["source_record_id"] == record.id for record in records)
    assert all("source_record_id" in record.field_provenance for record in records)


def test_parser_prefers_utf8_when_legacy_meta_charset_is_stale() -> None:
    html = (
        '<html><head><meta charset="iso-8859-1"></head><body><table><tr>'
        "<td>01/01/2026</td><td>01/01/2026</td>"
        "<td>AÇÃO DE INDENIZAÇÃO</td>"
        '<td><a href="https://intranetlegado.tjal.jus.br/bancodesentencas/arquivos/a.pdf">PDF</a></td>'
        "</tr></table></body></html>"
    ).encode()

    records = parse_tjal_esmal_html(
        html, query=JurisprudenceQuery(text="acao indenizacao"), trace=_trace()
    )

    assert records[0].summary == "AÇÃO DE INDENIZAÇÃO"


def test_parser_applies_local_negative_terms_and_rejects_untrusted_links() -> None:
    html = (FIXTURES / "tjal_esmal_success.html").read_text(encoding="utf-8")
    excluded = parse_tjal_esmal_html(
        html,
        query=JurisprudenceQuery(text="responsabilidade civil", without_words="ordinaria"),
        trace=_trace(),
    )
    assert len(excluded) == 1
    assert "ordinaria" not in (excluded[0].summary or "").casefold()
    untrusted = html.replace(
        "https://intranetlegado.tjal.jus.br//bancodesentencas/arquivos/4bd663a5ea4bafb51abd96d86f887f66.pdf",
        "https://example.invalid/arquivo.pdf",
    )
    assert parse_tjal_esmal_html(
        untrusted,
        query=JurisprudenceQuery(text="responsabilidade civil"),
        trace=_trace(),
    )


def test_empty_and_invalid_html_are_distinct() -> None:
    empty = (FIXTURES / "tjal_esmal_empty.html").read_bytes()
    assert (
        parse_tjal_esmal_html(empty, query=JurisprudenceQuery(text="sem resultado"), trace=_trace())
        == []
    )
    invalid = (FIXTURES / "tjal_esmal_invalid.html").read_bytes()
    with pytest.raises(ParserContractChangedError):
        parse_tjal_esmal_html(
            invalid, query=JurisprudenceQuery(text="responsabilidade"), trace=_trace()
        )


def test_provider_sends_observed_query_and_category() -> None:
    class Response:
        status_code = 200
        url = "https://esmal.tjal.jus.br/indexS.php?pag=ler&cat=C&text=responsabilidade"
        headers = {"Content-Type": "text/html; charset=UTF-8"}
        is_redirect = False

        def __init__(self, body: bytes) -> None:
            self.content = body

    class Session:
        def __init__(self, body: bytes) -> None:
            self.body = body
            self.params: dict[str, str] | None = None

        def request(
            self,
            _method: str,
            _url: str,
            *,
            params: dict[str, str],
            **_kwargs: object,
        ) -> Response:
            self.params = params
            return Response(self.body)

    session = Session((FIXTURES / "tjal_esmal_success.html").read_bytes())
    provider = TjalEsmalBancoSentencasProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=session,  # type: ignore[arg-type]
    )
    page = provider.search(
        JurisprudenceQuery(text="responsabilidade", legal_area="civil", page_size=2)
    )
    assert session.params == {
        "pag": "ler",
        "p": "1",
        "cat": "C",
        "text": "responsabilidade",
    }
    assert len(page.results) == 2
    assert page.total_known is False
    assert page.is_complete is False
    assert page.results[0].degree == "first"


def test_shared_transport_keeps_access_control_distinct_from_empty() -> None:
    class Response:
        status_code = 403
        url = "https://esmal.tjal.jus.br/indexS.php?pag=ler"
        headers = {"Content-Type": "text/html"}
        is_redirect = False
        content = b"<html><body>access denied</body></html>"

    class Session:
        def request(self, *_args: object, **_kwargs: object) -> Response:
            return Response()

    provider = TjalEsmalBancoSentencasProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=Session(),  # type: ignore[arg-type]
    )
    with pytest.raises(AccessControlRequiredError):
        provider.search(JurisprudenceQuery(text="responsabilidade"))


def test_capabilities_are_federated_as_partial_and_documented() -> None:
    capabilities = TjalEsmalBancoSentencasProvider().get_capabilities()
    assert capabilities.supports_unified_search is True
    assert capabilities.opt_in_unified_search is False
    assert capabilities.supports_full_text is True
    assert capabilities.completeness_contract == "curated_html_index_total_unknown"
    assert capabilities.filter_status("legal_area") == "native"
    assert capabilities.filter_status("case_class") == "unsupported"


@pytest.mark.parametrize("degree", ["second", "2", "cjsg"])
def test_provider_rejects_non_first_degree_scope(degree: str) -> None:
    provider = TjalEsmalBancoSentencasProvider(NanoJurisConfig(rate_limit_interval=0))
    with pytest.raises(QueryRejectedError):
        provider.search(JurisprudenceQuery(text="divorcio", degree=degree))
