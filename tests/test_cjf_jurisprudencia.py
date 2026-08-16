from __future__ import annotations

from pathlib import Path

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import AccessControlRequiredError, ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.cjf_jurisprudencia import CjfJurisprudenciaProvider, parse_cjf_results

FIXTURES = Path(__file__).parent / "fixtures"

HTML = """
<html><body>
<form id="formulario">
<input type="hidden" name="javax.faces.ViewState" value="view-state">
<input type="text" name="formulario:textoLivre">
<input type="checkbox" name="formulario:selectTiposDocumento" value="ACORDAO">
<button name="formulario:actPesquisar" type="submit">Pesquisar</button>
</form>
<div>Exibindo 1 - 30 de 7483, Página: 1/250</div>
<table class="table_resultado"><tbody>
<div><tr><td><span class="label_pontilhada">Tipo</span></td></tr><tr><td>Acórdão</td></tr></div>
<div><tr><td><span class="label_pontilhada">Número</span></td></tr>
<tr><td>1001321-42.2024.4.01.3300<br>10013214220244013300</td></tr></div>
<div><tr><td><span class="label_pontilhada">Classe</span></td></tr>
<tr><td>Apelação Cível</td></tr></div>
<div><tr><td><span class="label_pontilhada">Relator(a)</span></td></tr>
<tr><td>Relator Exemplo</td></tr></div>
<div><tr><td><span class="label_pontilhada">Origem</span></td></tr>
<tr><td>TRF - PRIMEIRA REGIÃO</td></tr></div>
<div><tr><td><span class="label_pontilhada">Órgão julgador</span></td></tr>
<tr><td>Primeira Turma</td></tr></div>
<div><tr><td><span class="label_pontilhada">Data</span></td></tr><tr><td>01/02/2025</td></tr></div>
<div><tr><td><span class="label_pontilhada">Data da publicação</span></td></tr>
<tr><td>05/02/2025</td></tr></div>
<div><tr><td><span class="label_pontilhada">Ementa</span></td></tr>
<tr><td>DANO MORAL. EMENTA PUBLICA.</td></tr></div>
<div><tr><td><span class="label_pontilhada">Decisão</span></td></tr>
<tr><td>Conhecido e provido.</td></tr></div>
<div><tr><td><span class="label_pontilhada">Inteiro teor</span></td></tr>
<tr><td><a href="https://pje2g.trf1.jus.br/publica">Acesse Aqui</a></td></tr></div>
</tbody></table>
</body></html>
"""


class FakeResponse:
    def __init__(self, text: str, url: str) -> None:
        self.text = text
        self.url = url
        self.status_code = 200
        self.encoding = "utf-8"


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def test_parse_cjf_trf1_result_tables() -> None:
    results, total = parse_cjf_results(
        HTML,
        trace=SourceTrace(provider="cjf_jurisprudencia", endpoint="/trf1/index.xhtml"),
    )

    assert total == 7483
    assert len(results) == 1
    assert results[0].id.startswith("cjf-trf1-")
    assert results[0].court == "TRF1"
    assert results[0].number == "1001321-42.2024.4.01.3300"
    assert results[0].rapporteur == "Relator Exemplo"
    assert results[0].raw["judging_body"] == "Primeira Turma"
    assert results[0].raw["document_url"] == "https://pje2g.trf1.jus.br/publica"


def test_parse_cjf_fixture_has_stable_identity_and_separate_dates() -> None:
    fixture = (FIXTURES / "cjf_trf1_success.html").read_text(encoding="utf-8")

    first, _ = parse_cjf_results(
        fixture,
        trace=SourceTrace(provider="cjf_jurisprudencia", endpoint="/trf1/index.xhtml"),
    )
    second, _ = parse_cjf_results(
        fixture,
        trace=SourceTrace(provider="cjf_jurisprudencia", endpoint="/trf1/index.xhtml"),
    )

    assert first[0].id == second[0].id
    assert first[0].judgment_date == "01/02/2025"
    assert first[0].publication_date == "05/02/2025"
    assert first[0].access_status is not None
    assert first[0].access_status.value == "public"


def test_cjf_parser_accepts_empty_fixture() -> None:
    results, total = parse_cjf_results(
        (FIXTURES / "cjf_trf1_empty.html").read_text(encoding="utf-8"),
        trace=SourceTrace(provider="cjf_jurisprudencia", endpoint="/trf1/index.xhtml"),
    )

    assert results == []
    assert total == 0


def test_cjf_parser_rejects_contract_fixture() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_cjf_results(
            (FIXTURES / "cjf_trf1_contract_changed.html").read_text(encoding="utf-8"),
            trace=SourceTrace(provider="cjf_jurisprudencia", endpoint="/trf1/index.xhtml"),
        )


def test_cjf_provider_detects_access_control_fixture() -> None:
    session = FakeSession(
        [
            FakeResponse(
                (FIXTURES / "cjf_trf1_access_control.html").read_text(encoding="utf-8"),
                "https://jurisprudencia.cjf.jus.br/trf1/index.xhtml",
            )
        ]
    )
    provider = CjfJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    with pytest.raises(AccessControlRequiredError, match="access-control"):
        provider.search(JurisprudenceQuery(text="teste"))


def test_cjf_provider_posts_viewstate_and_type() -> None:
    session = FakeSession(
        [
            FakeResponse(HTML, "https://jurisprudencia.cjf.jus.br/trf1/index.xhtml"),
            FakeResponse(HTML, "https://jurisprudencia.cjf.jus.br/trf1/index.xhtml"),
        ]
    )
    provider = CjfJurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="dano moral", types=["ACORDAO"], page_size=1))

    assert page.total == 7483
    assert [call["method"] for call in session.calls] == ["GET", "POST"]
    payload = session.calls[1]["kwargs"]["data"]
    assert payload["formulario:textoLivre"] == "dano moral"
    assert payload["formulario:selectTiposDocumento"] == ["ACORDAO"]
    assert payload["javax.faces.ViewState"] == "view-state"


def test_cjf_parser_rejects_unknown_shape() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_cjf_results(
            "<html><body>sem resultado conhecido</body></html>",
            trace=SourceTrace(provider="cjf_jurisprudencia", endpoint="/trf1/index.xhtml"),
        )


def test_cjf_provider_is_registered() -> None:
    assert "cjf_jurisprudencia" in NanoJurisClient().providers
