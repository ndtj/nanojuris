"""TJDFT public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
import unicodedata
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    ExtractionTrace,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider

TJDF_JURIS_ENDPOINT = "/IndexadorAcordaos-web/sistj"


class TjdfJurisProvider(JurisprudenceProvider):
    """Provider for TJDFT SISTJ public jurisprudence search."""

    name = "tjdf_juris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        initial_params = _build_initial_params(query)
        initial_html = self._request_text("GET", TJDF_JURIS_ENDPOINT, params=initial_params)
        total = parse_tjdf_total(initial_html)

        results_params = _build_results_params(query, total=total)
        results_html = self._request_text("GET", TJDF_JURIS_ENDPOINT, params=results_params)
        document_ids = parse_tjdf_result_ids(results_html)[: query.page_size]
        trace = SourceTrace(
            provider=self.name,
            endpoint=TJDF_JURIS_ENDPOINT,
            query=results_params,
            source_url=urljoin(self.config.tjdf_juris_url, TJDF_JURIS_ENDPOINT.lstrip("/")),
            limitations=[
                "Fonte HTML publica do TJDFT/SISTJ sujeita a mudancas de layout.",
                "Busca validada por sessao HTTP limpa, sem captcha ou login no fluxo testado.",
                "Detalhes sao coletados por numeroDoDocumento exposto na pagina de resultados.",
            ],
        )
        results = [
            parse_tjdf_detail(
                self._request_text("GET", TJDF_JURIS_ENDPOINT, params=_build_detail_params(item)),
                document_id=item,
                trace=trace,
            )
            for item in document_ids
        ]
        start = ((query.page - 1) * query.page_size) + 1 if results else 0
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            source_trace=trace,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _normalize_tjdf_document_id(precedent_id)
        html = self._request_text(
            "GET", TJDF_JURIS_ENDPOINT, params=_build_detail_params(document_id)
        )
        _extract_detail_fields_or_raise(html, document_id)
        trace = SourceTrace(
            provider=self.name,
            endpoint=TJDF_JURIS_ENDPOINT,
            query=_build_detail_params(document_id),
            source_url=urljoin(self.config.tjdf_juris_url, TJDF_JURIS_ENDPOINT.lstrip("/")),
            limitations=["Detalhe publico de acordao TJDFT/SISTJ."],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": html, "content_type": "text/html"}],
            source_trace=trace,
            raw={"numeroDoDocumento": document_id},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        normalized_document_id = _normalize_tjdf_document_id(document_id)
        canonical_document_id = f"tjdf-acordao-{normalized_document_id}"
        html = self._request_text(
            "GET", TJDF_JURIS_ENDPOINT, params=_build_detail_params(normalized_document_id)
        )
        _extract_detail_fields_or_raise(html, normalized_document_id)
        trace = SourceTrace(
            provider=self.name,
            endpoint=TJDF_JURIS_ENDPOINT,
            query=_build_detail_params(normalized_document_id),
            source_url=urljoin(self.config.tjdf_juris_url, TJDF_JURIS_ENDPOINT.lstrip("/")),
            limitations=["Documento HTML publico do TJDFT/SISTJ."],
        )
        soup = BeautifulSoup(html, "html.parser")
        text = _normalize_spaces(soup.get_text(" ", strip=True))
        content_bytes = html.encode("utf-8")
        return CanonicalDocument(
            id=canonical_document_id,
            source=self.name,
            document_type="acordao",
            content_type="text/html",
            title=f"TJDFT acordao {document_id}",
            text=text,
            url=trace.source_url,
            sha256=hashlib.sha256(content_bytes).hexdigest(),
            byte_size=len(content_bytes),
            retrieved_at=trace.retrieved_at,
            access_status=AccessStatus.PUBLIC,
            source_trace=trace,
            extraction_trace=ExtractionTrace(
                parser="tjdf_juris.get_document",
                parser_version="1",
                content_sha256=hashlib.sha256(content_bytes).hexdigest(),
                content_bytes=len(content_bytes),
                metadata={"numeroDoDocumento": normalized_document_id},
            ),
            raw_metadata={"numeroDoDocumento": normalized_document_id},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJDFT Jurisprudencia/SISTJ",
            source_url=self.config.tjdf_juris_url,
            category="court_jurisprudence",
            search_modes=["text", "summary", "date_range", "page", "document_id"],
            document_types=["acordao", "turma_recursal", "tema", "informativo"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "registry_number",
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
                "decision_outcome",
                "document_url",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /IndexadorAcordaos-web/sistj?nomeDaPagina=buscaLivre",
                "GET /IndexadorAcordaos-web/sistj?nomeDaPagina=buscaLivre2",
                "GET /IndexadorAcordaos-web/sistj?comando=abrirDadosDoAcordao",
            ],
            supports_full_text=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "exact_phrase"],
            limitations=[
                "Contrato HTML legado do SISTJ/TJDFT pode mudar sem aviso.",
                "Inteiro teor PJe pode depender de link/documento externo.",
                "Provider nao interpreta merito juridico nem substitui fonte oficial.",
            ],
            responsible_use=[
                "Usar com rate limit em coletas paginadas.",
                "Preservar SourceTrace e numeroDoDocumento para auditoria.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        self._respect_rate_limit()
        url = urljoin(self.config.tjdf_juris_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"TJDFT/SISTJ request failed: {exc}") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJDFT/SISTJ returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJDFT/SISTJ returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJDFT/SISTJ rejected request with HTTP {response.status_code}"
            )
        response.encoding = response.encoding or "ISO-8859-1"
        return response.text

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_tjdf_total(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    values = [
        _normalize_spaces(node.get_text(" ", strip=True))
        for node in soup.select(".conteudoComRotulo")
    ]
    for value in reversed(values):
        if value.isdigit():
            return int(value)
    match = re.search(r"Resultado.*?(\d+)", _normalize_spaces(soup.get_text(" ", strip=True)))
    return int(match.group(1)) if match else 0


def parse_tjdf_result_ids(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    ids: list[str] = []
    for node in soup.select("#id_link_abrir_dados_acordao, [id*=id_link_abrir_dados_acordao]"):
        value = _normalize_spaces(node.get_text(" ", strip=True)) or str(node.get("value") or "")
        if value and value.isdigit() and value not in ids:
            ids.append(value)
    return ids


def parse_tjdf_detail(html: str, *, document_id: str, trace: SourceTrace) -> JurisprudenceResult:
    fields = _extract_detail_fields_or_raise(html, document_id)
    case_text = fields.get("classe_do_processo", "")
    registry_number = fields.get("registro_do_acordao_numero") or document_id
    judgment_date = fields.get("data_de_julgamento")
    publication_text = fields.get("data_da_intimacao_ou_da_publicacao", "")
    publication_date = _extract_date(publication_text)
    summary = fields.get("ementa")
    decision_outcome = fields.get("decisao")
    document_url = trace.source_url
    case_number = _extract_case_number(case_text)
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query={"numeroDoDocumento": document_id},
        source_url=document_url,
        limitations=trace.limitations,
    )
    return JurisprudenceResult(
        id=f"tjdf-acordao-{registry_number}",
        source="tjdf_juris",
        court="TJDFT",
        type="acordao",
        number=case_number or registry_number,
        summary=summary,
        status=decision_outcome,
        rapporteur=fields.get("relatora"),
        updated_at=publication_date or judgment_date,
        source_trace=result_trace,
        raw={
            "registry_number": registry_number,
            "case_number": case_number,
            "case_class": _extract_case_class(case_text),
            "judging_body": fields.get("orgao_julgador"),
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "publication_text": publication_text,
            "decision_outcome": decision_outcome,
            "document_url": document_url,
            "fields": fields,
        },
    )


def _build_initial_params(query: JurisprudenceQuery) -> dict[str, str]:
    search_text = query.text or query.exact_phrase
    return {
        "argumentoDePesquisa": search_text,
        "visaoId": "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.VisaoBuscaAcordao",
        "nomeDaPagina": "buscaLivre",
        "comando": "pesquisar",
        "internet": "1",
        "camposSelecionados": "ESPELHO",
        "COMMAND": "ok",
        "quantidadeDeRegistros": str(query.page_size),
        "tokenDePaginacao": str(query.page),
    }


def _build_results_params(query: JurisprudenceQuery, *, total: int) -> dict[str, str]:
    search_text = query.text or query.exact_phrase
    return {
        "visaoId": "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.VisaoBuscaAcordao",
        "nomeDaPagina": "buscaLivre2",
        "buscaPorQuery": "1",
        "baseSelecionada": "BASE_ACORDAO_TODAS",
        "ramoJuridico": "",
        "baseDados": "[BASE_ACORDAOS, TURMAS_RECURSAIS, BASE_ACORDAO_PJE, BASE_HISTORICA]",
        "argumentoDePesquisa": search_text,
        "desembargador": "",
        "indexacao": "",
        "tipoDeNumero": "",
        "tipoDeRelator": "",
        "camposSelecionados": "[ESPELHO]",
        "numero": "",
        "tipoDeData": "",
        "dataFim": query.updated_to,
        "dataInicio": query.updated_from,
        "ementa": query.exact_phrase,
        "orgaoJulgador": "",
        "legislacao": "",
        "numeroDaPaginaAtual": str(query.page),
        "quantidadeDeRegistros": str(query.page_size),
        "totalHits": str(total),
    }


def _build_detail_params(document_id: str) -> dict[str, str]:
    view_id = "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.VisaoBuscaAcordao"
    controller_id = (
        "tjdf.sistj.acordaoeletronico.buscaindexada.apresentacao.ControladorBuscaAcordao"
    )
    return {
        "visaoId": view_id,
        "controladorId": controller_id,
        "visaoAnterior": view_id,
        "nomeDaPagina": "resultado",
        "comando": "abrirDadosDoAcordao",
        "enderecoDoServlet": "sistj",
        "historicoDePaginas": "buscaLivre",
        "quantidadeDeRegistros": "20",
        "baseSelecionada": "BASE_ACORDAO_TODAS",
        "numeroDaUltimaPagina": "1",
        "buscaIndexada": "1",
        "mostrarPaginaSelecaoTipoResultado": "false",
        "totalHits": "1",
        "internet": "1",
        "numeroDoDocumento": document_id,
    }


def _normalize_tjdf_document_id(document_id: str) -> str:
    return re.sub(r"^tjdf-acordao-", "", document_id.strip(), flags=re.I)


def _extract_labeled_fields(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}
    for label_node in soup.select(".rotulo"):
        label = _normalize_key(label_node.get_text(" ", strip=True))
        parent = label_node.find_parent("div")
        value_node = parent.select_one(".conteudoComRotulo") if parent else None
        value = _normalize_spaces(value_node.get_text(" ", strip=True)) if value_node else ""
        if label and value:
            fields[label] = value
    return fields


def _extract_detail_fields_or_raise(html: str, document_id: str) -> dict[str, str]:
    fields = _extract_labeled_fields(html)
    if not any(
        fields.get(key) for key in ("ementa", "classe_do_processo", "registro_do_acordao_numero")
    ):
        raise ParserContractChangedError(
            f"TJDFT/SISTJ detail for document {document_id!r} returned no acórdão fields"
        )
    return fields


def _extract_case_number(value: str) -> str | None:
    masked = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", value)
    if masked:
        return masked.group(0)
    unmasked = re.search(r"\b\d{20}\b", value)
    return unmasked.group(0) if unmasked else None


def _extract_case_class(value: str) -> str | None:
    parts = [part.strip(" -()") for part in value.split(" - ") if part.strip(" -()")]
    if len(parts) >= 2:
        return parts[-1]
    return None


def _extract_date(value: str) -> str | None:
    match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", value)
    return match.group(0) if match else None


def _normalize_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("(a)", "a")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
