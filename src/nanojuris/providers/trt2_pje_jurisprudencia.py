"""Diagnostic adapter for the public TRT2 PJe jurisprudence surface.

The TRT2 portal exposes its options and aggregation catalog publicly, but the
document search currently returns a human challenge (``tokenDesafio`` and an
image/audio challenge) before any decision records.  This adapter deliberately
implements the public transport and error contract so callers can inspect the
source without mistaking the challenge for an empty search.  It is opt-in and
never attempts to solve, replay, or bypass the challenge.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests

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
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

BASE_PATH = "/jurisprudencia"
OPTIONS_PATH = "/juris-backend/api/opcoes"
FILTERS_PATH = "/juris-backend/api/filtros"
DOCUMENTS_PATH = "/juris-backend/api/documentos"
MAX_RESPONSE_BYTES = 2_000_000
MAX_PAGE_SIZE = 20


class Trt2PjeJurisprudenciaProvider(JurisprudenceProvider):
    """Expose TRT2 options/catalog and preserve the result challenge state."""

    name = "trt2_pje_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.trt2_pje_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
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
        self._results: dict[str, JurisprudenceResult] = {}

    @property
    def base_url(self) -> str:
        return self.config.trt2_pje_jurisprudencia_url.rstrip("/")

    def get_parameters(self) -> dict[str, Any]:
        """Return the public options catalog without exposing challenge data."""

        response = self._request("GET", OPTIONS_PATH)
        data = _json(response)
        if not isinstance(data, dict):
            raise ParserContractChangedError("TRT2 opcoes nao retornaram um objeto JSON")
        # Public keys are useful for diagnostics; challenge/token material is
        # intentionally omitted even if a future response includes it.
        allowed = {
            "regional",
            "pjeConsultaUrl",
            "linkLogoUrl",
            "captchaOption",
            "recaptchaSiteKey",
            "recaptchaUrl",
            "habilitaPsiu",
            "version",
        }
        return {key: data[key] for key in allowed if key in data}

    def get_filter_catalog(self) -> dict[str, Any]:
        """Read the public aggregation catalog used by the official UI."""

        response = self._request(
            "POST",
            FILTERS_PATH,
            json_body=_initial_filter_payload(self.config.user_agent),
            idempotent=False,
        )
        data = _json(response)
        if not isinstance(data, dict):
            raise ParserContractChangedError("TRT2 filtros nao retornaram um objeto JSON")
        return data

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        page_size = min(max(int(query.page_size or 10), 1), MAX_PAGE_SIZE)
        payload = _build_payload(query, page_size, user_agent=self.config.user_agent)
        response = self._request("POST", DOCUMENTS_PATH, json_body=payload, idempotent=False)
        data = _json(response)
        if not isinstance(data, dict):
            raise ParserContractChangedError("TRT2 documentos nao retornaram um objeto JSON")
        if _is_challenge(data):
            raise AccessControlRequiredError(
                "TRT2/PJe exige desafio humano antes de liberar documentos; "
                "nenhum token foi gerado ou reutilizado"
            )
        documents = data.get("documents")
        if not isinstance(documents, list):
            raise ParserContractChangedError("TRT2 resposta nao possui a lista documents")
        safe_payload = {key: value for key, value in payload.items() if key != "token"}
        trace = _trace(self.name, response, safe_payload)
        results = [_parse_document(item, trace) for item in documents if isinstance(item, dict)]
        if any(result is None for result in results):
            raise ParserContractChangedError("TRT2 documento nao possui identificador estavel")
        typed = [result for result in results if result is not None]
        self._results.update({result.id: result for result in typed})
        raw_total = data.get("total")
        if not isinstance(raw_total, int) or raw_total < 0:
            raw_total = data.get("hits")
        reported_total: int | None = (
            raw_total if isinstance(raw_total, int) and raw_total >= 0 else None
        )
        total_known = reported_total is not None
        unconfirmed_empty = not typed and not total_known
        return SearchPage(
            source=self.name,
            total=reported_total if reported_total is not None else len(typed),
            total_known=total_known,
            start=(query.page - 1) * page_size + 1 if typed else 0,
            end=(query.page - 1) * page_size + len(typed) if typed else 0,
            page=query.page,
            page_size=page_size,
            results=typed,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=bool(reported_total is not None and len(typed) >= reported_total),
            completeness_reason=None if total_known else "a fonte nao informou total autoritativo",
            ordering="source_default",
            access_status=AccessStatus.PUBLIC,
            extraction_status=(
                ExtractionStatus.PARTIAL if unconfirmed_empty else ExtractionStatus.COMPLETE
            ),
        )

    def search_authorized(self, query: JurisprudenceQuery, *, challenge_token: str) -> SearchPage:
        """Search one page with a token obtained by a human in the official UI.

        TRT2 names the transient challenge value ``token`` in the JSON
        payload.  The provider never creates, solves, persists or reuses it;
        callers must supply a fresh value for this one bounded request.
        """

        _validate_query(query)
        if not challenge_token.strip():
            raise AccessControlRequiredError(
                "TRT2 exige token de desafio fornecido por interacao humana"
            )
        page_size = min(max(int(query.page_size or 10), 1), MAX_PAGE_SIZE)
        payload = _build_payload(query, page_size, user_agent=self.config.user_agent)
        payload["token"] = challenge_token
        response = self._request("POST", DOCUMENTS_PATH, json_body=payload, idempotent=False)
        data = _json(response)
        if not isinstance(data, dict):
            raise ParserContractChangedError("TRT2 documentos autorizados nao retornaram objeto")
        if _is_challenge(data):
            raise AccessControlRequiredError("TRT2 rejeitou o token de desafio fornecido")
        documents = data.get("documents")
        if not isinstance(documents, list):
            raise ParserContractChangedError("TRT2 resposta autorizada nao possui documents")
        safe_payload = {key: value for key, value in payload.items() if key != "token"}
        trace = _trace(self.name, response, safe_payload)
        results = [_parse_document(item, trace) for item in documents if isinstance(item, dict)]
        if any(result is None for result in results):
            raise ParserContractChangedError("TRT2 documento autorizado nao possui identificador")
        typed = [result for result in results if result is not None]
        self._results.update({result.id: result for result in typed})
        total = data.get("total")
        if isinstance(total, int) and total >= 0:
            total_known = True
            total_value = total
        else:
            total = data.get("hits")
            if isinstance(total, int) and total >= 0:
                total_known = True
                total_value = total
            else:
                total_known = False
                total_value = len(typed)
        unconfirmed_empty = not typed and not total_known
        return SearchPage(
            source=self.name,
            total=total_value,
            total_known=total_known,
            start=(query.page - 1) * page_size + 1 if typed else 0,
            end=(query.page - 1) * page_size + len(typed) if typed else 0,
            page=query.page,
            page_size=page_size,
            results=typed,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=bool(total_known and len(typed) >= total_value),
            completeness_reason=None if total_known else "a fonte nao informou total autoritativo",
            ordering="source_default",
            access_status=AccessStatus.PUBLIC,
            extraction_status=(
                ExtractionStatus.PARTIAL if unconfirmed_empty else ExtractionStatus.COMPLETE
            ),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise SourceUnavailableError("TRT2 detalhe disponivel somente apos uma busca observada")
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
            raw={
                "access_status": (
                    result.access_status.value if result.access_status is not None else None
                )
            },
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRT2 PJe jurisprudencia (diagnostico opt-in)",
            source_url=f"{self.base_url}{BASE_PATH}/",
            category="court_jurisprudence",
            search_modes=["text", "case_number", "filters", "authorized_human_challenge"],
            document_types=["acordao", "decisao"],
            content_formats=["json", "html"],
            canonical_records=["JurisprudenceResult"],
            semantic_discriminator="authority=TRT2;branch=labor;degree=second;collection=JURISPRUDENCIA",
            extracted_fields=[
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
            endpoints=[f"GET {OPTIONS_PATH}", f"POST {FILTERS_PATH}", f"POST {DOCUMENTS_PATH}"],
            supports_full_text=False,
            full_text_access="access_blocked",
            supports_unified_search=False,
            opt_in_unified_search=True,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="offset_unverified",
            max_remote_page_size=MAX_PAGE_SIZE,
            completeness_contract="unknown_until_challenge_passed",
            supported_filters=[
                "text",
                "number",
                "all_words",
                "any_words",
                "without_words",
                "exact_phrase",
                "case_class",
                "judging_body",
                "rapporteur",
                "published_from",
                "published_to",
                "degree",
                "instance",
                "document_type",
                "decision_type",
                "types",
            ],
            unsupported_filters=[
                "courts",
                "updated_from",
                "updated_to",
                "judgment_date_from",
                "judgment_date_to",
                "party_name",
                "lawyer_name",
                "oab",
            ],
            filter_semantics={
                "text": "native_when_challenge_is_satisfied",
                "number": "native_when_challenge_is_satisfied",
                "all_words": "native_when_challenge_is_satisfied",
                "any_words": "native_when_challenge_is_satisfied",
                "without_words": "native_when_challenge_is_satisfied",
                "exact_phrase": "translated_to_andField",
                "case_class": "native_when_challenge_is_satisfied",
                "judging_body": "native_when_challenge_is_satisfied",
                "rapporteur": "native_when_challenge_is_satisfied",
                "published_from": "native_when_challenge_is_satisfied",
                "published_to": "native_when_challenge_is_satisfied",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "document_type": "native_when_challenge_is_satisfied",
                "decision_type": "translated_to_tipoDocumento",
                "types": "translated_to_tipoDocumento",
            },
            limitations=[
                "A rota de documentos retorna tokenDesafio/imagem na chamada publica atual.",
                "search_authorized aceita somente token fornecido pelo usuario na mesma chamada.",
                "Nenhum token, cookie, captcha ou sessao humana e persistido.",
                "A paginacao e o inteiro teor permanecem sem contrato reproduzivel.",
            ],
            responsible_use=[
                "Consultar apenas rotas oficiais e bounded.",
                "Nao resolver, contornar ou reutilizar desafios de acesso.",
            ],
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        idempotent: bool | None = None,
    ):
        response = self.transport.request(
            TransportRequest(
                source=self.name,
                operation="pje_request",
                method=method,
                url=f"{self.base_url}{path}",
                json_body=json_body,
                idempotent=(method.upper() == "GET" if idempotent is None else idempotent),
                headers={"Accept": "application/json"},
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TRT2 transporte indisponivel: {response.error_type or response.status.value}"
            )
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TRT2 retornou HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT2 retornou HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT2 retornou HTTP {status}")
        return response


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TRT2 exige termo, numero ou frase exata")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT2 PJe suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TRT2 PJe suporta somente segunda instancia")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT2 pertence ao ramo trabalhista")
    if query.authority and query.authority.casefold().replace("-", "") not in {
        "trt2",
        "trt 2",
    }:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TRT2")


def _build_payload(
    query: JurisprudenceQuery,
    page_size: int,
    *,
    user_agent: str = "",
) -> dict[str, Any]:
    """Compile the NanoJuris query into the payload used by TRT2's SPA.

    The public frontend sends a ``QUERY_INICIAL`` object to both ``/filtros``
    and ``/documentos``.  Keeping this shape is important even while the
    document endpoint is challenge-gated: it lets a legitimately authorized
    request use the same contract, and prevents a future 400 from being
    misclassified as an empty result.
    """

    text_terms = _query_terms(query.all_words or query.text)
    if query.exact_phrase:
        text_terms = [query.exact_phrase.strip()]
    if query.number:
        # TRT2 has no separate public number field.  The official UI searches
        # the same ``andField`` channel, so preserve the number as one exact
        # token rather than claiming a native number filter.
        text_terms = _append_unique(text_terms, query.number.strip())

    document_types = list(query.types)
    for value in (query.document_type, query.decision_type):
        if value and value not in document_types:
            document_types.append(value)

    payload = _initial_filter_payload(
        user_agent,
        page_size=page_size,
        page=query.page,
    )
    payload.update(
        {
            "andField": text_terms or None,
            "orField": _query_terms(query.any_words) or None,
            "notField": _query_terms(query.without_words) or None,
            "dataPublicacaoStart": query.published_from or None,
            "dataPublicacaoEnd": query.published_to or None,
            "classeJudicial": [query.case_class] if query.case_class else None,
            "magistrado": [query.rapporteur] if query.rapporteur else None,
            "orgaoJulgador": [query.judging_body] if query.judging_body else None,
            "tipoDocumento": document_types or None,
            "ordenarPor": _order_field(query.order_by),
        }
    )
    return payload


def _initial_filter_payload(
    user_agent: str,
    *,
    page_size: int = 0,
    page: int = 1,
) -> dict[str, Any]:
    """Return the public ``QUERY_INICIAL`` shape observed in the TRT2 SPA."""

    return {
        "timestamp": "##timestamp##",
        "browserIpAddress": "##browserIpAddress##",
        "browserVia": "##browserVia##",
        "name": "query parameters",
        "dataPublicacaoStart": None,
        "dataPublicacaoEnd": None,
        "DataDistribuicaoStart": None,
        "DataDistribuicaoEnd": None,
        "ordenarPor": "relevancia",
        "andField": None,
        "orField": None,
        "notField": None,
        "andFieldEmenta": None,
        "andFieldDispositivo": None,
        "anoProcesso": None,
        "assunto": None,
        "classeJudicial": None,
        "magistrado": None,
        "meioTramitacao": None,
        "orgaoJulgador": None,
        "orgaoJulgadorColegiado": None,
        "tipoDocumento": None,
        "browserUserAgent": user_agent,
        "browserReferer": "",
        "paginationSize": page_size,
        "paginationPosition": page,
        "fragmentSize": 0,
        "token": None,
    }


def _query_terms(value: str) -> list[str]:
    """Match the UI's conservative quoted-term tokenizer."""

    if not value:
        return []
    return [quoted or bare for quoted, bare in re.findall(r'"([^"\\]+)"|(\S+)', value)]


def _append_unique(values: list[str], value: str) -> list[str]:
    if value and value not in values:
        values.append(value)
    return values


def _order_field(order_by: str) -> str:
    normalized = order_by.casefold().replace("-", "_").replace(" ", "_")
    return "dataPublicacao" if normalized in {"date", "data", "data_publicacao"} else "relevancia"


def _is_challenge(data: dict[str, Any]) -> bool:
    return bool(data.get("tokenDesafio") or data.get("imagem") or data.get("audio"))


def _parse_document(item: dict[str, Any], trace: SourceTrace) -> JurisprudenceResult | None:
    identifier = item.get("id") or item.get("codigo") or item.get("numero")
    if identifier is None:
        return None
    summary = item.get("ementa") or item.get("resumo") or item.get("texto")
    full_text = item.get("inteiroTeor") or item.get("textoDecisao")
    return JurisprudenceResult(
        id=f"trt2-pje-{identifier}",
        source="trt2_pje_jurisprudencia",
        court="TRT2",
        type=str(item.get("tipoDocumento") or item.get("tipo") or "acordao"),
        number=str(item.get("numeroProcesso") or item.get("numero") or "") or None,
        summary=str(summary).strip() if summary else None,
        full_text=str(full_text).strip() if full_text else None,
        rapporteur=item.get("magistrado") or item.get("relator"),
        judgment_date=item.get("dataJulgamento"),
        publication_date=item.get("dataPublicacao"),
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw={
            key: value
            for key, value in item.items()
            if key.casefold() not in {"token", "tokendesafio", "captchatoken", "resposta"}
        },
        case_class=item.get("classeJudicial") or item.get("classe"),
        degree="second",
        instance="second",
        branch="labor",
        authority="TRT2",
        collection="JURISPRUDENCIA",
        document_type=item.get("tipoDocumento") or item.get("tipo"),
        document_url=item.get("url") or item.get("documentUrl"),
    )


def _json(response: Any) -> Any:
    try:
        return response.json()
    except (ValueError, TypeError) as exc:
        raise ParserContractChangedError("TRT2 nao retornou JSON valido") from exc


def _trace(source: str, response: Any, payload: dict[str, Any]) -> SourceTrace:
    return SourceTrace(
        provider=source,
        endpoint=f"POST {DOCUMENTS_PATH}",
        query={key: value for key, value in payload.items() if value is not None},
        source_url=str(response.final_url or ""),
        http_status=response.status_code,
        final_url=response.final_url,
        content_type=response.content_type,
        content_sha256=response.content_sha256,
        response_bytes=response.byte_size,
        elapsed_ms=response.elapsed_ms,
        retrieval_status="ok",
        limitations=["resultado sujeito a desafio humano do portal TRT2"],
    )


__all__ = ["Trt2PjeJurisprudenciaProvider"]
