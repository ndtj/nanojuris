"""Diagnostic binding for the official TJMSP jurisprudence portal.

The portal is a genuine jurisprudence search surface, but bounded probes from
this environment receive an HTTP 403 before the public form is delivered.
The adapter records that state explicitly and remains opt-in; it never
confuses the access control response with an empty search.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    DecisionBundle,
    JurisprudenceQuery,
    ProviderCapabilities,
    SearchPage,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus


class TjmspJurisprudenciaProvider(JurisprudenceProvider):
    """TJMSP public jurisprudence portal, diagnostic and opt-in only."""

    name = "tjmsp_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjmsp_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=2_000_000,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        response = self._request()
        text = response.text.casefold()
        if not text.strip():
            raise ParserContractChangedError("TJMSP returned an empty portal response")
        raise ParserContractChangedError(
            "TJMSP portal shell was reached without a replayable result contract"
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        raise SourceUnavailableError(
            "TJMSP detail route is not reproducible while the public portal is blocked"
        )

    def get_parameters(self) -> dict[str, Any]:
        return {
            "source_url": self.config.tjmsp_jurisprudencia_url,
            "official_entry_url": (
                "https://www.tjmsp.jus.br/jurisprudencia-do-tjmsp-pesquisa-avancada/"
            ),
            "legacy_iframe_url": "https://ww2.tjmsp.jus.br/Jurisprudencia",
            "api_base_url": self.config.tjmsp_jurisprudencia_api_url,
            "observed_api_endpoint": "/tema/retornaRegistrosAtivos",
            "status": "access_control_required",
            "result_contract": "not_observed",
            "official_scope": "TJMSP appellate jurisprudence",
        }

    def get_capabilities(self) -> ProviderCapabilities:
        filters = [
            "text",
            "number",
            "case_class",
            "judging_body",
            "rapporteur",
            "published_from",
            "published_to",
            "judgment_date_from",
            "judgment_date_to",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMSP Jurisprudência (diagnóstico opt-in)",
            source_url=self.config.tjmsp_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=["text", "case_number", "filters"],
            document_types=["acordao", "decisao"],
            content_formats=["html", "pdf"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="authority=TJMSP;branch=military;degree=second",
            extracted_fields=[
                "authority",
                "degree",
                "instance",
                "case_number",
                "case_class",
                "decision_type",
                "judging_body",
                "rapporteur",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /",
                "GET /v1/tema/retornaRegistrosAtivos",
                "GET https://ww2.tjmsp.jus.br/Jurisprudencia",
            ],
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="unknown_until_contract",
            completeness_contract="pending_public_portal_contract",
            full_text_access="unknown",
            supported_filters=[],
            unsupported_filters=filters,
            filter_semantics={name: "unsupported" for name in filters},
            limitations=[
                "A entrada oficial respondeu HTTP 403 na sonda bounded.",
                "Nenhuma sessão, cookie, token ou mecanismo de bypass é utilizado.",
                "O provider permanece fora da federação padrão.",
            ],
            responsible_use=[
                "Solicitar allowlist, API ou exportação oficial ao TJMSP.",
                "Não repetir consultas contra a proteção de acesso.",
            ],
        )

    def _request(self) -> Any:
        request = TransportRequest(
            source=self.name,
            operation="availability_probe",
            method="GET",
            url=self.config.tjmsp_jurisprudencia_url,
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJMSP jurisprudence request failed") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJMSP transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJMSP transport returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJMSP returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJMSP returned HTTP {status_code}")
        if status_code < 200 or status_code >= 300:
            raise SourceUnavailableError(f"TJMSP returned HTTP {status_code}")
        return response


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJMSP exige termo, numero ou frase exata")


__all__ = ["TjmspJurisprudenciaProvider"]
