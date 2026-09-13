from __future__ import annotations

import io
from pathlib import Path

import pytest
from pypdf import PdfWriter

from nanojuris.config import NanoJurisConfig
from nanojuris.errors import QueryRejectedError
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.trt2_basis_jurisprudencia import (
    Trt2BasisJurisprudenciaProvider,
)


class _Response:
    status_code = 200
    headers = {"Content-Type": "text/html; charset=UTF-8"}

    def __init__(
        self,
        body: bytes,
        url: str,
        content_type: str = "text/html; charset=UTF-8",
    ) -> None:
        self.content = body
        self.url = url
        self.text = body.decode("utf-8", errors="replace")
        self.headers = {"Content-Type": content_type}


class _Session:
    def __init__(self) -> None:
        html = (Path(__file__).parent / "fixtures" / "trt2_basis_search.html").read_bytes()
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        pdf = io.BytesIO()
        writer.write(pdf)
        self.responses = [
            _Response(html, "https://basis.trt2.jus.br/discover"),
            _Response(
                pdf.getvalue(),
                "https://basis.trt2.jus.br/bitstream/handle/123456789/17787/Boletim.pdf",
                "application/pdf",
            ),
        ]

    def get(self, url: str, **kwargs: object) -> _Response:
        del kwargs
        response = self.responses.pop(0)
        response.url = url
        if response.headers.get("Content-Type", "").startswith("application/pdf"):
            return response
        response.headers = {"Content-Type": "text/html; charset=UTF-8"}
        return response

    def request(self, method: str, url: str, **kwargs: object) -> _Response:
        assert method.upper() == "GET"
        return self.get(url, **kwargs)


class _EmptySession:
    def get(self, url: str, **kwargs: object) -> _Response:
        del kwargs
        return _Response(b"<html><body><h1>Pesquisa</h1><p>Sem resultados</p></body></html>", url)

    def request(self, method: str, url: str, **kwargs: object) -> _Response:
        assert method.upper() == "GET"
        return self.get(url, **kwargs)


def test_trt2_basis_filters_curated_second_degree_records() -> None:
    provider = Trt2BasisJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=_Session(),  # type: ignore[arg-type]
    )
    page = provider.search(JurisprudenceQuery(text="responsabilidade", page_size=10))
    assert len(page.results) == 1
    assert page.total_known is False
    result = page.results[0]
    assert result.authority == "TRT2"
    assert result.branch == "labor"
    assert result.degree == "second"
    assert result.instance == "second"
    assert result.collection == "CJSG_CURATED_BULLETIN"
    assert result.number == "1001234-56.2025.5.02.0001"
    assert result.document_url and "/bitstream/" in result.document_url
    document = provider.get_document(result.id)
    assert document.access_status.value == "public"
    assert document.content_type.startswith("application/pdf")


def test_trt2_basis_rejects_first_degree_and_unsupported_filters() -> None:
    provider = Trt2BasisJurisprudenciaProvider()
    with pytest.raises(QueryRejectedError, match="segundo grau"):
        provider.search(JurisprudenceQuery(text="x", degree="first"))
    with pytest.raises(QueryRejectedError, match="case_class"):
        provider.search(JurisprudenceQuery(text="x", case_class="Ação trabalhista"))


def test_trt2_basis_does_not_treat_unknown_empty_page_as_complete() -> None:
    provider = Trt2BasisJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0),
        session=_EmptySession(),  # type: ignore[arg-type]
    )
    page = provider.search(JurisprudenceQuery(text="term absent", page_size=10))
    assert page.results == []
    assert page.total_known is False
    assert page.is_complete is False
    assert page.extraction_status.value == "partial"


def test_trt2_basis_capability_is_explicitly_curated() -> None:
    capabilities = Trt2BasisJurisprudenciaProvider().get_capabilities()
    assert capabilities.supports_unified_search is False
    assert capabilities.opt_in_unified_search is True
    assert capabilities.category == "curated_jurisprudence"
    assert "case_class" in capabilities.unsupported_filters
    assert "complete PJe" in capabilities.semantic_discriminator
