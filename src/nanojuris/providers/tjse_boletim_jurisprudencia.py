"""TJSE Boletim Jurídico public second-degree jurisprudence adapter."""

from __future__ import annotations

import hashlib
import re
from datetime import date, timedelta
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
    CanonicalDocument,
    DecisionBundle,
    ExtractionStatus,
    JurisprudenceQuery,
    JurisprudenceResult,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

SEARCH_PATH = "/revista/internet/pesquisar.wsp"
PRINCIPAL_PATH = "/revista/internet/principal.wsp"
MAX_PAGE_SIZE = 100
SERVER_PAGE_SIZE = 1000
_PUBLIC_HOSTS = {"diario.tjse.jus.br", "www.tjse.jus.br"}
_SECTION_RE = re.compile(
    r"verSecao\('(?P<edition>\d+)'\s*,\s*(?P<caderno>\d+)\s*,\s*(?P<section>\d+)\)"
)
_MONTHS = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


class TjseBoletimJurisprudenciaProvider(JurisprudenceProvider):
    """Read public TJSE Boletim Jurídico ementas and acórdão links."""

    name = "tjse_boletim_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlsplit(self.config.tjse_boletim_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=tuple(_PUBLIC_HOSTS | {host}),
                timeout_seconds=self.config.timeout,
                # A single public section can legitimately contain thousands
                # of ementas. Keep a hard bound while allowing the observed
                # ~8.5 MB HTML response through without treating it as a
                # transport failure.
                max_bytes=16_000_000,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http: dict[str, Any] = {}
        self._documents: dict[str, tuple[str, str, SourceTrace]] = {}

    @property
    def base_url(self) -> str:
        return self.config.tjse_boletim_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        form_html = self._request("GET", SEARCH_PATH)
        payload = _form_payload(form_html, query)
        search_html = self._request("POST", SEARCH_PATH, data=payload)
        entries = _parse_sections(search_html)
        if not entries:
            raise ParserContractChangedError("TJSE Boletim não retornou edições/seções")
        # One section is deliberately bounded per call. The public search page
        # can list several editions; the first matching section is stable and
        # contains the textual ementas for the selected appellate body.
        section = entries[min(query.page - 1, len(entries) - 1)]
        principal_payload = {
            "tmp.diario.cd_secao": str(section["section"]),
            "tmp.diario.nu_edicao": str(section["edition"]),
            "tmp.diario.id_advogado": payload.get("tmp.diario.id_advogado", ""),
            "tmp.diario.pal_chave": payload.get("tmp.diario.pal_chave", ""),
        }
        if query.page > len(entries):
            principal_payload["grid.lista_conteudodiario.next"] = str(
                (query.page - len(entries)) * SERVER_PAGE_SIZE + 1
            )
        principal_html = self._request("POST", PRINCIPAL_PATH, data=principal_payload)
        trace = self._trace(query, section, principal_html)
        results, has_next = _parse_principal(
            principal_html,
            edition=str(section["edition"]),
            section=str(section["section"]),
            trace=trace,
            base_url=self.base_url,
        )
        start = (query.page - 1) * query.page_size
        page_results = results[start : start + min(query.page_size, MAX_PAGE_SIZE)]
        for result in page_results:
            url = result.document_url
            if url and result.full_text:
                self._documents[result.id] = (url, result.full_text, trace)
        complete = not has_next and len(entries) <= query.page
        return SearchPage(
            source=self.name,
            total=len(results),
            start=start,
            end=start + len(page_results),
            page=query.page,
            page_size=min(query.page_size, MAX_PAGE_SIZE),
            results=page_results,
            source_trace=trace,
            pagination_mode="edition_section",
            is_complete=complete,
            completeness_reason=(
                "uma edição/seção processada; total entre edições não é informado"
                if not complete
                else "todas as linhas da seção foram processadas"
            ),
            ordering="source_order",
            filters_applied={
                "text": "native",
                "number": "native_as_keyword",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
            },
            total_known=False,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        entry = self._documents.get(precedent_id)
        if entry is None:
            raise SourceUnavailableError(
                "TJSE Boletim detalhe disponível somente após search na mesma sessão"
            )
        url, fallback_text, search_trace = entry
        # Fetch the linked public report lazily. Search remains bounded while
        # document callers receive the richest text exposed by TJNet.
        detail_markup = self._request("GET", url)
        detail_text = _parse_detail_text(detail_markup)
        text = detail_text or fallback_text
        trace = SourceTrace(
            provider=self.name,
            endpoint=f"GET {url}",
            query=search_trace.query,
            source_url=url,
            limitations=search_trace.limitations,
            retrieval_status="ok",
            transformations=["html_visible_text", "public_detail_fetch"],
            **self._last_http,
        )
        self._documents[precedent_id] = (url, text, trace)
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {"content": text, "content_type": "text/plain", "source_content_type": "text/html"}
            ],
            procedural_follow_url=url,
            source_trace=trace,
            raw={"document_url": url, "inline_from_boletim": True},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        text = str(bundle.texts[0].get("content") if bundle.texts else "")
        url = bundle.procedural_follow_url
        trace = bundle.source_trace
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao",
            content=text.encode("utf-8"),
            content_type="text/plain",
            title=f"TJSE Boletim Jurídico {document_id}",
            text_override=text,
            url=url,
            source_trace=trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"document_url": url, "inline_from_boletim": True},
            parser="tjse_boletim_jurisprudencia.inline",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJSE Boletim Jurídico (CJSG)",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=["text", "case_number", "summary", "full_text", "date_range"],
            document_types=["acordao", "ementa"],
            content_formats=["html", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
                "degree",
                "instance",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "POST /revista/internet/pesquisar.wsp",
                "POST /revista/internet/principal.wsp",
                "GET /tjnet/jurisprudencia/relatorio.wsp",
            ],
            supports_full_text=True,
            full_text_access="inline",
            # The surface is bounded to one edition/section and explicitly
            # reports an unknown cross-edition total; federation can therefore
            # include it without claiming national completeness.
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="edition_section",
            max_remote_page_size=SERVER_PAGE_SIZE,
            completeness_contract="section_rows_total_unknown_across_editions",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "degree",
                "instance",
                "branch",
                "page",
                "judgment_date_from",
                "judgment_date_to",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "case_class",
                "rapporteur",
                "judging_body",
                "party_name",
                "updated_from",
                "updated_to",
                "fetch_details",
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "native_as_keyword",
                "number": "native_as_keyword",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "page": "local_section_slice",
                "judgment_date_from": "native_date_window",
                "judgment_date_to": "native_date_window",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "decision_type": "unsupported",
                "case_class": "unsupported",
                "rapporteur": "unsupported",
                "judging_body": "unsupported",
                "fetch_details": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "party_document": "unsupported",
                "lawyer_name": "unsupported",
                "oab": "unsupported",
                "precatory_number": "unsupported",
                "police_document": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "legal_area": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
            },
            limitations=[
                "A busca é organizada por edição/seção; o total nacional entre "
                "edições é desconhecido.",
                "As ementas são texto integral da publicação do Boletim, não o voto completo.",
                "O adapter não acessa nem contorna a pesquisa judicial protegida por Turnstile.",
            ],
            responsible_use=["Usar apenas a superfície pública e chamadas bounded."],
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> str:
        url = (
            path
            if path.startswith(("http://", "https://"))
            else urljoin(self.base_url + "/", path.lstrip("/"))
        )
        request = TransportRequest(
            source=self.name,
            operation="boletim_request",
            method=method,
            url=url,
            data=kwargs.pop("data", None),
            params=kwargs.pop("params", {}),
            headers=kwargs.pop("headers", {}),
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        if kwargs:
            raise TypeError(f"unsupported transport arguments: {', '.join(sorted(kwargs))}")
        try:
            response = self.transport.request(request)
        except requests.exceptions.Timeout as exc:
            raise SourceUnavailableError("TJSE Boletim request timeout") from exc
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError("TJSE Boletim TLS negotiation failed") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJSE Boletim request failed") from exc
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJSE Boletim request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJSE Boletim transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJSE Boletim transport returned no HTTP status")
        body = response.body
        self._last_http = {
            "http_status": status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "response_bytes": len(body),
        }
        if status_code == 429:
            raise RateLimitDetectedError("TJSE Boletim returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJSE Boletim returned HTTP {status_code}")
        if status_code < 200 or status_code >= 300:
            raise SourceUnavailableError(f"TJSE Boletim returned HTTP {status_code}")
        charset = _response_charset(response.content_type) or "iso-8859-1"
        try:
            return body.decode(charset, errors="replace")
        except LookupError:
            return body.decode("iso-8859-1", errors="replace")

    def _trace(self, query: JurisprudenceQuery, section: dict[str, Any], html: str) -> SourceTrace:
        return SourceTrace(
            provider=self.name,
            endpoint=f"POST {PRINCIPAL_PATH}",
            query={
                "text": query.text,
                "number": query.number,
                "page": query.page,
                "page_size": query.page_size,
                "edition": section["edition"],
                "section": section["section"],
            },
            source_url=urljoin(self.base_url + "/", PRINCIPAL_PATH.lstrip("/")),
            limitations=[
                "O total entre edições/seções não é informado pela fonte.",
                "A publicação fornece ementas e links públicos de acórdãos.",
            ],
            retrieval_status="ok",
            **self._last_http,
        )


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJSE Boletim exige termo, número ou frase exata")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJSE Boletim suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJSE Boletim suporta somente instância de segundo grau")
    if query.branch and query.branch.casefold() not in {"state", "estadual"}:
        raise QueryRejectedError("TJSE Boletim pertence ao ramo estadual")
    if query.authority and query.authority.casefold() not in {
        "tjse",
        "tribunal de justiça de sergipe",
    }:
        raise QueryRejectedError("a autoridade solicitada não corresponde ao TJSE")


def _form_payload(markup: str, query: JurisprudenceQuery) -> dict[str, str]:
    soup = BeautifulSoup(markup, "html.parser")
    form = soup.find("form", attrs={"name": "formulario"})
    if not isinstance(form, Tag):
        raise ParserContractChangedError("TJSE Boletim não retornou formulário de pesquisa")
    payload: dict[str, str] = {}
    for control in form.find_all(["input", "select"]):
        name = control.get("name")
        if not name:
            continue
        if control.name == "select":
            selected = control.find("option", selected=True) or control.find("option")
            payload[name] = str(selected.get("value", "") if selected else "")
        else:
            payload[name] = str(control.get("value", ""))
    start = query.judgment_date_from or query.published_from
    end = query.judgment_date_to or query.published_to
    if not start:
        start = (date.today() - timedelta(days=365)).strftime("%d/%m/%Y")
    if not end:
        end = date.today().strftime("%d/%m/%Y")
    payload.update(
        {
            "tmp.diario.dt_inicio": _date_br(start),
            "tmp.diario.dt_fim": _date_br(end),
            "tmp.diario.pal_chave": query.exact_phrase or query.text or query.number,
            "tmp.bntEnviar": "Enviar",
            "tmp.diario.cd_caderno": "",
            "tmp.diario.cd_secao": "",
        }
    )
    return payload


def _parse_sections(markup: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(markup, "html.parser")
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for anchor in soup.find_all("a"):
        match = _SECTION_RE.search(str(anchor.get("onclick") or ""))
        if not match:
            continue
        values = match.groupdict()
        # Abreviaturas is not jurisprudence; all other published bodies are
        # appellate sections (câmaras, seção especializada or pleno).
        if values["caderno"] == "11":
            continue
        key = (values["edition"], values["caderno"], values["section"])
        if key in seen:
            continue
        seen.add(key)
        found.append({**values, "label": " ".join(anchor.get_text(" ", strip=True).split())})
    return found


def _parse_principal(
    markup: str,
    *,
    edition: str,
    section: str,
    trace: SourceTrace,
    base_url: str,
) -> tuple[list[JurisprudenceResult], bool]:
    soup = BeautifulSoup(markup, "html.parser")
    table = soup.find("table")
    if not isinstance(table, Tag):
        raise ParserContractChangedError("TJSE Boletim não retornou tabela de ementas")
    publication_date = _publication_date(soup)
    results: list[JurisprudenceResult] = []
    current_class = ""
    for row in table.find_all("tr"):
        cell = row.find("td")
        if not isinstance(cell, Tag):
            continue
        fonts = cell.find_all("font")
        if fonts and any("10pt" in str(font.get("style")) for font in fonts):
            current_class = " ".join(cell.get_text(" ", strip=True).split())
            continue
        links = cell.find_all("a")
        report = next((a for a in links if "relatorio.wsp" in str(a.get("href") or "")), None)
        process = next(
            (a for a in links if "respnumprocesso.wsp" in str(a.get("href") or "")), None
        )
        if not isinstance(report, Tag) or not isinstance(process, Tag):
            continue
        text = " ".join(cell.get_text(" ", strip=True).split())
        report_url = _secure_public_url(urljoin(base_url + "/", str(report.get("href"))))
        process_url = _secure_public_url(urljoin(base_url + "/", str(process.get("href"))))
        process_id = _query_value(process_url, "tmp.npro") or process.get_text(strip=True)
        decision_id = _query_value(report_url, "tmp.numacordao") or report.get_text(strip=True)
        result_id = f"tjse-boletim-{edition}-{section}-{decision_id}"
        rapporteur = _extract_rapporteur(text)
        results.append(
            JurisprudenceResult(
                id=result_id,
                source="tjse_boletim_jurisprudencia",
                court="TJSE",
                type="acordao",
                number=decision_id,
                summary=text,
                full_text=text,
                rapporteur=rapporteur,
                publication_date=publication_date,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                raw={
                    "edition": edition,
                    "section": section,
                    "case_class": current_class or None,
                    "process_number": process_id,
                    "process_url": process_url,
                    "acordao_number": decision_id,
                    "document_url": report_url,
                },
                case_class=current_class or None,
                degree="second",
                instance="second",
                branch="state",
                authority="TJSE",
                collection="CJSG",
                document_type="acordao",
                source_origin="tjse_boletim_juridico",
                document_url=report_url,
            )
        )
    has_next = bool(soup.select_one("a.nav_go"))
    return results, has_next


def _publication_date(soup: BeautifulSoup) -> str | None:
    heading = soup.find("h4")
    text = " ".join(heading.get_text(" ", strip=True).split()) if heading else ""
    match = re.search(
        r"Boletim n\.\s*\d+\s+de\s+(\d{1,2})\s+de\s+([A-Za-zçÇ]+)\s+de\s+(\d{4})", text, re.I
    )
    if not match:
        return None
    month = _MONTHS.get(match.group(2).casefold())
    if not month:
        return None
    try:
        return date(int(match.group(3)), month, int(match.group(1))).isoformat()
    except ValueError:
        return None


def _extract_rapporteur(text: str) -> str | None:
    match = re.search(
        r"RELATOR(?:\(A\))?\s*(?:ORIGIN[ÁA]RIO)?\s*:\s*([^\n]+?)(?=RELATOR|$)", text, re.I
    )
    return " ".join(match.group(1).split()) if match else None


def _query_value(url: str, key: str) -> str | None:
    from urllib.parse import parse_qs, urlparse

    values = parse_qs(urlparse(url).query).get(key)
    return values[0] if values else None


def _secure_public_url(value: str) -> str:
    """Allow only the official TJSE public hosts and require HTTPS."""

    parsed = urlsplit(value)
    host = (parsed.hostname or "").casefold()
    if parsed.scheme.casefold() not in {"http", "https"} or host not in _PUBLIC_HOSTS:
        raise ParserContractChangedError(
            "TJSE Boletim retornou link de documento fora da origem oficial"
        )
    if parsed.username or parsed.password:
        raise ParserContractChangedError("TJSE Boletim retornou link com credenciais embutidas")
    return urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, ""))


def _parse_detail_text(markup: str) -> str | None:
    """Extract visible TJNet report text, preserving a useful fallback."""

    soup = BeautifulSoup(markup, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    if not text:
        raise ParserContractChangedError("TJSE Boletim detalhe retornou texto vazio")
    # TJNet can return a valid report shell saying that the vote/ementa is not
    # available. Keep the search ementa in that case rather than replacing
    # good data with an error shell.
    unavailable = ("Ementa não disponível", "Acórdão não disponível")
    if all(marker.casefold() in text.casefold() for marker in unavailable):
        return None
    return text


def _date_br(value: str) -> str:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return __import__("datetime").datetime.strptime(value, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    raise QueryRejectedError(f"data inválida para TJSE Boletim: {value}")


def _response_charset(content_type: str | None) -> str | None:
    if not content_type:
        return None
    match = re.search(r"charset\s*=\s*['\"]?([^;\s'\"]+)", content_type, re.I)
    return match.group(1) if match else None


__all__ = ["TjseBoletimJurisprudenciaProvider"]
