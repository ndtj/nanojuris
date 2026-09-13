"""TRT15 public jurisprudence SPA adapter.

The TRT15 application publishes its backend contract and filter catalog, but
the search endpoint currently requires a CAPTCHA response.  This provider
therefore keeps the public catalog usable for discovery while preserving an
explicit access-control error for searches that cannot be reproduced without
human interaction.  No challenge token is generated, solved, replayed or
persisted here.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import requests

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
    ProviderCatalog,
    ProviderOption,
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient, TransportPolicy, TransportRequest, TransportStatus

SEARCH_PATH = "/backend/pesquisar"
OPTIONS_PATH = "/backend/listarOpcoes"
CONFIGURE_PATH = "/backend/configure"
DETAIL_PATH = "/backend/visualizarDocumento"
MAX_RESPONSE_BYTES = 8_000_000
_OFFICIAL_HOST = "jurisprudencia.trt15.jus.br"
_SUCCESS = 1
_CAPTCHA_REQUIRED = 3


class Trt15JurisprudenciaProvider(JurisprudenceProvider):
    """Expose TRT15's public catalog and CAPTCHA boundary."""

    name = "trt15_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http: dict[str, Any] = {}
        self._items: dict[str, dict[str, Any]] = {}
        self._transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(_OFFICIAL_HOST,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_RESPONSE_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )

    @property
    def base_url(self) -> str:
        return self.config.trt15_jurisprudencia_url.rstrip("/")

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        """Search the official endpoint or report its CAPTCHA boundary."""

        return self._search(query)

    def search_authorized(
        self,
        query: JurisprudenceQuery,
        *,
        captcha_response: str,
    ) -> SearchPage:
        """Search once with a CAPTCHA token supplied by the official UI.

        The provider never creates, solves, stores, refreshes or replays the
        token.  It is copied into this single bounded request only; traces and
        errors redact the challenge fields and the POST transport is
        explicitly non-cacheable.
        """

        token = str(captcha_response or "").strip()
        if not token:
            raise AccessControlRequiredError(
                "TRT15 exige resposta CAPTCHA fornecida por interacao humana"
            )
        return self._search(query, captcha_response=token)

    def _search(
        self,
        query: JurisprudenceQuery,
        *,
        captcha_response: str | None = None,
    ) -> SearchPage:
        """Execute the public search, optionally using one caller token."""

        _validate_query(query)
        payload = _build_search_payload(query)
        if captcha_response is not None:
            payload["captchaResponse"] = captcha_response
            payload["recaptcha"] = captcha_response
        response = self._request_json("POST", SEARCH_PATH, payload)
        outcome = _int_value(response.get("sucesso"))
        if outcome == _CAPTCHA_REQUIRED:
            raise AccessControlRequiredError(
                "TRT15 exige resposta CAPTCHA para pesquisar; "
                "nenhum resultado foi tratado como vazio"
            )
        if outcome != _SUCCESS:
            raise ParserContractChangedError("TRT15 retornou um estado de pesquisa não reconhecido")
        documents = response.get("documentos")
        if not isinstance(documents, list):
            raise ParserContractChangedError("TRT15 não retornou a lista documentos esperada")
        total_raw = response.get("resultadosEncontrados")
        total = _int_value(total_raw)
        total_known = total is not None
        total = total if total is not None else len(documents)
        trace = self._trace("POST", SEARCH_PATH, payload)
        results: list[JurisprudenceResult] = []
        for item in documents[: query.page_size]:
            if not isinstance(item, Mapping):
                raise ParserContractChangedError("TRT15 retornou documento fora do formato JSON")
            result = _parse_result(item, trace, query=query, search_id=str(payload["idPesquisa"]))
            results.append(result)
            self._items[result.id] = {
                "document": dict(item),
                "id_pesquisa": payload["idPesquisa"],
                "trace": trace,
            }
        if not results and total:
            raise ParserContractChangedError(
                "TRT15 informou resultados, mas não retornou documentos"
            )
        start = ((query.page - 1) * query.page_size) + 1 if results else 0
        return SearchPage(
            source=self.name,
            total=total,
            start=start,
            end=start + len(results) - 1 if results else 0,
            page=query.page,
            page_size=query.page_size,
            results=results,
            source_trace=trace,
            pagination_mode="page",
            is_complete=(start + len(results) >= total) if total_known else None,
            completeness_reason=(
                "TRT15 declarou resultadosEncontrados"
                if total_known
                else "TRT15 não declarou total autoritativo"
            ),
            ordering=_ordering_label(payload["ordenarPor"]),
            filters_applied=_filters_applied(query),
            total_known=total_known,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_catalog(self) -> ProviderCatalog:
        """Return the public organs/rapporteurs catalog without searching."""

        payload = self._request_json("GET", OPTIONS_PATH, None)
        outcome = _int_value(payload.get("sucesso"))
        if outcome not in {None, _SUCCESS}:
            raise ParserContractChangedError("TRT15 catálogo retornou estado inválido")
        organs = _option_pairs(payload.get("listaOrgaosJulgadores"))
        rapporteurs = _option_pairs(payload.get("listaRelatores"))
        trace = self._trace("GET", OPTIONS_PATH, {})
        return ProviderCatalog(
            source=self.name,
            courts=[
                ProviderOption(
                    code="TRT15", description="Tribunal Regional do Trabalho da 15ª Região"
                )
            ],
            species=[
                ProviderOption(code="ementa", description="Ementa"),
                ProviderOption(code="inteiro_teor", description="Inteiro teor"),
                ProviderOption(code="ambos", description="Ementa e inteiro teor"),
            ],
            source_trace=trace,
            raw={
                "listaOrgaosJulgadores": organs,
                "listaRelatores": rapporteurs,
                "catalog_status": "public_options_only",
                "search_requires_captcha": True,
            },
        )

    def get_parameters(self) -> dict[str, Any]:
        return {
            "source": self.name,
            "base_url": self.base_url,
            "endpoints": [
                "GET /assets/app-config.json",
                "GET /backend/configure",
                "GET /backend/listarOpcoes",
                "POST /backend/pesquisar",
                "POST /backend/irParaPagina",
                "POST /backend/filtrarFacet",
                "POST /backend/visualizarDocumento",
            ],
            "search_requires_captcha": True,
        }

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        item = self._items.get(precedent_id)
        if item is None:
            raise SourceUnavailableError(
                "TRT15 detalhe somente está disponível após uma busca na mesma sessão"
            )
        response = self._request_json(
            "POST",
            DETAIL_PATH,
            {"id": _raw_id(item["document"]), "idPesquisa": item["id_pesquisa"]},
        )
        content = response.get("documento")
        if content:
            return DecisionBundle(
                precedent_id=precedent_id,
                source=self.name,
                texts=[{"content": str(content), "content_type": "text/html"}],
                source_trace=self._trace(
                    "POST",
                    DETAIL_PATH,
                    {"id": _raw_id(item["document"]), "idPesquisa": item["id_pesquisa"]},
                ),
                raw={"document_id": _raw_id(item["document"])},
            )
        link = str(response.get("link") or "")
        if link:
            return DecisionBundle(
                precedent_id=precedent_id,
                source=self.name,
                procedural_follow_url=link,
                texts=[],
                source_trace=self._trace("POST", DETAIL_PATH, {}),
                raw={"document_link": link},
            )
        raise ParserContractChangedError("TRT15 detalhe não contém documento nem link")

    def get_document(self, document_id: str) -> CanonicalDocument:
        bundle = self.get_decisions(document_id)
        if not bundle.texts:
            raise SourceUnavailableError("TRT15 retornou somente link de documento")
        content = bundle.texts[0]["content"].encode("utf-8")
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao_ementa",
            content=content,
            content_type="text/html",
            title=f"TRT15 documento {document_id}",
            text_override=str(bundle.texts[0]["content"]),
            url=bundle.source_trace.source_url if bundle.source_trace else self.base_url,
            access_status=AccessStatus.PUBLIC,
            source_trace=bundle.source_trace,
            raw_metadata={"provider_detail": True},
            parser="trt15_jurisprudencia.visualizarDocumento",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TRT15 Jurisprudência",
            source_url=self.base_url,
            category="court_jurisprudence",
            search_modes=[
                "text",
                "authorized_human_challenge",
                "all_words",
                "any_words",
                "exact_phrase",
                "without_words",
                "date_range",
                "facets",
                "page",
            ],
            document_types=["acordao_ementa", "acordao_full_text"],
            content_formats=["json", "html"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator=(
                "TRT15 official jurisprudence SPA; degree and instance remain "
                "unknown until a result contract is observed"
            ),
            extracted_fields=[
                "id",
                "case_number",
                "case_class",
                "judging_body",
                "rapporteur",
                "judgment_date",
                "summary",
                "full_text",
                "document_url",
                "facets",
            ],
            access_statuses=[
                AccessStatus.PUBLIC,
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /backend/listarOpcoes",
                "POST /backend/pesquisar",
                "POST /backend/irParaPagina",
                "POST /backend/filtrarFacet",
                "POST /backend/visualizarDocumento",
            ],
            supports_full_text=True,
            supports_catalog=True,
            supports_live_tests=True,
            supports_cli=True,
            supports_unified_search=False,
            supports_mcp=True,
            supports_studio=True,
            pagination_mode="page",
            max_remote_page_size=1000,
            completeness_contract="resultadosEncontrados_when_search_is_authorized",
            full_text_access="detail_call",
            supported_filters=[
                "text",
                "all_words",
                "any_words",
                "exact_phrase",
                "without_words",
                "case_class",
                "judging_body",
                "rapporteur",
                "published_from",
                "published_to",
                "page",
                "document_type",
            ],
            unsupported_filters=[
                "courts",
                "types",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "party_name",
                "party_document",
                "lawyer_name",
                "oab",
                "updated_from",
                "updated_to",
                "number",
                "precatory_number",
                "police_document",
                "cda",
                "source_origin",
                "source_origins",
                "fetch_details",
                "legal_area",
                "decision_type",
                "judgment_date_from",
                "judgment_date_to",
            ],
            filter_semantics={
                "text": "native",
                "all_words": "native",
                "any_words": "native",
                "exact_phrase": "native",
                "without_words": "native",
                "case_class": "native",
                "judging_body": "native",
                "rapporteur": "native",
                "published_from": "translated",
                "published_to": "translated",
                "page": "native",
                "document_type": "translated",
                "degree": "unsupported",
                "instance": "unsupported",
                "courts": "unsupported",
                "types": "unsupported",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
                "number": "unsupported",
                "precatory_number": "unsupported",
                "police_document": "unsupported",
                "cda": "unsupported",
                "source_origin": "unsupported",
                "source_origins": "unsupported",
                "fetch_details": "unsupported",
                "legal_area": "unsupported",
                "decision_type": "unsupported",
                "judgment_date_from": "unsupported",
                "judgment_date_to": "unsupported",
            },
            limitations=[
                "O backend retorna sucesso=3 quando a resposta CAPTCHA está ausente ou expirada.",
                "O catálogo de órgãos/relatores é público, mas não prova grau por si só.",
                "Busca e detalhe permanecem fora da federação até existir chamada "
                "pública reproduzível.",
            ],
            responsible_use=[
                "Não gerar, resolver, extrair ou persistir CAPTCHA/Turnstile.",
                "Respeitar os limites da fonte e usar o catálogo somente para diagnóstico.",
            ],
            ordering_modes=["S3", "native"],
            detail_modes=["visualizarDocumento", "official_link"],
        )

    def _request_json(
        self, method: str, path: str, payload: dict[str, Any] | None
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != _OFFICIAL_HOST:
            raise QueryRejectedError("TRT15 URL fora da allowlist oficial")
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="trt15_api",
                method=method,
                url=url,
                json_body=payload,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                idempotent=method.upper() != "POST",
                cacheable=False,
            )
        )
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(f"TRT15 transport failed: {response.status.value}")
        final = urlparse(str(response.final_url or url))
        self._last_http = {
            "http_status": response.status_code,
            "final_url": str(response.final_url or url),
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if 200 <= (response.status_code or 0) < 400 else "error",
        }
        if final.scheme != "https" or (final.hostname or "").lower() != _OFFICIAL_HOST:
            raise SourceUnavailableError("TRT15 redirecionou para host não autorizado")
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TRT15 returned HTTP 429")
        if status in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TRT15 returned HTTP {status}")
        if status < 200 or status >= 300:
            raise SourceUnavailableError(f"TRT15 returned HTTP {status}")
        try:
            value = response.json()
        except (TypeError, ValueError) as exc:
            raise ParserContractChangedError("TRT15 não retornou JSON") from exc
        if not isinstance(value, dict):
            raise ParserContractChangedError("TRT15 JSON não é um objeto")
        return value

    def _trace(self, method: str, path: str, payload: dict[str, Any]) -> SourceTrace:
        return SourceTrace(
            provider=self.name,
            endpoint=f"{method} {path}",
            query={k: v for k, v in payload.items() if k not in {"captchaResponse", "recaptcha"}},
            source_url=f"{self.base_url}{path}",
            limitations=["A busca depende de CAPTCHA da fonte; o provider não tenta contorná-lo."],
            **self._last_http,
        )


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any(
        (
            query.text.strip(),
            query.all_words.strip(),
            query.any_words.strip(),
            query.exact_phrase.strip(),
            query.number.strip(),
        )
    ):
        raise QueryRejectedError("TRT15 exige termo, frase exata ou número")
    if query.authority and query.authority.casefold() not in {"trt15", "trt-15", "trt 15"}:
        raise QueryRejectedError("a autoridade solicitada não corresponde ao TRT15")
    if query.branch and query.branch.casefold() not in {"labor", "trabalhista"}:
        raise QueryRejectedError("TRT15 pertence ao ramo trabalhista")
    if query.degree or query.instance:
        raise QueryRejectedError("TRT15 ainda não comprovou filtro de grau ou instância")


def _build_search_payload(query: JurisprudenceQuery) -> dict[str, Any]:
    source_text = query.text.strip()
    all_words = query.all_words.strip() or source_text
    exact = query.exact_phrase.strip()
    start_date = query.published_from.strip() or query.judgment_date_from.strip()
    end_date = query.published_to.strip() or query.judgment_date_to.strip()
    year_start = _year(start_date) or "1980"
    year_end = _year(end_date) or str(datetime.now().year)
    tipo = "ambos"
    requested_types = {str(value).casefold() for value in query.types}
    if query.document_type.casefold() in {"ementa", "summary"} or "ementa" in requested_types:
        tipo = "ementa"
    elif query.document_type.casefold() in {"inteiro_teor", "full_text"}:
        tipo = "inteiro_teor"
    material = {
        "buscarPalavrasTodas": all_words,
        "buscarPalavrasQuaisquer": query.any_words.strip(),
        "buscarPalavrasTrechoExato": exact,
        "excluirPalavras": query.without_words.strip(),
        "classeJudicial": query.case_class.strip(),
        "orgaoJulgador": query.judging_body.strip(),
        "relator": query.rapporteur.strip(),
        "dataInicio": start_date or None,
        "dataFim": end_date or None,
        "anoInicio": year_start,
        "anoFim": year_end,
        "pagina": max(1, query.page),
        "ordenarPor": query.order_by.strip() or "S3",
        "tipoBusca": tipo,
    }
    query_id = hashlib.sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:20]
    return {
        **material,
        "captchaResponse": "",
        "idPesquisa": f"nanojuris-{query_id}",
        "recaptcha": "",
    }


def _parse_result(
    item: Mapping[str, Any],
    trace: SourceTrace,
    *,
    query: JurisprudenceQuery,
    search_id: str,
) -> JurisprudenceResult:
    raw_id = _raw_id(item)
    if not raw_id:
        raise ParserContractChangedError("TRT15 documento não possui id")
    result_id = f"trt15-{raw_id}"
    summary = _first_text(item, "ementa", "ementa_html", "resumo", "summary")
    document_url = _first_text(item, "link", "documentUrl", "document_url") or None
    case_number = _first_text(item, "nrProcesso", "numeroProcesso", "processoDocumento") or None
    return JurisprudenceResult(
        id=result_id,
        source="trt15_jurisprudencia",
        court="TRT15",
        type="acordao_ementa",
        number=case_number,
        summary=summary or None,
        judgment_date=_first_text(item, "dataAssinatura", "dataJulgamento") or None,
        publication_date=_first_text(item, "dataPublicacao", "dataDisponibilizacao") or None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        case_class=_first_text(item, "classeJudicialSigla", "classeJudicial") or None,
        judging_body=_first_text(item, "orgaoJulgador") or None,
        rapporteur=_first_text(item, "relator") or None,
        authority="TRT15",
        branch="labor",
        collection="JURISPRUDENCIA",
        document_type="acordao_ementa",
        document_url=document_url,
        raw={"source_document": dict(item), "id_pesquisa": search_id, "degree": "unknown"},
        field_provenance={
            "authority": {"source": "official_endpoint_scope", "confidence": "high"},
            "branch": {"source": "official_authority", "confidence": "high"},
            "degree": {"source": "not_declared", "confidence": "unknown"},
        },
    )


def _filters_applied(query: JurisprudenceQuery) -> dict[str, str]:
    filters = {
        "text": "native",
        "all_words": "native",
        "any_words": "native",
        "exact_phrase": "native",
        "without_words": "native",
        "case_class": "native",
        "judging_body": "native",
        "rapporteur": "native",
        "published_from": "translated",
        "published_to": "translated",
        "document_type": "translated",
        "authority": "validated_scope",
        "branch": "validated_scope",
        "page": "native",
    }
    return {
        key: value
        for key, value in filters.items()
        if _query_filter_present(query, key) or key in {"authority", "branch", "page"}
    }


def _query_filter_present(query: JurisprudenceQuery, name: str) -> bool:
    value = getattr(query, name, None)
    return bool(value) if not isinstance(value, list) else bool(value)


def _option_pairs(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        pair: Any = item
        if isinstance(item, Mapping):
            pair = item.get("value")
        if isinstance(pair, Sequence) and not isinstance(pair, (str, bytes)) and len(pair) >= 2:
            result.append({"description": str(pair[0]), "code": str(pair[1])})
    return result


def _raw_id(item: Mapping[str, Any]) -> str:
    for key in ("id", "identificador", "documentoId"):
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _first_text(item: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return " ".join(str(value).replace("\xa0", " ").split())
    return ""


def _int_value(value: Any) -> int | None:
    try:
        if value is None or isinstance(value, bool):
            return None
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _year(value: str) -> str | None:
    cleaned = value.strip()
    if len(cleaned) >= 4 and cleaned[:4].isdigit():
        return cleaned[:4]
    return None


def _ordering_label(value: Any) -> str:
    return {"S3": "relevance", "S1": "date_asc", "S2": "date_desc"}.get(str(value), "native")


__all__ = ["Trt15JurisprudenciaProvider"]
