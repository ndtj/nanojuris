"""TJMA JurisConsult public catalog provider.

The catalog endpoints are public. The result-search endpoints require a
captcha challenge, which remains explicit and is never automated here.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urljoin, urlparse

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
from nanojuris.transport import (
    SharedHttpClient,
    TransportPolicy,
    TransportRequest,
    TransportStatus,
)


class TjmaJurisconsultProvider(JurisprudenceProvider):
    """Expose TJMA JurisConsult catalogs without automating captcha search."""

    name = "tjma_jurisconsult"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self._last_http_metadata: dict[str, Any] = {}
        # Results obtained through an explicitly user-authorized search are
        # retained only for this provider instance.  This lets callers open
        # the observed decision without persisting challenge material or
        # turning the gated source into a federated provider.
        self._results: dict[str, JurisprudenceResult] = {}
        host = urlparse(self.config.tjma_jurisconsult_url).hostname or ""
        self._transport_policy = TransportPolicy(
            allowed_hosts=(host,),
            timeout_seconds=self.config.timeout,
            max_bytes=4_000_000,
            max_retries=0,
            rate_limit_interval=self.config.rate_limit_interval,
            user_agent=self.config.user_agent,
            verify_ssl=self.config.verify_ssl,
        )
        self._transport = SharedHttpClient(self._transport_policy, session=self.session)

    @property
    def base_url(self) -> str:
        return self.config.tjma_jurisconsult_url.rstrip("/")

    def search(self, query: Any):
        raise AccessControlRequiredError(
            "TJMA JurisConsult exige captcha na busca de resultados; "
            "o NanoJuris disponibiliza somente o catalogo publico."
        )

    def search_authorized(
        self,
        query: JurisprudenceQuery,
        *,
        captcha_token: str,
        google_token: str,
        key_id: str,
        report_id: str = "1",
    ) -> SearchPage:
        """Run one result page after a user has completed the official challenge.

        The tokens are accepted only for this call and are never put in a
        ``SourceTrace``, cache key, fixture or object attribute.  This method
        is intentionally separate from :meth:`search`: federated execution
        must not manufacture or retain a CAPTCHA challenge.  ``captcha_token``
        is the short-lived server token returned by the official image flow,
        while ``google_token`` is the browser-generated reCAPTCHA token.
        """

        _validate_authorized_query(query, captcha_token, google_token, key_id, report_id)
        endpoint = _REPORT_ENDPOINTS[report_id]
        page_size = min(max(query.page_size, 1), 20)
        start = (query.page - 1) * page_size + 1
        params = _build_authorized_params(query, report_id, start, start + page_size - 1)
        response = self._transport.request(
            TransportRequest(
                source=self.name,
                operation="authorized_result_page",
                method="GET",
                url=urljoin(self.base_url + "/", endpoint.lstrip("/")),
                params=params | {"tokenG": google_token, "keyId": key_id},
                headers={
                    "Accept": "application/json",
                    # The bearer value is transient and is redacted by the
                    # shared transport.  It is never persisted by the provider.
                    "Authorization": f"Bearer {captcha_token}",
                },
                cacheable=False,
                idempotent=True,
            )
        )
        self._update_http_metadata(response)
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJMA JurisConsult authorized request failed: {response.status.value}"
            )
        status = int(response.status_code or 0)
        if status == 429:
            raise RateLimitDetectedError("TJMA JurisConsult returned HTTP 429")
        if status in {401, 403}:
            raise AccessControlRequiredError(
                f"TJMA JurisConsult rejected the supplied challenge (HTTP {status})"
            )
        if status >= 400:
            raise SourceUnavailableError(f"TJMA JurisConsult returned HTTP {status}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ParserContractChangedError(
                "TJMA JurisConsult authorized route returned invalid JSON"
            ) from exc
        page = _parse_authorized_page(
            payload,
            query=query,
            report_id=report_id,
            endpoint=endpoint,
            metadata=self._last_http_metadata,
        )
        self._results.update({result.id: result for result in page.results})
        return page

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise AccessControlRequiredError(
                "TJMA JurisConsult nao oferece detalhe automatizado sem o desafio da busca."
            )
        content = result.full_text or result.summary or ""
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            rapporteur=result.rapporteur,
            texts=[{"content": content, "content_type": "text/plain"}],
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
        paths = {
            "reports": "/jurisprudencia/lista_relatorios",
            "types": "/jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=1",
            "classes": "/jurisprudencia/lista_todos_classes?tipoRelatorio=1",
            "magistrates": "/jurisprudencia/lista_todos_magistrados?tipoRelatorio=1",
            "chambers": "/jurisprudencia/lista_todos_camaras?tipoRelatorio=1",
            "counties": "/jurisprudencia/lista_todos_comarcas?tipoRelatorio=1",
            "precedent_links": "/jurisprudencia/links_pesquisa_sumulas",
        }
        payloads = {key: self._request_json(path)[0] for key, path in paths.items()}
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /jurisprudencia/lista_*",
            query={"catalog": True},
            source_url=self.base_url,
            limitations=[
                "Os endpoints de catalogo sao publicos e nao substituem a busca de resultados.",
                "A busca principal exige tokenG/keyId de captcha e nao e automatizada.",
            ],
            **self._last_http_metadata,
        )
        return parse_tjma_catalog(payloads, trace=trace)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJMA JurisConsult",
            source_url="https://jurisconsult.tjma.jus.br/",
            category="court_catalog",
            search_modes=[
                "catalog",
                "text_gated",
                "authorized_human_challenge",
                "precedent_links",
            ],
            document_types=["acordao", "decisao_monocratica", "sentenca", "sumula"],
            content_formats=["json"],
            canonical_records=["ProviderCatalog", "JurisprudenceResult", "SearchPage"],
            detail_modes=["authorized_search_inline"],
            extracted_fields=[
                "report_type",
                "search_type",
                "case_class",
                "rapporteur",
                "chamber",
                "county",
                "precedent_links",
                "id",
                "case_number",
                "summary",
                "full_text",
                "document_url",
                "judgment_date",
                "publication_date",
                "degree",
                "instance",
                "branch",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.ACCESS_CONTROL_REQUIRED],
            endpoints=[
                "GET /jurisprudencia/lista_relatorios",
                "GET /jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_classes?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_magistrados?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_camaras?tipoRelatorio=<id>",
                "GET /jurisprudencia/lista_todos_comarcas?tipoRelatorio=<id>",
                "GET /jurisprudencia/links_pesquisa_sumulas",
                # These are the official result routes exposed by the public
                # application.  They are intentionally declared even though
                # the application requires a human CAPTCHA token before it
                # will return a result page.
                "GET /sg/jurisprudencias/processos",
                "GET /jurisprudencia/processos/pesquisa_acordaos_tr",
                "GET /jurisprudencia/processos/pesquisa_monocraticas",
                "GET /jurisprudencia/processos/pesquisa_monocraticas_tr",
            ],
            supports_catalog=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            supports_live_tests=True,
            pagination_mode="offset",
            max_remote_page_size=20,
            completeness_contract="authorized_processos_int_count",
            # The result surface exists but is gated by a CAPTCHA challenge;
            # no public automated document route was observed.  Keep this as
            # an explicit terminal access state rather than implying missing
            # implementation or an empty corpus.
            full_text_access="access_blocked",
            supported_filters=[
                "types",
                "catalog",
                "text",
                "exact_phrase",
                "case_class",
                "judging_body",
                "rapporteur",
                "published_from",
                "published_to",
                "page",
            ],
            filter_semantics={
                "types": "native",
                "authority": "validated_scope",
                "branch": "validated_scope",
                "collection": "validated_scope",
                "document_type": "validated_scope",
                "text": "native",
                "exact_phrase": "native",
                "case_class": "native",
                "judging_body": "native",
                "rapporteur": "native",
                "published_from": "native",
                "published_to": "native",
                "page": "native",
                **{
                    name: "unsupported"
                    for name in (
                        "courts",
                        "all_words",
                        "any_words",
                        "without_words",
                        "updated_from",
                        "updated_to",
                        "number",
                        "party_name",
                        "party_document",
                        "lawyer_name",
                        "oab",
                        "precatory_number",
                        "police_document",
                        "cda",
                        "source_origin",
                        "source_origins",
                        "fetch_details",
                        "degree",
                        "instance",
                        "legal_area",
                        "decision_type",
                        "judgment_date_from",
                        "judgment_date_to",
                    )
                },
            },
            limitations=[
                "A busca de acordaos, decisoes e sentencas exige captcha.",
                "search_authorized exige tokens fornecidos pelo usuario na mesma chamada; "
                "nenhum token e gerado, armazenado ou reutilizado pelo provider.",
                "Catalogos sao snapshots de vocabulario e nao representam resultados coletados.",
            ],
            responsible_use=[
                "Usar o catalogo para desenho amostral e preenchimento de filtros.",
                "Nao interpretar o provider como acervo textual pesquisavel.",
                "Nao enviar tokenG, keyId ou qualquer desafio de captcha.",
            ],
        )

    def _request_json(self, path: str) -> tuple[dict[str, Any], str]:
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        try:
            response = self._transport.request(
                TransportRequest(
                    source=self.name,
                    operation="catalog",
                    method="GET",
                    url=url,
                    headers={"Accept": "application/json"},
                )
            )
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJMA JurisConsult request failed: {exc}") from exc
        status = int(response.status_code or 0)
        response_url = response.final_url or response.url or url
        self._update_http_metadata(response)
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJMA JurisConsult request failed: {response.status.value}"
            )
        if status == 429:
            raise RateLimitDetectedError("TJMA JurisConsult returned HTTP 429")
        if status >= 500:
            raise SourceUnavailableError(f"TJMA JurisConsult returned HTTP {status}")
        if status >= 400:
            # JurisConsult reports a missing/invalid human challenge as a
            # structured 400. Preserve that access boundary instead of
            # flattening it into a generic source failure.
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = None
            if isinstance(error_payload, dict) and str(error_payload.get("error", "")) in {
                "captcha_not_provided",
                "captcha_invalid",
            }:
                raise AccessControlRequiredError(
                    "TJMA JurisConsult requires a human captcha challenge"
                )
            raise SourceUnavailableError(f"TJMA JurisConsult rejected request with HTTP {status}")
        try:
            data = response.json()
        except ValueError as exc:
            raise SourceUnavailableError("TJMA JurisConsult returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise SourceUnavailableError("TJMA JurisConsult catalog root is not an object")
        return data, response_url

    def _update_http_metadata(self, response: Any) -> None:
        """Capture response metadata without retaining request credentials."""

        status = int(response.status_code or 0)
        self._last_http_metadata = {
            "http_status": status,
            "final_url": response.final_url or response.url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256,
            "response_bytes": response.byte_size,
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok"
            if response.status is TransportStatus.COMPLETE and status < 400
            else response.status.value,
        }


_REPORT_ENDPOINTS = {
    "1": "/sg/jurisprudencias/processos",
    "2": "/jurisprudencia/processos/pesquisa_monocraticas",
    "5": "/jurisprudencia/processos/pesquisa_monocraticas_tr",
    "6": "/jurisprudencia/processos/pesquisa_acordaos_tr",
}


def _validate_authorized_query(
    query: JurisprudenceQuery,
    captcha_token: str,
    google_token: str,
    key_id: str,
    report_id: str,
) -> None:
    if report_id not in _REPORT_ENDPOINTS:
        raise QueryRejectedError(f"TJMA report_id nao suportado: {report_id!r}")
    if not isinstance(query, JurisprudenceQuery):
        raise QueryRejectedError("TJMA exige JurisprudenceQuery")
    if not query.text.strip() and not query.exact_phrase.strip() and not query.number.strip():
        raise QueryRejectedError("TJMA exige termo, frase exata ou numero")
    if not captcha_token.strip() or not google_token.strip() or not key_id.strip():
        raise AccessControlRequiredError(
            "TJMA exige tokens de desafio fornecidos por uma interacao humana"
        )
    if query.authority and query.authority.casefold() not in {"tjma", "tj-ma"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TJMA")
    if query.branch and query.branch.casefold() not in {"state", "estadual"}:
        raise QueryRejectedError("TJMA pertence ao ramo estadual")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("a rota de jurisprudencia selecionada e de segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("a rota de jurisprudencia selecionada e de segundo grau")


def _build_authorized_params(
    query: JurisprudenceQuery,
    report_id: str,
    start: int,
    end: int,
) -> dict[str, Any]:
    """Mirror only the documented fields emitted by the official frontend."""

    text = query.exact_phrase.strip() or query.text.strip() or query.number.strip()
    params: dict[str, Any] = {
        "chave": text,
        "tipoPesquisa": 1,
        "checkForm": 0,
        "inicioPagina": start,
        "fimPagina": end,
        "fraseExata": bool(query.exact_phrase.strip()),
    }
    if query.rapporteur.strip():
        params["relator"] = query.rapporteur.strip()
    if query.case_class.strip():
        params["classe"] = query.case_class.strip()
    if query.judging_body.strip():
        params["camara"] = query.judging_body.strip()
    if query.published_from.strip():
        params["dtaInicio"] = query.published_from.strip()
    if query.published_to.strip():
        params["dtaFim"] = query.published_to.strip()
    # The report id is part of the route selection in the official app.  It is
    # included as a query field for the non-default report routes as well.
    if report_id != "1":
        params["tipoRelatorio"] = report_id
    return params


def _parse_authorized_page(
    payload: Any,
    *,
    query: JurisprudenceQuery,
    report_id: str,
    endpoint: str,
    metadata: dict[str, Any],
) -> SearchPage:
    if not isinstance(payload, dict):
        raise ParserContractChangedError("TJMA resposta autorizada nao e um objeto JSON")
    response = payload.get("response")
    if not isinstance(response, dict):
        error = str(payload.get("error") or payload.get("message") or "")
        if "captcha" in error.casefold() or "token" in error.casefold():
            raise AccessControlRequiredError("TJMA rejeitou o desafio fornecido")
        raise ParserContractChangedError("TJMA resposta autorizada sem envelope response")
    rows = response.get("processos")
    if rows is None:
        # The official UI treats a missing processos collection as an
        # authoritative empty result, but only when the envelope is valid.
        return SearchPage(
            source="tjma_jurisconsult",
            total=0,
            start=0,
            end=0,
            page=query.page,
            page_size=query.page_size,
            results=[],
            source_trace=_authorized_trace(endpoint, query, metadata),
            pagination_mode="offset",
            is_complete=True,
            completeness_reason="TJMA response envelope contained no processos",
            total_known=True,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )
    if not isinstance(rows, list):
        raise ParserContractChangedError("TJMA processos nao e uma lista")
    trace = _authorized_trace(endpoint, query, metadata)
    results = [
        _parse_authorized_result(item, report_id, trace) for item in rows if isinstance(item, dict)
    ]
    declared_total = next(
        (
            _as_int(item.get("int_count"))
            for item in rows
            if isinstance(item, dict) and _as_int(item.get("int_count")) is not None
        ),
        None,
    )
    total = declared_total if declared_total is not None else len(results)
    total_known = declared_total is not None
    observed_end = (query.page - 1) * query.page_size + len(results)
    unconfirmed_empty = not results and not total_known
    page_complete = (
        observed_end >= total if total_known else bool(results) and len(results) < query.page_size
    )
    return SearchPage(
        source="tjma_jurisconsult",
        total=total,
        start=(query.page - 1) * query.page_size + 1 if results else 0,
        end=(query.page - 1) * query.page_size + len(results) if results else 0,
        page=query.page,
        page_size=query.page_size,
        results=results,
        source_trace=trace,
        pagination_mode="offset",
        is_complete=page_complete,
        completeness_reason=(
            "TJMA returned a short page"
            if page_complete and not total_known
            else "TJMA nao informou total autoritativo; janela vazia nao confirmada"
            if unconfirmed_empty
            else None
        ),
        total_known=total_known,
        access_status=AccessStatus.PUBLIC,
        extraction_status=(
            ExtractionStatus.PARTIAL if unconfirmed_empty else ExtractionStatus.COMPLETE
        ),
    )


def _parse_authorized_result(
    item: dict[str, Any], report_id: str, trace: SourceTrace
) -> JurisprudenceResult:
    source_id = _first_text(item, "pkJurisprudencia", "id", "NUMCOL", "numCol", "txNumeroAcordao")
    if not source_id:
        raise ParserContractChangedError("TJMA resultado nao possui identificador")
    summary = _first_text(item, "txEmenta", "ementa", "txEmentaFormated") or None
    case_number = _first_text(item, "numeroProcesso", "numProcesso", "nrProcesso") or None
    document_url = _first_text(item, "documentUrl", "url", "link") or _public_document_url(item)
    return JurisprudenceResult(
        id=f"tjma-{source_id}",
        source="tjma_jurisconsult",
        court="TJMA",
        type="acordao" if report_id in {"1", "6"} else "decisao_monocratica",
        number=case_number,
        summary=summary,
        full_text=_first_text(
            item,
            "txAcordao",
            "strAcordao",
            "txtAcordao",
            "texto",
            "fullText",
        )
        or None,
        rapporteur=_first_text(item, "relator", "strRelator", "nomeRelator") or None,
        judgment_date=_first_text(item, "dtaJulgamento", "dataJulgamento") or None,
        publication_date=_first_text(item, "dtaPublicacao", "dataPublicacao") or None,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
        source_trace=trace,
        raw=item,
        case_class=_first_text(item, "classe", "strClasse", "classeProcessual") or None,
        judging_body=_first_text(item, "camara", "strCamara", "orgaoJulgador") or None,
        degree="second",
        instance="second",
        branch="state",
        authority="TJMA",
        collection="CJSG",
        document_type="acordao" if report_id in {"1", "6"} else "decisao_monocratica",
        document_url=document_url,
    )


def _public_document_url(item: dict[str, Any]) -> str | None:
    """Build the official PDF route when the result explicitly exposes it.

    The TJMA frontend only renders the download action when the first
    ``arquivosAcordao`` entry is marked ``bol_permite_consulta_publica`` and
    contains both a filename and document type.  Keep this conservative: a
    missing permission flag, filename or type means that no document URL is
    claimed.  The URL is a route reference, not a fetch; downloading it still
    happens only through an explicitly authorized, user-triggered flow.
    """

    files = item.get("arquivosAcordao")
    if not isinstance(files, list) or not files or not isinstance(files[0], dict):
        return None
    file_info = files[0]
    allowed = file_info.get("bol_permite_consulta_publica")
    if allowed not in {True, "1", "true", "True"}:
        return None
    filename = _first_text(file_info, "strArquivo", "arquivo", "filename")
    document_type = _first_text(file_info, "strTipoDocumento", "tipoDocumento", "extension")
    if not filename or not document_type:
        return None
    return (
        "https://apijuris.tjma.jus.br/v1/sg/download_acordao_pauta_julgamento?filename="
        f"{quote(filename, safe='')}.{quote(document_type.lstrip('.'), safe='')}"
    )


def _authorized_trace(
    endpoint: str, query: JurisprudenceQuery, metadata: dict[str, Any]
) -> SourceTrace:
    return SourceTrace(
        provider="tjma_jurisconsult",
        endpoint=f"GET {endpoint}",
        query={
            "text": query.text,
            "exact_phrase": query.exact_phrase,
            "page": query.page,
            "page_size": query.page_size,
        },
        source_url="https://jurisconsult.tjma.jus.br/",
        limitations=[
            "Resultado obtido somente apos desafio oficial concluido pelo usuario.",
            "Tokens nao sao persistidos nem incluidos no trace.",
        ],
        **metadata,
    )


def _first_text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def parse_tjma_catalog(
    payloads: dict[str, dict[str, Any]], *, trace: SourceTrace
) -> ProviderCatalog:
    """Normalize the public TJMA vocabulary endpoints into ProviderCatalog."""

    reports = payloads.get("reports", {}).get("response", {}).get("relatorios", [])
    types = payloads.get("types", {}).get("tipos", [])
    classes = payloads.get("classes", {}).get("classes", [])
    magistrates = payloads.get("magistrates", {}).get("relatores", [])
    chambers = payloads.get("chambers", {}).get("camaras", [])
    counties = payloads.get("counties", {}).get("comarcas", [])
    links = payloads.get("precedent_links", {}).get("response", {}).get("pesquisaSumulas", [])
    species = [
        ProviderOption(
            code=str(item.get("id", "")),
            description=str(item.get("titulo", "")),
            metadata={"url": item.get("url")},
        )
        for item in reports
        if isinstance(item, dict) and item.get("id") is not None
    ]
    return ProviderCatalog(
        source="tjma_jurisconsult",
        courts=[ProviderOption(code="TJMA", description="Tribunal de Justica do Maranhao")],
        species=species,
        species_groups=[
            {
                "code": "public_search_catalog",
                "description": "Catalogos publicos do JurisConsult",
                "search_requires_captcha": True,
            }
        ],
        source_trace=trace,
        raw={
            "reports": reports,
            "search_types": types,
            "classes": classes,
            "magistrates": magistrates,
            "chambers": chambers,
            "counties": counties,
            "precedent_links": links,
            "search_access_status": AccessStatus.ACCESS_CONTROL_REQUIRED.value,
        },
    )
