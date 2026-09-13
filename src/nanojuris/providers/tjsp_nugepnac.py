"""TJSP/NugepNac public precedent provider."""

from __future__ import annotations

import re
import time
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import DocumentReference, fetch_document_reference
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
    JurisprudenceResult,
    ParadigmCase,
    ProviderCapabilities,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import TransportPolicy

PROCESS_NUMBER_RE = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


class TjspNugepnacProvider(JurisprudenceProvider):
    """Provider for TJSP/NugepNac IRDR and IAC precedent pages."""

    name = "tjsp_nugepnac"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_request = 0.0
        tjsp_host = urlparse(self.config.tjsp_url).hostname or "www.tjsp.jus.br"
        self._document_policy = TransportPolicy(
            allowed_hosts=(tjsp_host, "esaj.tjsp.jus.br"),
            timeout_seconds=self.config.timeout,
            max_retries=2,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._document_urls: dict[str, str] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        precedent_types = _selected_precedent_types(query.types)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/NugepNac/(Irdr|Iac)",
            query=query.to_dict(),
            source_url=self.config.tjsp_url,
            limitations=[
                "Catalogo publico TJSP/NugepNac validado com sessao HTTP limpa.",
                "Links de acordaos do CJSG podem redirecionar para verificacao de acesso.",
                "O provider nao tenta contornar captcha, login ou controle de acesso.",
            ],
        )
        candidates: list[_NugepLink] = []
        for precedent_type in precedent_types:
            html, source_url = self._request_text("GET", _list_path(precedent_type))
            candidates.extend(
                parse_nugepnac_list(
                    html,
                    source_url=source_url,
                    precedent_type=precedent_type,
                )
            )

        normalized_query = _normalize_text(query.text or query.exact_phrase)
        results: list[JurisprudenceResult] = []
        scanned = 0
        for candidate in candidates:
            if query.number and query.number not in candidate.title:
                continue
            title_matches = not normalized_query or normalized_query in _normalize_text(
                candidate.title
            )
            if not title_matches and scanned >= max(query.page_size * 4, 12):
                continue
            detail_html, detail_url = self._request_text("GET", candidate.detail_path)
            scanned += 1
            detail_text = BeautifulSoup(detail_html, "html.parser").get_text(" ", strip=True)
            if normalized_query and normalized_query not in _normalize_text(
                f"{candidate.title} {detail_text}"
            ):
                continue
            results.append(
                parse_nugepnac_detail(
                    detail_html,
                    source_url=detail_url,
                    precedent_type=candidate.precedent_type,
                    trace=trace,
                )
            )
            if len(results) >= query.page * query.page_size:
                break

        start_index = (query.page - 1) * query.page_size
        limited = results[start_index : start_index + query.page_size]
        for result in results:
            links = result.raw.get("related_links") if isinstance(result.raw, dict) else None
            if isinstance(links, list):
                document_link = _select_document_link(links)
                if document_link is not None:
                    self._document_urls[result.id] = document_link
        start = start_index + 1 if limited else 0
        # The public catalog has a finite, observable link set when no
        # content-dependent detail filter is requested.  For text searches,
        # matching requires fetching detail pages and the complete total is
        # intentionally unknown rather than being reported as zero.
        total_known = not bool(normalized_query)
        reported_total = len(candidates) if total_known else len(results)
        return SearchPage(
            source=self.name,
            total=reported_total,
            start=start,
            end=start + len(limited) - 1 if limited else 0,
            page=query.page,
            page_size=query.page_size,
            results=limited,
            source_trace=trace,
            total_known=total_known,
            is_complete=total_known and start_index + len(limited) >= reported_total,
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        """Fetch an observed TJSP/NugepNac related decision document."""

        document_url = (
            document_id
            if document_id.startswith("https://")
            else self._document_urls.get(document_id)
        )
        if not document_url:
            raise ValueError(
                "TJSP/NugepNac document_id must be an observed official HTTPS URL or a result id"
            )
        parsed = urlparse(document_url)
        allowed_hosts = {
            urlparse(self.config.tjsp_url).hostname or "www.tjsp.jus.br",
            "esaj.tjsp.jus.br",
        }
        if parsed.hostname not in allowed_hosts:
            raise ValueError("TJSP/NugepNac document URL is outside the official host allowlist")
        reference = DocumentReference(
            id=document_id,
            source=self.name,
            url=document_url,
            document_type="acordao_relacionado",
            expected_content_types=("application/pdf", "text/html", "text/plain"),
        )
        document = fetch_document_reference(
            reference,
            policy=self._document_policy,
            session=self.session,
            title="TJSP NugepNac Acordao Relacionado",
        )
        if not (document.text or "").strip():
            body = (document.raw_bytes or b"").decode("utf-8", errors="ignore").casefold()
            if "captcha" in body or "recaptcha" in body:
                raise AccessControlRequiredError(
                    "TJSP/NugepNac inteiro teor exige validacao de acesso"
                )
            raise ParserContractChangedError("TJSP/NugepNac document returned no extractable text")
        return document

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        detail_path = _detail_path_from_id(precedent_id)
        html, source_url = self._request_text("GET", detail_path)
        trace = SourceTrace(
            provider=self.name,
            endpoint=detail_path,
            query={"precedent_id": precedent_id},
            source_url=source_url,
            limitations=["Detalhe publico de precedente TJSP/NugepNac."],
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": html, "content_type": "text/html"}],
            source_trace=trace,
            raw={"detail_path": detail_path},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJSP NugepNac Precedentes",
            source_url=self.config.tjsp_url.rstrip("/") + "/NugepNac",
            category="court_precedents",
            search_modes=["text", "number", "precedent_type", "catalog_detail"],
            document_types=["irdr", "iac"],
            content_formats=["html"],
            canonical_records=["CanonicalPrecedent"],
            extracted_fields=[
                "theme_number",
                "id",
                "precedent_type",
                "status",
                "case_number",
                "subject",
                "judging_body",
                "rapporteur",
                "admission_date",
                "admissibility_publication_date",
                "merit_judgment_date",
                "merit_publication_date",
                "judgment_date",
                "publication_date",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
                "question",
                "thesis",
                "related_decision_links",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.PARTIAL,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /NugepNac/Irdr",
                "GET /NugepNac/Iac",
                "GET /NugepNac/(Irdr|Iac)/DetalheTema?codigoNoticia=<id>&pagina=1",
            ],
            supports_full_text=False,
            pagination_mode="local_window",
            completeness_contract="observed_window_only",
            full_text_access="link_only",
            supports_cli=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=True,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=["text", "number", "types"],
            unsupported_filters=[
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "rapporteur",
                "updated_from",
                "updated_to",
                "published_from",
                "published_to",
                "source_origin",
                "source_origins",
                "fetch_details",
                "case_class",
                "judging_body",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "document_type",
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
            ],
            filter_semantics={
                "text": "native",
                "number": "native",
                "types": "native",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "exact_phrase": "unsupported",
                "rapporteur": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "fetch_details": "unsupported",
                "case_class": "unsupported",
                "judging_body": "unsupported",
                "degree": "unsupported",
                "instance": "unsupported",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
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
            },
            limitations=[
                "A pagina de detalhe contem tese e questao; inteiro teor CJSG pode exigir "
                "verificacao.",
                "Fonte HTML institucional sujeita a mudancas de layout.",
            ],
            responsible_use=[
                "Usar consultas pequenas e preservar codigoNoticia e SourceTrace.",
                "Nao reutilizar URLs com tokens de captcha presentes em links do CJSG.",
            ],
        )

    def _request_text(self, method: str, path: str, **kwargs: Any) -> tuple[str, str]:
        self._respect_rate_limit()
        url = urljoin(self.config.tjsp_url.rstrip("/") + "/", path.lstrip("/"))
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
            raise SourceUnavailableError(f"TJSP/NugepNac request failed: {exc}") from exc

        response.encoding = response.encoding or response.apparent_encoding or "utf-8"
        if response.status_code == 429:
            raise RateLimitDetectedError("TJSP/NugepNac returned HTTP 429")
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJSP/NugepNac returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJSP/NugepNac rejected request with HTTP {response.status_code}"
            )
        return response.text, getattr(response, "url", url)

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()


class _NugepLink:
    def __init__(self, *, title: str, detail_path: str, precedent_type: str) -> None:
        self.title = title
        self.detail_path = detail_path
        self.precedent_type = precedent_type


def parse_nugepnac_list(
    html: str,
    *,
    source_url: str,
    precedent_type: str,
) -> list[_NugepLink]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[_NugepLink] = []
    marker = f"/NugepNac/{precedent_type.capitalize()}/DetalheTema"
    for node in soup.find_all("a", href=True):
        href = str(node.get("href") or "")
        if marker not in href:
            continue
        title = _clean_text(node.get_text(" ", strip=True))
        if not title:
            continue
        links.append(
            _NugepLink(
                title=title,
                detail_path=_relative_url_path(urljoin(source_url, href)),
                precedent_type=precedent_type,
            )
        )
    if not links:
        raise ParserContractChangedError("TJSP/NugepNac precedent links not found")
    return links


def parse_nugepnac_detail(
    html: str,
    *,
    source_url: str,
    precedent_type: str,
    trace: SourceTrace,
) -> JurisprudenceResult:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")
    if not isinstance(article, Tag):
        raise ParserContractChangedError("TJSP/NugepNac detail article not found")
    text = _clean_text(article.get_text(" ", strip=True))
    title = _extract_title(article, text)
    theme_number = _extract_theme_number(title)
    status = _extract_status(title) or _extract_labeled_value(text, "Suspensão")
    case_number = _find_case_number(text)
    code = _query_value(source_url, "codigoNoticia") or str(theme_number or _digits(title))
    result_id = f"tjsp-nugepnac-{precedent_type}-{code}"
    question = _extract_section(
        text,
        "Questão submetida a julgamento",
        ["Tese firmada", "Dispositivos normativos relacionados", "Observação"],
    )
    thesis = _extract_section(
        text,
        "Tese firmada",
        ["Dispositivos normativos relacionados", "Observação", "Link"],
    )
    related_links = _related_links(article, source_url)
    merit_judgment_date = _extract_labeled_value(text, "Data de Julgamento do M\u00e9rito")
    merit_publication_date = _extract_labeled_value(
        text, "Data de Publica\u00e7\u00e3o do Ac\u00f3rd\u00e3o de M\u00e9rito"
    ) or _extract_labeled_value(text, "Publica\u00e7\u00e3o do Ac\u00f3rd\u00e3o de M\u00e9rito")
    document_url = _select_document_link(related_links)
    paradigm_url = next(
        (item["url"] for item in related_links if case_number and case_number in item["label"]),
        None,
    )

    return JurisprudenceResult(
        id=result_id,
        source="tjsp_nugepnac",
        court="TJSP",
        type=precedent_type,
        number=theme_number,
        question=question,
        thesis=thesis,
        summary=title,
        status=status,
        judgment_date=merit_judgment_date,
        publication_date=merit_publication_date,
        access_status=AccessStatus.PUBLIC,
        degree="second",
        instance="second",
        branch="state",
        authority="TJSP",
        collection="NUGEP_NAC",
        document_type=precedent_type,
        source_origin=source_url,
        document_url=document_url,
        rapporteur=_extract_labeled_value(text, "Relator(a)"),
        updated_at=_extract_labeled_value(text, "Data de Publicação do Acórdão de Mérito")
        or _extract_labeled_value(text, "Publicação do Acórdão de Mérito"),
        paradigm_cases=[ParadigmCase(number=case_number, url=paradigm_url)] if case_number else [],
        source_trace=SourceTrace(
            provider=trace.provider,
            endpoint=trace.endpoint,
            query={"codigoNoticia": code, "type": precedent_type},
            source_url=source_url,
            limitations=trace.limitations,
        ),
        raw={
            "title": title,
            "theme_number": theme_number,
            "case_number": case_number,
            "subject": _extract_labeled_value(text, "Assunto"),
            "judging_body": _extract_labeled_value(text, "Órgão Julgador"),
            "admission_date": _extract_labeled_value(text, "Data de Admissão"),
            "admissibility_publication_date": _extract_labeled_value(
                text, "Publicação do Acórdão de Admissibilidade"
            )
            or _extract_labeled_value(text, "Data de Publicação do Acórdão de Admissibilidade"),
            "merit_judgment_date": _extract_labeled_value(text, "Data de Julgamento do Mérito"),
            "merit_publication_date": _extract_labeled_value(
                text, "Data de Publicação do Acórdão de Mérito"
            )
            or _extract_labeled_value(text, "Publicação do Acórdão de Mérito"),
            "stj_controversy": _extract_labeled_value(text, "Controvérsia STJ"),
            "stj_resource": _extract_labeled_value(text, "Número do recurso no STJ"),
            "related_links": related_links,
            "document_url": document_url,
            "source_url": source_url,
        },
    )


def _selected_precedent_types(values: list[str]) -> list[str]:
    selected = [
        _normalize_type(value) for value in values if _normalize_type(value) in {"irdr", "iac"}
    ]
    return selected or ["irdr", "iac"]


def _select_document_link(links: Iterable[object]) -> str | None:
    """Choose an official decision URL instead of a process-search link."""

    candidates: list[tuple[int, str]] = []
    for link in links:
        if not isinstance(link, dict):
            continue
        url = link.get("url")
        label = str(link.get("label") or "").casefold()
        if not isinstance(url, str) or not url.startswith("https://"):
            continue
        if "uuidcaptcha" in url.casefold() or "g-recaptcha-response" in url.casefold():
            continue
        parsed = urlparse(url)
        if parsed.hostname not in {"esaj.tjsp.jus.br", "www.tjsp.jus.br"}:
            continue
        score = 0
        if "/cjsg/getarquivo.do" in parsed.path.casefold():
            score += 4
        if "acórdão" in label or "acordao" in label:
            score += 2
        if "processo" in label or "/cposg/" in parsed.path.casefold():
            score -= 3
        candidates.append((score, url))
    # A process-search URL is related context, not an observed decision
    # document.  Do not cache it as ``get_document`` input: doing so would
    # turn an unavailable related document into a misleading document fetch.
    best_score, best_url = max(candidates, default=(0, None))
    return best_url if best_score > 0 else None


def _normalize_type(value: str) -> str:
    return _normalize_text(value).replace(" ", "_")


def _list_path(precedent_type: str) -> str:
    return "/NugepNac/Irdr" if precedent_type == "irdr" else "/NugepNac/Iac"


def _detail_path_from_id(precedent_id: str) -> str:
    match = re.search(r"tjsp-nugepnac-(irdr|iac)-(\d+)$", precedent_id)
    if not match:
        raise ParserContractChangedError(
            "TJSP/NugepNac id must be tjsp-nugepnac-<type>-<codigoNoticia>"
        )
    precedent_type, code = match.groups()
    area = "Irdr" if precedent_type == "irdr" else "Iac"
    return f"/NugepNac/{area}/DetalheTema?codigoNoticia={code}&pagina=1"


def _extract_title(article: Tag, fallback_text: str) -> str:
    first_article = article.find("article")
    if isinstance(first_article, Tag):
        title = _clean_text(first_article.get_text(" ", strip=True))
        if title:
            return title
    first_heading = article.find(["h1", "h2", "h3"])
    if isinstance(first_heading, Tag):
        title = _clean_text(first_heading.get_text(" ", strip=True))
        if title:
            return title
    return fallback_text.split(" Processo Paradigma:", 1)[0]


def _extract_theme_number(title: str) -> int | None:
    match = re.search(r"Tema\s+0*(\d+)", title, flags=re.I)
    return int(match.group(1)) if match else None


def _extract_status(title: str) -> str | None:
    match = re.search(r"\(([^)]+)\)\s*$", title)
    return _clean_text(match.group(1)) if match else None


def _extract_labeled_value(text: str, label: str) -> str | None:
    labels = [
        "Processo Paradigma",
        "Assunto",
        "Órgão Julgador",
        "NUT",
        "Relator(a)",
        "Data de Admissão",
        "Data de Publicação do Acórdão de Admissibilidade",
        "Publicação do Acórdão de Admissibilidade",
        "Data de Julgamento do Mérito",
        "Data de Publicação do Acórdão de Mérito",
        "Publicação do Acórdão de Mérito",
        "Recursos Especial e Extraordinário admitidos",
        "Controvérsia STJ",
        "Número do recurso no STJ",
        "Suspensão",
        "Termo Final da Suspensão",
        "Questão submetida a julgamento",
        "Tese firmada",
        "Dispositivos normativos relacionados",
        "Observação",
    ]
    for label_variant in _text_variants(label):
        following = [item for item in labels if item != label]
        following_variants = [variant for item in following for variant in _text_variants(item)]
        next_label_pattern = "|".join(re.escape(item) + r"\s*:" for item in following_variants)
        pattern = rf"{re.escape(label_variant)}\s*:\s*(.*?)\s*(?={next_label_pattern}|$)"
        match = re.search(pattern, text, flags=re.I)
        if match:
            return _clean_text(match.group(1))
    return None


def _extract_section(text: str, label: str, end_labels: list[str]) -> str | None:
    for label_variant in _text_variants(label):
        end_label_variants = [variant for item in end_labels for variant in _text_variants(item)]
        end_label_pattern = "|".join(re.escape(item) + r"\s*:" for item in end_label_variants)
        pattern = rf"{re.escape(label_variant)}\s*:\s*(.*?)\s*(?={end_label_pattern}|$)"
        match = re.search(pattern, text, flags=re.I)
        if match:
            return _clean_text(match.group(1))
    return None


def _related_links(article: Tag, source_url: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    for node in article.find_all("a", href=True):
        label = _clean_text(node.get_text(" ", strip=True))
        href = str(node.get("href") or "")
        if not label:
            continue
        links.append({"label": label, "url": urljoin(source_url, href)})
    return links


def _find_case_number(text: str) -> str | None:
    match = PROCESS_NUMBER_RE.search(text)
    return match.group(0) if match else None


def _query_value(url: str, key: str) -> str | None:
    values = parse_qs(urlparse(url).query).get(key)
    return values[0] if values else None


def _base_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _relative_url_path(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path + (f"?{parsed.query}" if parsed.query else "")


def _digits(value: object) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _text_variants(value: str) -> tuple[str, ...]:
    """Return the source spelling and a repaired UTF-8/Latin-1 variant.

    Some archived TJSP pages were captured with an incorrect Latin-1 decode
    (for example ``QuestÃ£o``), while current responses are valid UTF-8.  The
    parser must accept both without rewriting the extracted value.
    """

    repaired = value
    try:
        candidate = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        candidate = value
    if candidate != value:
        repaired = candidate
    return (value, repaired)


def _normalize_text(value: str) -> str:
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
