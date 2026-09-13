from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, QueryRejectedError, SourceUnavailableError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjse_jurisprudencia import TjseJurisprudenciaProvider


class _Response:
    status_code = 200
    text = (Path(__file__).parent / "fixtures" / "tjse_jurisprudencia_form.html").read_text(
        encoding="utf-8"
    )
    body = text.encode()
    final_url = "https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse"
    content_type = "text/html"
    content_sha256 = ""


class _Session:
    def request(self, *args, **kwargs):
        return _Response()


def test_tjse_form_is_explicitly_blocked_by_turnstile() -> None:
    provider = TjseJurisprudenciaProvider(
        NanoJurisConfig(timeout=2),
        session=_Session(),  # type: ignore[arg-type]
    )
    with pytest.raises(AccessControlRequiredError, match="Turnstile"):
        provider.search(JurisprudenceQuery(text="responsabilidade", degree="second"))


def test_tjse_rejects_non_second_degree_scope() -> None:
    provider = TjseJurisprudenciaProvider(session=_Session())  # type: ignore[arg-type]
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="responsabilidade", degree="first"))


def test_tjse_capabilities_expose_observed_filters_without_federation() -> None:
    capabilities = TjseJurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.filter_status("case_class") == "native"
    assert capabilities.filter_status("party_name") == "unsupported"
    assert capabilities.filter_status("degree") == "validated_scope"
    assert capabilities.full_text_access == "access_blocked"


def test_tjse_public_filter_catalog_is_metadata_only() -> None:
    class _CatalogResponse(_Response):
        text = (Path(__file__).parent / "fixtures" / "tjse_jurisprudencia_catalog.html").read_text(
            encoding="utf-8"
        )
        body = text.encode()

    class _CatalogSession:
        def request(self, *args, **kwargs):
            return _CatalogResponse()

    provider = TjseJurisprudenciaProvider(
        NanoJurisConfig(timeout=2),
        session=_CatalogSession(),  # type: ignore[arg-type]
    )
    catalog = provider.get_catalog()
    assert catalog.species[0].code == "APELACAO"
    assert catalog.raw["counts"]["rapporteur"] == 1
    assert catalog.raw["challenge_required_for_search"] is True
    assert catalog.source_trace is not None


def test_tjse_authorized_search_uses_human_token_once_and_parses_second_degree() -> None:
    class _AuthorizedResponse(_Response):
        def __init__(self, text: str) -> None:
            self.text = text
            self.body = text.encode()

    class _AuthorizedSession:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def request(self, *args, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return _Response()
            return _AuthorizedResponse(
                (
                    Path(__file__).parent / "fixtures" / "tjse_jurisprudencia_authorized.html"
                ).read_text(encoding="utf-8")
            )

    session = _AuthorizedSession()
    provider = TjseJurisprudenciaProvider(
        NanoJurisConfig(timeout=2),
        session=session,  # type: ignore[arg-type]
    )
    page = provider.search_authorized(
        JurisprudenceQuery(text="dano moral", degree="second"),
        turnstile_token="human-token",
    )
    assert len(page.results) == 1
    result = page.results[0]
    assert result.degree == "second"
    assert result.collection == "CJSG"
    assert result.document_url == "/Dgorg/documentos/42"
    assert page.total_known is False
    assert all("human-token" not in str(result.raw) for result in page.results)
    assert page.source_trace is not None
    assert "human-token" not in str(page.source_trace.to_dict())
    bundle = provider.get_decisions(result.id)
    assert bundle.source == "tjse_jurisprudencia"
    assert bundle.texts[0]["content"]
    assert bundle.raw["document_url"] == "/Dgorg/documentos/42"
    assert "human-token" not in str(bundle.to_dict())


def test_tjse_authorized_search_rejects_empty_token() -> None:
    provider = TjseJurisprudenciaProvider(session=_Session())  # type: ignore[arg-type]
    with pytest.raises(AccessControlRequiredError, match="token"):
        provider.search_authorized(
            JurisprudenceQuery(text="dano moral", degree="second"),
            turnstile_token=" ",
        )


def test_tjse_detail_requires_an_observed_authorized_result() -> None:
    provider = TjseJurisprudenciaProvider(session=_Session())  # type: ignore[arg-type]
    with pytest.raises(SourceUnavailableError, match="busca autorizada observada"):
        provider.get_decisions("tjse-unknown")
