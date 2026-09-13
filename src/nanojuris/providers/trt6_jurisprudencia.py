"""Diagnostic binding for the official TRT6 jurisprudence surfaces.

TRT6 exposes two public entry points: a legacy ``Consulta de Acórdãos`` form
and a newer PJe jurisprudence SPA.  Both advertise appellate jurisprudence,
but the bounded public search requires a Google reCAPTCHA response.  This
adapter records that boundary explicitly and never treats the challenge as an
empty result or attempts to solve/replay it.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from nanojuris.config import NanoJurisConfig, configure_requests_session
from nanojuris.errors import (
    AccessControlRequiredError,
    ParserContractChangedError,
    QueryRejectedError,
    RateLimitDetectedError,
    SourceUnavailableError,
)
from nanojuris.models import (
    AccessStatus,
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

PJE_PATH = "/juris-backend/api"
PJE_OPTIONS_PATH = f"{PJE_PATH}/opcoes"
PJE_FILTERS_PATH = f"{PJE_PATH}/filtros"
PJE_DOCUMENTS_PATH = f"{PJE_PATH}/documentos"
LEGACY_PATH = "/acordaos/"
LEGACY_SEARCH_PATH = "/acordaos/pesquisar"
MAX_RESPONSE_BYTES = 2_000_000
LEGACY_PAGE_SIZE = 10
_PROCESS_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
_TOTAL_RE = re.compile(r"Foram encontrados\s+([\d.]+)\s+resultados", re.I)


class Trt6JurisprudenciaProvider(JurisprudenceProvider):
    """Expose TRT6 public metadata and preserve its CAPTCHA boundary."""

    name = "trt6_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._pje_transport = self._transport_for(self.config.trt6_jurisprudencia_url)
        self._legacy_transport = self._transport_for(self.config.trt6_acordaos_url)
        self._results: dict[str, JurisprudenceResult] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        # The legacy official portal exposes a bounded HTML search contract
        # without a challenge for ordinary public queries.  Prefer it over
        # the newer PJe SPA, whose document endpoint remains challenge-gated.
        payload = _build_legacy_payload(query)
        response = self._request_legacy("POST", LEGACY_SEARCH_PATH, data=payload)
        html = response.body.decode("iso-8859-1", errors="replace")
        trace = _legacy_trace(response, payload)
        results = parse_trt6_legacy_results(
            html, trace=trace, base_url=self.config.trt6_acordaos_url
        )
        total, total_known = _parse_legacy_total(html)
        explicit_empty = not results and _looks_like_legacy_empty(html)
        if not results and not explicit_empty:
            raise ParserContractChangedError(
                "TRT6 resposta legada nao possui resultados nem vazio autoritativo"
            )
        # ``SearchPage.total`` is always an integer.  Keep the explicit
        # ``total_known`` bit separate while providing a safe fallback for
        # legacy responses that omit the count altogether.
        effective_total = total if total is not None else len(results)
        self._results.update({result.id: result for result in results})
        start = ((query.page - 1) * LEGACY_PAGE_SIZE) + 1 if results else 0
        end = start + len(results) - 1 if results else 0
        return SearchPage(
            source=self.name,
            total=effective_total,
            total_known=total_known,
            start=start,
            end=end,
            page=query.page,
            page_size=LEGACY_PAGE_SIZE,
            results=results,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=True if explicit_empty else (False if results else None),
            completeness_reason=(
                None
                if explicit_empty
                else "TRT6 expôs somente a janela HTML solicitada; total remoto ausente"
                if not total_known
                else "TRT6 limita a janela a 1.000 registros e exige paginação adicional"
            ),
            ordering="source_default",
            access_status=AccessStatus.PUBLIC,
            extraction_status=(
                ExtractionStatus.EMPTY if explicit_empty else ExtractionStatus.COMPLETE
            ),
        )

    def search_authorized(self, query: JurisprudenceQuery, *, recaptcha_token: str) -> SearchPage:
        """Search one page with a token produced by a human in the official UI.

        TRT6 uses reCAPTCHA v3 (``captchaOption=1``).  The browser obtains a
        short-lived token and places it in the JSON body.  NanoJuris accepts a
        caller-supplied token for this single bounded request only; it never
        solves, stores, replays or sends an empty token.
        """

        _validate_query(query)
        if not recaptcha_token.strip():
            raise AccessControlRequiredError(
                "TRT6 exige token reCAPTCHA fornecido por interacao humana"
            )
        page_size = min(max(int(query.page_size or 10), 1), 20)
        payload = _build_pje_payload(query)
        payload["paginationSize"] = page_size
        payload["paginationPosition"] = max(int(query.page), 1)
        payload["token"] = recaptcha_token
        response = self._request_pje("POST", PJE_DOCUMENTS_PATH, json_body=payload)
        try:
            body = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError(
                "TRT6 PJe autorizado nao retornou JSON valido"
            ) from exc
        if not isinstance(body, dict):
            raise ParserContractChangedError("TRT6 PJe autorizado retornou envelope inesperado")
        message = str(body.get("erro") or body.get("mensagem") or "")
        if "recaptcha" in message.casefold() or "tokenDesafio" in body:
            raise AccessControlRequiredError("TRT6 rejeitou o token reCAPTCHA fornecido")
        documents = body.get("documents")
        if not isinstance(documents, list):
            raise ParserContractChangedError(
                "TRT6 resposta autorizada nao possui a lista documents"
            )
        safe_payload = {key: value for key, value in payload.items() if key != "token"}
        trace = _trt6_trace(response, safe_payload)
        parsed = [_parse_pje_document(item, trace) for item in documents if isinstance(item, dict)]
        if any(result is None for result in parsed):
            raise ParserContractChangedError(
                "TRT6 documento autorizado nao possui identificador estavel"
            )
        results = [result for result in parsed if result is not None]
        self._results.update({result.id: result for result in results})
        raw_total = body.get("hits")
        if isinstance(raw_total, int) and raw_total >= 0:
            total_known = True
            total_value = raw_total
        else:
            raw_total = body.get("total")
            if isinstance(raw_total, int) and raw_total >= 0:
                total_known = True
                total_value = raw_total
            else:
                total_known = False
                total_value = len(results)
        unconfirmed_empty = not results and not total_known
        return SearchPage(
            source=self.name,
            total=total_value,
            total_known=total_known,
            start=(query.page - 1) * page_size + 1 if results else 0,
            end=(query.page - 1) * page_size + len(results) if results else 0,
            page=query.page,
            page_size=page_size,
            results=results,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=bool(total_known and len(results) >= total_value),
            completeness_reason=(None if total_known else "TRT6 nao informou total autoritativo"),
            ordering="source_default",
            access_status=AccessStatus.PUBLIC,
            extraction_status=(
                ExtractionStatus.PARTIAL if unconfirmed_empty else ExtractionStatus.COMPLETE
            ),
        )

    def get_parameters(self) -> dict[str, Any]:
        """Return the public SPA options without challenge material."""

        response = self._request_pje("GET", PJE_OPTIONS_PATH)
        try:
            body = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TRT6 opcoes nao retornaram JSON valido") from exc
        if not isinstance(body, dict):
            raise ParserContractChangedError("TRT6 opcoes nao retornaram um objeto JSON")
        allowed = {
            "regional",
            "captchaOption",
            "recaptchaSiteKey",
            "version",
            "pjeConsultaUrl",
        }
        return {
            "source_url": self.config.trt6_jurisprudencia_url,
            "legacy_url": self.config.trt6_acordaos_url,
            "status": "metadata_public_search_requires_recaptcha",
            "metadata": {key: body[key] for key in allowed if key in body},
        }

    def get_filter_catalog(self) -> dict[str, Any]:
        """Inspect the public filter catalog without running a document search.

        TRT6 exposes the available classes, subjects, judges and document types
        through a separate metadata endpoint.  It is useful for capability
        discovery, but it is deliberately not treated as search evidence: the
        document endpoint still requires a user-generated reCAPTCHA token.
        """

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "browserIpAddress": "",
            "browserVia": "",
            "name": "query parameters",
            "ordenarPor": "relevancia",
            "paginationSize": 0,
            "paginationPosition": 1,
            "fragmentSize": 0,
        }
        response = self._request_pje("POST", PJE_FILTERS_PATH, json_body=payload)
        try:
            body = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TRT6 filtros nao retornaram JSON valido") from exc
        return parse_trt6_filter_catalog(body, response_bytes=len(response.body))

    def get_legacy_form(self) -> dict[str, Any]:
        """Inspect the legacy form contract without submitting a challenge."""

        response = self._request_legacy("GET", LEGACY_PATH)
        text = response.body.decode("utf-8", errors="replace")
        fields = [
            name
            for name in (
                "numeroCnj",
                "numeroTst",
                "texto",
                "redator",
                "orgaoJulgador",
                "dataInicio",
                "dataFim",
            )
            if f'name="{name}"' in text
        ]
        return {
            "source_url": self.config.trt6_acordaos_url,
            "search_url": f"{self.config.trt6_acordaos_url.rstrip('/')}{LEGACY_SEARCH_PATH}",
            "method": "POST",
            "fields": fields,
            "requires_recaptcha": "g-recaptcha" in text.casefold()
            or "recaptcha" in text.casefold(),
            "status": "form_public_search_requires_recaptcha",
        }

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise SourceUnavailableError(
                "TRT6 detalhe disponivel somente apos uma busca autorizada observada"
            )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[
                {
                    "content": result.full_text or result.summary or "",
                    "content_type": "text/html",
                }
            ],
            source_trace=result.source_trace,
            raw={"access_status": result.access_status.value if result.access_status else None},
        )

    def get_capabilities(self) -> ProviderCapabilities:
        filters = [
            "text",
            "number",
            "case_class",
            "judging_body",
            "rapporteur",
            "published_from",
            "published_to",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TRT6 Jurisprudencia",
            source_url=self.config.trt6_acordaos_url,
            category="court_jurisprudence",
            search_modes=["text", "case_number", "filters", "full_text"],
            document_types=["acordao"],
            content_formats=["json", "html"],
            canonical_records=["JurisprudenceResult"],
            semantic_discriminator="authority=TRT6;branch=labor;degree=second;collection=JURISPRUDENCIA",
            extracted_fields=[
                "authority",
                "branch",
                "degree",
                "instance",
                "case_number",
                "case_class",
                "judging_body",
                "rapporteur",
                "judgment_date",
                "publication_date",
                "summary",
                "full_text",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                f"GET {PJE_OPTIONS_PATH}",
                f"POST {PJE_FILTERS_PATH}",
                f"POST {PJE_DOCUMENTS_PATH}",
                f"GET {LEGACY_PATH}",
                f"POST {LEGACY_SEARCH_PATH}",
            ],
            supports_full_text=True,
            full_text_access="inline_result_text",
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="offset",
            max_remote_page_size=LEGACY_PAGE_SIZE,
            completeness_contract="bounded_html_window_total_when_reported",
            supported_filters=[
                "text",
                "number",
                "published_from",
                "published_to",
                "rapporteur",
                "judging_body",
                "authority",
                "branch",
                "degree",
                "instance",
                "collection",
                "document_type",
            ],
            unsupported_filters=[
                "case_class",
                "party_name",
                "updated_from",
                "updated_to",
                "judgment_date_from",
                "judgment_date_to",
                "legal_area",
                "decision_type",
            ],
            filter_semantics={
                **{name: "native" for name in filters},
                "text": "native",
                "number": "native",
                "published_from": "native",
                "published_to": "native",
                "rapporteur": "native",
                "judging_body": "native",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "case_class": "unsupported",
                "party_name": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
                "legal_area": "unsupported",
                "decision_type": "unsupported",
            },
            limitations=[
                (
                    "A rota legada retorna dez cards por pagina e limita pesquisas amplas "
                    "a mil registros."
                ),
                (
                    "O total pode nao ser reportado para consultas exatas; isso permanece "
                    "total_unknown."
                ),
                "A SPA PJe continua challenge-gated e nao e usada pela busca federada.",
            ],
            responsible_use=[
                "Usar somente rotas oficiais e sondas publicas bounded.",
                "Solicitar API/exportacao oficial sem CAPTCHA ao TRT6 quando necessario.",
            ],
        )

    def _transport_for(self, base_url: str) -> SharedHttpClient:
        host = urlparse(base_url).hostname or ""
        return SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_RESPONSE_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    def _request_pje(self, method: str, path: str, *, json_body: Any = None) -> Any:
        return self._request(self._pje_transport, method, path, json_body=json_body)

    def _request_legacy(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        data: Any = None,
    ) -> Any:
        return self._request(self._legacy_transport, method, path, json_body=json_body, data=data)

    def _request(
        self,
        transport: SharedHttpClient,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        data: Any = None,
    ) -> Any:
        response = transport.request(
            TransportRequest(
                source=self.name,
                operation="trt6_request",
                method=method,
                url=(
                    f"{self.config.trt6_jurisprudencia_url.rstrip('/')}{path}"
                    if transport is self._pje_transport
                    else f"{self.config.trt6_acordaos_url.rstrip('/')}{path}"
                ),
                data=data,
                json_body=json_body,
                headers={"Accept": "application/json, text/html"},
                idempotent=method.upper() == "GET",
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TRT6 transporte indisponivel: {response.error_type or response.status.value}"
            )
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TRT6 retornou HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT6 retornou HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT6 retornou HTTP {status}")
        return response


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TRT6 exige termo, numero ou frase exata")
    if query.authority and query.authority.casefold().replace("-", "") not in {"trt6", "trt 6"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TRT6")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT6 pertence ao ramo trabalhista")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2", "2nd"}:
        raise QueryRejectedError("TRT6 suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2", "2nd"}:
        raise QueryRejectedError("TRT6 suporta somente segunda instancia")


def parse_trt6_filter_catalog(payload: Any, *, response_bytes: int | None = None) -> dict[str, Any]:
    """Return a compact, non-document summary of the TRT6 filter metadata."""

    if not isinstance(payload, dict):
        raise ParserContractChangedError("TRT6 filtros retornaram envelope inesperado")
    aggregations = payload.get("aggregations")
    if not isinstance(aggregations, list) or not aggregations:
        raise ParserContractChangedError("TRT6 filtros nao retornaram agregacoes")
    fields: list[dict[str, int | str]] = []
    for aggregation in aggregations:
        if not isinstance(aggregation, dict):
            raise ParserContractChangedError("TRT6 agregacao possui schema inesperado")
        field_name = aggregation.get("fieldName")
        values = aggregation.get("list")
        if not isinstance(field_name, str) or not field_name.strip():
            raise ParserContractChangedError("TRT6 agregacao nao informa fieldName")
        if not isinstance(values, list):
            raise ParserContractChangedError(
                f"TRT6 agregacao {field_name!r} nao informa lista de valores"
            )
        fields.append({"field_name": field_name, "value_count": len(values)})
    result: dict[str, Any] = {
        "status": "metadata_public",
        "hits": payload.get("hits"),
        "document_count": len(payload.get("documents", []))
        if isinstance(payload.get("documents"), list)
        else None,
        "fields": fields,
        "search_results_observed": False,
        "recaptcha_required_for_documents": True,
    }
    if response_bytes is not None:
        result["response_bytes"] = response_bytes
    return result


def _build_legacy_payload(query: JurisprudenceQuery) -> dict[str, str]:
    """Translate the canonical query to the public TRT6 legacy form."""

    number = query.number.strip()
    cnj = number if _PROCESS_RE.fullmatch(number) else ""
    return {
        "numeroCnj": cnj,
        "numeroTst": "" if cnj else number,
        "texto": (query.exact_phrase or query.text).strip(),
        "redator": query.rapporteur.strip(),
        "orgaoJulgador": query.judging_body.strip(),
        "dataInicio": (query.published_from or query.judgment_date_from).strip(),
        "dataFim": (query.published_to or query.judgment_date_to).strip(),
        "pagina": str(max(int(query.page), 1)),
    }


def parse_trt6_legacy_results(
    html: str, *, trace: SourceTrace, base_url: str
) -> list[JurisprudenceResult]:
    """Parse the bounded public TRT6 ``/acordaos/pesquisar`` HTML page."""

    soup = BeautifulSoup(html, "html.parser")
    panels = soup.select("#acordaos .panel")
    if not panels:
        if _looks_like_legacy_empty(html):
            return []
        raise ParserContractChangedError("TRT6 resposta legada nao possui cards de acordaos")
    results: list[JurisprudenceResult] = []
    for panel in panels:
        if not isinstance(panel, Tag):
            continue
        process_text = panel.get_text(" ", strip=True)
        process_match = _PROCESS_RE.search(process_text)
        link = panel.select_one('a[href*="exibirInteiroTeor"]')
        if process_match is None or link is None:
            raise ParserContractChangedError("TRT6 card sem processo CNJ ou link de inteiro teor")
        metadata = _trt6_legacy_metadata(panel)
        summary_node = panel.select_one("p.ementa")
        summary = (
            _clean_legacy_text(summary_node.get_text(" ", strip=True)) if summary_node else None
        )
        if summary:
            summary = re.sub(r"^EMENTA:\s*", "", summary, flags=re.I).strip() or None
        decision = _trt6_legacy_decision(panel)
        full_text = "\n\n".join(value for value in (summary, decision) if value) or None
        href = str(link.get("href") or "")
        document_url = urljoin(base_url.rstrip("/") + "/acordaos/", href)
        document_id = _document_id_from_href(href)
        results.append(
            JurisprudenceResult(
                id=f"trt6-acordao-{document_id}",
                source="trt6_jurisprudencia",
                court="TRT6",
                type="acordao",
                number=process_match.group(0),
                summary=summary,
                full_text=full_text,
                rapporteur=metadata.get("rapporteur"),
                judgment_date=metadata.get("judgment_date"),
                publication_date=metadata.get("publication_date"),
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                raw={
                    **metadata,
                    "document_id": document_id,
                    "document_url": document_url,
                    "download_url": urljoin(
                        base_url.rstrip("/") + "/acordaos/",
                        f"baixarInteiroTeor?documento={document_id}",
                    ),
                },
                case_class=metadata.get("case_class"),
                judging_body=metadata.get("judging_body"),
                degree="second",
                instance="second",
                branch="labor",
                authority="TRT6",
                collection="JURISPRUDENCIA",
                document_type="acordao",
                document_url=document_url,
            )
        )
    return results


def _trt6_legacy_metadata(panel: Tag) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in panel.select(".panel-heading .span6"):
        label = item.select_one("strong")
        if label is None:
            continue
        key = _ascii_fold(_clean_legacy_text(label.get_text(" ", strip=True))).rstrip(":")
        if key.startswith("classe processual"):
            mapped = "case_class"
        elif key.startswith("redator"):
            mapped = "rapporteur"
        elif "orga" in key and "colegiado" in key:
            mapped = "judging_body"
        elif "data de public" in key:
            mapped = "publication_date"
        elif "data de julgamento" in key:
            mapped = "judgment_date"
        else:
            mapped = None
        if mapped is None:
            continue
        full = _clean_legacy_text(item.get_text(" ", strip=True))
        prefix = _clean_legacy_text(label.get_text(" ", strip=True))
        value = full[len(prefix) :].lstrip(" :") if full.startswith(prefix) else full
        if value:
            values[mapped] = value
    return values


def _trt6_legacy_decision(panel: Tag) -> str | None:
    for strong in panel.select("p > strong"):
        label = _ascii_fold(_clean_legacy_text(strong.get_text(" ", strip=True))).rstrip(":")
        if not label.startswith("decis"):
            continue
        candidate = strong.parent.find_next_sibling("p") if strong.parent else None
        if candidate is not None:
            text = _clean_legacy_text(candidate.get_text(" ", strip=True))
            return text or None
    return None


def _document_id_from_href(href: str) -> str:
    match = re.search(r"documento=(\d+)", href)
    if not match:
        raise ParserContractChangedError("TRT6 link de inteiro teor sem identificador")
    return match.group(1)


def _parse_legacy_total(html: str) -> tuple[int | None, bool]:
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    match = _TOTAL_RE.search(text)
    if not match:
        return None, False
    return int(match.group(1).replace(".", "")), True


def _looks_like_legacy_empty(html: str) -> bool:
    folded = BeautifulSoup(html, "html.parser").get_text(" ", strip=True).casefold()
    return any(
        marker in folded
        for marker in (
            "nenhum acórdão foi encontrado",
            "nenhum acordao foi encontrado",
            "nenhum resultado encontrado",
            "não foram encontrados resultados",
            "nao foram encontrados resultados",
        )
    )


def _clean_legacy_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _legacy_trace(response: Any, payload: dict[str, str]) -> SourceTrace:
    return SourceTrace(
        provider="trt6_jurisprudencia",
        endpoint=f"POST {LEGACY_SEARCH_PATH}",
        query=dict(payload),
        source_url=str(response.final_url or ""),
        http_status=response.status_code,
        final_url=response.final_url,
        content_type=response.content_type,
        content_sha256=response.content_sha256,
        response_bytes=response.byte_size,
        elapsed_ms=response.elapsed_ms,
        retrieval_status="ok",
        limitations=[
            (
                "A fonte retorna uma janela HTML de dez cards e limita pesquisas amplas "
                "a mil registros."
            ),
            (
                "O total remoto pode estar ausente para pesquisas exatas; a completude "
                "permanece explícita."
            ),
        ],
    )


def _build_pje_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    return {
        "timestamp": "##timestamp##",
        "browserIpAddress": "##browserIpAddress##",
        "browserVia": "##browserVia##",
        "name": "query parameters",
        "ordenarPor": "relevancia",
        "andField": [query.exact_phrase or query.text or query.number],
        "browserUserAgent": "NanoJuris",
        "browserReferer": "https://pje.trt6.jus.br/jurisprudencia/",
        "paginationSize": min(max(int(query.page_size or 10), 1), 20),
        "paginationPosition": max(int(query.page), 1),
        "fragmentSize": 512,
        "token": "",
    }


def _parse_pje_document(item: dict[str, Any], trace: SourceTrace) -> JurisprudenceResult | None:
    """Parse only fields observed in the public TRT6 PJe document envelope.

    The portal's metadata endpoint is stable, but the document response is
    challenge-gated.  The parser therefore accepts the field aliases used by
    the Angular view and rejects a row without a stable source identifier.
    """

    identifier = _first_value(
        item,
        "id",
        "codigo",
        "idDocumento",
        "documentId",
        "identificador",
        "numeroProcesso",
    )
    if identifier is None or not str(identifier).strip():
        return None
    summary = _first_value(item, "ementa", "resumo", "fragment", "highlight", "texto")
    full_text = _first_value(item, "inteiroTeor", "textoDecisao", "fullText", "content")
    document_url = _first_value(item, "url", "documentUrl", "urlDocumento", "link")
    document_type = _first_value(item, "tipoDocumento", "tipo") or "acordao"
    return JurisprudenceResult(
        id=f"trt6-pje-{identifier}",
        source="trt6_jurisprudencia",
        court="TRT6",
        type=str(document_type),
        number=_as_optional_text(_first_value(item, "numeroProcesso", "numero")),
        summary=_as_optional_text(summary),
        full_text=_as_optional_text(full_text),
        rapporteur=_as_optional_text(_first_value(item, "magistrado", "relator")),
        judgment_date=_as_optional_text(_first_value(item, "dataJulgamento", "dataAssinatura")),
        publication_date=_as_optional_text(
            _first_value(item, "dataPublicacao", "dataDisponibilizacao")
        ),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={
            key: value
            for key, value in item.items()
            if key.casefold() not in {"token", "tokendesafio", "captchatoken", "resposta"}
        },
        case_class=_as_optional_text(_first_value(item, "classeJudicial", "classe")),
        judging_body=_as_optional_text(
            _first_value(item, "orgaoJulgador", "orgaoJulgadorColegiado")
        ),
        degree="second",
        instance="second",
        branch="labor",
        authority="TRT6",
        collection="JURISPRUDENCIA",
        document_type=str(document_type),
        document_url=_as_optional_text(document_url),
    )


def _first_value(item: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = item.get(name)
        if value is not None and (not isinstance(value, str) or value.strip()):
            return value
    return None


def _as_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _trt6_trace(response: Any, payload: dict[str, Any]) -> SourceTrace:
    return SourceTrace(
        provider="trt6_jurisprudencia",
        endpoint=f"POST {PJE_DOCUMENTS_PATH}",
        query={key: value for key, value in payload.items() if value is not None},
        source_url=str(response.final_url or ""),
        http_status=response.status_code,
        final_url=response.final_url,
        content_type=response.content_type,
        content_sha256=response.content_sha256,
        response_bytes=response.byte_size,
        elapsed_ms=response.elapsed_ms,
        retrieval_status="ok",
        limitations=["resultado obtido mediante token reCAPTCHA fornecido pelo usuario"],
    )


__all__ = ["Trt6JurisprudenciaProvider"]
