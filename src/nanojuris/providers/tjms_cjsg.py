"""TJMS CJSG public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
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
from nanojuris.providers.tjsp_cjsg import (
    _response_bytes,
    cjsg_decision_bundle_to_document,
    decode_cjsg_response_text,
    diagnose_cjsg_access,
    extract_cjsg_document_text,
    extract_cjsg_document_text_bytes,
    fetch_cjsg_page,
)
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus


class TjmsCjsgProvider(JurisprudenceProvider):
    """Provider for the public TJMS CJSG jurisprudence search."""

    name = "tjms_cjsg"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjms_cjsg_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=8_000_000,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http_metadata: dict[str, Any] = {}
        self._last_response_content = b""
        self._pending_access_diagnostic: str | None = None

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        return fetch_cjsg_page(
            self,
            query,
            payload_builder=_build_payload,
            base_url=self.config.tjms_cjsg_url,
            source=self.name,
            court="TJMS",
            id_prefix="tjms-cjsg",
            source_label="TJMS/CJSG",
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        cd_acordao, cd_foro = self._parse_precedent_id(precedent_id)
        endpoint = f"/getArquivo.do?cdAcordao={cd_acordao}&cdForo={cd_foro}"
        content = self._request_text("GET", endpoint)
        raw_content = self._last_response_content or content.encode("utf-8")
        content_type = str(self._last_http_metadata.get("content_type") or "text/html")
        is_pdf = raw_content.startswith(b"%PDF") or "application/pdf" in content_type.lower()
        if is_pdf:
            document_text, extraction_metadata = extract_cjsg_document_text_bytes(raw_content)
        else:
            document_text, extraction_metadata = extract_cjsg_document_text(content)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/getArquivo.do",
            query={"cdAcordao": cd_acordao, "cdForo": cd_foro},
            source_url=urljoin(self.config.tjms_cjsg_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=["O retorno pode ser HTML, PDF ou tela de controle da propria fonte."],
            **self._last_http_metadata,
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document_text,
                    "content_type": "application/pdf" if is_pdf else "text/plain",
                    "source_content_type": content_type,
                }
            ],
            source_trace=trace,
            raw={
                "cd_acordao": cd_acordao,
                "cd_foro": cd_foro,
                "raw_content_sha256": hashlib.sha256(raw_content).hexdigest(),
                "raw_content_bytes": len(raw_content),
                "raw_content_type": content_type,
                **extraction_metadata,
            },
            raw_bytes=raw_content,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        return cjsg_decision_bundle_to_document(
            bundle,
            document_id=document_id,
            source=self.name,
            title=f"TJMS/CJSG inteiro teor {document_id}",
            parser="tjms_cjsg.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMS Consulta de Jurisprudencia/CJSG",
            source_url=self.config.tjms_cjsg_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "decision_type"],
            document_types=["acordao", "homologation", "decision"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "subject",
                "rapporteur",
                "origin_county",
                "judging_body",
                "publication_date",
                "summary",
                "document_url",
                "cd_acordao",
                "cd_foro",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "POST /resultadoCompleta.do",
                "GET /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>",
                "GET /getArquivo.do?cdAcordao=<id>&cdForo=<foro>",
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
            completeness_contract="reported_window_or_source_page_limit",
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "number",
                "exact_phrase",
                "case_class",
                "judging_body",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "types",
                "order_by",
            ],
            filter_semantics={
                "text": "native",
                "number": "translated",
                "exact_phrase": "translated",
                "case_class": "translated",
                "judging_body": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "types": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "decision_type": "translated",
                "lawyer_name": "unsupported",
                "legal_area": "unsupported",
                "oab": "unsupported",
                "party_document": "unsupported",
                "party_name": "unsupported",
                "police_document": "unsupported",
                "precatory_number": "unsupported",
                "cda": "unsupported",
                "rapporteur": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "fetch_details": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
            },
            limitations=[
                "A fonte compartilha padrao CJSG/e-SAJ e pode mudar sem aviso.",
                "Provider nao tenta contornar captcha, login ou controles de acesso.",
            ],
            responsible_use=[
                "Usar coletas paginadas com rate limit.",
                "Preservar cdAcordao/cdForo e SourceTrace para auditoria.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        url = urljoin(self.config.tjms_cjsg_url.rstrip("/") + "/", path.lstrip("/"))
        skip_access_diagnostic = bool(kwargs.pop("skip_access_diagnostic", False))
        request_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        request_headers.update(kwargs.pop("headers", {}) or {})
        request = TransportRequest(
            source=self.name,
            operation=f"cjsg_{method.lower()}",
            method=method,
            url=url,
            headers=request_headers,
            data=kwargs.pop("data", None),
            params=kwargs.pop("params", {}),
            json_body=kwargs.pop("json", None),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except (AssertionError, IndexError) as exc:
            if self._pending_access_diagnostic:
                raise AccessControlRequiredError(
                    "TJMS/CJSG requires captcha or another access-control step "
                    f"({self._pending_access_diagnostic})"
                ) from exc
            raise
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJMS/CJSG request failed: {exc}") from exc
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJMS/CJSG request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJMS/CJSG transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJMS/CJSG transport returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJMS/CJSG returned HTTP 429")
        if status_code >= 500:
            raise SourceUnavailableError(f"TJMS/CJSG returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJMS/CJSG rejected request with HTTP {status_code}")
        text = decode_cjsg_response_text(response)
        content = _response_bytes(response)
        self._last_response_content = content
        headers = getattr(response, "headers", {}) or {}
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(getattr(response, "url", url) or url),
            "content_type": headers.get("Content-Type") or headers.get("content-type"),
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "response_bytes": len(content),
            "retrieval_status": "ok" if 200 <= status_code < 300 else "http_error",
        }
        diagnostic = diagnose_cjsg_access(text)
        if skip_access_diagnostic:
            self._pending_access_diagnostic = (
                diagnostic.summary() if diagnostic.access_control_required else None
            )
        else:
            self._pending_access_diagnostic = None
        if diagnostic.access_control_required and not skip_access_diagnostic:
            raise AccessControlRequiredError(
                "TJMS/CJSG requires captcha or another access-control step "
                f"({diagnostic.summary()})"
            )
        return text

    @staticmethod
    def _parse_precedent_id(precedent_id: str) -> tuple[str, str]:
        match = re.fullmatch(r"tjms-cjsg-(?P<cd>\d+)(?:-(?P<foro>\d+))?", precedent_id)
        if not match:
            raise ParserContractChangedError(
                "TJMS/CJSG precedent id must look like tjms-cjsg-<cdAcordao>-<cdForo>"
            )
        return match.group("cd"), match.group("foro") or "0"


def _build_payload(query: JurisprudenceQuery) -> dict[str, str | list[str]]:
    # e-SAJ keeps hidden tree/counter fields in its form state.  Sending the
    # complete public form (as Juscraper does) avoids a HTTP-200 search/anti-bot
    # response that would otherwise be mistaken for an empty result page.
    return {
        "conversationId": "",
        "paginaConsulta": str(query.page),
        "dados.buscaInteiroTeor": query.text,
        "dados.buscaEmenta": query.exact_phrase,
        "dados.nuProcOrigem": query.number,
        "dados.pesquisarComSinonimos": "S",
        "dados.nuRegistro": "",
        "agenteSelectedEntitiesList": "",
        "contadoragente": "0",
        "contadorMaioragente": "0",
        "codigoCr": "",
        "codigoTr": "",
        "nmAgente": "",
        "juizProlatorSelectedEntitiesList": "",
        "contadorjuizProlator": "0",
        "contadorMaiorjuizProlator": "0",
        "codigoJuizCr": "",
        "codigoJuizTr": "",
        "nmJuiz": "",
        "classesTreeSelection.values": query.case_class,
        "classesTreeSelection.text": "",
        "assuntosTreeSelection.values": "",
        "assuntosTreeSelection.text": "",
        "comarcaSelectedEntitiesList": "",
        "contadorcomarca": "1",
        "contadorMaiorcomarca": "1",
        "cdComarca": "",
        "nmComarca": "",
        "secoesTreeSelection.values": query.judging_body,
        "secoesTreeSelection.text": "",
        "dados.dtJulgamentoInicio": query.updated_from,
        "dados.dtJulgamentoFim": query.updated_to,
        "dados.dtRegistroInicio": "",
        "dados.dtRegistroFim": "",
        "dados.dtPublicacaoInicio": query.published_from,
        "dados.dtPublicacaoFim": query.published_to,
        "dados.origensSelecionadas": "T",
        "tipoDecisaoSelecionados": [_map_decision_type(item) for item in (query.types or ["A"])],
        "dados.ordenarPor": _map_order_by(query.order_by),
        "pbSubmit": "Pesquisar",
    }


def _map_decision_type(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "a": "A",
        "acordao": "A",
        "acórdão": "A",
        "h": "H",
        "homologacao": "H",
        "homologação": "H",
        "d": "D",
        "decisao": "D",
        "decisão": "D",
    }
    return mapping.get(normalized, value.upper())


def _map_order_by(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "text": "dtPublicacao",
        "relevance": "dtPublicacao",
        "dtpublicacao": "dtPublicacao",
        "publication": "dtPublicacao",
        "date": "dtPublicacao",
    }
    return mapping.get(normalized, value or "dtPublicacao")
