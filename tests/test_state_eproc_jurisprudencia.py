from __future__ import annotations

from pathlib import Path

from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjrj_eproc_jurisprudencia import TjrjEprocJurisprudenciaProvider
from nanojuris.providers.tjsc_eproc_jurisprudencia import TjscEprocJurisprudenciaProvider

FIXTURE = Path(__file__).parent / "fixtures" / "tjsp_eproc_jurisprudencia_result.html"


class FakeResponse:
    def __init__(self, text: str, url: str) -> None:
        self.text = text
        self.status_code = 200
        self.encoding = "iso-8859-1"
        self.url = url


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append({"method": method, "url": url, "kwargs": kwargs})
        return self.response


def test_tjrj_eproc_uses_own_endpoint_and_court() -> None:
    session = FakeSession(
        FakeResponse(
            FIXTURE.read_text(encoding="utf-8"),
            "https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php",
        )
    )
    provider = TjrjEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.source == "tjrj_eproc_jurisprudencia"
    assert page.results[0].court == "TJRJ"
    assert page.results[0].id.startswith("tjrj-eproc-jurisprudencia-")
    assert session.calls[0]["method"] == "POST"
    assert "eproc1g.tjrj.jus.br" in str(session.calls[0]["url"])
    assert provider.get_capabilities().source_url.endswith("/eproc")


def test_tjsc_eproc_uses_own_endpoint_and_court() -> None:
    session = FakeSession(
        FakeResponse(
            FIXTURE.read_text(encoding="utf-8"),
            "https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php",
        )
    )
    provider = TjscEprocJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0), session=session
    )

    page = provider.search(JurisprudenceQuery(text="dano moral", page_size=1))

    assert page.source == "tjsc_eproc_jurisprudencia"
    assert page.results[0].court == "TJSC"
    assert page.results[0].id.startswith("tjsc-eproc-jurisprudencia-")
    assert "eprocwebcon.tjsc.jus.br" in str(session.calls[0]["url"])


def test_state_eproc_providers_are_registered() -> None:
    client = NanoJurisClient()

    assert "tjrj_eproc_jurisprudencia" in client.providers
    assert "tjsc_eproc_jurisprudencia" in client.providers
