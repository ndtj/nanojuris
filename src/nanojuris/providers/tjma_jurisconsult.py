"""TJMA JurisConsult public catalog provider.

The catalog endpoints are public. The result-search endpoints require a
captcha challenge, which remains explicit and is never automated here.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any
from urllib.parse import urljoin

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    DecisionBundle,
    ProviderCapabilities,
    ProviderCatalog,
    ProviderOption,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider


class TjmaJurisconsultProvider(JurisprudenceProvider):
    """Expose TJMA JurisConsult catalogs without automating captcha search."""

    name = "tjma_jurisconsult"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0
        self._last_http_metadata: dict[str, Any] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjma_jurisconsult_url.rstrip("/")

    def search(self, query: Any):
        raise AccessControlRequiredError(
            "TJMA JurisConsult exige captcha na busca de resultados; "
            "o NanoJuris disponibiliza somente o catalogo publico."
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise AccessControlRequiredError(
            "TJMA JurisConsult nao oferece detalhe automatizado sem o desafio da busca."
        )

    def get_catalog(self) -> ProviderCatalog:
        paths = {
            "reports": "/jurisprudencia/lista_relatorios",
            "types": "/jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=1",
            "classes": "/jurisprudencia/lista_todos_classes?tipoRelatorio=1",
            "magistrates": "/jurisprudencia/lista_todos_magistrados?tipoRelatorio=1",
            "chambers": "/jurisprudencia/lista_todos_camaras?tipoRelatorio=1",
            "counties": "/jurisprudencia/lista_todos_comarcas?tipoRelatorio=1",
            "precedent_links": "/jurisprudencia/links_pesquisa_sumulas",
        }
        payloads = {key: self._request_json(path)[0] for key, path in paths.items()}
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /jurisprudencia/lista_*",
            query={"catalog": True},
            source_url=self.base_url,
            limitations=[
                "Os endpoints de catalogo sao publicos e nao substituem a busca de resultados.",
                "A busca principal exige tokenG/keyId de captcha e nao e automatizada.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjma_catalog(payloads, trace=trace)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMA JurisConsult",
            source_url="https://jurisconsult.tjma.jus.br/",
            category="court_catalog",
            search_modes=["catalog", "text_gated", "precedent_links"],
            document_types=["acordao", "decisao_monocratica", "sentenca", "sumula"],
            content_formats=["json"],
            canonical_records=["ProviderCatalog"],
            extracted_fields=[
                "report_type",
                "search_type",
                "case_class",
                "rapporteur",
                "chamber",
                "county",
                "precedent_links",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.ACCESS_CONTROL_REQUIRED],
            endpoints=[
                "GET /jurisprudencia/lista_relatorios",
                "GET /jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_classes?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_magistrados?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_camaras?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_comarcas?tipoRelatorio=<id>",
                "GET /jurisprudencia/links_pesquisa_sumulas",
            ],
            supports_catalog=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            supports_live_tests=True,
            pagination_mode="none",
            completeness_contract="public_catalog_snapshot_only",
            full_text_access="not_implemented",
            supported_filters=["types", "catalog"],
            limitations=[
                "A busca de acordaos, decisoes e sentencas exige captcha.",
                "Catalogos sao snapshots de vocabulario e nao representam resultados coletados.",
            ],
            responsible_use=[
                "Usar o catalogo para desenho amostral e preenchimento de filtros.",
                "Nao interpretar o provider como acervo textual pesquisavel.",
                "Nao enviar tokenG, keyId ou qualquer desafio de captcha.",
            ],
        )

    def _request_json(self, path: str) -> tuple[dict[str, Any], str]:
        self._respect_rate_limit()
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        try:
            response = self.session.request(
                "GET",
                url,
                headers={"Accept": "application/json"},
                timeout=self.config.timeout,
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJMA JurisConsult request failed: {exc}") from exc
        content = bytes(getattr(response, "content", b"") or response.text.encode("utf-8"))
        response_url = str(getattr(response, "url", url) or url)
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response_url,
            "content_type": (getattr(response, "headers", {}) or {}).get("Content-Type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJMA JurisConsult returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJMA JurisConsult returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJMA JurisConsult rejected request with HTTP {response.status_code}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise SourceUnavailableError("TJMA JurisConsult returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise SourceUnavailableError("TJMA JurisConsult catalog root is not an object")
        return data, response_url

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_tjma_catalog(
    payloads: dict[str, dict[str, Any]], *, trace: SourceTrace
) -> ProviderCatalog:
    """Normalize the public TJMA vocabulary endpoints into ProviderCatalog."""

    reports = payloads.get("reports", {}).get("response", {}).get("relatorios", [])
    types = payloads.get("types", {}).get("tipos", [])
    classes = payloads.get("classes", {}).get("classes", [])
    magistrates = payloads.get("magistrates", {}).get("relatores", [])
    chambers = payloads.get("chambers", {}).get("camaras", [])
    counties = payloads.get("counties", {}).get("comarcas", [])
    links = payloads.get("precedent_links", {}).get("response", {}).get("pesquisaSumulas", [])
    species = [
        ProviderOption(
            code=str(item.get("id", "")),
            description=str(item.get("titulo", "")),
            metadata={"url": item.get("url")},
        )
        for item in reports
        if isinstance(item, dict) and item.get("id") is not None
    ]
    return ProviderCatalog(
        source="tjma_jurisconsult",
        courts=[ProviderOption(code="TJMA", description="Tribunal de Justica do Maranhao")],
        species=species,
        species_groups=[
            {
                "code": "public_search_catalog",
                "description": "Catalogos publicos do JurisConsult",
                "search_requires_captcha": True,
            }
        ],
        source_trace=trace,
        raw={
            "reports": reports,
            "search_types": types,
            "classes": classes,
            "magistrates": magistrates,
            "chambers": chambers,
            "counties": counties,
            "precedent_links": links,
            "search_access_status": AccessStatus.ACCESS_CONTROL_REQUIRED.value,
        },
    )
