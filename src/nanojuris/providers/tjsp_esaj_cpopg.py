"""TJSP e-SAJ first-instance public case lookup provider."""

from __future__ import annotations

import hashlib
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
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    ExtractionStatus,
    ExtractionTrace,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider

PROCESS_NUMBER_RE = re.compile(r"^(\d{7}-\d{2}\.\d{4})\.\d\.\d{2}\.(\d{4})$")
ANY_PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
LIST_RESULT_NUMBER_RE = re.compile(r"(?P<number>\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})")
ESAJ_SEARCH_MODES = {
    "party_name": "NMPARTE",
    "party_document": "DOCPARTE",
    "lawyer_name": "NMADVOGADO",
    "oab": "NUMOAB",
    "precatory_number": "PRECATORIA",
    "police_document": "DOCDELEG",
    "cda": "NUMCDA",
}


class TjspEsajCpopgProvider(JurisprudenceProvider):
    """Provider for public TJSP e-SAJ CPOPg first-instance case pages."""

    name = "tjsp_esaj_cpopg"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        if _query_has_process_number(query):
            return self._search_by_process_number(query)
        return self._search_list(query)

    def _search_by_process_number(self, query: JurisprudenceQuery) -> SearchPage:
        process_number = _normalize_process_number(query.number or query.text)
        document = self.get_document(process_number)
        result = JurisprudenceResult(
            id=document.id,
            source=self.name,
            court="TJSP",
            type="processo",
            number=process_number,
            summary=document.title,
            status=document.raw_metadata.get("status"),
            updated_at=document.raw_metadata.get("last_movement_date"),
            source_trace=document.source_trace,
            raw={
                **document.raw_metadata,
                "document_url": document.url,
                "record_kind": "case_lookup",
            },
        )
        return SearchPage(
            source=self.name,
            total=1,
            start=1,
            end=1,
            page=query.page,
            page_size=query.page_size,
            results=[result],
            source_trace=document.source_trace,
        )

    def _search_list(self, query: JurisprudenceQuery) -> SearchPage:
        mode, value = _select_list_search_mode(query)
        endpoint = "/cpopg/search.do"
        params = _build_list_search_params(mode, value, query.page)
        html, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=[
                "Consulta processual publica de primeiro grau no e-SAJ/TJSP.",
                "Buscas por lista podem acionar limitacao por consultas simultaneas.",
                "Detalhes completos exigem abrir cada processo publico listado.",
            ],
        )
        results = parse_esaj_cpopg_list(
            html,
            trace=trace,
            source_url=source_url,
            page=query.page,
            page_size=query.page_size,
            search_mode=mode,
            search_value=value,
        )
        if query.fetch_details:
            results = [self._with_detail_metadata(result) for result in results]
        start = ((query.page - 1) * query.page_size) + 1 if results else 0
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            source_trace=trace,
        )

    def _with_detail_metadata(self, result: JurisprudenceResult) -> JurisprudenceResult:
        if not result.number:
            return result
        try:
            document = self.get_document(str(result.number))
        except (
            AccessControlRequiredError,
            ParserContractChangedError,
            SourceUnavailableError,
        ) as exc:
            result.raw["detail_error"] = str(exc)
            return result
        result.summary = document.title
        result.status = document.raw_metadata.get("status") or result.status
        result.updated_at = document.raw_metadata.get("last_movement_date") or result.updated_at
        result.raw = {
            **result.raw,
            **document.raw_metadata,
            "document_url": document.url,
            "record_kind": "case_lookup_list_detail",
        }
        return result

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[],
            raw={"message": "tjsp_esaj_cpopg is a public case lookup provider"},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        process_number = _normalize_process_number(document_id)
        endpoint = "/cpopg/search.do"
        params = _build_search_params(process_number)
        html, source_url = self._request_text("GET", endpoint, params=params)
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint,
            query=params,
            source_url=source_url,
            limitations=[
                "Consulta processual publica de primeiro grau no e-SAJ/TJSP.",
                "Autos, anexos e partes sob segredo podem exigir login ou senha.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )
        return parse_esaj_cpopg_document(
            html,
            process_number=process_number,
            trace=trace,
            source_url=source_url,
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJSP e-SAJ Consulta Processual 1o Grau",
            source_url=self.config.tjsp_esaj_url,
            category="case_lookup",
            search_modes=[
                "case_number",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "precatory_number",
                "police_document",
                "cda",
            ],
            document_types=["processo_1g"],
            content_formats=["html"],
            canonical_records=["CanonicalDocument", "JurisprudenceResult"],
            extracted_fields=[
                "case_number",
                "status",
                "case_class",
                "subject",
                "origin_county",
                "court_unit",
                "judge",
                "distribution",
                "control_number",
                "area",
                "parties_text",
                "movements_text",
                "document_url",
                "search_mode",
                "result_role",
                "received_date",
                "parties",
                "movements",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.LOGIN_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=["GET /cpopg/search.do", "GET /cpopg/show.do"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            limitations=[
                "Busca por numero CNJ validada como detalhe direto.",
                "Busca por nome da parte e OAB validada como lista publica.",
                "Documento da parte, advogado, precatoria, documento de delegacia "
                "e CDA estao mapeados.",
                "Dados processuais sao objetivos; autos e documentos podem ser restritos.",
                "A fonte pode exibir captcha ou exigir validacao em algumas rotas.",
            ],
            responsible_use=[
                "Consultar apenas dados publicos e respeitar limites da fonte.",
                "Nao reutilizar cookies, sessoes ou tokens de navegador para bypass.",
                "Tratar controle de acesso como estado da fonte, nao como obstaculo a vencer.",
            ],
        )

    def _request_text(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.config.tjsp_esaj_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"TJSP/e-SAJ CPOPg request failed: {exc}") from exc

        response.encoding = response.encoding or "utf-8"
        text = response.text
        if response.status_code == 429:
            raise RateLimitDetectedError("TJSP/e-SAJ CPOPg returned HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError("TJSP/e-SAJ CPOPg requires access validation")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJSP/e-SAJ CPOPg returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJSP/e-SAJ CPOPg rejected request with HTTP {response.status_code}"
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


def parse_esaj_cpopg_document(
    html: str,
    *,
    process_number: str,
    trace: SourceTrace,
    source_url: str | None = None,
    source: str = "tjsp_esaj_cpopg",
    id_prefix: str = "tjsp-esaj-cpopg",
    parser_name: str = "tjsp_esaj_cpopg.parse_esaj_cpopg_document",
) -> CanonicalDocument:
    """Parse a public e-SAJ CPOPg case page into a canonical document."""

    if _looks_like_access_control(html, process_number):
        raise AccessControlRequiredError("TJSP/e-SAJ CPOPg returned access-control HTML")

    soup = BeautifulSoup(html, "html.parser")
    visible_text = _normalize_spaces(soup.get_text(" ", strip=True))
    detected_number = _find_process_number(visible_text)
    if detected_number != process_number:
        raise ParserContractChangedError("TJSP/e-SAJ CPOPg process number not found")

    metadata = _extract_case_metadata(soup, visible_text)
    metadata["case_number"] = process_number
    metadata["document_url"] = source_url or trace.source_url
    title = _build_title(metadata)
    content_bytes = html.encode("utf-8")

    return CanonicalDocument(
        id=f"{id_prefix}-{process_number}",
        source=source,
        document_type="processo_1g",
        content_type="text/html",
        title=title,
        text=visible_text,
        url=source_url or trace.source_url,
        sha256=hashlib.sha256(content_bytes).hexdigest(),
        byte_size=len(content_bytes),
        retrieved_at=trace.retrieved_at,
        access_status=AccessStatus.PUBLIC,
        source_trace=trace,
        extraction_trace=ExtractionTrace(
            parser=parser_name,
            parser_version="1",
            status=ExtractionStatus.COMPLETE,
            access_status=AccessStatus.PUBLIC,
            content_sha256=hashlib.sha256(content_bytes).hexdigest(),
            content_bytes=len(content_bytes),
            metadata={"case_number": process_number},
        ),
        raw_metadata=metadata,
    )


def parse_esaj_cpopg_list(
    html: str,
    *,
    trace: SourceTrace,
    source_url: str,
    page: int,
    page_size: int,
    search_mode: str,
    search_value: str,
) -> list[JurisprudenceResult]:
    """Parse an e-SAJ CPOPg result list into normalized process results."""

    if _looks_like_list_access_control(html):
        raise AccessControlRequiredError("TJSP/e-SAJ CPOPg returned access-control HTML")

    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a.linkProcesso, a[href*='show.do']")
    results: list[JurisprudenceResult] = []
    seen: set[str] = set()
    for link in links:
        item = _parse_list_item(link, source_url=source_url)
        case_number = item.get("case_number", "")
        if not case_number or case_number in seen:
            continue
        seen.add(case_number)
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint=trace.endpoint,
            query=trace.query,
            source_url=item.get("document_url") or source_url,
            limitations=trace.limitations,
        )
        results.append(
            JurisprudenceResult(
                id=f"tjsp-esaj-cpopg-{case_number}",
                source="tjsp_esaj_cpopg",
                court="TJSP",
                type="processo",
                number=case_number,
                summary=_build_list_summary(item),
                updated_at=item.get("received_date"),
                source_trace=result_trace,
                raw={
                    **item,
                    "search_mode": search_mode,
                    "search_value": search_value,
                    "record_kind": "case_lookup_list_item",
                },
            )
        )
    return results[:page_size]


def _parse_list_item(link: Any, *, source_url: str) -> dict[str, str]:
    container = (
        link.find_parent("div", class_="fundocinza1")
        or link.find_parent("tr")
        or link.find_parent("li")
        or link.find_parent("div")
        or link
    )
    text = _normalize_spaces(container.get_text(" ", strip=True))
    case_number = _find_process_number(text)
    link_text = _normalize_spaces(link.get_text(" ", strip=True))
    href = str(link.get("href") or "")
    document_url = urljoin(source_url, href)
    without_number = text.replace(link_text or case_number, "", 1).strip()
    role, party_name, remainder = _split_list_role_party(without_number)
    received_date = _extract_received_date(text)
    court_unit = _extract_after_received_court_unit(text)
    case_class, subject = _split_list_case_subject(remainder, received_date=received_date)
    return {
        "case_number": case_number,
        "result_role": role,
        "party_name": party_name,
        "case_class": case_class,
        "subject": subject,
        "received_date": received_date,
        "court_unit": court_unit,
        "document_url": document_url,
        "list_text": text,
    }


def _build_search_params(process_number: str) -> dict[str, str]:
    match = PROCESS_NUMBER_RE.match(process_number)
    if match is None:
        raise ParserContractChangedError("TJSP/e-SAJ CPOPg requires a valid CNJ case number")
    unified_prefix, forum_code = match.groups()
    return {
        "conversationId": "",
        "cbPesquisa": "NUMPROC",
        "numeroDigitoAnoUnificado": unified_prefix,
        "foroNumeroUnificado": forum_code,
        "dadosConsulta.valorConsultaNuUnificado": process_number,
        "dadosConsulta.valorConsulta": process_number,
        "dadosConsulta.tipoNuProcesso": "UNIFICADO",
    }


def _build_list_search_params(mode: str, value: str, page: int) -> dict[str, str]:
    return {
        "conversationId": "",
        "dadosConsulta.localPesquisa.cdLocal": "-1",
        "cbPesquisa": mode,
        "dadosConsulta.valorConsulta": value,
        "paginaConsulta": str(page),
    }


def _query_has_process_number(query: JurisprudenceQuery) -> bool:
    value = query.number or query.text
    return bool(ANY_PROCESS_NUMBER_RE.search(value.strip()))


def _select_list_search_mode(query: JurisprudenceQuery) -> tuple[str, str]:
    candidates = [
        ("party_name", query.party_name),
        ("party_document", query.party_document),
        ("lawyer_name", query.lawyer_name),
        ("oab", query.oab),
        ("precatory_number", query.precatory_number),
        ("police_document", query.police_document),
        ("cda", query.cda),
        ("party_name", query.text),
    ]
    for key, value in candidates:
        if value.strip():
            return ESAJ_SEARCH_MODES[key], value.strip()
    raise ParserContractChangedError(
        "TJSP/e-SAJ CPOPg requires a CNJ number or one mapped list-search parameter"
    )


def _normalize_process_number(value: str) -> str:
    number = value.strip()
    match = ANY_PROCESS_NUMBER_RE.search(number)
    if match is None:
        raise ParserContractChangedError("TJSP/e-SAJ CPOPg requires a CNJ case number")
    return match.group(0)


def _extract_case_metadata(soup: BeautifulSoup, text: str) -> dict[str, Any]:
    labels = [
        "Classe",
        "Assunto",
        "Foro",
        "Vara",
        "Juiz",
        "Distribuição",
        "Controle",
        "Área",
        "Partes do processo",
        "Movimentações",
    ]
    movements_text = _dom_text(soup, "#tabelaTodasMovimentacoes") or _between_labels(
        text,
        "Movimentações",
        labels,
    )
    parties_text = _join_dom_text(soup, ".nomeParteEAdvogado") or _between_labels(
        text,
        "Partes do processo",
        labels,
    )
    parties = _extract_parties(soup)
    movements = _extract_movements(soup, movements_text)
    return {
        "status": _dom_text(soup, "#labelSituacaoProcesso") or _extract_status(text),
        "case_class": _dom_text(soup, "#classeProcesso") or _between_labels(text, "Classe", labels),
        "subject": _dom_text(soup, "#assuntoProcesso") or _between_labels(text, "Assunto", labels),
        "origin_county": _dom_text(soup, "#foroProcesso") or _between_labels(text, "Foro", labels),
        "court_unit": _dom_text(soup, "#varaProcesso") or _between_labels(text, "Vara", labels),
        "judge": _dom_text(soup, "#juizProcesso") or _between_labels(text, "Juiz", labels),
        "distribution": _dom_text(soup, "#dataHoraDistribuicaoProcesso")
        or _between_labels(text, "Distribuição", labels),
        "control_number": _dom_text(soup, "#numeroControleProcesso")
        or _between_labels(text, "Controle", labels),
        "area": _dom_text(soup, "#areaProcesso") or _between_labels(text, "Área", labels),
        "parties_text": parties_text,
        "movements_text": movements_text,
        "parties": parties,
        "movements": movements,
        "last_movement_date": _extract_last_movement_date(movements_text or text),
    }


def _extract_parties(soup: BeautifulSoup) -> list[dict[str, str]]:
    parties: list[dict[str, str]] = []
    for element in soup.select(".nomeParteEAdvogado"):
        text = _normalize_spaces(element.get_text(" ", strip=True))
        if not text:
            continue
        role, name = _split_party_text(text)
        parties.append({"role": role, "name": name, "text": text})
    return parties


def _extract_movements(soup: BeautifulSoup, movements_text: str) -> list[dict[str, str]]:
    movements: list[dict[str, str]] = []
    movement_rows = soup.select(".containerMovimentacao")
    for row in movement_rows:
        date = _dom_text(row, ".dataMovimentacao")
        description = _dom_text(row, ".descricaoMovimentacao")
        if date or description:
            movements.append({"date": date, "description": description})
    if movements:
        return movements
    return _split_movements_text(movements_text)


def _split_party_text(text: str) -> tuple[str, str]:
    if ":" in text:
        role, name = text.split(":", 1)
        return role.strip(), name.strip()
    known_roles = [
        "Justiça Pública",
        "Justica Publica",
        "Autor",
        "Autora",
        "Réu",
        "Reu",
        "Executado",
        "Exectdo",
        "Reqte",
        "Reqdo",
    ]
    for role in known_roles:
        if text.lower().startswith(role.lower() + " "):
            return role, text[len(role) :].strip()
    return "", text


def _split_movements_text(text: str) -> list[dict[str, str]]:
    if not text:
        return []
    matches = list(re.finditer(r"\b\d{2}/\d{2}/\d{4}\b", text))
    movements: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        movements.append(
            {
                "date": match.group(0),
                "description": _normalize_spaces(text[start:end]),
            }
        )
    return movements


def _build_list_summary(item: dict[str, str]) -> str:
    parts = [
        item.get("case_number", ""),
        item.get("result_role", ""),
        item.get("party_name", ""),
        item.get("case_class", ""),
        item.get("subject", ""),
    ]
    return " - ".join(part for part in parts if part)


def _split_list_role_party(text: str) -> tuple[str, str, str]:
    roles = ["Exectdo", "Executado", "Réu", "Reu", "Autor", "Autora", "Reqte", "Reqdo"]
    for role in roles:
        marker = f"{role}:"
        if text.startswith(marker):
            remainder = text[len(marker) :].strip()
            next_match = re.search(
                r"\b(Ação|Acao|Execução|Execucao|Procedimento|Cumprimento|Carta|Processo)\b",
                remainder,
            )
            if next_match:
                party_name = remainder[: next_match.start()].strip()
                remaining_text = remainder[next_match.start() :].strip()
                return role, party_name, remaining_text
            return role, remainder, ""
    return "", "", text


def _extract_received_date(text: str) -> str:
    match = re.search(r"Recebido em:\s*(\d{2}/\d{2}/\d{4})", text, re.I)
    return match.group(1) if match else ""


def _extract_after_received_court_unit(text: str) -> str:
    match = re.search(r"Recebido em:\s*\d{2}/\d{2}/\d{4}\s*-\s*(.+)$", text, re.I)
    return _normalize_spaces(match.group(1)) if match else ""


def _split_list_case_subject(remainder: str, *, received_date: str) -> tuple[str, str]:
    text = remainder
    if received_date:
        text = text.split("Recebido em:", 1)[0]
    text = _normalize_spaces(text)
    known_subject_markers = [
        "Pena Privativa",
        "Homicídio",
        "Homicidio",
        "Pena ",
        "Crimes ",
        "DIREITO ",
        "Responsabilidade ",
    ]
    for marker in known_subject_markers:
        index = text.find(marker)
        if index > 0:
            return text[:index].strip(), text[index:].strip()
    return text, ""


def _between_labels(text: str, label: str, labels: list[str]) -> str:
    start = text.find(label)
    if start < 0:
        return ""
    start += len(label)
    end_candidates = [text.find(candidate, start) for candidate in labels if candidate != label]
    end_candidates = [candidate for candidate in end_candidates if candidate >= 0]
    end = min(end_candidates) if end_candidates else len(text)
    return _normalize_spaces(text[start:end]).strip(" :-")


def _extract_status(text: str) -> str:
    match = ANY_PROCESS_NUMBER_RE.search(text)
    if match is None:
        return ""
    remainder = text[match.end() :]
    next_label = remainder.find("Classe")
    if next_label < 0:
        return ""
    return _normalize_spaces(remainder[:next_label]).strip(" :-")


def _extract_last_movement_date(text: str) -> str:
    movements = _between_labels(text, "Movimentações", ["Movimentações"])
    match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", movements or text)
    return match.group(0) if match else ""


def _find_process_number(text: str) -> str:
    match = ANY_PROCESS_NUMBER_RE.search(text)
    return match.group(0) if match else ""


def _dom_text(soup: BeautifulSoup | Tag, selector: str) -> str:
    element = soup.select_one(selector)
    if element is None:
        return ""
    return _normalize_spaces(element.get_text(" ", strip=True))


def _join_dom_text(soup: BeautifulSoup, selector: str) -> str:
    items = [
        _normalize_spaces(element.get_text(" ", strip=True)) for element in soup.select(selector)
    ]
    return " ".join(item for item in items if item)


def _build_title(metadata: dict[str, Any]) -> str:
    parts = [metadata.get("case_number", "")]
    if metadata.get("case_class"):
        parts.append(metadata["case_class"])
    if metadata.get("subject"):
        parts.append(metadata["subject"])
    return " - ".join(part for part in parts if part)


def _looks_like_access_control(html: str, process_number: str) -> bool:
    lowered = html.lower()
    if process_number in html:
        return False
    return any(signal in lowered for signal in ["turnstile", "cf-challenge", "captcha"])


def _looks_like_list_access_control(html: str) -> bool:
    lowered = html.lower()
    has_result_link = "linkprocesso" in lowered or "show.do" in lowered
    if has_result_link:
        return False
    return any(
        signal in lowered
        for signal in [
            "turnstile",
            "cf-challenge",
            "captcha",
            "multiplas consultas simultâneas",
            "multiplas consultas simultaneas",
        ]
    )


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
