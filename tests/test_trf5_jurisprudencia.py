from __future__ import annotations

import pytest

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.errors import ParserContractChangedError
from nanojuris.models import JurisprudenceQuery, SourceTrace
from nanojuris.providers.trf5_jurisprudencia import (
    Trf5JurisprudenciaProvider,
    parse_trf5_results,
)

HTML = """
<html><body>
<input type="hidden" name="wi.token" value="session-token">
<table><tr><td class="grid">
<a href="javascript:exibir(25751)"><img src="view16.gif"></a>
<b>Órgão Julgador:</b> Primeira Turma - JFSE /
<b>Tipo de Documento:</b> Acórdãos /
<b>Data de Julgamento:</b> 05/07/2013 /
<b>Nr. Processo:</b> 0500731-14.2013.4.05.8501<br>
<a onclick="detalhesDocumento('25751')">Exibir Inteiro Teor</a>
<br>EMENTA: DANO MORAL. INSCRIÇÃO EM CADASTRO DE RESTRIÇÃO DE CRÉDITO.
</td></tr></table>
</body></html>
"""


class FakeResponse:
    def __init__(self, text: str, url: str, status_code: int = 200) -> None:
        self.text = text
        self.url = url
        self.status_code = status_code
        self.encoding = "iso-8859-1"


class FakeSession:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.responses.pop(0)


def test_parse_trf5_results_maps_html_row() -> None:
    page = parse_trf5_results(
        HTML,
        trace=SourceTrace(provider="trf5_jurisprudencia", endpoint="/resultado"),
        base_url="https://jurisprudencia.trf5.jus.br",
    )

    assert len(page) == 1
    assert page[0].id == "trf5-jurisprudencia-25751"
    assert page[0].number == "0500731-14.2013.4.05.8501"
    assert page[0].type == "acordao"
    assert page[0].raw["orgao_julgador"] == "Primeira Turma - JFSE"
    assert "DANO MORAL" in (page[0].summary or "")


def test_trf5_search_performs_session_get_then_result_post() -> None:
    session = FakeSession(
        [
            FakeResponse(HTML, "https://jurisprudencia.trf5.jus.br/jurisprudencia/pesquisa.wsp"),
            FakeResponse(
                HTML,
                "https://jurisprudencia.trf5.jus.br/jurisprudencia/resultado_pesquisa.wsp",
            ),
        ]
    )
    provider = Trf5JurisprudenciaProvider(NanoJurisConfig(rate_limit_interval=0), session=session)

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.total == 1
    assert [call["method"] for call in session.calls] == ["GET", "POST"]
    payload = session.calls[1]["kwargs"]["data"]
    assert payload["tmp.search.query"] == "dano moral"
    assert payload["wi.token"] == "session-token"


def test_trf5_parser_rejects_unknown_result_shape() -> None:
    with pytest.raises(ParserContractChangedError):
        parse_trf5_results(
            "<html><body>Resposta sem resultados conhecidos</body></html>",
            trace=SourceTrace(provider="trf5_jurisprudencia", endpoint="/resultado"),
            base_url="https://example.test",
        )


def test_trf5_provider_is_registered() -> None:
    assert "trf5_jurisprudencia" in NanoJurisClient().providers
