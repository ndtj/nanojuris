"""Federal eproc public jurisprudence providers."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.config import NanoJurisConfig
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    JurisprudenceQuery,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.providers.tjsp_eproc_jurisprudencia import (
    _extract_document_id,
    _looks_like_access_control,
    _looks_like_source_unavailable,
    fetch_eproc_page,
)
from nanojuris.providers.trf4_eproc_jurisprudencia import Trf4EprocJurisprudenciaProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus


class FederalEprocJurisprudenciaProvider(JurisprudenceProvider):
    """Base provider for public federal eproc jurisprudence instances."""

    name = "federal_eproc_jurisprudencia"
    court = "FEDERAL"
    display_name = "Federal eproc Jurisprudencia"
    config_url_attr = ""
    id_prefix = "federal-eproc-jurisprudencia"
    source_label = "Federal/eproc jurisprudence"
    origins: tuple[str, ...] = ()
    document_types: tuple[str, ...] = (
        "acordao",
        "decisao_monocratica",
        "sumula",
        "despacho",
        "sentenca",
    )

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = session or requests.Session()
        host = urlparse(self.source_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_retries=2,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self._last_response_content = b""

    @property
    def source_url(self) -> str:
        return str(getattr(self.config, self.config_url_attr))

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return fetch_eproc_page(
            self,
            query,
            source=self.name,
            court=self.court,
            id_prefix=self.id_prefix,
            source_label=self.source_label,
            limitations=[
                f"Jurisprudencia publica {self.court}/eproc validada com sessao HTTP limpa.",
                "Resultados podem conter acordaos, decisoes monocraticas, sumulas, "
                "despachos e sentencas conforme a instancia.",
                "O provider preserva o conteudo publico retornado pela fonte e nao "
                "tenta contornar captcha, login ou controle de acesso.",
            ],
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document = self.get_document(precedent_id)
        document_id = self._extract_document_id(precedent_id)
        content = document.text or ""
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": content, "content_type": document.content_type or "text/plain"}],
            source_trace=document.source_trace,
            raw={"id_jurisprudencia": document_id, **document.raw_metadata},
            raw_bytes=document.raw_bytes,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        eproc_id = self._extract_document_id(document_id)
        endpoint = (
            "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor"
        )
        params = {"id_jurisprudencia": eproc_id}
        content, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=[
                f"Documento publico retornado pela rota de inteiro teor eproc/{self.court}."
            ],
            **self._last_http_metadata,
        )
        raw_content = self._last_response_content or content.encode("utf-8")
        return build_canonical_document(
            document_id=f"{self.id_prefix}-document-{eproc_id}",
            source=self.name,
            document_type="decisao",
            content=raw_content,
            content_type=self._last_http_metadata.get("content_type") or "text/html",
            title=f"{self.court} eproc inteiro teor",
            url=source_url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"id_jurisprudencia": eproc_id},
            parser=f"{self.name}.get_document",
        )

    def _extract_document_id(self, precedent_id: str) -> str:
        """Extract the source identifier from a canonical eproc result id.

        State eproc installations use the same public route but do not all
        allocate the long numeric identifiers used by TJSP.  Keeping the
        extraction hook on the provider lets each installation enforce its
        own identifier contract without weakening the TJSP parser.
        """

        return _extract_document_id(precedent_id)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name=self.display_name,
            source_url=self.source_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range"],
            document_types=list(self.document_types),
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "document_url",
                "full_text_url",
                "id_jurisprudencia",
                "source_origin",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                (
                    "POST /externo_controlador.php?"
                    "acao=jurisprudencia@jurisprudencia/listar_resultados"
                ),
                (
                    "GET /externo_controlador.php?"
                    "acao=jurisprudencia@jurisprudencia/download_inteiro_teor&"
                    "id_jurisprudencia=<id>"
                ),
            ],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            pagination_mode="page",
            completeness_contract="reported_form_total_and_page_window",
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
                "source_origin",
                "degree",
                "instance",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "rapporteur",
                "fetch_details",
                "case_class",
                "judging_body",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
                "lawyer_name",
                "legal_area",
                "oab",
                "party_document",
                "party_name",
                "police_document",
                "precatory_number",
                "cda",
                "source_origins",
            ],
            filter_semantics={
                "text": "native",
                "number": "native",
                "published_from": "native",
                "published_to": "native",
                "updated_from": "native",
                "updated_to": "native",
                "source_origin": "translated",
                # eproc names the dimension ``selOrigem[]``. The shared
                # adapter translates canonical values and validates cards
                # locally so first/second degree records cannot be mixed.
                "degree": "local_postfilter",
                "instance": "local_postfilter",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "types": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "exact_phrase": "unsupported",
                "rapporteur": "unsupported",
                "fetch_details": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "source_origins": "unsupported",
            },
            limitations=[
                "Rota publica validada por requests limpo em 2026-08-16.",
                "A paginação usa a URL ajax_paginar_resultado e os campos ocultos "
                "do formulario retornado pela propria fonte.",
                "Origens observadas: "
                f"{', '.join(self.origins) if self.origins else 'variavel por instancia'}.",
                "A fonte pode alterar layout, filtros e labels sem aviso.",
                "O provider detecta controles de acesso e nao implementa bypass.",
            ],
            responsible_use=[
                "Usar consultas pequenas e rate limit em coletas exploratorias.",
                "Preservar id_jurisprudencia, URLs e SourceTrace para auditoria.",
                "Nao reutilizar cookies ou sessao de navegador para contornar restricoes.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        url = urljoin(self.source_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self.transport.request(
                TransportRequest(
                    source=self.name,
                    operation="document_or_search",
                    method=method,
                    url=url,
                    params=dict(kwargs.get("params") or {}),
                    data=kwargs.get("data"),
                    json_body=kwargs.get("json"),
                    headers=headers,
                    idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
                )
            )
        except (requests.RequestException, SourceUnavailableError) as exc:
            raise SourceUnavailableError(f"{self.source_label} request failed: {exc}") from exc

        response_url = response.final_url or url
        content = response.body
        text = content.decode("iso-8859-1", errors="replace")
        headers = response.headers
        self._last_response_content = content
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": response_url,
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": response.content_sha256 or hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok"
            if response.status_code is not None and 200 <= response.status_code < 300
            else response.status.value,
        }
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"{self.source_label} transport failed: {response.status.value}"
            )
        status_code = response.status_code or 0
        if status_code == 429:
            raise RateLimitDetectedError(f"{self.source_label} returned HTTP 429")
        if status_code in {401, 403}:
            raise AccessControlRequiredError(f"{self.source_label} requires access validation")
        if status_code >= 500:
            raise SourceUnavailableError(f"{self.source_label} returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(
                f"{self.source_label} rejected request with HTTP {status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError(f"{self.source_label} returned access-control HTML")
        if _looks_like_source_unavailable(text):
            raise SourceUnavailableError(f"{self.source_label} source is temporarily unavailable")
        return text, response_url


class TnuEprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    name = "tnu_eproc_jurisprudencia"
    court = "TNU"
    display_name = "TNU eproc Jurisprudencia"
    config_url_attr = "tnu_eproc_jurisprudencia_url"
    id_prefix = "tnu-eproc-jurisprudencia"
    source_label = "TNU/eproc jurisprudence"
    origins = ("TNU",)
    document_types = ("acordao", "decisao_monocratica", "decisao_presidente")


class Trf2EprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    name = "trf2_eproc_jurisprudencia"
    court = "TRF2"
    display_name = "TRF2 eproc Jurisprudencia"
    config_url_attr = "trf2_eproc_jurisprudencia_url"
    id_prefix = "trf2-eproc-jurisprudencia"
    source_label = "TRF2/eproc jurisprudence"
    origins = ("TRF2", "TRU2", "Turmas Recursais")


class Trf6EprocJurisprudenciaProvider(FederalEprocJurisprudenciaProvider):
    name = "trf6_eproc_jurisprudencia"
    court = "TRF6"
    display_name = "TRF6 eproc Jurisprudencia"
    config_url_attr = "trf6_eproc_jurisprudencia_url"
    id_prefix = "trf6-eproc-jurisprudencia"
    source_label = "TRF6/eproc jurisprudence"
    origins = ("TRF6", "TRU6", "Turmas Recursais", "Varas Federais")


class FederalEprocJurisprudenciaFamilyProvider(JurisprudenceProvider):
    """Explicit-authority dispatcher for the public federal eproc family.

    The eproc installations share an HTML protocol but not a host or a
    tribunal scope.  A family binding therefore requires ``authority`` and
    delegates to the already tested, tribunal-specific implementation.  It
    deliberately does not expose an aggregate search or claim that all
    federal courts are covered.
    """

    name = "eproc_jurisprudencia_federal"
    _AUTHORITY_ALIASES = {
        "TNU": "TNU",
        "TRF2": "TRF2",
        "TRF02": "TRF2",
        "TRF4": "TRF4",
        "TRF04": "TRF4",
        "TRF6": "TRF6",
        "TRF06": "TRF6",
    }

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = session or requests.Session()
        self._providers: dict[str, JurisprudenceProvider] = {}

    @classmethod
    def _normalize_authority(cls, value: str | None) -> str:
        normalized = "".join(str(value or "").upper().split()).replace("-", "")
        authority = cls._AUTHORITY_ALIASES.get(normalized)
        if authority is None:
            supported = ", ".join(cls._AUTHORITY_ALIASES.values())
            raise QueryRejectedError(
                f"eproc federal exige authority explícita; suportadas: {supported}"
            )
        return authority

    def _provider_for(self, authority: str) -> JurisprudenceProvider:
        normalized = self._normalize_authority(authority)
        provider = self._providers.get(normalized)
        if provider is not None:
            return provider
        provider_cls: type[JurisprudenceProvider]
        if normalized == "TNU":
            provider_cls = TnuEprocJurisprudenciaProvider
        elif normalized == "TRF2":
            provider_cls = Trf2EprocJurisprudenciaProvider
        elif normalized == "TRF4":
            provider_cls = Trf4EprocJurisprudenciaProvider
        else:
            provider_cls = Trf6EprocJurisprudenciaProvider
        provider = provider_cls(self.config, session=self.session)
        self._providers[normalized] = provider
        return provider

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if not query.authority:
            raise QueryRejectedError("eproc federal exige authority explícita (por exemplo, TRF4)")
        provider = self._provider_for(query.authority)
        # Child adapters do not forward ``authority`` to the remote form; it
        # is consumed solely by this dispatcher to select the official host.
        return provider.search(query)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        provider = self._provider_for(self._authority_from_id(precedent_id))
        return provider.get_decisions(precedent_id)

    def get_document(self, document_id: str) -> CanonicalDocument:
        provider = self._provider_for(self._authority_from_id(document_id))
        return provider.get_document(document_id)

    @classmethod
    def _authority_from_id(cls, identifier: str) -> str:
        lowered = str(identifier or "").lower()
        for prefix, authority in (
            ("tnu-eproc-jurisprudencia-", "TNU"),
            ("trf2-eproc-jurisprudencia-", "TRF2"),
            ("trf4-eproc-jurisprudencia-", "TRF4"),
            ("trf6-eproc-jurisprudencia-", "TRF6"),
        ):
            if lowered.startswith(prefix):
                return authority
        raise QueryRejectedError("identificador eproc federal deve conter o prefixo da autoridade")

    def get_parameters(self) -> dict[str, Any]:
        return {
            "source_url": "https://www.cnj.jus.br/relatorio-por-tribunal/",
            "authorities": ["TNU", "TRF2", "TRF4", "TRF6"],
            "provider_bindings": {
                authority: self._provider_for(authority).name
                for authority in ("TNU", "TRF2", "TRF4", "TRF6")
            },
            "status": "opt_in_explicit_authority",
        }

    def get_capabilities(self) -> ProviderCapabilities:
        base = self._provider_for("TRF4").get_capabilities()
        semantics = dict(base.filter_semantics)
        semantics["authority"] = "required_scope"
        supported = list(base.supported_filters)
        if "authority" not in supported:
            supported.append("authority")
        return replace(
            base,
            source=self.name,
            display_name="eproc federal jurisprudência (família opt-in)",
            source_url="https://www.cnj.jus.br/relatorio-por-tribunal/",
            semantic_discriminator=("authority=TNU|TRF2|TRF4|TRF6;branch=federal;collection=EPROC"),
            supported_filters=supported,
            filter_semantics=semantics,
            supports_unified_search=False,
            opt_in_unified_search=True,
            limitations=[
                *base.limitations,
                "A autoridade deve ser informada; não há escopo federal agregado.",
                "Cada instalação mantém contrato, host e evidência próprios.",
            ],
        )


__all__ = [
    "FederalEprocJurisprudenciaFamilyProvider",
    "FederalEprocJurisprudenciaProvider",
    "TnuEprocJurisprudenciaProvider",
    "Trf2EprocJurisprudenciaProvider",
    "Trf6EprocJurisprudenciaProvider",
]
