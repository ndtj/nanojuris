"""TJAP Tucujuris jurisprudence adapter.

The public Tucujuris contract is kept here even though the endpoint currently
requires a server-validated Turnstile token.  A failed challenge is surfaced as
an access-control error; it is never interpreted as an empty search.
"""

from __future__ import annotations

import hashlib
from typing import Any

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
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider

BASE_URL = "https://tucujuris.tjap.jus.br/api/publico/consultar-jurisprudencia"
FILTER_CATALOG_URL = (
    "https://tucujuris.tjap.jus.br/api/publico/carregar-filtros-combo-jurisprudencia"
)
LAST_UPDATE_URL = "https://tucujuris.tjap.jus.br/api/publico/buscar-data-banco-dados-jurisprudencia"
FRONT_URL = (
    "https://tucujuris.tjap.jus.br/pages/consultar-jurisprudencia/consultar-jurisprudencia.html"
)
PAGE_SIZE = 20
NO_RESULTS = "nenhum resultado encontrado."


class TjapTucujurisProvider(JurisprudenceProvider):
    """Expose the documented TJAP REST contract with safe access semantics."""

    name = "tjap_tucujuris"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._results: dict[str, JurisprudenceResult] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        payload = _build_payload(query)
        response = self._request(payload)
        data = _json(response)
        message = str(data.get("mensagem") or "").strip()
        if str(data.get("status") or "").upper() == "ERRO":
            if message.casefold() == NO_RESULTS:
                return _empty_page(query, response)
            if "seguran" in message.casefold() or "turnstile" in message.casefold():
                raise AccessControlRequiredError(
                    "TJAP/Tucujuris exige validação server-side de Cloudflare Turnstile"
                )
            raise ParserContractChangedError(
                f"TJAP retornou envelope de erro: {message or 'mensagem ausente'}"
            )
        rows = data.get("dados")
        if not isinstance(rows, list):
            raise ParserContractChangedError("TJAP não retornou a lista 'dados' esperada")
        results = [_result(row, query, response) for row in rows if isinstance(row, dict)]
        total = _total(data, len(results), query.page)
        trace = _trace(response, payload)
        return SearchPage(
            source=self.name,
            total=total,
            start=(query.page - 1) * PAGE_SIZE + 1 if results else 0,
            end=(query.page - 1) * PAGE_SIZE + len(results) if results else 0,
            page=query.page,
            page_size=PAGE_SIZE,
            results=results,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=len(results) < PAGE_SIZE,
            completeness_reason="a fonte retornou menos de uma página"
            if len(results) < PAGE_SIZE
            else None,
            ordering="source_default",
            total_known=isinstance(data.get("total"), int),
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def search_authorized(self, query: JurisprudenceQuery, *, turnstile_token: str) -> SearchPage:
        """Run one bounded search with a pass produced by the official UI.

        Tucujuris places the human-issued Turnstile pass in the JSON field
        ``captcha``.  NanoJuris accepts it only for this call; it is never
        generated, persisted, refreshed, or sent in a trace/raw record.
        """

        _validate_query(query)
        if not turnstile_token.strip():
            raise AccessControlRequiredError(
                "TJAP exige passe Turnstile fornecido por interacao humana"
            )
        payload = _build_payload(query)
        payload["captcha"] = turnstile_token
        response = self._request(payload)
        data = _json(response)
        message = str(data.get("mensagem") or "").strip()
        if str(data.get("status") or "").upper() == "ERRO":
            if "seguran" in message.casefold() or "turnstile" in message.casefold():
                raise AccessControlRequiredError("TJAP rejeitou o passe Turnstile fornecido")
            if message.casefold() == NO_RESULTS:
                return _empty_page(query, response)
            raise ParserContractChangedError(
                f"TJAP retornou envelope autorizado de erro: {message or 'mensagem ausente'}"
            )
        rows = data.get("dados")
        if not isinstance(rows, list):
            raise ParserContractChangedError(
                "TJAP resposta autorizada nao retornou a lista 'dados' esperada"
            )
        safe_payload = {key: value for key, value in payload.items() if key != "captcha"}
        trace = _trace(response, safe_payload)
        results = [
            _result(row, query, response, trace=trace) for row in rows if isinstance(row, dict)
        ]
        self._results.update({result.id: result for result in results})
        total = _total(data, len(results), query.page)
        return SearchPage(
            source=self.name,
            total=total,
            start=(query.page - 1) * PAGE_SIZE + 1 if results else 0,
            end=(query.page - 1) * PAGE_SIZE + len(results) if results else 0,
            page=query.page,
            page_size=PAGE_SIZE,
            results=results,
            source_trace=trace,
            pagination_mode="offset",
            is_complete=len(results) < PAGE_SIZE,
            completeness_reason=(
                "a fonte retornou menos de uma pagina" if len(results) < PAGE_SIZE else None
            ),
            ordering="source_default",
            total_known=isinstance(data.get("total"), int),
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise SourceUnavailableError(
                "TJAP detalhe disponivel somente apos busca autorizada observada"
            )
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=result.rapporteur,
            texts=[
                {
                    "content": result.full_text or result.summary or "",
                    "content_type": "text/html",
                }
            ],
            source_trace=result.source_trace,
            raw={
                "source_id": result.id,
                "document_url": result.document_url,
                "access_status": (
                    result.access_status.value if result.access_status is not None else None
                ),
            },
        )

    def get_catalog(self) -> ProviderCatalog:
        """Load the public TJAP filter vocabulary without running a search."""

        data, response = self._get_json(FILTER_CATALOG_URL, "filter_catalog")
        filters = data.get("dados")
        if not isinstance(filters, dict):
            raise ParserContractChangedError("TJAP catalogo nao retornou o objeto dados")
        classes = filters.get("classes")
        origens = filters.get("origens")
        if not isinstance(classes, list) or not isinstance(origens, list):
            raise ParserContractChangedError("TJAP catalogo nao retornou classes/origens")
        species = [
            ProviderOption(
                code=str(item.get("id") or "").strip(),
                description=str(item.get("descricao") or item.get("id") or "").strip(),
            )
            for item in classes
            if isinstance(item, dict) and str(item.get("id") or "").strip()
        ]
        return ProviderCatalog(
            source=self.name,
            # ``origens`` are source locations, not courts; preserve them in
            # raw metadata rather than mislabeling them as authorities.
            courts=[],
            species=species,
            source_trace=_trace(
                response, {}, endpoint="GET /publico/carregar-filtros-combo-jurisprudencia"
            ),
            raw={
                "filter_names": [key for key, value in filters.items() if isinstance(value, list)],
                "counts": {
                    key: len(value) for key, value in filters.items() if isinstance(value, list)
                },
                "filters": filters,
            },
        )

    def get_filter_catalog(self) -> dict[str, Any]:
        """Return all public filter options with counts and source provenance."""

        catalog = self.get_catalog()
        return {
            "status": "public_metadata",
            "source": self.name,
            "source_url": FILTER_CATALOG_URL,
            "counts": catalog.raw.get("counts", {}),
            "filters": catalog.raw.get("filters", {}),
            "source_trace": catalog.source_trace.to_dict() if catalog.source_trace else None,
        }

    def get_last_update(self) -> str:
        """Return the source-reported update timestamp for the jurisprudence bank."""

        data, _ = self._get_json(LAST_UPDATE_URL, "last_update")
        value = data.get("dados")
        if not isinstance(value, str) or not value.strip():
            raise ParserContractChangedError("TJAP nao retornou a data de atualizacao")
        return value.strip()

    def get_capabilities(self) -> ProviderCapabilities:
        filters = [
            "text",
            "number",
            "case_class",
            "rapporteur",
            "judging_body",
            "degree",
            "instance",
            "branch",
            "collection",
            "judgment_date_from",
            "judgment_date_to",
            "source_origin",
            "decision_type",
            "types",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAP Tucujuris",
            source_url=FRONT_URL,
            category="court_jurisprudence",
            search_modes=["text", "case_number", "filters", "authorized_human_challenge"],
            document_types=["acordao"],
            content_formats=["json"],
            canonical_records=["CanonicalDecision"],
            semantic_discriminator="orgao=0|tj|recursal; fonte CJSG",
            extracted_fields=[
                "id",
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "publication_date",
                "summary",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "POST /api/publico/consultar-jurisprudencia",
                "GET /api/publico/carregar-filtros-combo-jurisprudencia",
                "GET /api/publico/buscar-data-banco-dados-jurisprudencia",
            ],
            supports_full_text=False,
            supports_catalog=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            opt_in_unified_search=False,
            pagination_mode="offset",
            max_remote_page_size=PAGE_SIZE,
            completeness_contract="page_size_and_explicit_empty",
            full_text_access="access_blocked",
            supported_filters=filters,
            filter_semantics={
                **{name: "native" for name in filters},
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
            },
            limitations=[
                "A busca exige token Cloudflare Turnstile validado no servidor.",
                "Não há rota de detalhe pública reproduzível observada.",
                (
                    "search_authorized aceita somente passe Turnstile fornecido pelo "
                    "usuário na mesma chamada; nenhum desafio é gerado ou persistido."
                ),
            ],
            responsible_use=["Não contornar Turnstile, WAF ou limites de frequência."],
        )

    def get_parameters(self) -> dict[str, Any]:
        return {"search_url": BASE_URL, "front_url": FRONT_URL, "page_size": PAGE_SIZE}

    def _request(self, payload: dict[str, Any]) -> requests.Response:
        try:
            response = self.session.post(
                BASE_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Referer": FRONT_URL,
                    "tucujuris-front-url": FRONT_URL,
                },
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        except requests.exceptions.Timeout as exc:
            raise SourceUnavailableError("TJAP request timeout") from exc
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError("TJAP TLS negotiation failed") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJAP request failed") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJAP returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJAP returned HTTP {response.status_code}")
        if response.status_code < 200 or response.status_code >= 300:
            raise SourceUnavailableError(f"TJAP returned HTTP {response.status_code}")
        return response

    def _get_json(self, url: str, operation: str) -> tuple[dict[str, Any], requests.Response]:
        try:
            response = self.session.get(
                url,
                headers={
                    "Accept": "application/json",
                    "Referer": FRONT_URL,
                    "tucujuris-front-url": FRONT_URL,
                },
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        except requests.exceptions.Timeout as exc:
            raise SourceUnavailableError(f"TJAP {operation} timeout") from exc
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError(f"TJAP {operation} TLS negotiation failed") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError(f"TJAP {operation} request failed") from exc
        if response.status_code == 429:
            raise RateLimitDetectedError("TJAP returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJAP returned HTTP {response.status_code}")
        if response.status_code < 200 or response.status_code >= 300:
            raise SourceUnavailableError(f"TJAP returned HTTP {response.status_code}")
        data = _json(response)
        if str(data.get("status") or "").upper() != "OK":
            message = data.get("mensagem") or "status ausente"
            raise ParserContractChangedError(
                f"TJAP {operation} retornou envelope inesperado: {message}"
            )
        return data, response


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJAP exige termo, número ou frase exata")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJAP/CJSG aceita somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJAP/CJSG aceita somente instância de segundo grau")
    if query.branch and query.branch.casefold() not in {"state", "estadual"}:
        raise QueryRejectedError("TJAP pertence ao ramo estadual")
    if query.authority and query.authority.casefold() not in {
        "tjap",
        "tribunal de justiça do amapá",
    }:
        raise QueryRejectedError("a autoridade solicitada não corresponde ao TJAP")


def _build_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "orgao": "0",
        "ementa": query.text or query.exact_phrase,
        "votacao": "0",
        "tipo_jurisprudencia": None,
    }
    if query.page > 1:
        payload["offset"] = (query.page - 1) * PAGE_SIZE
    if query.number:
        payload["numeroCNJ"] = query.number
    if query.exact_phrase:
        payload["palavrasExatas"] = True
    if query.rapporteur:
        payload["relator"] = query.rapporteur
    if query.case_class:
        payload["classe"] = query.case_class
    if query.judging_body:
        payload["secretaria"] = query.judging_body
    if query.source_origin:
        payload["origem"] = query.source_origin
    if query.decision_type:
        payload["tipo_jurisprudencia"] = query.decision_type
    if query.types:
        payload["tipo_jurisprudencia"] = query.types[0]
    return payload


def _json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except (TypeError, ValueError) as exc:
        raise ParserContractChangedError("TJAP não retornou JSON válido") from exc
    if not isinstance(data, dict):
        raise ParserContractChangedError("TJAP retornou JSON fora do envelope esperado")
    return data


def _result(
    row: dict[str, Any],
    query: JurisprudenceQuery,
    response: requests.Response,
    *,
    trace: SourceTrace | None = None,
) -> JurisprudenceResult:
    identifier = str(row.get("id") or row.get("identificador") or "").strip()
    if not identifier:
        raise ParserContractChangedError("TJAP retornou registro sem identificador")
    summary = (
        str(row.get("ementa") or row.get("textoementa") or row.get("textoEmenta") or "").strip()
        or None
    )
    return JurisprudenceResult(
        id=identifier,
        source="tjap_tucujuris",
        court="TJAP",
        type="decision",
        number=row.get("numeroacordao") or row.get("numeroano"),
        summary=summary,
        rapporteur=str(row.get("nomerelator") or "").strip() or None,
        judgment_date=str(row.get("datajulgamento") or "").strip() or None,
        publication_date=str(row.get("datapublicacao") or "").strip() or None,
        case_class=str(row.get("classe") or "").strip() or None,
        judging_body=str(row.get("lotacao") or "").strip() or None,
        degree="second",
        instance="second",
        branch="state",
        authority="TJAP",
        collection="CJSG",
        document_type="acordao",
        access_status=AccessStatus.PUBLIC,
        source_trace=trace or _trace(response, _build_payload(query)),
        raw=dict(row),
    )


def _total(data: dict[str, Any], count: int, page: int) -> int:
    for key in ("total", "totalRegistros", "quantidade"):
        value = data.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    return (page - 1) * PAGE_SIZE + count


def _empty_page(query: JurisprudenceQuery, response: requests.Response) -> SearchPage:
    return SearchPage(
        source="tjap_tucujuris",
        total=0,
        start=0,
        end=0,
        page=query.page,
        page_size=PAGE_SIZE,
        results=[],
        source_trace=_trace(response, _build_payload(query)),
        pagination_mode="offset",
        is_complete=True,
        completeness_reason="a fonte declarou nenhum resultado",
        total_known=True,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.EMPTY,
    )


def _trace(
    response: requests.Response,
    payload: dict[str, Any],
    *,
    endpoint: str = "POST /api/publico/consultar-jurisprudencia",
) -> SourceTrace:
    body = response.content
    return SourceTrace(
        provider="tjap_tucujuris",
        endpoint=endpoint,
        source_url=BASE_URL,
        final_url=response.url,
        http_status=response.status_code,
        content_type=response.headers.get("Content-Type"),
        content_sha256=hashlib.sha256(body).hexdigest(),
        response_bytes=len(body),
        query=payload,
        retrieval_status="ok",
        transformations=["json_envelope", "degree_scope_second"],
    )
