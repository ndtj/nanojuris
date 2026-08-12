"""TJMS CJSG public jurisprudence provider."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urljoin

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
    cjsg_decision_bundle_to_document,
    decode_cjsg_response_text,
    diagnose_cjsg_access,
    parse_cjsg_results,
)


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
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        endpoint = "/resultadoCompleta.do"
        payload = _build_payload(query)
        html = self._request_text("POST", endpoint, data=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=payload,
            source_url=urljoin(self.config.tjms_cjsg_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=[
                "Fonte HTML publica do TJMS/CJSG sujeita a mudancas de layout.",
                "Fluxo validado por sessao HTTP limpa a partir de inteligencia de projeto aberto.",
                "Inteiro teor depende de cdAcordao/cdForo publico retornado pela fonte.",
            ],
        )
        return parse_cjsg_results(
            html,
            query=query,
            trace=trace,
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
        trace = SourceTrace(
            provider=self.name,
            endpoint="/getArquivo.do",
            query={"cdAcordao": cd_acordao, "cdForo": cd_foro},
            source_url=urljoin(self.config.tjms_cjsg_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=["O retorno pode ser HTML, PDF ou tela de controle da propria fonte."],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": content, "content_type": "text/html"}],
            source_trace=trace,
            raw={"cd_acordao": cd_acordao, "cd_foro": cd_foro},
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
            supported_filters=["text", "number"],
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
        self._respect_rate_limit()
        url = urljoin(self.config.tjms_cjsg_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
            raise SourceUnavailableError(f"TJMS/CJSG request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJMS/CJSG returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJMS/CJSG returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJMS/CJSG rejected request with HTTP {response.status_code}"
            )
        text = decode_cjsg_response_text(response)
        diagnostic = diagnose_cjsg_access(text)
        if diagnostic.access_control_required:
            raise AccessControlRequiredError(
                "TJMS/CJSG requires captcha or another access-control step "
                f"({diagnostic.summary()})"
            )
        return text

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()

    @staticmethod
    def _parse_precedent_id(precedent_id: str) -> tuple[str, str]:
        match = re.fullmatch(r"tjms-cjsg-(?P<cd>\d+)(?:-(?P<foro>\d+))?", precedent_id)
        if not match:
            raise ParserContractChangedError(
                "TJMS/CJSG precedent id must look like tjms-cjsg-<cdAcordao>-<cdForo>"
            )
        return match.group("cd"), match.group("foro") or "0"


def _build_payload(query: JurisprudenceQuery) -> dict[str, str | list[str]]:
    return {
        "conversationId": "",
        "paginaConsulta": str(query.page),
        "dados.buscaInteiroTeor": query.text,
        "dados.buscaEmenta": query.exact_phrase,
        "dados.nuProcOrigem": query.number,
        "dados.pesquisarComSinonimos": "S",
        "dados.dtJulgamentoInicio": query.updated_from,
        "dados.dtJulgamentoFim": query.updated_to,
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
