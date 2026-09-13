"""TJSE judicial jurisprudence diagnostic provider.

The official form is public and exposes a rich second-degree search contract,
but its submit action is protected by Cloudflare Turnstile.  This adapter
deliberately stops at that boundary and reports an explicit access-control
state instead of pretending that the source returned no results.
"""

from __future__ import annotations

import hashlib
import re
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
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

_CHALLENGE_MARKERS = (
    "cf-turnstile",
    "challenges.cloudflare.com/turnstile",
    "captcha invalido",
    "captcha inválido",
    "turnstile-hidden",
)


class TjseJurisprudenciaProvider(JurisprudenceProvider):
    """Expose TJSE's public form while preserving the Turnstile boundary."""

    name = "tjse_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.config.tjse_jurisprudencia_url).hostname or ""
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
                timeout_seconds=self.config.timeout,
                max_bytes=4_000_000,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._results: dict[str, JurisprudenceResult] = {}

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        response = self._request("GET", self.config.tjse_jurisprudencia_url)
        text = response.text
        if _has_challenge(text):
            raise AccessControlRequiredError(
                "TJSE exige Cloudflare Turnstile para submeter a pesquisa judicial; "
                "nenhum resultado reproduzível foi obtido"
            )
        if not BeautifulSoup(text, "html.parser").select_one("form#frmPrincipal"):
            raise ParserContractChangedError("TJSE não retornou o formulário JSF esperado")
        raise AccessControlRequiredError(
            "TJSE requer token de desafio emitido por interação legítima antes da pesquisa"
        )

    def search_authorized(
        self,
        query: JurisprudenceQuery,
        *,
        turnstile_token: str,
    ) -> SearchPage:
        """Submit one bounded search with a token produced by the official UI.

        The token is caller-supplied and is used only for this request.  The
        adapter never solves, stores, refreshes, or replays Turnstile tokens.
        This path is deliberately opt-in and does not make TJSE federated.
        """

        _validate_query(query)
        if not turnstile_token.strip():
            raise AccessControlRequiredError(
                "TJSE exige token Turnstile fornecido por interacao humana"
            )
        initial = self._request("GET", self.config.tjse_jurisprudencia_url)
        soup = BeautifulSoup(initial.text, "html.parser")
        form = soup.select_one("form#frmPrincipal")
        if form is None:
            raise ParserContractChangedError("TJSE nao retornou o formulario JSF esperado")
        action = urljoin(self.config.tjse_jurisprudencia_url, form.get("action") or "")
        payload = _build_form_payload(form, query, turnstile_token)
        response = self._request(
            "POST",
            action,
            data=payload,
            operation="authorized_search",
        )
        if _has_invalid_challenge(response.text):
            raise AccessControlRequiredError("TJSE rejeitou o token Turnstile fornecido")
        trace = _trace(response, "POST /Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse")
        results = _parse_authorized_results(response.text, trace)
        self._results.update({result.id: result for result in results})
        explicit_empty = _has_authoritative_empty(response.text)
        if not results and _has_challenge(response.text) and not explicit_empty:
            raise AccessControlRequiredError(
                "TJSE retornou novamente o desafio Turnstile sem resultados"
            )
        if not results and not explicit_empty:
            raise ParserContractChangedError(
                "TJSE resposta autorizada nao possui resultados ou vazio autoritativo"
            )
        return SearchPage(
            source=self.name,
            total=len(results),
            total_known=explicit_empty,
            start=1 if results else 0,
            end=len(results),
            page=max(int(query.page), 1),
            page_size=max(int(query.page_size or 10), 1),
            results=results,
            source_trace=trace,
            pagination_mode="unknown_until_live_contract",
            is_complete=True if explicit_empty else None,
            completeness_reason=(
                "TJSE confirmou nenhum resultado"
                if not results and explicit_empty
                else "TJSE autorizada retornou uma pagina sem total"
            ),
            ordering="source_default",
            access_status=AccessStatus.PUBLIC,
            extraction_status=(
                ExtractionStatus.EMPTY if not results else ExtractionStatus.COMPLETE
            ),
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._results.get(precedent_id)
        if result is None:
            raise SourceUnavailableError(
                "TJSE detalhe disponivel somente apos busca autorizada observada"
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
        """Extract public filter vocabularies without submitting the form."""

        response = self._request("GET", self.config.tjse_jurisprudencia_url)
        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.select_one("form#frmPrincipal")
        if form is None:
            raise ParserContractChangedError("TJSE nao retornou o formulario JSF esperado")

        filters = {
            "case_class": _select_options(soup, "#somClassesProcessuais_input"),
            "rapporteur": _select_options(soup, "#somRelator_input"),
            "judging_body": _select_options(soup, "#somOrgaoJulgador_input"),
            "document_type": _radio_values(soup, "sorTipoDocumento"),
            "degree": _radio_values(soup, "sorCompetencia"),
        }
        trace = _trace(response, "GET /Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse")
        return ProviderCatalog(
            source=self.name,
            species=[
                ProviderOption(code=item["code"], description=item["description"])
                for item in filters["case_class"]
            ],
            source_trace=trace,
            raw={
                "status": "public_metadata",
                "filters": filters,
                "counts": {key: len(value) for key, value in filters.items()},
                "challenge_required_for_search": True,
            },
        )

    def get_filter_catalog(self) -> dict[str, object]:
        """Return the public filter vocabulary and its challenge boundary."""

        catalog = self.get_catalog()
        return {
            "status": "public_metadata",
            "source": self.name,
            "filters": catalog.raw.get("filters", {}),
            "counts": catalog.raw.get("counts", {}),
            "challenge_required_for_search": True,
            "source_trace": catalog.source_trace.to_dict() if catalog.source_trace else None,
        }

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            source=self.name,
            display_name="TJSE Jurisprudência Judicial",
            source_url=self.config.tjse_jurisprudencia_url,
            category="court_jurisprudence",
            search_modes=[
                "text",
                "case_number",
                "date_range",
                "summary",
                "full_text",
                "authorized_human_challenge",
            ],
            document_types=["acordao", "monocratic_decision"],
            content_formats=["html", "jsf"],
            canonical_records=["CanonicalDecision"],
            extracted_fields=[
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "summary",
                "full_text",
                "document_url",
            ],
            access_statuses=[
                AccessStatus.ACCESS_CONTROL_REQUIRED,
                AccessStatus.PUBLIC,
                AccessStatus.SOURCE_UNAVAILABLE,
            ],
            endpoints=[
                "GET /Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse",
                "POST /Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse",
            ],
            supports_full_text=False,
            supports_catalog=True,
            supports_unified_search=False,
            supports_mcp=True,
            supports_cli=True,
            supports_live_tests=True,
            pagination_mode="unknown_until_challenge_passed",
            completeness_contract="unknown_until_challenge_passed",
            full_text_access="access_blocked",
            supported_filters=[
                "text",
                "number",
                "case_class",
                "rapporteur",
                "judging_body",
                "degree",
                "instance",
                "document_type",
                "judgment_date_from",
                "judgment_date_to",
            ],
            unsupported_filters=["party_name", "lawyer_name", "oab", "updated_from", "updated_to"],
            filter_semantics={
                "text": "native",
                "number": "native",
                "case_class": "native",
                "rapporteur": "native",
                "judging_body": "native",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "document_type": "native",
                "judgment_date_from": "native",
                "judgment_date_to": "native",
                "party_name": "unsupported",
                "lawyer_name": "unsupported",
                "oab": "unsupported",
                "updated_from": "unsupported",
                "updated_to": "unsupported",
            },
            limitations=[
                "A submissão pública exige Cloudflare Turnstile.",
                "Nenhum token, cookie ou sessão humana é persistido.",
                "Resultado, paginação e inteiro teor ainda não possuem contrato reproduzível.",
            ],
            responsible_use=["Não contornar CAPTCHA/Turnstile ou controles de frequência."],
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        data: dict[str, str] | None = None,
        operation: str = "form_discovery",
    ):
        request = TransportRequest(
            source=self.name,
            operation=operation,
            method=method,
            url=url,
            data=data,
            idempotent=method.upper() in {"GET", "HEAD", "OPTIONS"},
        )
        try:
            response = self.transport.request(request)
        except requests.exceptions.Timeout as exc:
            raise SourceUnavailableError("TJSE request timeout") from exc
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError("TJSE TLS negotiation failed") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJSE request failed") from exc
        except SourceUnavailableError as exc:
            raise SourceUnavailableError(f"TJSE request failed: {exc}") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJSE transport failed: {response.error_type or response.status.value}"
            )
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJSE transport returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJSE returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(
                f"TJSE returned HTTP {status_code} during public form discovery"
            )
        if status_code < 200 or status_code >= 300:
            raise SourceUnavailableError(f"TJSE returned HTTP {status_code}")
        return response


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJSE exige termo, número do processo ou frase exata")
    if query.degree and query.degree.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJSE judicial suporta somente segundo grau")
    if query.instance and query.instance.casefold() not in {"second", "segundo", "2"}:
        raise QueryRejectedError("TJSE judicial suporta somente instância de segundo grau")
    if query.branch and query.branch.casefold() not in {"state", "estadual"}:
        raise QueryRejectedError("TJSE pertence ao ramo estadual")
    if query.authority and query.authority.casefold() not in {
        "tjse",
        "tribunal de justiça de sergipe",
    }:
        raise QueryRejectedError("a autoridade solicitada não corresponde ao TJSE")


def _has_challenge(markup: str) -> bool:
    lowered = markup.casefold()
    return any(marker in lowered for marker in _CHALLENGE_MARKERS)


def _has_invalid_challenge(markup: str) -> bool:
    lowered = " ".join(markup.casefold().split())
    return any(
        marker in lowered
        for marker in (
            "captcha inval",
            "turnstile inval",
            "desafio inval",
            "token inval",
            "challenge failed",
        )
    )


def _has_authoritative_empty(markup: str) -> bool:
    lowered = " ".join(markup.casefold().split())
    return any(
        marker in lowered
        for marker in (
            "nenhum resultado",
            "nao foram encontrados resultados",
            "não foram encontrados resultados",
            "sem resultados para a pesquisa",
        )
    )


def _build_form_payload(form: object, query: JurisprudenceQuery, token: str) -> dict[str, str]:
    """Serialize only ordinary form controls plus the explicit user query."""

    payload: dict[str, str] = {}
    for element in getattr(form, "select", lambda *_args: [])("input[name], textarea[name]"):
        name = str(element.get("name") or "").strip()
        if not name:
            continue
        input_type = str(element.get("type") or "text").casefold()
        if input_type in {"radio", "checkbox"} and not element.has_attr("checked"):
            continue
        payload[name] = str(element.get("value") or element.text or "").strip()
    for element in getattr(form, "select", lambda *_args: [])("select[name]"):
        name = str(element.get("name") or "").strip()
        if not name:
            continue
        selected = element.select_one("option[selected]") or element.select_one("option")
        if selected is not None:
            payload[name] = str(selected.get("value") or selected.text or "").strip()

    payload["itTermos"] = (query.exact_phrase or query.text or query.all_words).strip()
    if query.number.strip():
        payload["nrUnico"] = query.number.strip()
        payload["nrProc"] = query.number.strip()
    if query.judgment_date_from.strip():
        payload["dtInicial_input"] = query.judgment_date_from.strip()
    if query.judgment_date_to.strip():
        payload["dtFinal_input"] = query.judgment_date_to.strip()
    payload["sorCompetencia"] = "SG"
    payload["turnstile-hidden"] = token
    return payload


def _parse_authorized_results(markup: str, trace: SourceTrace) -> list[JurisprudenceResult]:
    """Parse only result containers with a stable id or explicit data marker."""

    soup = BeautifulSoup(markup, "html.parser")
    containers = soup.select(
        ".resultado, .resultadoJurisprudencia, [data-jurisprudencia-id], [data-id]"
    )
    results: list[JurisprudenceResult] = []
    for index, container in enumerate(containers, start=1):
        text = " ".join(container.get_text(" ", strip=True).split())
        if not text:
            continue
        identifier = str(
            container.get("data-jurisprudencia-id")
            or container.get("data-id")
            or container.get("id")
            or ""
        ).strip()
        if not identifier:
            identifier = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
        summary_node = container.select_one(".ementa, .summary, .resumo, .texto")
        summary = (
            " ".join(summary_node.get_text(" ", strip=True).split())
            if summary_node is not None
            else text
        )
        link = container.select_one("a[href]")
        document_url = str(link.get("href") or "").strip() if link else None
        case_match = re.search(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b", text)
        results.append(
            JurisprudenceResult(
                id=identifier,
                source="tjse_jurisprudencia",
                court="TJSE",
                type="acordao",
                number=case_match.group(0) if case_match else None,
                summary=summary,
                full_text=text,
                degree="second",
                instance="second",
                branch="state",
                authority="TJSE",
                collection="CJSG",
                document_type="acordao",
                document_url=document_url,
                source_trace=trace,
                raw={"result_index": index, "parser": "authorized_form_v1"},
            )
        )
    return results


def _select_options(soup: BeautifulSoup, selector: str) -> list[dict[str, str]]:
    select = soup.select_one(selector)
    if select is None:
        return []
    options: list[dict[str, str]] = []
    for option in select.select("option"):
        value = str(option.get("value") or "").strip()
        description = " ".join(option.get_text(" ", strip=True).split())
        if value or description:
            options.append({"code": value or description, "description": description or value})
    return options


def _radio_values(soup: BeautifulSoup, name: str) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for element in soup.select(f"input[type='radio'][name='{name}']"):
        value = str(element.get("value") or "").strip()
        if value:
            values.append({"code": value, "description": value})
    return values


def _trace(response: object, endpoint: str) -> SourceTrace:
    body = getattr(response, "body", b"")
    return SourceTrace(
        provider="tjse_jurisprudencia",
        endpoint=endpoint,
        source_url="https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse",
        final_url=getattr(response, "final_url", None),
        http_status=getattr(response, "status_code", None),
        content_type=(getattr(response, "content_type", None) or None),
        content_sha256=getattr(response, "content_sha256", None)
        or hashlib.sha256(body).hexdigest(),
        response_bytes=len(body),
        query={},
        retrieval_status="ok",
        transformations=["jsf_filter_catalog"],
    )
