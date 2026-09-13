"""TJRJ EJURIS public second-degree jurisprudence provider.

The public EJURIS portal is an ASP.NET form followed by a JSON XHR.  The
recaptcha widget displayed by the form is decorative for this route; no token
is generated or bypassed by this adapter.  The implementation intentionally
keeps this surface separate from the TJRJ eproc provider.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

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
from nanojuris.pagination import page_completeness
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import (
    TransportPolicy,
    TransportRequest,
    TransportResponse,
    TransportStatus,
)

FORM_PATH = "/ejuris/ConsultarJurisprudencia.aspx"
RESULT_PATH = "/EJURIS/ProcessarConsJurisES.aspx/ExecutarConsultarJurisprudencia"
FIELD_PREFIX = "ctl00$ContentPlaceHolder1$"
PAGE_SIZE = 10
CNJ_PATTERN = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
ASP_DATE_PATTERN = re.compile(r"/Date\((-?\d+)\)/")
HIDDEN_PATTERN = re.compile(
    r'<input[^>]*name="(?P<name>__VIEWSTATE|__VIEWSTATEGENERATOR|__EVENTVALIDATION|'
    r'ctl00\$ContentPlaceHolder1\$hfListaPalavrasBloqueadas)"[^>]*value="(?P<value>[^"]*)"',
    re.IGNORECASE,
)
YEAR_SELECT_PATTERN = re.compile(
    r'<select[^>]*name="ctl00\$ContentPlaceHolder1\$cmbAnoInicio".*?</select>',
    re.IGNORECASE | re.DOTALL,
)
YEAR_OPTION_PATTERN = re.compile(r'<option[^>]*value="(?P<value>\d{4})"', re.IGNORECASE)


class TjrjEjurisProvider(JurisprudenceProvider):
    """Provider for TJRJ's public EJURIS appellate jurisprudence search."""

    name = "tjrj_ejuris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http_metadata: dict[str, Any] = {}
        self._results: dict[str, JurisprudenceResult] = {}
        host = urlparse(self.config.tjrj_ejuris_url).hostname or "www3.tjrj.jus.br"
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=16_000_000,
                # The ASP.NET form carries session-bound state.  Retrying a
                # POST could replay stale ViewState or an access challenge;
                # surface the bounded outcome instead.
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def base_url(self) -> str:
        return self.config.tjrj_ejuris_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        self._validate_scope(query)
        if not any((query.text, query.exact_phrase, query.number)):
            raise QueryRejectedError("TJRJ EJURIS exige texto, frase exata ou número")

        form_url = urljoin(self.base_url + "/", FORM_PATH.lstrip("/"))
        form_response = self._request("GET", FORM_PATH)
        hidden = _extract_hidden_fields(form_response.text)
        default_year = _extract_default_year(form_response.text)
        data = _build_form_payload(
            hidden,
            query,
            year_from=_query_year(query.published_from or query.updated_from) or default_year,
            year_to=_query_year(query.published_to or query.updated_to) or default_year,
        )
        self._request("POST", FORM_PATH, data=data)

        page_index = query.page - 1
        response = self._request(
            "POST",
            RESULT_PATH,
            json={"numPagina": page_index, "pageSeq": "0"},
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        try:
            envelope = response.json()
        except ValueError as exc:
            raise ParserContractChangedError("TJRJ EJURIS XHR não retornou JSON") from exc
        if not isinstance(envelope, dict) or not isinstance(envelope.get("d"), dict):
            raise ParserContractChangedError("TJRJ EJURIS XHR não possui envelope d")

        payload = envelope["d"]
        trace = SourceTrace(
            provider=self.name,
            endpoint=RESULT_PATH,
            # The ASP.NET form contains per-session hidden state and a
            # CAPTCHA field.  Those values are transport credentials/state,
            # not query semantics, and must never enter a persisted trace.
            query=_safe_trace_query(query, data),
            source_url=form_url,
            **self._last_http_metadata,
            limitations=[
                "O backend público fixa dez registros por página.",
                "O escopo desta superfície é exclusivamente origem 2 (segundo grau).",
                "O widget reCAPTCHA não é submetido nem contornado; "
                "o backend público não o valida nesta rota.",
            ],
        )
        return _parse_page(payload, query=query, trace=trace, store=self._results)

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise NotImplementedError(
                "O EJURIS não oferece detalhe estável por id fora da sessão de busca; "
                "execute a busca e use o resultado embutido."
            )
        text = result.full_text or result.summary or ""
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=result.rapporteur,
            texts=[{"type": result.document_type or result.type, "text": text}],
            source_trace=result.source_trace,
            raw={"source_id": precedent_id, "document_url": result.document_url},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        result = self._results.get(document_id)
        if result is None:
            raise NotImplementedError(
                "O EJURIS não possui endpoint de documento independente; "
                "o inteiro teor é entregue no resultado da sessão."
            )
        text = result.full_text or result.summary or ""
        content = text.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        return CanonicalDocument(
            id=document_id,
            source=self.name,
            document_type=result.document_type or result.type,
            content_type="text/plain",
            title=f"TJRJ EJURIS {result.type} {result.number or ''}".strip(),
            text=text or None,
            url=result.document_url,
            sha256=digest,
            byte_size=len(content),
            retrieved_at=result.retrieved_at,
            access_status=AccessStatus.PUBLIC,
            source_trace=result.source_trace,
            extraction_trace=ExtractionTrace(
                parser="tjrj_ejuris.inline_result",
                parser_version="1",
                status=ExtractionStatus.COMPLETE if text else ExtractionStatus.EMPTY,
                access_status=AccessStatus.PUBLIC,
                content_sha256=digest,
                content_bytes=len(content),
            ),
            raw_metadata=dict(result.raw),
        )

    def get_capabilities(self) -> ProviderCapabilities:
        unsupported = (
            "courts",
            "all_words",
            "any_words",
            "without_words",
            "rapporteur",
            "case_class",
            "judging_body",
            "legal_area",
            "source_origins",
            "fetch_details",
            "party_name",
            "party_document",
            "lawyer_name",
            "oab",
            "precatory_number",
            "police_document",
            "cda",
            "judgment_date_from",
            "judgment_date_to",
        )
        return ProviderCapabilities(
            source=self.name,
            display_name="TJRJ EJURIS Jurisprudência (CJSG)",
            source_url=self.base_url + FORM_PATH,
            category="court_jurisprudence",
            search_modes=["full_text", "summary", "case_number", "year", "decision_type"],
            document_types=["acordao", "decisao_monocratica"],
            content_formats=["html", "json"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="origem=2 (segundo grau)",
            extracted_fields=[
                "case_number",
                "case_class",
                "decision_type",
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
            endpoints=[f"GET {FORM_PATH}", f"POST {FORM_PATH}", f"POST {RESULT_PATH}"],
            supports_full_text=True,
            supports_cli=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            supports_catalog=False,
            supports_live_tests=True,
            pagination_mode="page",
            max_remote_page_size=PAGE_SIZE,
            completeness_contract="reported_total_and_page_window",
            full_text_access="inline_result_text",
            supported_filters=[
                "text",
                "exact_phrase",
                "number",
                "types",
                "document_type",
                "decision_type",
                "published_from",
                "published_to",
                "updated_from",
                "updated_to",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "source_origin",
            ],
            unsupported_filters=list(unsupported),
            filter_semantics={
                "text": "native",
                "exact_phrase": "translated",
                "number": "translated",
                "types": "translated",
                "document_type": "translated",
                "decision_type": "translated",
                "published_from": "translated",
                "published_to": "translated",
                "updated_from": "translated",
                "updated_to": "translated",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "source_origin": "translated",
                **{name: "unsupported" for name in unsupported},
            },
            limitations=[
                "O backend expõe somente ano para intervalo temporal.",
                "O inteiro teor é o texto sem formatação retornado no card; "
                "não há download separado promovido.",
                "A origem é fixada em 2 para impedir mistura com primeiro grau.",
            ],
            responsible_use=[
                "Respeitar o intervalo entre requisições e o limite de dez itens por página.",
                "Não enviar tokens de CAPTCHA nem tentar contornar controles de acesso.",
                "Preservar SourceTrace e os campos brutos do JSON oficial.",
            ],
        )

    def _validate_scope(self, query: JurisprudenceQuery) -> None:
        if query.degree and query.degree.casefold() not in {
            "second",
            "2",
            "segundo",
            "segundo grau",
        }:
            raise QueryRejectedError("TJRJ EJURIS é uma superfície exclusivamente de segundo grau")
        if query.instance and query.instance.casefold() not in {
            "second",
            "2",
            "segundo",
            "segundo grau",
        }:
            raise QueryRejectedError(
                "TJRJ EJURIS é uma superfície exclusivamente de segunda instância"
            )
        if query.branch and query.branch.casefold() not in {"state", "estadual"}:
            raise QueryRejectedError("TJRJ EJURIS pertence ao ramo estadual")
        if query.source_origin and query.source_origin.casefold() not in {
            "segundo grau",
            "second",
            "2",
            "2o grau",
            "2º grau",
        }:
            raise QueryRejectedError("TJRJ EJURIS usa exclusivamente origem de segundo grau")
        if query.authority and query.authority.casefold() not in {
            "tjrj",
            "tribunal de justiça do rio de janeiro",
        }:
            raise QueryRejectedError("autoridade incompatível com TJRJ EJURIS")

    def _request(self, method: str, path: str, **kwargs: Any) -> TransportResponse:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        headers = {
            "Accept": "application/json, text/html, */*",
            "User-Agent": self.config.user_agent,
        }
        headers.update(kwargs.pop("headers", {}))
        data = kwargs.pop("data", None)
        json_body = kwargs.pop("json", None)
        params = kwargs.pop("params", {})
        if kwargs:
            raise TypeError(f"unsupported TJRJ EJURIS transport arguments: {sorted(kwargs)}")
        request = TransportRequest(
            source=self.name,
            operation=f"{method.lower()}_{path.lstrip('/').replace('/', '_')}",
            method=method,
            url=url,
            params=params,
            data=data,
            json_body=json_body,
            headers=headers,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        try:
            response = self._transport.request(request)
        except (requests.RequestException, SourceUnavailableError) as exc:
            raise SourceUnavailableError(f"TJRJ EJURIS request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJRJ EJURIS transport failed: {response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TJRJ EJURIS transport returned no HTTP status")
        self._last_http_metadata = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if response.status_code < 400 else "error",
        }
        if response.status_code == 429:
            raise RateLimitDetectedError("TJRJ EJURIS retornou HTTP 429")
        if response.status_code in {401, 403}:
            raise AccessControlRequiredError(
                f"TJRJ EJURIS exige controle de acesso (HTTP {response.status_code})"
            )
        if response.status_code >= 500:
            raise SourceUnavailableError(f"TJRJ EJURIS retornou HTTP {response.status_code}")
        if response.status_code >= 400:
            raise SourceUnavailableError(f"TJRJ EJURIS rejeitou HTTP {response.status_code}")
        return response


def _extract_hidden_fields(html: str) -> dict[str, str]:
    return {match.group("name"): match.group("value") for match in HIDDEN_PATTERN.finditer(html)}


def _extract_default_year(html: str) -> str:
    block = YEAR_SELECT_PATTERN.search(html) or None
    values = YEAR_OPTION_PATTERN.findall(block.group(0) if block else html)
    return values[0] if values else str(datetime.now(timezone.utc).year)


def _query_year(value: str) -> str:
    match = re.search(r"(?:^|[-/])(\d{4})(?:$|[-/])", value or "")
    return match.group(1) if match else ""


def _safe_trace_query(query: JurisprudenceQuery, payload: dict[str, str]) -> dict[str, Any]:
    """Return only reproducible, non-secret query semantics for ``SourceTrace``.

    Hidden ASP.NET fields (VIEWSTATE, EVENTVALIDATION, session-bound
    allowlists) and challenge fields are deliberately excluded.  Traces may be
    retained in manifests and diagnostics, so they must remain safe to export.
    """

    prefix = FIELD_PREFIX
    return {
        "page": query.page,
        "page_size": PAGE_SIZE,
        "text": query.text or query.exact_phrase or query.number,
        "number": query.number,
        "types": list(query.types),
        "document_type": query.document_type,
        "decision_type": query.decision_type,
        "published_from": query.published_from,
        "published_to": query.published_to,
        "updated_from": query.updated_from,
        "updated_to": query.updated_to,
        "degree": query.degree or "second",
        "instance": query.instance or "second",
        "branch": query.branch or "state",
        "authority": query.authority or "TJRJ",
        "collection": query.collection or "CJSG",
        "origin": payload.get(f"{prefix}cmbOrigem", ""),
        "competencia": payload.get(f"{prefix}cmbCompetencia", ""),
        "year_from": payload.get(f"{prefix}cmbAnoInicio", ""),
        "year_to": payload.get(f"{prefix}cmbAnoFim", ""),
        "include_acordao": f"{prefix}chkAcordao" in payload,
        "include_decisao_monocratica": f"{prefix}chkDecMon" in payload,
    }


def _build_form_payload(
    hidden: dict[str, str],
    query: JurisprudenceQuery,
    *,
    year_from: str,
    year_to: str,
) -> dict[str, str]:
    prefix = FIELD_PREFIX
    text = query.text or query.exact_phrase or query.number
    payload = {
        "__EVENTTARGET": f"{prefix}btnPesquisar",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": hidden.get("__VIEWSTATE", ""),
        "__VIEWSTATEGENERATOR": hidden.get("__VIEWSTATEGENERATOR", ""),
        "__EVENTVALIDATION": hidden.get("__EVENTVALIDATION", ""),
        f"{prefix}hfListaPalavrasBloqueadas": hidden.get(f"{prefix}hfListaPalavrasBloqueadas", ""),
        f"{prefix}hfCodRamos": "",
        f"{prefix}hfCodMags": "",
        f"{prefix}hfCodOrgs": "",
        f"{prefix}txtTextoPesq": text,
        f"{prefix}cmbOrigem": "1",
        f"{prefix}cmbAnoInicio": year_from,
        f"{prefix}cmbAnoFim": year_to,
        f"{prefix}cmbCompetencia": "1",
        f"{prefix}cmbRamo": "",
        f"{prefix}cmbMagistrado": "",
        f"{prefix}chkAtivo": "on",
        f"{prefix}chkInativo": "on",
        f"{prefix}cmbOrgaoJulgador": "",
        f"{prefix}cmbTipNumeracao": "1",
        f"{prefix}txtNumeracao": query.number,
        f"{prefix}chkIntTeor": "on",
        f"{prefix}chkEmentario": "on",
        "g-recaptcha-response": "",
    }
    requested_types = [
        *query.types,
        *[value for value in (query.document_type, query.decision_type) if value],
    ]
    if not requested_types or any("acord" in value.casefold() for value in requested_types):
        payload[f"{prefix}chkAcordao"] = "on"
    if not requested_types or any(
        "monocrat" in value.casefold() or "decis" in value.casefold() for value in requested_types
    ):
        payload[f"{prefix}chkDecMon"] = "on"
    return payload


def _parse_page(
    payload: dict[str, Any],
    *,
    query: JurisprudenceQuery,
    trace: SourceTrace,
    store: dict[str, JurisprudenceResult],
) -> SearchPage:
    docs = payload.get("DocumentosConsulta")
    if not isinstance(docs, list):
        raise ParserContractChangedError("TJRJ EJURIS não retornou DocumentosConsulta")
    total_raw = payload.get("TotalDocs")
    try:
        total = int(str(total_raw))
    except (TypeError, ValueError):
        total = len(docs)
        total_known = False
    else:
        total_known = True
    results: list[JurisprudenceResult] = []
    for item in docs:
        if not isinstance(item, dict):
            continue
        result = _parse_result(item, trace=trace)
        if result is not None:
            results.append(result)
            store[result.id] = result
    if total > 0 and not results:
        raise ParserContractChangedError(
            "TJRJ EJURIS informou resultados mas nenhum item foi parseado"
        )
    page_size = PAGE_SIZE
    page_results = results[: query.page_size]
    start = ((query.page - 1) * page_size) + 1 if page_results else 0
    complete, reason = page_completeness(
        reported_total=total,
        start=start,
        returned=len(page_results),
        total_is_authoritative=total_known,
    )
    return SearchPage(
        source="tjrj_ejuris",
        total=total,
        start=start,
        end=start + len(page_results) - 1 if page_results else 0,
        page=query.page,
        page_size=page_size,
        results=page_results,
        source_trace=trace,
        pagination_mode="page",
        ordering="data_julgamento",
        is_complete=complete,
        completeness_reason=reason,
        total_known=total_known,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if results else ExtractionStatus.EMPTY,
        filters_applied={
            "degree": "validated_scope",
            "instance": "validated_scope",
            "branch": "validated_scope",
            "authority": "validated_scope",
            "collection": "validated_scope",
            "text": "native" if query.text else "not_requested",
            "exact_phrase": "translated" if query.exact_phrase else "not_requested",
            "number": "translated" if query.number else "not_requested",
            "source_origin": "translated" if query.source_origin else "not_requested",
        },
    )


def _parse_result(item: dict[str, Any], *, trace: SourceTrace) -> JurisprudenceResult | None:
    case_number = _first_text(item.get("NumProcCnj"), item.get("Processo"))
    if not case_number:
        return None
    source_id = str(item.get("CodDoc") or "").strip()
    if not source_id:
        source_id = hashlib.sha256(case_number.encode("utf-8")).hexdigest()[:16]
    full_text = _strip_html(item.get("TextoSemFormat") or item.get("Texto"))
    decision_type = _first_text(item.get("DescrTipDoc"), item.get("DescrRecurso")) or "decisao"
    result_trace = SourceTrace(
        provider=trace.provider,
        endpoint=trace.endpoint,
        query=trace.query,
        source_url=trace.source_url,
        limitations=trace.limitations,
        http_status=trace.http_status,
        final_url=trace.final_url,
        content_type=trace.content_type,
        content_sha256=trace.content_sha256,
        response_bytes=trace.response_bytes,
        elapsed_ms=trace.elapsed_ms,
        retrieval_status=trace.retrieval_status,
    )
    return JurisprudenceResult(
        id=f"tjrj-ejuris-{source_id}",
        source="tjrj_ejuris",
        court="TJRJ",
        type=decision_type,
        number=case_number,
        summary=full_text or None,
        full_text=full_text or None,
        rapporteur=_first_text(item.get("NomeMagRel")),
        judgment_date=_parse_asp_date(item.get("DtHrMov")),
        publication_date=_parse_asp_date(item.get("DtHrPubl")),
        updated_at=_parse_asp_date(item.get("DtHrMov")),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE if full_text else ExtractionStatus.EMPTY,
        source_trace=result_trace,
        raw={
            "source_id": source_id,
            "case_number": case_number,
            "old_number": item.get("NumAntigo"),
            "case_class": item.get("Classe") or item.get("DescrRecurso"),
            "judging_body": item.get("NomeOrgJulg"),
            "rapporteur": item.get("NomeMagRel"),
            "document_type": decision_type,
            "arq_ged": item.get("ArqGed"),
            "raw_document": item,
        },
        case_class=_first_text(item.get("Classe"), item.get("DescrRecurso")),
        judging_body=_first_text(item.get("NomeOrgJulg")),
        degree="second",
        instance="second",
        branch="state",
        authority="TJRJ",
        collection="CJSG",
        document_type=decision_type,
        source_origin="segundo grau",
        document_url=urljoin("https://www3.tjrj.jus.br/", FORM_PATH.lstrip("/")),
    )


def _parse_asp_date(value: Any) -> str | None:
    match = ASP_DATE_PATTERN.search(str(value or ""))
    if not match:
        return None
    try:
        millis = int(match.group(1))
        if millis <= 0:
            return None
        return datetime.fromtimestamp(millis / 1000, tz=timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _strip_html(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(BeautifulSoup(str(value), "html.parser").get_text(" ").split())


def _first_text(*values: Any) -> str | None:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return None
