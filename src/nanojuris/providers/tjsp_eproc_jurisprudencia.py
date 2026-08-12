"""TJSP eproc public jurisprudence provider."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    RateLimitDetectedError,
    SourceUnavailableError,
    UnsupportedQueryError,
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

PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


class TjspEprocJurisprudenciaProvider(JurisprudenceProvider):
    """Provider for the public TJSP eproc jurisprudence search."""

    name = "tjsp_eproc_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if query.page != 1:
            raise UnsupportedQueryError(
                "TJSP/eproc ainda nao possui paginacao remota comprovada; use page=1."
            )
        endpoint = "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados"
        payload = _build_payload(query)
        html, source_url = self._request_text("POST", endpoint, data=payload)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=payload,
            source_url=source_url,
            limitations=[
                "Jurisprudencia publica do eproc/TJSP validada com sessao HTTP limpa.",
                "Resultados podem conter sentencas, acordaos e decisoes monocraticas.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )
        results = parse_eproc_jurisprudencia_results(html, trace=trace, source_url=source_url)
        limited = results[: query.page_size]
        start = ((query.page - 1) * query.page_size) + 1 if limited else 0
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start,
            end=start + len(limited) - 1 if limited else 0,
            page=query.page,
            page_size=query.page_size,
            results=limited,
            source_trace=trace,
            pagination_mode="unknown",
            is_complete=False,
            completeness_reason=(
                "A rota observada retorna a primeira pagina; paginação remota ainda "
                "não foi comprovada."
            ),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        document_id = _extract_document_id(precedent_id)
        endpoint = (
            "/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor"
        )
        params = {"id_jurisprudencia": document_id}
        content, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=["Inteiro teor retornado pela rota publica de jurisprudencia eproc/TJSP."],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": content, "content_type": "text/html"}],
            source_trace=trace,
            raw={"id_jurisprudencia": document_id},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJSP eproc Jurisprudencia",
            source_url=self.config.tjsp_eproc_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range"],
            document_types=["sentenca", "acordao", "decisao_monocratica"],
            content_formats=["html"],
            canonical_records=["CanonicalDecision"],
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
            supports_full_text=False,
            supports_cli=True,
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number"],
            limitations=[
                "Rota publica descoberta e validada por requests limpo em 2026-08-02.",
                "O filtro source_origin aceita colegio_recursal, primeiro_grau e segundo_grau.",
                "Cards de resultado trazem texto de decisao; inteiro teor separado pode "
                "redirecionar para controle de acesso.",
                "A fonte pode alterar hashes, layouts e listas de filtros sem aviso.",
                "O provider detecta controles de acesso e nao implementa bypass.",
            ],
            responsible_use=[
                "Usar consultas pequenas e rate limit em coletas exploratorias.",
                "Preservar id_jurisprudencia, URLs e SourceTrace para auditoria.",
                "Nao reutilizar cookies ou sessao de navegador para contornar restricoes.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.config.tjsp_eproc_url.rstrip("/") + "/", path.lstrip("/"))
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
                allow_redirects=True,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJSP/eproc jurisprudence request failed: {exc}") from exc

        response.encoding = response.encoding or "utf-8"
        text = response.text
        if response.status_code == 429:
            raise RateLimitDetectedError("TJSP/eproc jurisprudence returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJSP/eproc jurisprudence requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(
                f"TJSP/eproc jurisprudence returned HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJSP/eproc jurisprudence rejected request with HTTP {response.status_code}"
            )
        if _looks_like_access_control(text):
            raise AccessControlRequiredError(
                "TJSP/eproc jurisprudence returned access-control HTML"
            )
        return text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


def parse_eproc_jurisprudencia_results(
    html: str,
    *,
    trace: SourceTrace,
    source_url: str,
    source: str = "tjsp_eproc_jurisprudencia",
    court: str = "TJSP",
    id_prefix: str = "tjsp-eproc-jurisprudencia",
    source_label: str = "TJSP/eproc jurisprudence",
) -> list[JurisprudenceResult]:
    """Parse public eproc jurisprudence result cards."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError(f"{source_label} returned access-control HTML")

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".resultadoItem")
    if not items and _looks_like_search_page(soup):
        return []
    if not items:
        raise ParserContractChangedError(f"{source_label} result cards not found")
    return [
        _parse_result_item(
            item,
            trace=trace,
            source_url=source_url,
            source=source,
            court=court,
            id_prefix=id_prefix,
            source_label=source_label,
        )
        for item in items
    ]


def _parse_result_item(
    item: Tag,
    *,
    trace: SourceTrace,
    source_url: str,
    source: str,
    court: str,
    id_prefix: str,
    source_label: str,
) -> JurisprudenceResult:
    labels = _extract_label_values(item)
    process_link = item.select_one("a.numero-processo")
    process_text = _clean_text(process_link.get_text(" ", strip=True) if process_link else "")
    process_number = _find_process_number(process_text or labels.get("processo", ""))
    if not process_number:
        raise ParserContractChangedError(f"{source_label} process number not found")

    document_type = _clean_text(_text(item.select_one(".resValueTipoJurisprudencia")))
    document_id = _extract_item_id(item)
    process_url = _absolute_url(process_link.get("href") if process_link else None, source_url)
    full_text_url = _data_link(item.select_one("a.inteiroTeor"), source_url)
    case_class = _extract_case_class(labels.get("processo", ""), process_number)
    publication_date = labels.get("data da publicacao")
    judgment_date = labels.get("data do julgamento")

    return JurisprudenceResult(
        id=f"{id_prefix}-{document_id or _digits(process_number)}",
        source=source,
        court=court,
        type=_normalize_decision_type(document_type),
        number=process_number,
        summary=labels.get("decisao") or labels.get("ementa"),
        rapporteur=labels.get("magistrado") or labels.get("relator"),
        updated_at=publication_date,
        source_trace=trace,
        raw={
            "id_jurisprudencia": document_id,
            "decision_type_label": document_type,
            "case_class": case_class,
            "judging_body": labels.get("orgao julgador"),
            "judgment_date": judgment_date,
            "publication_date": publication_date,
            "state": labels.get("uf"),
            "document_url": process_url,
            "full_text_url": full_text_url,
            "source_url": source_url,
        },
    )


def _build_payload(query: JurisprudenceQuery) -> dict[str, str | list[str]]:
    search_text = query.text or query.exact_phrase
    payload: dict[str, str | list[str]] = {
        "txtPesquisa": search_text,
        "rdoCampo": "E" if query.exact_phrase else "I",
        "hdnExibirPesquisaAvancada": "",
        "txtProcesso": _digits(query.number),
        "dtDecisaoInicio": query.updated_from,
        "dtDecisaoFim": query.updated_to,
        "hdnDecisaoInicio": query.updated_from,
        "hdnDecisaoFim": query.updated_to,
        "dtPublicacaoInicio": query.published_from,
        "dtPublicacaoFim": query.published_to,
        "hdnPublicacaoInicio": query.published_from,
        "hdnPublicacaoFim": query.published_to,
        "chkAgruparResultados": "on",
    }
    document_types = _map_document_types(query.types)
    if document_types:
        payload["selTipoDocumento[]"] = document_types
    source_origins = _map_source_origins(query.source_origins or [query.source_origin])
    if source_origins:
        payload["selOrigem[]"] = source_origins
    return payload


def _map_document_types(values: list[str]) -> list[str]:
    mapping = {
        "1": "1",
        "acordao": "1",
        "2": "2",
        "monocratica": "2",
        "decisao_monocratica": "2",
        "3": "3",
        "sumula": "3",
        "4": "4",
        "despacho": "4",
        "despacho_decisao_vice_presidencia": "4",
        "5": "5",
        "sentenca": "5",
    }
    return [mapped for value in values if (mapped := mapping.get(_normalize_label(value)))]


def _map_source_origins(values: list[str]) -> list[str]:
    mapping = {
        "3": "3",
        "colegio_recursal": "3",
        "colegio recursal": "3",
        "4": "4",
        "primeiro_grau": "4",
        "primeiro grau": "4",
        "1g": "4",
        "5": "5",
        "segundo_grau": "5",
        "segundo grau": "5",
        "2g": "5",
    }
    return [
        mapped for value in values if value and (mapped := mapping.get(_normalize_label(value)))
    ]


def _extract_label_values(item: Tag) -> dict[str, str]:
    values: dict[str, str] = {}
    for label in item.select(".resLabel"):
        key = _normalize_label(label.get_text(" ", strip=True))
        parent = label.parent if isinstance(label.parent, Tag) else None
        value_node = parent.select_one(".resValue") if parent else None
        value = _clean_text(_text(value_node))
        if key and value:
            values[key] = value
    return values


def _extract_item_id(item: Tag) -> str:
    checkbox = item.select_one("input.chkDocumento")
    value = checkbox.get("value") if checkbox else ""
    if value:
        return str(value)
    raw_id = str(item.get("id") or "")
    return raw_id.removeprefix("resultado")


def _extract_document_id(precedent_id: str) -> str:
    match = re.search(r"(\d{12,})$", precedent_id)
    if not match:
        raise ParserContractChangedError(
            "TJSP/eproc jurisprudence id must end with id_jurisprudencia digits"
        )
    return match.group(1)


def _extract_case_class(process_label_value: str, process_number: str) -> str | None:
    value = process_label_value.replace(process_number, "")
    value = re.sub(r"/[A-Z0-9]{2,6}\b", "", value)
    value = _clean_text(value)
    return value or None


def _normalize_decision_type(value: str) -> str:
    normalized = _normalize_label(value)
    mapping = {
        "acordao": "acordao",
        "decisao monocatica": "monocratica",
        "decisao monocratica": "monocratica",
        "sentenca": "sentenca",
        "sumula": "sumula",
    }
    return mapping.get(normalized, normalized or "decisao")


def _data_link(node: Tag | None, base_url: str) -> str | None:
    if node is None:
        return None
    return _absolute_url(node.get("data-link"), base_url)


def _absolute_url(value: object, base_url: str) -> str | None:
    if not value:
        return None
    return urljoin(base_url, str(value).replace("&amp;", "&"))


def _find_process_number(text: str) -> str | None:
    match = PROCESS_NUMBER_RE.search(text)
    return match.group(0) if match else None


def _looks_like_search_page(soup: BeautifulSoup) -> bool:
    return soup.select_one("#frmJurisprudenciaPesquisa") is not None


def _looks_like_access_control(html: str) -> bool:
    lowered = html.lower()
    return (
        any(
            signal in lowered
            for signal in [
                "g-recaptcha",
                "cf-turnstile",
                "cloudflare",
                "captcha",
                "login e senha",
                "entrar no sistema",
            ]
        )
        and "resultadoitem" not in lowered
    )


def _digits(value: object) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _normalize_label(value: str) -> str:
    normalized = _clean_text(value).casefold()
    replacements = {
        "á": "a",
        "à": "a",
        "â": "a",
        "ã": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for original, replacement in replacements.items():
        normalized = normalized.replace(original, replacement)
    return normalized
