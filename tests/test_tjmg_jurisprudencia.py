from __future__ import annotations

import json

import pytest

from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
)
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjmg_jurisprudencia import TjmgJurisprudenciaProvider


class _Response:
    status_code = 200
    text = "<html><form><input name='txtcaptcha'></form></html>"


class _Session:
    headers: dict[str, str] = {}

    def get(self, *args, **kwargs):
        return _Response()

    def request(self, method, *args, **kwargs):
        del method, args, kwargs
        return _Response()


class _ModernResponse:
    status_code = 200
    headers = {"Content-Type": "application/json"}
    url = "https://jurisprudencia-api.tjmg.jus.br"

    def __init__(self, payload):
        self._payload = payload
        self.text = payload if isinstance(payload, str) else json.dumps(payload)
        self.content = self.text.encode("utf-8")

    def json(self):
        if isinstance(self._payload, str):
            raise ValueError("not json")
        return self._payload


class _ModernSession:
    headers: dict[str, str] = {}

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def post(self, url, *, json, **kwargs):
        self.calls.append((url, json))
        if url.endswith("/jurisprudencias/document"):
            response = _ModernResponse("<html><body>Inteiro teor TJMG</body></html>")
            response.headers = {"Content-Type": "application/json"}
            return response
        return _ModernResponse(
            {
                "totalRecords": 1,
                "jurisprudencias": [
                    {
                        "id": "abc",
                        "tipoDocumento": "Acórdão",
                        "ementa": "Ementa de teste",
                        "orgaoJulgador": "1ª Câmara Cível",
                        "julgamentoData": "01/01/2024",
                        "publicacaoData": "10/01/2024",
                        "numeroProcessoCnj": "00000000000000000000",
                        "documentoId": "doc-1",
                        "magistrado": "Relator Teste",
                        "classe": "Apelação",
                    }
                ],
            }
        )

    def request(self, method, url, *, json=None, **kwargs):
        del kwargs
        if method.upper() != "POST":
            return _ModernResponse("<html><form></form></html>")
        return self.post(url, json=json or {})


def test_tjmg_captcha_is_explicitly_blocked() -> None:
    provider = TjmgJurisprudenciaProvider(session=_Session())  # type: ignore[arg-type]
    with pytest.raises(AccessControlRequiredError, match="CAPTCHA"):
        provider.search(JurisprudenceQuery(text="responsabilidade", degree="second"))


def test_tjmg_rejects_first_degree_scope() -> None:
    provider = TjmgJurisprudenciaProvider(session=_Session())  # type: ignore[arg-type]
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="responsabilidade", degree="first"))


def test_tjmg_capabilities_preserve_juscraper_filters() -> None:
    capabilities = TjmgJurisprudenciaProvider().get_capabilities()
    assert capabilities.filter_status("case_class") == "native"
    assert capabilities.filter_status("degree") == "validated_scope"
    assert capabilities.filter_status("types") == "native"
    assert capabilities.filter_status("document_type") == "native"
    assert capabilities.filter_status("decision_type") == "native"
    assert capabilities.filter_status("courts") == "native"
    assert capabilities.filter_status("legal_area") == "native"
    assert capabilities.filter_status("exact_phrase") == "translated"
    assert capabilities.filter_status("all_words") == "translated"
    assert capabilities.filter_status("without_words") == "unsupported"
    assert capabilities.full_text_access == "detail_call"
    assert capabilities.supports_unified_search is True


def test_tjmg_modern_api_compiles_all_native_structured_filters() -> None:
    session = _ModernSession()
    provider = TjmgJurisprudenciaProvider(session=session)  # type: ignore[arg-type]
    provider.search(
        JurisprudenceQuery(
            text="dano moral",
            types=["acordao"],
            decision_type="decisao_monocratica",
            case_class="Apelação",
            judging_body="1ª Câmara Cível",
            rapporteur="Relator Teste",
            courts=["Belo Horizonte"],
            legal_area="responsabilidade civil",
            degree="second",
            page_size=1,
        )
    )
    payload = session.calls[0][1]
    assert payload["tiposDocumento"] == ["Acórdão", "Decisão Monocrática"]
    assert payload["classes"] == ["Apelação"]
    assert payload["orgaosJulgadores"] == ["1ª Câmara Cível"]
    assert payload["magistrados"] == ["Relator Teste"]
    assert payload["comarcas"] == ["Belo Horizonte"]
    assert payload["assuntos"] == ["responsabilidade civil"]


def test_tjmg_rejects_unproven_negative_word_filter() -> None:
    provider = TjmgJurisprudenciaProvider(session=_ModernSession())  # type: ignore[arg-type]
    with pytest.raises(QueryRejectedError, match="without_words"):
        provider.search(JurisprudenceQuery(text="dano", without_words="contrato"))


def test_tjmg_modern_api_normalizes_second_degree_and_document() -> None:
    session = _ModernSession()
    provider = TjmgJurisprudenciaProvider(session=session)  # type: ignore[arg-type]
    page = provider.search(
        JurisprudenceQuery(
            text="dano",
            degree="second",
            instance="second",
            branch="state",
            case_class="Apelação",
            page_size=1,
        )
    )
    assert page.total == 1
    assert page.total_known is True
    assert page.results[0].degree == "second"
    assert page.results[0].collection == "CJSG"
    assert page.results[0].document_url and "documentoId=doc-1" in page.results[0].document_url
    document = provider.get_document("abc")
    assert document.text == "Inteiro teor TJMG"
    assert len(session.calls) == 2
    assert session.calls[0][1]["classes"] == ["Apelação"]


def test_tjmg_modern_api_rejects_schema_drift() -> None:
    class DriftSession(_ModernSession):
        def post(self, url, *, json, **kwargs):
            return _ModernResponse({"totalRecords": 1, "items": []})

    provider = TjmgJurisprudenciaProvider(session=DriftSession())  # type: ignore[arg-type]
    with pytest.raises(ParserContractChangedError, match="contrato"):
        provider.search(JurisprudenceQuery(text="dano", degree="second"))


def test_tjmg_modern_api_translates_canonical_document_type() -> None:
    session = _ModernSession()
    provider = TjmgJurisprudenciaProvider(session=session)  # type: ignore[arg-type]
    provider.search(
        JurisprudenceQuery(
            text="dano",
            degree="second",
            document_type="acordao",
        )
    )
    assert session.calls[0][1]["tiposDocumento"] == ["Acórdão"]
