"""Comunica PJe/DJEN public judicial communications provider."""

from __future__ import annotations

import time
from typing import Any

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    DecisionBundle,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider


class ComunicaPjeProvider(JurisprudenceProvider):
    """Provider for public Comunica PJe/DJEN communications."""

    name = "comunica_pje"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/api/v1/comunicacao"
        params = self._build_params(query)
        data = self._request_json("GET", endpoint, params=params)
        _validate_response(data)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=self.config.comunica_pje_url.rstrip("/") + endpoint,
            limitations=[
                "Fonte publica de comunicacoes judiciais, nao base de acordaos.",
                "A API pode ignorar tamanho de pagina; o provider limita localmente.",
                "Textos sao publicacoes/comunicacoes objetivas do DJEN/Comunica PJe.",
            ],
        )
        items = list(data.get("items") or [])
        limited_items = items[: query.page_size]
        results = [_map_item(item, trace) for item in limited_items if isinstance(item, dict)]
        start = 1 if results else 0
        return SearchPage(
            source=self.name,
            total=int(data.get("count") or len(results)),
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            source_trace=trace,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "comunica_pje exposes public communications via search"},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="Comunica PJe / DJEN",
            source_url=self.config.comunica_pje_url,
            category="judicial_communications",
            search_modes=["text", "court", "case_number"],
            document_types=["comunicacao", "intimacao", "edital"],
            content_formats=["json"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "communication_id",
                "court",
                "case_number",
                "case_class",
                "publication_date",
                "communication_type",
                "source_body",
                "summary",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET /api/v1/comunicacao"],
            supports_full_text=False,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number", "published_from", "published_to"],
            limitations=[
                "Nao e uma base de jurisprudencia/acordaos; cobre comunicacoes publicas.",
                "Filtros observados: texto, siglaTribunal, numeroProcesso, "
                "dataDisponibilizacaoInicio/Fim, pagina.",
                "A API pode retornar ate 100 itens por pagina mesmo com size menor.",
            ],
            responsible_use=[
                "Usar para descoberta objetiva de publicacoes e movimentacoes publicas.",
                "Nao interpretar o teor como aconselhamento juridico.",
                "Preservar texto, link, tribunal e numero de processo para auditoria.",
            ],
        )

    def _build_params(self, query: JurisprudenceQuery) -> dict[str, str | int]:
        params: dict[str, str | int] = {
            "pagina": max(query.page - 1, 0),
            "size": query.page_size,
        }
        if query.text.strip():
            params["texto"] = query.text.strip()
        if query.number.strip():
            params["numeroProcesso"] = _digits_only(query.number)
        if query.courts:
            params["siglaTribunal"] = query.courts[0].strip().upper()
        if query.published_from.strip():
            params["dataDisponibilizacaoInicio"] = query.published_from.strip()
        if query.published_to.strip():
            params["dataDisponibilizacaoFim"] = query.published_to.strip()
        return params

    def _request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        self._respect_rate_limit()
        url = self.config.comunica_pje_url.rstrip("/") + path
        headers = {
            "Accept": "application/json",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"Comunica PJe request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("Comunica PJe returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"Comunica PJe returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"Comunica PJe rejected request with HTTP {response.status_code}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ParserContractChangedError("Comunica PJe response is not JSON") from exc

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def _validate_response(data: Any) -> None:
    if not isinstance(data, dict):
        raise ParserContractChangedError("Comunica PJe response is not an object")
    if "items" not in data or not isinstance(data.get("items"), list):
        raise ParserContractChangedError("Comunica PJe response does not contain items")


def _map_item(item: dict[str, Any], trace: SourceTrace) -> JurisprudenceResult:
    communication_id = str(item.get("id") or "")
    if not communication_id:
        raise ParserContractChangedError("Comunica PJe item without id")
    court = str(item.get("siglaTribunal") or "")
    communication_type = str(item.get("tipoComunicacao") or item.get("tipoDocumento") or "")
    case_number = item.get("numeroprocessocommascara") or item.get("numero_processo")
    source_url = str(item.get("link") or "") or trace.source_url
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=source_url,
        limitations=trace.limitations,
    )
    return JurisprudenceResult(
        id=f"comunica-pje-{communication_id}",
        source="comunica_pje",
        court=court,
        type="comunicacao",
        number=str(case_number or "") or None,
        summary=str(item.get("texto") or "") or None,
        status=str(item.get("status") or "") or None,
        updated_at=str(item.get("data_disponibilizacao") or item.get("datadisponibilizacao") or "")
        or None,
        source_trace=result_trace,
        raw={
            **item,
            "communication_id": communication_id,
            "communication_type": communication_type,
            "case_class": item.get("nomeClasse"),
            "origin_county": item.get("nomeOrgao"),
            "document_url": source_url,
            "publication_date": item.get("data_disponibilizacao"),
        },
    )


def _digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())
