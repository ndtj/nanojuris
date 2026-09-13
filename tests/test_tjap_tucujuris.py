from __future__ import annotations

import pytest

from nanojuris.errors import AccessControlRequiredError, QueryRejectedError, SourceUnavailableError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjap_tucujuris import TjapTucujurisProvider, _build_payload


class _Response:
    status_code = 200
    url = "https://tucujuris.tjap.jus.br/api/publico/consultar-jurisprudencia"
    headers = {"Content-Type": "application/json"}
    content = b'{"status":"ERRO"}'

    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.content = str(payload).encode()

    def json(self) -> dict:
        return self.payload


class _Session:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def post(self, *args, **kwargs):
        self.kwargs = kwargs
        return _Response(self.payload)

    def get(self, *args, **kwargs):
        self.get_kwargs = kwargs
        return _Response(self.payload)


def test_tjap_payload_matches_juscraper_contract() -> None:
    payload = _build_payload(
        JurisprudenceQuery(
            text="responsabilidade",
            number="0000000-00.0000.0.00.0000",
            case_class="Apelação",
            rapporteur="Relator",
            judging_body="Câmara",
            source_origin="Macapá",
            decision_type="acórdão",
            page=2,
            degree="second",
        )
    )
    assert payload["ementa"] == "responsabilidade"
    assert payload["numeroCNJ"].startswith("0000000")
    assert payload["classe"] == "Apelação"
    assert payload["relator"] == "Relator"
    assert payload["secretaria"] == "Câmara"
    assert payload["origem"] == "Macapá"
    assert payload["tipo_jurisprudencia"] == "acórdão"
    assert payload["offset"] == 20


def test_tjap_turnstile_error_never_becomes_empty() -> None:
    provider = TjapTucujurisProvider(
        session=_Session({"status": "ERRO", "mensagem": "A verificação de segurança falhou"})  # type: ignore[arg-type]
    )
    with pytest.raises(AccessControlRequiredError, match="Turnstile"):
        provider.search(JurisprudenceQuery(text="responsabilidade", degree="second"))


def test_tjap_authorized_search_accepts_one_human_pass_and_redacts_it() -> None:
    session = _Session(
        {
            "status": "OK",
            "total": 1,
            "dados": [
                {
                    "id": "123",
                    "textoementa": "Responsabilidade civil administrativa.",
                    "numeroacordao": "123/2025",
                    "nomerelator": "Relator",
                }
            ],
        }
    )
    provider = TjapTucujurisProvider(session=session)  # type: ignore[arg-type]
    page = provider.search_authorized(
        JurisprudenceQuery(text="responsabilidade", degree="second"),
        turnstile_token="human-pass",
    )
    assert len(page.results) == 1
    assert page.results[0].summary == "Responsabilidade civil administrativa."
    assert page.extraction_status.value == "complete"
    assert page.source_trace is not None
    assert "captcha" not in page.source_trace.query
    assert session.kwargs["json"]["captcha"] == "human-pass"
    bundle = provider.get_decisions(page.results[0].id)
    assert bundle.source == "tjap_tucujuris"
    assert bundle.texts[0]["content"] == page.results[0].summary
    assert "human-pass" not in str(bundle.to_dict())


def test_tjap_authorized_search_requires_nonempty_pass() -> None:
    provider = TjapTucujurisProvider(session=_Session({}))  # type: ignore[arg-type]
    with pytest.raises(AccessControlRequiredError, match="passe Turnstile"):
        provider.search_authorized(
            JurisprudenceQuery(text="responsabilidade", degree="second"),
            turnstile_token=" ",
        )


def test_tjap_detail_requires_an_observed_authorized_result() -> None:
    provider = TjapTucujurisProvider(session=_Session({}))  # type: ignore[arg-type]
    with pytest.raises(SourceUnavailableError, match="busca autorizada observada"):
        provider.get_decisions("tjap-unknown")


def test_tjap_public_filter_catalog_is_metadata_not_search_results() -> None:
    provider = TjapTucujurisProvider(
        session=_Session(
            {
                "status": "OK",
                "dados": {
                    "classes": [{"id": "APELACAO", "descricao": "Apelação"}],
                    "origens": [{"id": "AMAPA", "descricao": "Amapá"}],
                    "relatores": [{"mat_relat": "R1", "descricao": "R1"}],
                    "secretarias": [{"id": "CAMARA", "descricao": "Câmara"}],
                },
            }
        )  # type: ignore[arg-type]
    )
    catalog = provider.get_catalog()
    assert catalog.species[0].code == "APELACAO"
    assert catalog.courts == []
    assert catalog.raw["filters"]["origens"][0]["id"] == "AMAPA"
    assert catalog.raw["counts"]["relatores"] == 1
    assert catalog.source_trace is not None
    assert catalog.source_trace.endpoint.startswith("GET")


def test_tjap_public_last_update_is_exposed_without_search() -> None:
    provider = TjapTucujurisProvider(
        session=_Session({"status": "OK", "dados": "2026-09-10 18:09:40-03"})  # type: ignore[arg-type]
    )
    assert provider.get_last_update().startswith("2026-09-10")


def test_tjap_explicit_empty_is_distinct() -> None:
    provider = TjapTucujurisProvider(
        session=_Session({"status": "ERRO", "mensagem": "Nenhum resultado encontrado."})  # type: ignore[arg-type]
    )
    page = provider.search(JurisprudenceQuery(text="termo raro", degree="second"))
    assert page.is_explicit_empty
    assert page.total_known is True
    assert page.access_status.value == "public"
    assert page.extraction_status.value == "empty"


def test_tjap_rejects_first_degree_scope() -> None:
    provider = TjapTucujurisProvider(session=_Session({}))  # type: ignore[arg-type]
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="responsabilidade", degree="first"))
