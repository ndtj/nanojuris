from __future__ import annotations

from dataclasses import dataclass

from tools.qa_jurisprudence_documents import _is_search_endpoint, _probe_source, _select_sources


@dataclass
class _Result:
    payload: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return self.payload


@dataclass
class _Page:
    results: list[_Result]
    total: int = 1
    source: str = "fixture"


class _Capabilities:
    supports_full_text = True


@dataclass
class _SourceCapability:
    source: str
    supports_full_text: bool
    endpoints: tuple[str, ...] = ()
    full_text_access: str = "unknown"


class _SourceListClient:
    def list_sources(self) -> list[_SourceCapability]:
        return [
            _SourceCapability("inline", True, ("GET /doc",), "detail_call"),
            _SourceCapability("summary_only", False),
            _SourceCapability("link_only", False, ("GET /doc",), "link_only"),
        ]


class _InlineClient:
    def search(self, query: str, *, source: str, page_size: int) -> _Page:
        return _Page(
            results=[
                _Result(
                    {
                        "id": "tjpa-bff-1",
                        "number": "0000001-00.2024.8.14.0001",
                        "full_text": "inteiro teor inline",
                        "summary": "ementa",
                        "document_url": "https://jurisprudencia.tjpa.jus.br/bff/api/decisoes/buscar",
                        "raw": {},
                        "access_status": "public",
                        "extraction_status": "complete",
                    }
                )
            ]
        )

    def get_capabilities(self, *, source: str) -> _Capabilities:
        return _Capabilities()

    def get_document(self, document_id: str, *, source: str) -> object:
        raise AssertionError("inline text must not trigger a detail call")


def test_search_endpoint_is_not_probed_as_a_document() -> None:
    assert _is_search_endpoint("https://example.test/bff/api/decisoes/buscar")
    assert _is_search_endpoint("https://example.test/jurisprudencia/ajax.php")
    assert not _is_search_endpoint("https://example.test/jurisprudencia/123/public")


def test_source_selection_is_explicit_and_excludes_candidates() -> None:
    client = _SourceListClient()

    assert _select_sources(client, all_supported=True) == ["inline"]
    assert _select_sources(client, requested=["inline"]) == ["inline"]
    assert _select_sources(client, pending_documents=True) == ["link_only"]


def test_inline_full_text_is_a_terminal_document_check() -> None:
    report = _probe_source(_InlineClient(), "tjpa_jurisprudencia_bff", "responsabilidade", 5)

    assert report["status"] == "checked"
    assert report["provider_document"]["status"] == "inline_text"
    assert "public_url" not in report
    assert "document_failures" not in report
