"""TJSP CJSG public jurisprudence provider."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, replace
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from nanojuris.adaptive_selectors import USE_DEFAULT_MEMORY, resilient_find_all
from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.documents import build_canonical_document, extract_text
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
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

_TJSP_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
)
_ESAJ_HEADERS = {
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


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
        host = urlparse(self.config.tjsp_cjsg_url).hostname or ""
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
        self._pending_access_diagnostic: str | None = None
        # Metadata from the most recent shared-transport response is copied
        # into the page trace.  Keeping it on the provider preserves the
        # existing parser contract while making live provenance auditable.
        self._last_http_metadata: dict[str, Any] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_cjsg_scope(query, court="TJSP", source_label="TJSP/CJSG")
        submit_endpoint = "/resultadoCompleta.do"
        payload = self._build_payload(query)
        # e-SAJ treats the POST as a form submission/acknowledgement.  The
        # result HTML is returned by trocaDePagina.do, including for page 1.
        # Keeping this two-step flow is required to establish the public
        # result session and mirrors the Juscraper contract.
        # The POST is an acknowledgement; the result (and access-control
        # decision) is authoritative only on the subsequent page GET.
        self._request_text("POST", submit_endpoint, data=payload, skip_access_diagnostic=True)
        decision_type = self._first_decision_type(payload)
        first_endpoint = f"/trocaDePagina.do?tipoDeDecisao={quote(decision_type)}&pagina=1"
        first_html = self._request_text(
            "GET",
            first_endpoint,
            headers={
                "Accept": "text/html; charset=latin1;",
                "Referer": urljoin(
                    self.config.tjsp_cjsg_url.rstrip("/") + "/", submit_endpoint.lstrip("/")
                ),
            },
        )
        endpoint = first_endpoint
        html = first_html
        trace_query: dict[str, Any] = {
            "payload": payload,
            "tipoDeDecisao": decision_type,
            "pagina": 1,
        }
        conversation_id = _extract_conversation_id(first_html)
        if query.page > 1 and _looks_like_cjsg_results(html):
            endpoint = f"/trocaDePagina.do?tipoDeDecisao={quote(decision_type)}&pagina={query.page}"
            if conversation_id:
                endpoint = f"{endpoint}&conversationId={quote(conversation_id, safe='')}"
            html = self._request_text(
                "GET",
                endpoint,
                headers={
                    "Accept": "text/html; charset=latin1;",
                    "Referer": urljoin(
                        self.config.tjsp_cjsg_url.rstrip("/") + "/", submit_endpoint.lstrip("/")
                    ),
                },
            )
            trace_query["pagina"] = query.page
            trace_query["conversation_id_present"] = bool(conversation_id)
        elif query.page > 1:
            # The first-page response is still the authoritative diagnostic;
            # do not silently interpret an access/error page as page N.
            trace_query["conversation_id_present"] = bool(conversation_id)
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
            **self._last_http_metadata,
        )
        return parse_cjsg_results(
            html,
            query=query,
            trace=trace,
            base_url=self.config.tjsp_cjsg_url,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        cd_acordao, cd_foro = self._parse_precedent_id(precedent_id)
        # The anonymous e-SAJ flow first returns a small JavaScript page that
        # redirects to the same official endpoint with ``casChecked=true``.
        # Supplying that documented continuation flag directly avoids
        # stopping at the intermediate login-check page; it is not an
        # authentication or CAPTCHA bypass and remains within the public flow.
        endpoint = f"/getArquivo.do?cdAcordao={cd_acordao}&cdForo={cd_foro}&casChecked=true"
        response = self._request_response(
            "GET",
            endpoint,
            headers={
                # e-SAJ serves the public PDF continuation to a normal
                # browser user-agent.  This is the same public header profile
                # used by the upstream Juscraper client; it does not carry
                # credentials, cookies, CAPTCHA tokens or session bypasses.
                "User-Agent": _TJSP_CHROME_USER_AGENT,
                "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
            },
        )
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
            raw_bytes=raw_content,
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
            pagination_mode="page",
            completeness_contract="reported_total_and_page_window",
            full_text_access="detail_call",
            supports_cli=True,
            # A bounded public smoke on 2026-09-06 returned a textual CJSG
            # page. Keep it federated while preserving explicit challenge
            # errors when the source changes its access decision.
            supports_unified_search=True,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_suggestions=False,
            supports_live_tests=True,
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "types",
                "updated_from",
                "updated_to",
                "order_by",
            ],
            unsupported_filters=[
                "courts",
                "all_words",
                "any_words",
                "without_words",
                "rapporteur",
                "published_from",
                "published_to",
                "source_origin",
                "source_origins",
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
            ],
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "translated",
                "types": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "order_by": "translated",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "courts": "unsupported",
                "all_words": "unsupported",
                "any_words": "unsupported",
                "without_words": "unsupported",
                "rapporteur": "unsupported",
                "published_from": "unsupported",
                "published_to": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
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
            },
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
            "dados.pesquisarComSinonimos": "S",
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
            "dados.dtRegistroInicio": "",
            "dados.dtRegistroFim": "",
            "dados.dtPublicacaoInicio": "",
            "dados.dtPublicacaoFim": "",
            "dados.origensSelecionadas": "T",
            "tipoDecisaoSelecionados": mapped_types,
            "dados.ordenarPor": self._map_order_by(query.order_by),
            # The public TJSP form names this field ``ordenacao``.  Keep the
            # legacy alias above for backwards-compatible fixtures; sending
            # the canonical field matches Juscraper's request contract.
            "dados.ordenacao": self._map_order_by(query.order_by),
        }

    def _request_text(self, method: str, path: str, **kwargs: Any) -> str:
        configured_ua = self.config.user_agent
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": (
                _TJSP_CHROME_USER_AGENT
                if configured_ua == NanoJurisConfig().user_agent
                else configured_ua
            ),
        }
        headers.update(_ESAJ_HEADERS)
        headers.update(kwargs.pop("headers", {}) or {})
        try:
            response = self._request_response(method, path, headers=headers, **kwargs)
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJSP/CJSG request failed: {exc}") from exc
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJSP/CJSG request failed: {exc}") from exc

        return decode_cjsg_response_text(response)

    def _request_response(self, method: str, path: str, **kwargs: Any):
        url = urljoin(self.config.tjsp_cjsg_url.rstrip("/") + "/", path.lstrip("/"))
        skip_access_diagnostic = bool(kwargs.pop("skip_access_diagnostic", False))
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "User-Agent": self.config.user_agent,
            **kwargs.pop("headers", {}),
        }
        request = TransportRequest(
            source=self.name,
            operation=f"cjsg_{method.lower()}",
            method=method,
            url=url,
            headers=headers,
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
                    "TJSP/CJSG requires captcha or another access-control step "
                    f"({self._pending_access_diagnostic})"
                ) from exc
            raise
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJSP/CJSG request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJSP/CJSG transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        # Capture transport facts before any access/error classification so a
        # successful result page carries HTTP status, final URL, content hash,
        # byte count and latency.  These values are intentionally limited to
        # response metadata; request bodies and credentials are never stored.
        self._last_http_metadata = {
            "http_status": status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": (
                "ok" if status_code is not None and 200 <= status_code < 300 else "http_error"
            ),
        }
        if status_code is None:
            raise SourceUnavailableError("TJSP/CJSG transport returned no HTTP status")

        if status_code == 429:
            raise RateLimitDetectedError("TJSP/CJSG returned HTTP 429")
        content_type = response.headers.get("Content-Type", "")
        if "pdf" in content_type.lower() or _response_bytes(response).startswith(b"%PDF"):
            return response
        text = decode_cjsg_response_text(response)
        diagnostic = diagnose_cjsg_access(text)
        if skip_access_diagnostic:
            self._pending_access_diagnostic = (
                diagnostic.summary() if diagnostic.access_control_required else None
            )
        else:
            self._pending_access_diagnostic = None
        if status_code == 404 and diagnostic.has_empty_session:
            raise AccessControlRequiredError(
                f"TJSP/CJSG requires an active public search session ({diagnostic.summary()})"
            )
        if status_code >= 500:
            raise SourceUnavailableError(f"TJSP/CJSG returned HTTP {status_code}")
        if status_code >= 400:
            raise SourceUnavailableError(f"TJSP/CJSG rejected request with HTTP {status_code}")
        if diagnostic.access_control_required and not skip_access_diagnostic:
            raise AccessControlRequiredError(
                "TJSP/CJSG requires captcha or another access-control step "
                f"({diagnostic.summary()})"
            )
        return response

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
    memory: Any = USE_DEFAULT_MEMORY,
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
    page_text = soup.get_text(" ", strip=True)
    explicit_empty = _looks_like_cjsg_empty_results(soup)
    filters_applied = _cjsg_filters_applied(query)
    # The ementa anchors carry the identifiers; relocate them by structure if
    # the source renames ``a.downloadEmenta`` (recorded on the trace).
    anchors = (
        []
        if explicit_empty
        else resilient_find_all(
            result_root or soup,
            "a.downloadEmenta",
            name="ementa_anchor",
            source=source,
            trace=trace,
            memory=memory,
        )
    )
    if explicit_empty:
        return SearchPage(
            source=source,
            total=0,
            start=0,
            end=0,
            page=query.page,
            page_size=query.page_size,
            results=[],
            source_trace=trace,
            is_complete=True,
            completeness_reason="A fonte declarou explicitamente que nao ha resultados.",
            # The source emitted an explicit zero-result marker.  This is
            # authoritative zero, distinct from an omitted/unknown total.
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.EMPTY,
            filters_applied=filters_applied,
        )
    if result_root is None and not anchors:
        raise ParserContractChangedError(f"{source_label} result container not found")

    total, start, end = _parse_pagination(page_text, soup=soup)
    results: list[JurisprudenceResult] = []
    seen: set[tuple[str, str]] = set()
    for anchor in anchors:
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
            publication_date=labels.get("data de publicação") or labels.get("data de publicacao"),
            access_status=AccessStatus.PUBLIC,
            # CJSG/e-SAJ is a fixed second-degree state-court collection.
            # Populate the canonical scope on every row instead of leaving
            # degree/branch/collection implicit in the provider name.
            degree="second",
            instance="second",
            branch="state",
            authority=court,
            collection="CJSG",
            document_type="acordao",
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
                "data_publicacao": labels.get("data de publicação")
                or labels.get("data de publicacao"),
                "labels": labels,
            },
        )
        results.append(result)

    if not results and total is not None and total > 0:
        raise ParserContractChangedError(f"{source_label} parser found total results but no items")
    limited_results = results[: query.page_size]
    complete, reason = page_completeness(
        reported_total=total,
        start=start or (1 if limited_results else 0),
        returned=len(limited_results),
        total_is_authoritative=total is not None,
    )

    return SearchPage(
        source=source,
        total=total if total is not None else len(results),
        start=start or (1 if results else 0),
        end=(start or 1) + len(limited_results) - 1 if limited_results else 0,
        page=query.page,
        page_size=query.page_size,
        results=limited_results,
        source_trace=trace,
        is_complete=complete,
        completeness_reason=reason,
        total_known=total is not None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if limited_results else ExtractionStatus.EMPTY,
        filters_applied=filters_applied,
    )


def _cjsg_filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    """Describe e-SAJ form fields actually represented in a request."""

    translated = {
        "number": query.number,
        "exact_phrase": query.exact_phrase,
        "case_class": query.case_class,
        "judging_body": query.judging_body,
        "updated_from": query.updated_from,
        "updated_to": query.updated_to,
        "published_from": query.published_from,
        "published_to": query.published_to,
        "types": query.types,
        "order_by": query.order_by,
    }
    applied = {name: "translated" for name, value in translated.items() if value}
    if query.text:
        applied["text"] = "native"
    for name, value in (
        ("degree", query.degree),
        ("instance", query.instance),
        ("branch", query.branch),
        ("authority", query.authority),
        ("collection", query.collection),
    ):
        if value:
            applied[name] = "validated_scope"
    return applied


def _validate_cjsg_scope(
    query: JurisprudenceQuery,
    *,
    court: str,
    source_label: str,
) -> None:
    """Reject identity scopes that the e-SAJ CJSG route cannot satisfy.

    The e-SAJ endpoint is a fixed second-degree state-court collection.  It
    is better to fail explicitly for a first-degree or foreign-court query
    than to send the request and return a misleading result set.  Empty
    values remain accepted for backwards compatibility with the generic
    search API.
    """

    degree = str(query.degree or "").strip().casefold()
    if degree and degree not in {"second", "segundo", "segundo_grau", "2", "2o", "2º"}:
        raise QueryRejectedError(
            f"{source_label} only supports second-degree jurisprudence; "
            f"received degree={query.degree!r}"
        )
    instance = str(query.instance or "").strip().casefold()
    if instance and instance not in {"second", "segundo", "segundo_grau", "2", "2o", "2º"}:
        raise QueryRejectedError(
            f"{source_label} only supports second-degree jurisprudence; "
            f"received instance={query.instance!r}"
        )
    branch = str(query.branch or "").strip().casefold()
    if branch and branch not in {"state", "estadual", "estadual_public"}:
        raise QueryRejectedError(
            f"{source_label} only supports state-court jurisprudence; "
            f"received branch={query.branch!r}"
        )
    authority = str(query.authority or "").strip().casefold()
    if authority and authority not in {court.casefold(), source_label.split("/", 1)[0].casefold()}:
        raise QueryRejectedError(
            f"{source_label} cannot query authority={query.authority!r}; use {court}"
        )
    collection = str(query.collection or "").strip().casefold()
    if collection and collection not in {"cjsg", "jurisprudencia", "e-saj"}:
        raise QueryRejectedError(
            f"{source_label} only supports the CJSG collection; "
            f"received collection={query.collection!r}"
        )


def fetch_cjsg_page(
    provider: Any,
    query: JurisprudenceQuery,
    *,
    payload_builder: Any,
    base_url: str,
    source: str,
    court: str,
    id_prefix: str,
    source_label: str,
) -> SearchPage:
    """Fetch one CJSG page through the source's public session flow.

    CJSG/e-SAJ uses the initial search to establish the public result session
    and a separate ``trocaDePagina.do`` request for subsequent pages. Keeping
    both requests on the provider's session is required by the source
    contract; it is not an access-control bypass.
    """

    _validate_cjsg_scope(query, court=court, source_label=source_label)
    initial_query = query if query.page == 1 else replace(query, page=1)
    payload = payload_builder(initial_query)
    # The POST only submits the form.  e-SAJ serves the actual first page from
    # trocaDePagina.do, and the same session must be used for every request.
    # The POST response is only an acknowledgement; Juscraper deliberately
    # ignores its HTML and diagnoses access controls on the authoritative GET.
    provider._request_text(
        "POST", "/resultadoCompleta.do", data=payload, skip_access_diagnostic=True
    )
    selected = payload.get("tipoDecisaoSelecionados")
    if isinstance(selected, list) and selected:
        decision_type = str(selected[0])
    else:
        decision_type = str(payload.get("tipoDeDecisao") or "A")
    first_endpoint = f"/trocaDePagina.do?tipoDeDecisao={quote(decision_type)}&pagina=1"
    submit_url = urljoin(base_url.rstrip("/") + "/", "resultadoCompleta.do")
    request_headers = {
        "Accept": "text/html; charset=latin1;",
        "Referer": submit_url,
    }
    first_html = provider._request_text("GET", first_endpoint, headers=request_headers)
    endpoint = first_endpoint
    html = first_html
    trace_query: dict[str, Any] = {
        "payload": payload,
        "tipoDeDecisao": decision_type,
        "pagina": 1,
    }
    if query.page > 1 and _looks_like_cjsg_results(first_html):
        endpoint = f"/trocaDePagina.do?tipoDeDecisao={quote(decision_type)}&pagina={query.page}"
        html = provider._request_text("GET", endpoint, headers=request_headers)
        trace_query["pagina"] = query.page
    metadata = getattr(provider, "_last_http_metadata", {}) or {}
    trace = SourceTrace(
        provider=source,
        endpoint=endpoint.split("?", 1)[0],
        query=trace_query,
        source_url=urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/")),
        limitations=[
            f"Fonte HTML publica {source_label} sujeita a mudancas de layout.",
            "A paginacao usa a sessao publica e a rota trocaDePagina.do da fonte.",
            "O provider nao tenta contornar captcha, login ou controles de acesso.",
        ],
        **metadata,
    )
    return parse_cjsg_results(
        html,
        query=query,
        trace=trace,
        base_url=base_url,
        source=source,
        court=court,
        id_prefix=id_prefix,
        source_label=source_label,
    )


def decode_cjsg_response_text(response: requests.Response) -> str:
    """Decode CJSG HTML using the source-declared charset or detected encoding."""

    headers = getattr(response, "headers", {})
    content_type = headers.get("Content-Type", "")
    # SharedHttpClient exposes an immutable byte body rather than a mutable
    # requests.Response.  Decode it here so the parser keeps the same
    # windows-1252/UTF-8 behavior for both transport paths.
    transport_body = getattr(response, "body", None)
    if transport_body is not None:
        charset: str | None = None
        match = re.search(r"charset\s*=\s*['\"]?([^;\s'\"]+)", content_type, re.I)
        if match:
            charset = match.group(1)
        if charset:
            try:
                return bytes(transport_body).decode(charset, errors="replace")
            except LookupError:
                pass
        raw = bytes(transport_body)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("windows-1252", errors="replace")
    if "charset=" not in content_type.lower():
        response.encoding = (
            getattr(response, "apparent_encoding", None)
            or getattr(response, "encoding", None)
            or "windows-1252"
        )
    elif response.encoding is None:
        response.encoding = getattr(response, "apparent_encoding", None) or "utf-8"
    return response.text


def _extract_conversation_id(html: str) -> str:
    """Extract the public e-SAJ conversation id without exposing its value."""

    soup = BeautifulSoup(html, "html.parser")
    field = soup.find("input", attrs={"name": "conversationId"})
    if field is None:
        return ""
    value = field.get("value")
    return str(value or "").strip()


def _looks_like_cjsg_empty_results(soup: BeautifulSoup) -> bool:
    """Recognize the e-SAJ empty-result variants without masking failures.

    Some e-SAJ installations return only ``Acórdãos(0)`` and a message such
    as ``Não foi encontrado nenhum resultado`` instead of the normal result
    container.  This is a valid zero-result response, not a parser contract
    failure.  The checks intentionally require an explicit zero-result signal
    so an arbitrary HTML/error page is never converted into an empty page.
    """

    text = soup.get_text(" ", strip=True).casefold()
    if "não foi encontrado nenhum resultado" in text:
        return True
    if "nao foi encontrado nenhum resultado" in text:
        return True
    if "nenhum resultado encontrado" in text:
        return True
    return bool(re.search(r"ac[oó]rd[aã]os?\s*\(\s*0\s*\)", text))


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
    source_content_type = bundle.texts[0].get("source_content_type") if bundle.texts else None
    extracted_content_type = bundle.texts[0].get("content_type") if bundle.texts else None
    content_type = str(source_content_type or extracted_content_type or "text/plain")
    metadata = dict(bundle.raw or {})
    access_status = _metadata_access_status(metadata)
    warnings = [str(item) for item in metadata.get("warnings") or []]
    extraction_status = (
        ExtractionStatus.PARTIAL if warnings or not content.strip() else ExtractionStatus.COMPLETE
    )
    raw_content = bundle.raw_bytes or content.encode("utf-8")
    return build_canonical_document(
        document_id=document_id,
        source=source,
        document_type="acordao",
        content=raw_content,
        content_type=content_type,
        title=str(metadata.get("document_title") or title),
        text_override=content,
        url=bundle.source_trace.source_url if bundle.source_trace else None,
        access_status=access_status,
        source_trace=bundle.source_trace,
        raw_metadata=metadata,
        parser=parser,
        extraction_status_override=extraction_status,
        extraction_warnings=warnings,
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

    body = getattr(response, "body", None)
    if body is not None:
        return bytes(body)
    content = getattr(response, "content", None)
    if content is not None:
        return bytes(content)
    return str(getattr(response, "text", "")).encode("utf-8")


def _parse_pagination(
    text: str, *, soup: BeautifulSoup | None = None
) -> tuple[int | None, int, int]:
    match = re.search(r"Resultados\s+(\d+)\s+a\s+(\d+)\s+de\s+(\d+)", text, re.I)
    if match:
        start, end, total = (int(match.group(index)) for index in (1, 2, 3))
        return total, start, end
    if soup is None:
        return None, 0, 0
    fragment_total = _parse_total_from_fragment(soup, text)
    row_numbers = _parse_result_row_numbers(soup)
    if row_numbers:
        return fragment_total, row_numbers[0], row_numbers[-1]
    return fragment_total, 0, 0


def _parse_total_from_fragment(soup: BeautifulSoup, text: str) -> int | None:
    total_input = soup.select_one("#totalResultadoAbaRetornoFiltro-A")
    if total_input is not None:
        raw_value = str(total_input.get("value") or "")
        if raw_value.isdigit():
            return int(raw_value)
    match = re.search(r"Ac[oó]rd[aã]os\((\d+)\)", text, re.I)
    if match:
        return int(match.group(1))
    return None


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
    return total is not None and total > 0 and start > 0 and end >= start


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
    """Extract CJSG content without replacing the bytes used for auditing.

    e-SAJ commonly returns a PDF while keeping an HTML content type.  Delegate
    PDF parsing to the shared bounded extractor instead of treating every PDF
    as an opaque placeholder; scanned PDFs remain explicitly unsupported until
    OCR is opted in by the caller.
    """

    if content.startswith(b"%PDF"):
        text, status, warnings, transformations = extract_text(content, "application/pdf")
        metadata = {
            "source_content_type": "application/pdf",
            "extraction_status": status.value,
            "text_characters": len(text or ""),
            "warnings": list(warnings),
            "transformations": list(transformations),
        }
        return text or "", metadata
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
