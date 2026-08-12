"""FastAPI application factory for NanoJuris Studio."""

from __future__ import annotations

import logging
from importlib import resources
from pathlib import Path
from typing import Any
from uuid import uuid4

from nanojuris import __version__
from nanojuris.client import NanoJurisClient
from nanojuris.errors import (
    AccessControlRequiredError,
    InvalidQueryError,
    NanoJurisError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedProviderError,
)
from nanojuris.web.schemas import StudioSearchRequest
from nanojuris.web.studio import studio_search, studio_sources_payload


def create_app(client: NanoJurisClient | None = None) -> Any:
    """Create the optional FastAPI app used by ``nanojuris studio``."""

    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:  # pragma: no cover - exercised without importing FastAPI.
        raise RuntimeError(
            "NanoJuris Studio requires optional dependencies. "
            'Install with: pip install "nanojuris[studio]"'
        ) from exc

    active_client = client or NanoJurisClient()
    app = FastAPI(
        title="NanoJuris Studio",
        version=__version__,
        description="Local unified jurisprudence search UI for NanoJuris.",
    )
    static_dir = _static_dir()

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "name": "NanoJuris Studio",
            "version": __version__,
            "providers": len(active_client.providers),
        }

    @app.get("/api/sources")
    def sources() -> dict[str, Any]:
        return studio_sources_payload(active_client)

    @app.get("/api/sources/{source}")
    def source_detail(source: str) -> dict[str, Any]:
        try:
            capability = active_client.get_capabilities(source=source).to_dict()
            contract = active_client.get_source_contract(source=source).to_dict()
        except Exception as exc:  # noqa: BLE001 - API boundary
            raise _as_http_exception(HTTPException, exc, not_found=True) from exc
        return {"capability": capability, "contract": contract}

    @app.post("/api/search")
    def search(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            request = StudioSearchRequest.from_payload(payload)
            return studio_search(active_client, request)
        except Exception as exc:  # noqa: BLE001 - API boundary
            raise _as_http_exception(HTTPException, exc) from exc

    @app.get("/api/documents/{source}/{document_id:path}")
    def document(source: str, document_id: str) -> dict[str, Any]:
        try:
            return active_client.get_document(document_id, source=source).to_dict()
        except Exception as exc:  # noqa: BLE001 - API boundary
            raise _as_http_exception(HTTPException, exc, not_found=True) from exc

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> FileResponse:
        return FileResponse(static_dir / "assets" / "favicon.svg", media_type="image/svg+xml")

    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    return app


def _as_http_exception(
    http_exception: Any, exc: Exception, *, not_found: bool = False
) -> Exception:
    """Map domain failures without exposing internal exception details."""

    if isinstance(exc, InvalidQueryError):
        status_code = 400
        detail = str(exc)
    elif isinstance(exc, AccessControlRequiredError):
        status_code = 403
        detail = "A fonte exige uma etapa de controle de acesso."
    elif isinstance(exc, RateLimitDetectedError):
        status_code = 429
        detail = "A fonte sinalizou limite de requisicoes."
    elif isinstance(exc, SourceUnavailableError):
        status_code = 503
        detail = "A fonte publica esta indisponivel no momento."
    elif isinstance(exc, ParserContractChangedError):
        status_code = 502
        detail = "A resposta da fonte mudou e precisa de validacao do provider."
    elif isinstance(exc, UnsupportedProviderError):
        status_code = 404
        detail = "Provider nao encontrado."
    elif isinstance(exc, NanoJurisError):
        status_code = 422
        detail = "A operacao nao e suportada por esta fonte."
    else:
        request_id = uuid4().hex
        logging.getLogger("nanojuris.web").exception(
            "unexpected Studio error request_id=%s", request_id
        )
        status_code = 500
        detail = f"Erro interno ao processar a requisicao. request_id={request_id}"
    return http_exception(status_code=status_code, detail=detail)


def _static_dir() -> Path:
    return Path(str(resources.files("nanojuris.web.static")))
