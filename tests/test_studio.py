from __future__ import annotations

import os
import sys
from types import ModuleType, SimpleNamespace

import pytest

from nanojuris import NanoJurisClient
from nanojuris.models import CanonicalDecision, ProviderCapabilities
from nanojuris.web.schemas import StudioSearchRequest, StudioValidationRequest
from nanojuris.web.server import main as studio_server_main
from nanojuris.web.studio import (
    studio_search,
    studio_sources_payload,
    supported_filters_for,
)


class FakeStudioClient:
    providers = {"tjdf_juris": object(), "stj_scon": object()}

    def list_sources(self):
        return [
            ProviderCapabilities(
                source="tjdf_juris",
                display_name="TJDFT Juris",
                source_url="https://example.test/tjdf",
                category="court_jurisprudence",
                search_modes=["text", "date_range"],
                extracted_fields=["case_number", "rapporteur", "judging_body"],
                supports_full_text=True,
            ),
            ProviderCapabilities(
                source="outside_scope_communications",
                display_name="Comunicacoes judiciais",
                source_url="https://example.test/communications",
                category="judicial_communications",
                search_modes=["text"],
            ),
        ]

    def search_many(self, text, **kwargs):
        assert text == "idpj"
        assert kwargs["sources"] == ["tjdf_juris"]
        assert kwargs["published_from"] == "2026-01-01"
        return {
            "sources": ["tjdf_juris"],
            "searched_sources": ["tjdf_juris"],
            "skipped_sources": [],
            "routing_summary": [
                {
                    "source": "tjdf_juris",
                    "action": "searched",
                    "reason": "source_applicable",
                    "message": "Fonte consultada.",
                }
            ],
            "page": 1,
            "page_size": 5,
            "total_returned": 1,
            "results": [
                CanonicalDecision(
                    id="dec-1",
                    source="tjdf_juris",
                    court="TJDFT",
                    case_number="0000000-00.2026.8.07.0000",
                    summary="Ementa publica completa",
                )
            ],
            "errors": [],
        }

    def validate_sources(self, *, sources, text, page_size, timeout):
        assert sources == ["tjdf_juris"]
        assert text == "responsabilidade civil"
        assert page_size == 1
        assert timeout == 10
        return {
            "query": {"text": text, "page_size": page_size},
            "checked_sources": sources,
            "reports": [
                {
                    "source": "tjdf_juris",
                    "status": "valid",
                    "passed": True,
                    "returned": 1,
                }
            ],
            "summary": {"valid": 1},
            "complete": True,
            "passed": True,
        }


def test_studio_search_request_normalizes_payload():
    request = StudioSearchRequest.from_payload(
        {
            "query": "idpj",
            "sources": "tjdf_juris, stj_scon",
            "limit": 200,
            "filters": {"date_from": "2026-01-01"},
        }
    )

    assert request.query == "idpj"
    assert request.sources == ["tjdf_juris", "stj_scon"]
    assert request.page_size == 50
    assert request.search_kwargs()["published_from"] == "2026-01-01"


def test_studio_search_request_rejects_invalid_filters():
    with pytest.raises(ValueError, match="filters"):
        StudioSearchRequest.from_payload({"filters": []})


def test_supported_filters_are_inferred_from_capabilities():
    capability = ProviderCapabilities(
        source="fake",
        display_name="Fake",
        source_url="https://example.test",
        category="court_jurisprudence",
        search_modes=["full_text", "date_range"],
        extracted_fields=["case_number", "rapporteur", "case_class"],
        supports_full_text=True,
    )

    assert supported_filters_for(capability) == [
        "case_class",
        "case_number",
        "date_range",
        "full_text",
        "rapporteur",
        "text",
    ]


def test_studio_sources_payload_marks_recommended_jurisprudence_sources():
    payload = studio_sources_payload(FakeStudioClient())

    assert payload["total"] == 2
    assert payload["default_sources"] == ["tjdf_juris"]
    assert payload["recommended_sources"] == ["tjdf_juris"]
    assert payload["tier_counts"] == {"stable": 1, "context": 1}
    assert payload["selection_policy"]["default"] == "stable"
    assert payload["sources"][0]["documentation_url"].endswith(
        "/docs/providers/tjdf_juris/README.md"
    )
    assert payload["sources"][0]["contract_level"] == 5
    assert payload["sources"][0]["risk_level"] == "baixo"
    assert payload["sources"][0]["studio_tier"] == "stable"
    assert payload["sources"][0]["supported_filters"] == [
        "case_number",
        "date_range",
        "full_text",
        "judging_body",
        "rapporteur",
        "text",
    ]
    assert payload["sources"][1]["recommended_for_studio"] is False
    assert payload["sources"][1]["studio_tier"] == "context"


def test_studio_search_returns_source_status_and_jsonable_results():
    request = StudioSearchRequest(
        query="idpj",
        sources=["tjdf_juris"],
        filters={"date_from": "2026-01-01"},
        page_size=5,
    )

    payload = studio_search(FakeStudioClient(), request)

    assert payload["total"] == 1
    assert payload["source_status"]["tjdf_juris"]["status"] == "ok"
    assert payload["source_status"]["tjdf_juris"]["count"] == 1
    assert payload["results"][0]["case_number"] == "0000000-00.2026.8.07.0000"


def test_studio_validation_request_has_bounded_defaults():
    request = StudioValidationRequest.from_payload({"sources": "tjdf_juris", "timeout": 10})

    assert request.query == "responsabilidade civil"
    assert request.sources == ["tjdf_juris"]
    assert request.timeout == 10

    with pytest.raises(ValueError, match="between 1 and 120"):
        StudioValidationRequest.from_payload({"timeout": 121})


def test_studio_validate_reuses_shared_validation_contract():
    from nanojuris.web.studio import studio_validate

    payload = studio_validate(
        FakeStudioClient(),
        StudioValidationRequest(query="responsabilidade civil", sources=["tjdf_juris"], timeout=10),
    )

    assert payload["passed"] is True
    assert payload["reports"][0]["status"] == "valid"


def test_real_studio_catalog_exposes_maturity_selection_profiles():
    payload = studio_sources_payload(NanoJurisClient())

    assert payload["total"] == 37
    assert len(payload["default_sources"]) == 7
    assert len(payload["recommended_sources"]) == 34
    assert payload["tier_counts"] == {
        "advanced": 18,
        "context": 3,
        "restricted": 9,
        "stable": 7,
    }


def test_studio_server_reports_missing_optional_dependency(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    monkeypatch.setitem(sys.modules, "uvicorn", None)

    with pytest.raises(RuntimeError, match="nanojuris\\[studio\\]"):
        studio_server_main(["--no-browser"])


def test_studio_server_reports_missing_fastapi_before_uvicorn(monkeypatch):
    monkeypatch.setattr(
        "importlib.util.find_spec", lambda name: None if name == "fastapi" else object()
    )

    with pytest.raises(RuntimeError, match="FastAPI"):
        studio_server_main(["--no-browser"])


def test_studio_server_invokes_uvicorn_without_browser(monkeypatch):
    calls = []
    fake_uvicorn = ModuleType("uvicorn")
    fake_uvicorn.run = lambda *args, **kwargs: calls.append((args, kwargs))
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)
    monkeypatch.setattr("webbrowser.open", lambda url: calls.append(("browser", url)))

    exit_code = studio_server_main(["--host", "127.0.0.1", "--port", "9999", "--no-browser"])

    assert exit_code == 0
    assert calls == [
        (
            ("nanojuris.web.app:create_app",),
            {"host": "127.0.0.1", "port": 9999, "factory": True},
        )
    ]


def test_studio_server_can_ignore_environment_proxy(monkeypatch):
    calls = []
    fake_uvicorn = ModuleType("uvicorn")
    fake_uvicorn.run = lambda *args, **kwargs: calls.append((args, kwargs))
    monkeypatch.setattr("importlib.util.find_spec", lambda name: object())
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)
    monkeypatch.delenv("NANOJURIS_TRUST_ENV", raising=False)

    exit_code = studio_server_main(["--no-browser", "--ignore-env-proxy"])

    assert exit_code == 0
    assert calls
    assert sys.modules["uvicorn"] is fake_uvicorn
    assert os.environ["NANOJURIS_TRUST_ENV"] == "0"


def test_create_app_reports_missing_fastapi(monkeypatch):
    from nanojuris.web import app as studio_app

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "fastapi":
            raise ImportError("fastapi missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(RuntimeError, match="nanojuris\\[studio\\]"):
        studio_app.create_app(client=SimpleNamespace())


def test_create_app_serves_static_entrypoints():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from nanojuris.web import app as studio_app

    client = TestClient(studio_app.create_app(client=FakeStudioClient()))

    assert client.get("/").status_code == 200
    assert client.get("/assets/studio.js").status_code == 200
    assert client.get("/favicon.ico").status_code == 200


def test_create_app_exposes_validation_endpoint():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from nanojuris.web import app as studio_app

    client = TestClient(studio_app.create_app(client=FakeStudioClient()))
    response = client.post(
        "/api/validate",
        json={"sources": ["tjdf_juris"], "timeout": 10},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == {"valid": 1}


def test_create_app_rejects_invalid_validation_timeout():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from nanojuris.web import app as studio_app

    client = TestClient(studio_app.create_app(client=FakeStudioClient()))
    response = client.post("/api/validate", json={"timeout": 0})

    assert response.status_code == 400
