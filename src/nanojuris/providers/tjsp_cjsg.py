"""TJSP CJSG public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

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


@dataclass(slots=True, frozen=True)
class CjsgAccessDiagnostic:
    """Access and response-shape signals observed in TJSP/CJSG HTML."""

    has_result_container: bool
    has_download_links: bool
    has_search_form: bool
    has_recaptcha_field: bool
    has_uuid_captcha_field: bool
    has_recaptcha_widget: bool
    has_access_control_route: bool
    has_login_script: bool
    has_empty_session: bool

    @property
    def access_control_required(self) -> bool:
        return (
            not self.has_result_container
            and not self.has_download_links
            and (
                self.has_recaptcha_field
                or self.has_uuid_captcha_field
                or self.has_recaptcha_widget
                or self.has_access_control_route
                or self.has_empty_session
            )
        )

    @property
    def returned_to_search_form(self) -> bool:
        return self.has_search_form and not self.has_result_container

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)

    def summary(self) -> str:
        flags = [name for name, value in self.to_dict().items() if value]
        return ", ".join(flags) if flags else "no known TJSP/CJSG access signals"


class TjspCjsgProvider(JurisprudenceProvider):
    """Provider for the public TJSP CJSG jurisprudence search."""

    name = "tjsp_cjsg"

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
        payload = self._build_payload(query)
        html = self._request_text("POST", endpoint, data=payload)
        trace_query: dict[str, Any] = {"payload": payload}
        if query.page > 1 and _looks_like_cjsg_results(html):
            decision_type = self._first_decision_type(payload)
            endpoint = f"/trocaDePagina.do?tipoDeDecisao={decision_type}&pagina={query.page}"
            html = self._request_text("GET", endpoint)
            trace_query = {
                "payload": payload,
                "tipoDeDecisao": decision_type,
                "pagina": query.page,
            }
        trace = SourceTrace(
            provider=self.name,
            endpoint=endpoint.split("?", 1)[0],
            query=trace_query,
            source_url=urljoin(self.config.tjsp_cjsg_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=[
                "Fonte HTML publica do TJSP/CJSG sujeita a mudancas de layout.",
                "O provider detecta captcha/controle de acesso e nao implementa bypass.",
                (
                    "Inteiro teor e acessivel apenas quando a fonte publica "
                    "disponibiliza cdAcordao/cdForo."
                ),
            ],
        )
        return parse_cjsg_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjsp_cjsg_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        cd_acordao, cd_foro = self._parse_precedent_id(precedent_id)
        endpoint = f"/getArquivo.do?cdAcordao={cd_acordao}&cdForo={cd_foro}"
        response = self._request_response("GET", endpoint)
        raw_content = _response_bytes(response)
        content_type = response.headers.get("Content-Type", "")
        is_pdf = raw_content.startswith(b"%PDF") or "application/pdf" in content_type.lower()
        extracted_content_type = "application/pdf" if is_pdf else "text/plain"
        if is_pdf:
            document_text, extraction_metadata = extract_cjsg_document_text_bytes(raw_content)
        else:
            document_text = decode_cjsg_response_text(response)
            document_text, extraction_metadata = extract_cjsg_document_text(document_text)
        trace = SourceTrace(
            provider=self.name,
            endpoint="/getArquivo.do",
            query={"cdAcordao": cd_acordao, "cdForo": cd_foro},
            source_url=urljoin(self.config.tjsp_cjsg_url.rstrip("/") + "/", endpoint.lstrip("/")),
            limitations=[
                "O retorno pode ser HTML, PDF ou uma tela de controle de acesso da propria fonte.",
            ],
            http_status=int(getattr(response, "status_code", 0) or 0) or None,
            final_url=str(getattr(response, "url", None) or "") or None,
            content_type=content_type or None,
            content_sha256=hashlib.sha256(raw_content).hexdigest(),
            response_bytes=len(raw_content),
            retrieval_status="ok" if 200 <= response.status_code < 300 else "http_error",
        )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": document_text,
                    "content_type": extracted_content_type,
                    "source_content_type": content_type or "text/html",
                }
            ],
            source_trace=trace,
            raw={
                "cd_acordao": cd_acordao,
                "cd_foro": cd_foro,
                "raw_content_sha256": hashlib.sha256(raw_content).hexdigest(),
                "raw_content_bytes": len(raw_content),
                "raw_content_type": content_type or "text/html",
                **extraction_metadata,
            },
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        return cjsg_decision_bundle_to_document(
            bundle,
            document_id=document_id,
            source=self.name,
            title=f"TJSP/CJSG inteiro teor {document_id}",
            parser="tjsp_cjsg.get_document",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJSP Consulta de Jurisprudencia/CJSG",
            source_url=self.config.tjsp_cjsg_url,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "date_range", "decision_type"],
            document_types=["acordao", "monocratic_decision", "homologation"],
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
                "access_diagnostic_flags",
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
            supported_filters=["text", "number"],
            limitations=[
                "A fonte pode exigir captcha ou outro controle de acesso.",
                "Inteiro teor depende de cdAcordao/cdForo publico e da resposta da fonte.",
                (
                    "O provider diagnostica sinais de formulario, reCAPTCHA, "
                    "uuidCaptcha e login sem bypass."
                ),
            ],
            responsible_use=[
                "Nao tentar contornar captcha, login ou controles de acesso.",
                "Usar testes live apenas quando explicitamente habilitados.",
            ],
        )

    def _build_payload(self, query: JurisprudenceQuery) -> dict[str, str | list[str]]:
        decision_types = query.types or ["A"]
        mapped_types = [self._map_decision_type(item) for item in decision_types]
        return {
            "conversationId": "",
            "dados.buscaInteiroTeor": query.text,
            "dados.pesquisarComSinonimos": ["S", "S"],
            "dados.buscaEmenta": query.exact_phrase,
            "dados.nuProcOrigem": query.number,
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
            "classesTreeSelection.values": "",
            "classesTreeSelection.text": "",
            "assuntosTreeSelection.values": "",
            "assuntosTreeSelection.text": "",
            "comarcaSelectedEntitiesList": "",
            "contadorcomarca": "0",
            "contadorMaiorcomarca": "0",
            "cdComarca": "",
            "nmComarca": "",
            "secoesTreeSelection.values": "",
            "secoesTreeSelection.text": "",
            "dados.dtJulgamentoInicio": query.updated_from,
            "dados.dtJulgamentoFim": query.updated_to,
            "dados.dtPublicacaoInicio": "",
            "dados.dtPublicacaoFim": "",
            "dados.origensSelecionadas": "T",
            "tipoDecisaoSelecionados": mapped_types,
            "dados.ordenarPor": self._map_order_by(query.order_by),
        }

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
        }
        try:
            response = self._request_response(method, path, headers=headers, **kwargs)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJSP/CJSG request failed: {exc}") from exc

        return decode_cjsg_response_text(response)

    def _request_response(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        self._respect_rate_limit()
        url = urljoin(self.config.tjsp_cjsg_url.rstrip("/") + "/", path.lstrip("/"))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJSP/CJSG request failed: {exc}") from exc

        if response.status_code == 429:
            raise RateLimitDetectedError("TJSP/CJSG returned HTTP 429")
        content_type = response.headers.get("Content-Type", "")
        if "pdf" in content_type.lower() or _response_bytes(response).startswith(b"%PDF"):
            return response
        text = decode_cjsg_response_text(response)
        diagnostic = diagnose_cjsg_access(text)
        if response.status_code == 404 and diagnostic.has_empty_session:
            raise AccessControlRequiredError(
                f"TJSP/CJSG requires an active public search session ({diagnostic.summary()})"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJSP/CJSG returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(
                f"TJSP/CJSG rejected request with HTTP {response.status_code}"
            )
        if diagnostic.access_control_required:
            raise AccessControlRequiredError(
                "TJSP/CJSG requires captcha or another access-control step "
                f"({diagnostic.summary()})"
            )
        return response

    def _respect_rate_limit(self) -> None:
        interval = self.config.rate_limit_interval
        if interval <= 0:
            return
        elapsed = time.monotonic() - self._last_request
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_request = time.monotonic()

    @staticmethod
    def _map_decision_type(value: str) -> str:
        normalized = value.strip().lower()
        mapping = {
            "a": "A",
            "acordao": "A",
            "acórdão": "A",
            "m": "M",
            "monocratica": "M",
            "monocrática": "M",
            "h": "H",
            "homologacao": "H",
            "homologação": "H",
        }
        return mapping.get(normalized, value.upper())

    @staticmethod
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

    @staticmethod
    def _parse_precedent_id(precedent_id: str) -> tuple[str, str]:
        match = re.fullmatch(r"tjsp-cjsg-(?P<cd>\d+)(?:-(?P<foro>\d+))?", precedent_id)
        if not match:
            raise ParserContractChangedError(
                "TJSP/CJSG precedent id must look like tjsp-cjsg-<cdAcordao>-<cdForo>"
            )
        return match.group("cd"), match.group("foro") or "0"

    @staticmethod
    def _first_decision_type(payload: dict[str, str | list[str]]) -> str:
        value = payload.get("tipoDecisaoSelecionados")
        if isinstance(value, list) and value:
            return str(value[0])
        if isinstance(value, str) and value:
            return value
        return "A"


def parse_cjsg_results(
    html: str,
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    base_url: str,
    source: str = "tjsp_cjsg",
    court: str = "TJSP",
    id_prefix: str = "tjsp-cjsg",
    source_label: str = "TJSP/CJSG",
) -> SearchPage:
    """Parse a CJSG result page into normalized results."""

    if _looks_like_access_control(html):
        raise AccessControlRequiredError(f"{source_label} returned captcha/access-control HTML")

    soup = BeautifulSoup(html, "html.parser")
    result_root = (
        soup.select_one("#divDadosResultado-A")
        or soup.select_one("#tdResultados")
        or (soup if soup.select("a.downloadEmenta") else None)
    )
    if result_root is None:
        if "Resultado consulta" in html or "Resultados" in html:
            return SearchPage(
                source=source,
                total=0,
                start=0,
                end=0,
                page=query.page,
                page_size=query.page_size,
                results=[],
                source_trace=trace,
            )
        raise ParserContractChangedError(f"{source_label} result container not found")

    total, start, end = _parse_pagination(soup.get_text(" ", strip=True), soup=soup)
    results: list[JurisprudenceResult] = []
    seen: set[tuple[str, str]] = set()
    for anchor in result_root.select("a.downloadEmenta"):
        cd_acordao = str(anchor.get("cdacordao") or anchor.get("cdAcordao") or "")
        cd_foro = str(anchor.get("cdforo") or anchor.get("cdForo") or "0")
        key = (cd_acordao, cd_foro)
        if not cd_acordao or key in seen:
            continue
        case_number = anchor.get_text(" ", strip=True)
        if not case_number:
            continue
        seen.add(key)
        container = anchor.find_parent("table")
        if container is None:
            continue
        labels = _extract_labeled_fields(container)
        summary = _extract_summary(container, cd_acordao)
        class_subject = labels.get("classe/assunto")
        case_class, subject = _split_class_subject(class_subject)
        full_text_url = urljoin(
            base_url.rstrip("/") + "/",
            f"getArquivo.do?cdAcordao={cd_acordao}&cdForo={cd_foro}",
        )
        result_trace = SourceTrace(
            provider=trace.provider,
            endpoint=trace.endpoint,
            query=trace.query,
            source_url=full_text_url,
            limitations=trace.limitations,
        )
        result = JurisprudenceResult(
            id=f"{id_prefix}-{cd_acordao}-{cd_foro}",
            source=source,
            court=court,
            type="acordao",
            number=case_number,
            summary=summary,
            rapporteur=labels.get("relator(a)") or labels.get("relator"),
            updated_at=labels.get("data de registro") or labels.get("data de publicação"),
            highlights={},
            source_trace=result_trace,
            raw={
                "cd_acordao": cd_acordao,
                "cd_foro": cd_foro,
                "full_text_url": full_text_url,
                "classe": case_class,
                "assunto": subject,
                "comarca": labels.get("comarca"),
                "orgao_julgador": labels.get("órgão julgador") or labels.get("orgao julgador"),
                "labels": labels,
            },
        )
        results.append(result)

    if not results and total > 0:
        raise ParserContractChangedError(f"{source_label} parser found total results but no items")
    limited_results = results[: query.page_size]

    return SearchPage(
        source=source,
        total=total or len(results),
        start=start or (1 if results else 0),
        end=(start or 1) + len(limited_results) - 1 if limited_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
    )


def decode_cjsg_response_text(response: requests.Response) -> str:
    """Decode CJSG HTML using the source-declared charset or detected encoding."""

    headers = getattr(response, "headers", {})
    content_type = headers.get("Content-Type", "")
    if "charset=" not in content_type.lower():
        response.encoding = (
            getattr(response, "apparent_encoding", None)
            or getattr(response, "encoding", None)
            or "windows-1252"
        )
    elif response.encoding is None:
        response.encoding = getattr(response, "apparent_encoding", None) or "utf-8"
    return response.text


def cjsg_decision_bundle_to_document(
    bundle: DecisionBundle,
    *,
    document_id: str,
    source: str,
    title: str,
    parser: str,
) -> CanonicalDocument:
    """Convert a CJSG public getArquivo response into a canonical document."""

    content = str(bundle.texts[0].get("content") if bundle.texts else "")
    content_type = str(bundle.texts[0].get("content_type") if bundle.texts else "text/plain")
    metadata = dict(bundle.raw or {})
    warnings = list(metadata.get("warnings") or [])
    raw_content_sha256 = str(metadata.get("raw_content_sha256") or "") or None
    raw_content_bytes = metadata.get("raw_content_bytes")
    content_sha256 = raw_content_sha256
    content_byte_size = int(raw_content_bytes) if raw_content_bytes is not None else None
    if raw_content_sha256 is None or content_byte_size is None:
        warnings.append(
            "A resposta bruta nao foi preservada; hash e tamanho do documento original "
            "nao podem ser afirmados com integridade binaria."
        )
    access_status = _metadata_access_status(metadata)
    status = (
        ExtractionStatus.COMPLETE if content.strip() and not warnings else ExtractionStatus.PARTIAL
    )
    return CanonicalDocument(
        id=document_id,
        source=source,
        document_type="acordao",
        content_type=content_type,
        title=str(metadata.get("document_title") or title),
        text=content,
        url=bundle.source_trace.source_url if bundle.source_trace else None,
        sha256=content_sha256,
        byte_size=content_byte_size,
        retrieved_at=bundle.source_trace.retrieved_at if bundle.source_trace else None,
        access_status=access_status,
        source_trace=bundle.source_trace,
        extraction_trace=ExtractionTrace(
            parser=parser,
            parser_version="1",
            status=status,
            access_status=access_status,
            content_sha256=content_sha256,
            content_bytes=content_byte_size,
            warnings=warnings,
            metadata=metadata,
        ),
        raw_metadata=metadata,
    )


def _metadata_access_status(metadata: dict[str, Any]) -> AccessStatus:
    raw_status = metadata.get("access_status")
    if isinstance(raw_status, AccessStatus):
        return raw_status
    if isinstance(raw_status, str):
        try:
            return AccessStatus(raw_status)
        except ValueError:
            return AccessStatus.PARTIAL
    return AccessStatus.PUBLIC


def _response_bytes(response: requests.Response) -> bytes:
    """Read raw bytes while remaining compatible with lightweight test responses."""

    content = getattr(response, "content", None)
    if content is not None:
        return bytes(content)
    return str(getattr(response, "text", "")).encode("utf-8")


def _parse_pagination(text: str, *, soup: BeautifulSoup | None = None) -> tuple[int, int, int]:
    match = re.search(r"Resultados\s+(\d+)\s+a\s+(\d+)\s+de\s+(\d+)", text, re.I)
    if match:
        start, end, total = (int(match.group(index)) for index in (1, 2, 3))
        return total, start, end
    if soup is None:
        return 0, 0, 0
    total = _parse_total_from_fragment(soup, text)
    row_numbers = _parse_result_row_numbers(soup)
    if row_numbers:
        return total, row_numbers[0], row_numbers[-1]
    return total, 0, 0


def _parse_total_from_fragment(soup: BeautifulSoup, text: str) -> int:
    total_input = soup.select_one("#totalResultadoAbaRetornoFiltro-A")
    if total_input is not None:
        raw_value = str(total_input.get("value") or "")
        if raw_value.isdigit():
            return int(raw_value)
    match = re.search(r"Ac[oó]rd[aã]os\((\d+)\)", text, re.I)
    if match:
        return int(match.group(1))
    return 0


def _parse_result_row_numbers(soup: BeautifulSoup) -> list[int]:
    numbers: list[int] = []
    for strong in soup.select("tr.fundocinza1 td.ementaClass strong"):
        match = re.search(r"\d+", strong.get_text(" ", strip=True))
        if match:
            numbers.append(int(match.group(0)))
    if numbers:
        return numbers
    for strong in soup.select("td.ementaClass strong"):
        match = re.search(r"\d+", strong.get_text(" ", strip=True))
        if match:
            numbers.append(int(match.group(0)))
    return numbers


def _looks_like_cjsg_results(html: str) -> bool:
    diagnostic = diagnose_cjsg_access(html)
    if diagnostic.has_result_container or diagnostic.has_download_links:
        return True
    soup = BeautifulSoup(html, "html.parser")
    total, start, end = _parse_pagination(soup.get_text(" ", strip=True), soup=soup)
    return total > 0 and start > 0 and end >= start


def _extract_labeled_fields(container: Any) -> dict[str, str]:
    labels: dict[str, str] = {}
    for row in container.select("tr.ementaClass2"):
        strong = row.find("strong")
        if strong is None:
            continue
        label = _normalize_label(strong.get_text(" ", strip=True))
        full_text = row.get_text(" ", strip=True)
        value = full_text.replace(strong.get_text(" ", strip=True), "", 1).strip(" :\xa0")
        if label and value:
            labels[label] = value
    text = container.get_text("\n", strip=True)
    for label in ("Data de Registro", "Data de Publicação", "Data de julgamento"):
        match = re.search(rf"{label}\s*:\s*(\d{{2}}/\d{{2}}/\d{{4}})", text, re.I)
        if match:
            labels[_normalize_label(label)] = match.group(1)
    return labels


def _extract_summary(container: Any, cd_acordao: str) -> str | None:
    text_area = container.select_one(f"#textAreaDados_{cd_acordao}")
    if text_area is not None:
        return text_area.get_text(" ", strip=True) or None
    candidates = [
        row.get_text(" ", strip=True) for row in container.select("tr.ementaClass, tr.ementaClass2")
    ]
    joined = " ".join(candidates)
    return joined or None


def _split_class_subject(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    if "/" not in value:
        return value.strip(), None
    case_class, subject = value.split("/", 1)
    return case_class.strip(), subject.strip()


def _normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.replace(":", "")).strip().lower()


def extract_cjsg_document_text(html: str) -> tuple[str, dict[str, Any]]:
    """Extract readable text and audit metadata from a public CJSG document page."""

    warnings: list[str] = []
    stripped = html.strip()
    raw_lowered = stripped.lower()
    if stripped.startswith("%PDF"):
        warnings.append(
            "CJSG returned PDF bytes; NanoJuris preserves metadata but does not parse PDF text yet."
        )
        return "", {
            "document_title": "TJSP/CJSG inteiro teor em PDF",
            "source_content_type": "application/pdf",
            "access_status": AccessStatus.PUBLIC.value,
            "text_characters": 0,
            "warnings": warnings,
        }
    access_status = AccessStatus.PUBLIC
    if (
        "verificarloginarquivo" in raw_lowered
        or "usuariologadonocasserver" in raw_lowered
        or "j_spring_cas_security_check" in raw_lowered
        or "sajcas/login" in raw_lowered
    ):
        access_status = AccessStatus.LOGIN_REQUIRED
        warnings.append("CJSG document response is a login/access verification page.")

    soup = BeautifulSoup(html, "html.parser")
    for element in soup.select("script, style, noscript, iframe, object"):
        element.decompose()
    title = _document_title(soup)
    candidates = [
        "#documento",
        "#divDocumento",
        "#conteudoDocumento",
        "#corpoDocumento",
        ".documento",
        ".inteiroTeor",
        "body",
    ]
    text = ""
    for selector in candidates:
        candidate_element = soup.select_one(selector)
        if candidate_element is None:
            continue
        text = _normalize_document_text(candidate_element.get_text("\n", strip=True))
        if text:
            break
    if not text:
        text = _normalize_document_text(soup.get_text("\n", strip=True))
    lowered = text.lower()
    if "captcha" in lowered or "recaptcha" in lowered:
        access_status = AccessStatus.ACCESS_CONTROL_REQUIRED
        warnings.append("CJSG document response contains captcha/access-control text.")
    if len(text) < 120:
        warnings.append("CJSG document text is unusually short for a full-text decision.")
    return text, {
        "document_title": title,
        "source_content_type": "text/html",
        "access_status": access_status.value,
        "text_characters": len(text),
        "warnings": warnings,
    }


def extract_cjsg_document_text_bytes(content: bytes) -> tuple[str, dict[str, Any]]:
    """Extract CJSG content without replacing the bytes used for auditing."""

    if content.startswith(b"%PDF"):
        return extract_cjsg_document_text("%PDF-raw-document")
    return extract_cjsg_document_text(content.decode("utf-8", errors="replace"))


def _document_title(soup: BeautifulSoup) -> str:
    heading = soup.select_one("h1, h2, h3, title")
    if heading is None:
        return "TJSP/CJSG inteiro teor"
    text = _normalize_document_text(heading.get_text(" ", strip=True))
    return text or "TJSP/CJSG inteiro teor"


def _normalize_document_text(text: str) -> str:
    normalized_lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in normalized_lines if line)


def _looks_like_access_control(html: str) -> bool:
    return diagnose_cjsg_access(html).access_control_required


def diagnose_cjsg_access(html: str) -> CjsgAccessDiagnostic:
    """Classify public TJSP/CJSG response signals without solving access controls."""

    lowered = html.lower()
    return CjsgAccessDiagnostic(
        has_result_container="divdadosresultado" in lowered or "tdresultados" in lowered,
        has_download_links="downloadementa" in lowered,
        has_search_form="consultacompletaform" in lowered or "consultasimplesform" in lowered,
        has_recaptcha_field="recaptcha_response_token" in lowered,
        has_uuid_captcha_field="uuidcaptcha" in lowered,
        has_recaptcha_widget="g-recaptcha" in lowered,
        has_access_control_route="captchacontroleacesso" in lowered,
        has_login_script="verificarlogin" in lowered or "sajcas" in lowered,
        has_empty_session="emptysession.jsp" in lowered or "empty session" in lowered,
    )
