"""Official TJAL Turmas Recursais ementario provider.

The source publishes selected historical ementas as PDF volumes.  It is a
recursal collection, not CJPG or CJSG, and therefore keeps an explicit
``degree=recursal`` identity.  The provider performs bounded, in-memory PDF
extraction and never builds a persistent index.
"""

from __future__ import annotations

import hashlib
import re
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

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
    SearchPage,
    SourceTrace,
)
from nanojuris.providers.base import JurisprudenceProvider
from nanojuris.transport import SharedHttpClient
from nanojuris.transport.models import TransportPolicy, TransportRequest, TransportStatus

MAX_PDF_BYTES = 8_000_000
MAX_PAGES = 700
MAX_RESULTS = 100
_OFFICIAL_HOST = "aceco.tjal.jus.br"
_PROCESS_RE = re.compile(
    r"(?im)(?=^\s*(?:PROC(?:ESSO)?\.?\s*(?:N[ÃÂºOÂ°]\s*)?|"
    r"Procn[ÃÂºOÂ°0o]?\s*|Recurso\s+Inominado\s*(?:N[ÃÂºOÂ°]\s*)?))"
)
_NUMBER_RE = re.compile(
    r"(?:PROC(?:ESSO)?\.?|Procn|Recurso\s+Inominado)\s*(?:N[ÃÂºOÂ°]\s*)?"
    r"(?P<value>[A-Z0-9][A-Z0-9./-]{2,})",
    re.I,
)
_SAJ_RE = re.compile(r"SAJ\s*(?:N[ÃÂºOÂ°]\s*)?(?P<value>[0-9][0-9.-]+)", re.I)
_RELATOR_RE = re.compile(r"Relator(?:a)?\s*:\s*(?P<value>[^\n]+)", re.I)
_ORIGIN_RE = re.compile(r"Origem\s*:\s*(?P<value>[^\n]+)", re.I)
_HEADER_RE = re.compile(r"^\s*(?:EMENTA|_EMENTA_|AC[ÃÂ³O]RD[ÃÂA]O)\s*:?", re.I)
_NOISE_RE = re.compile(
    r"^(?:PODER JUDICI[ÃÂA]RIO.*|COORDENADORIA.*|TELEFONE.*|PUBLICA[ÃÂC][ÃÂA]O.*)$",
    re.I,
)

# Keep parser markers ASCII-tolerant because legacy PDF extraction commonly
# replaces ordinal/accented glyphs with replacement characters.
_PROCESS_RE = re.compile(r"(?im)(?=^\s*(?:PROC(?:ESSO)?\.?|Procn\b|Recurso\s+Inominado\b))")
_NUMBER_RE = re.compile(
    r"(?:PROC(?:ESSO)?\.?|Procn|Recurso\s+Inominado)\s*"
    r"(?:N(?:\u00ba|\u00b0|\ufffd)?[\s.:-]{0,5})?"
    r"(?P<value>[A-Z0-9][A-Z0-9./-]{2,})",
    re.I,
)
_SAJ_RE = re.compile(
    r"SAJ\s*(?:N(?:\u00ba|\u00b0|\ufffd)?[\s.:-]{0,5})?"
    r"(?P<value>[0-9][0-9.-]+)",
    re.I,
)
_HEADER_RE = re.compile(r"^\s*(?:EMENTA|_EMENTA_|AC.RD)\s*:??", re.I)
_NOISE_RE = re.compile(r"^(?:PODER JUDICI.*|COORDENADORIA.*|TELEFONE.*|PUBLICA.*)$", re.I)


class TjalTurmaRecursalEmentarioProvider(JurisprudenceProvider):
    """Read one bounded official TJAL Turmas Recursais PDF volume."""

    name = "tjal_turma_recursal_ementario"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        self.transport = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(_OFFICIAL_HOST,),
                timeout_seconds=self.config.timeout,
                max_bytes=MAX_PDF_BYTES,
                max_retries=0,
                rate_limit_interval=self.config.rate_limit_interval,
                user_agent=self.config.user_agent,
                verify_ssl=self.config.verify_ssl,
            ),
            session=self.session,
        )
        self._last_http: dict[str, Any] = {}
        self._records: dict[str, JurisprudenceResult] = {}

    @property
    def volume_url(self) -> str:
        return self.config.tjal_turma_recursal_volume_url

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        content, trace = self._request_pdf(query)
        records = parse_tjal_turma_recursal_pdf(content, query=query, trace=trace)
        for record in records:
            self._records[record.id] = record
        page_size = min(query.page_size, MAX_RESULTS)
        start = (query.page - 1) * page_size
        page_results = records[start : start + page_size]
        return SearchPage(
            source=self.name,
            total=len(records),
            start=start,
            end=start + len(page_results),
            page=query.page,
            page_size=page_size,
            results=page_results,
            source_trace=trace,
            pagination_mode="local_pdf_window",
            is_complete=False,
            completeness_reason=(
                "volume editorial historico; a fonte nao publica total "
                "autoritativo nem acervo integral de Turmas Recursais"
            ),
            ordering="source_order",
            filters_applied={
                "text": "local_postfilter",
                "exact_phrase": "local_postfilter",
                "number": "local_postfilter",
                "without_words": "local_postfilter",
                "degree": "validated_scope",
                "instance": "validated_scope",
                "branch": "validated_scope",
                "authority": "validated_scope",
                "collection": "validated_scope",
            },
            total_known=False,
            access_status=AccessStatus.PUBLIC,
            extraction_status=ExtractionStatus.COMPLETE,
        )

    def get_decisions(self, precedent_id: str) -> DecisionBundle:
        result = self._records.get(precedent_id)
        if result is None:
            raise SourceUnavailableError(
                "TJAL Turmas Recursais exige resultado observado na sessao"
            )
        text = result.summary or ""
        return DecisionBundle(
            precedent_id=precedent_id,
            source=self.name,
            texts=[{"content": text, "content_type": "text/plain"}],
            procedural_follow_url=result.document_url,
            source_trace=result.source_trace,
            raw={"volume_url": result.document_url, "source_id": result.id},
        )

    def get_document(self, document_id: str) -> CanonicalDocument:
        result = self._records.get(document_id)
        if result is None:
            raise SourceUnavailableError(
                "TJAL Turmas Recursais exige resultado observado na sessao"
            )
        text = result.summary or ""
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao_ementa_recursal",
            content=text.encode("utf-8"),
            content_type="text/plain",
            title=f"TJAL Turmas Recursais {result.number or document_id}",
            text_override=text,
            url=result.document_url,
            source_trace=result.source_trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={
                "volume_only": True,
                "collection": "TJAL_TURMAS_RECURSAIS",
                "degree": "recursal",
            },
            parser="tjal_turma_recursal_ementario.pdf_text",
        )

    def get_capabilities(self) -> ProviderCapabilities:
        unsupported = [
            "all_words",
            "any_words",
            "courts",
            "case_class",
            "judging_body",
            "rapporteur",
            "judgment_date_from",
            "judgment_date_to",
            "published_from",
            "published_to",
            "party_name",
            "party_document",
            "fetch_details",
            "types",
            "updated_from",
            "updated_to",
            "lawyer_name",
            "oab",
            "precatory_number",
            "police_document",
            "cda",
            "source_origin",
            "source_origins",
            "legal_area",
            "document_type",
            "decision_type",
        ]
        supported = [
            "text",
            "exact_phrase",
            "number",
            "without_words",
            "degree",
            "instance",
            "branch",
            "authority",
            "collection",
            "page",
        ]
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAL Ementario das Turmas Recursais",
            source_url=self.config.tjal_turma_recursal_index_url,
            category="court_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "summary", "page"],
            document_types=["acordao_ementa", "recurso_inominado", "decisao"],
            content_formats=["pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator=(
                "official TJAL Turmas Recursais; degree=recursal; instance=turma_recursal"
            ),
            extracted_fields=[
                "case_number",
                "decision_type",
                "case_class",
                "rapporteur",
                "judging_body",
                "summary",
                "judgment_date",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
                "source_origin",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=[
                "GET /?pag=juizados_jurisprudencias",
                "GET /juizados/relatorios/Ementas-3.pdf",
            ],
            supports_full_text=False,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=False,
            opt_in_unified_search=True,
            pagination_mode="local_pdf_window",
            max_remote_page_size=MAX_RESULTS,
            completeness_contract="static_volume_total_unknown",
            full_text_access="summary_only",
            supported_filters=supported,
            unsupported_filters=unsupported,
            filter_semantics={
                **{
                    name: "local_postfilter"
                    for name in ("text", "exact_phrase", "number", "without_words")
                },
                **{
                    name: "validated_scope"
                    for name in ("degree", "instance", "branch", "authority", "collection")
                },
                "page": "local_postfilter",
                **{name: "unsupported" for name in unsupported},
            },
            ordering_modes=["source_order"],
            detail_modes=["inline_ementa"],
            limitations=[
                "Colecao editorial historica; nao substitui busca CJSG/CJPG.",
                "Turmas Recursais sao mantidas fora de first/second degree.",
                "Volumes image-only nao sao submetidos a OCR.",
                "Nao ha total remoto nem link individual de decisao.",
            ],
            responsible_use=[
                "Consultar no maximo um volume por busca e respeitar o rate limit.",
                "Nao tratar ausencia de termo no volume como ausencia nacional.",
                "Nao converter PDF indisponivel ou sem texto em resultado vazio.",
            ],
        )

    def _request_pdf(self, query: JurisprudenceQuery) -> tuple[bytes, SourceTrace]:
        parsed = urlparse(self.volume_url)
        if parsed.scheme != "https" or parsed.hostname != _OFFICIAL_HOST:
            raise ParserContractChangedError("TJAL Turmas Recursais fora da allowlist")
        request = TransportRequest(
            source=self.name,
            operation="turma_recursal_volume",
            method="GET",
            url=self.volume_url,
            headers={
                "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
                "User-Agent": self.config.user_agent,
            },
            idempotent=True,
        )
        try:
            response = self.transport.request(request)
        except SourceUnavailableError:
            raise
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJAL Turmas Recursais request failed") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                "TJAL Turmas Recursais transport failed: "
                f"{response.error_type or response.status.value}"
            )
        if response.status_code is None:
            raise SourceUnavailableError("TJAL Turmas Recursais transport returned no status")
        body = bytes(response.body)
        final_url = str(response.final_url or self.volume_url)
        self._last_http = {
            "http_status": response.status_code,
            "final_url": final_url,
            "content_type": response.content_type,
            "content_sha256": hashlib.sha256(body).hexdigest(),
            "response_bytes": len(body),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok" if 200 <= response.status_code < 300 else "error",
        }
        if urlparse(final_url).hostname != _OFFICIAL_HOST:
            raise ParserContractChangedError("TJAL Turmas Recursais redirect fora da allowlist")
        if response.status_code == 429:
            raise RateLimitDetectedError("TJAL Turmas Recursais returned HTTP 429")
        if response.status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(
                f"TJAL Turmas Recursais returned HTTP {response.status_code}"
            )
        if response.status_code < 200 or response.status_code >= 300:
            raise SourceUnavailableError(
                f"TJAL Turmas Recursais returned HTTP {response.status_code}"
            )
        if len(body) > MAX_PDF_BYTES or not body.startswith(b"%PDF-"):
            raise ParserContractChangedError("TJAL Turmas Recursais PDF invalido ou excedido")
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /juizados/relatorios/Ementas-3.pdf",
            query=query.to_dict(),
            source_url=self.volume_url,
            limitations=[
                "Volume historico oficial; total entre volumes desconhecido.",
                "Ementas de Turmas Recursais; nao sao CJPG/CJSG.",
            ],
            **self._last_http,
        )
        return body, trace


def parse_tjal_turma_recursal_pdf(
    content: bytes, *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    """Parse a bounded TJAL volume without persisting a searchable index."""

    try:
        reader = PdfReader(BytesIO(content), strict=False)
    except Exception as exc:  # noqa: BLE001
        raise ParserContractChangedError("TJAL Turmas Recursais PDF malformado") from exc
    if len(reader.pages) > MAX_PAGES:
        raise ParserContractChangedError("TJAL Turmas Recursais PDF excede paginas")
    page_texts = [str(page.extract_text() or "") for page in reader.pages]
    if not any(text.strip() for text in page_texts):
        raise ParserContractChangedError("TJAL Turmas Recursais PDF sem texto extraivel")
    return parse_tjal_turma_recursal_text("\n".join(page_texts), query=query, trace=trace)


def parse_tjal_turma_recursal_text(
    text: str, *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    blocks = [block.strip() for block in _PROCESS_RE.split(text) if block.strip()]
    records: list[JurisprudenceResult] = []
    for index, block in enumerate(blocks):
        number_match = _NUMBER_RE.search(block) or _SAJ_RE.search(block)
        number = number_match.group("value") if number_match else None
        if not number and not re.search(r"EMENTA|AC.RD", block, re.I):
            continue
        summary = _summary_text(block)
        if len(summary) < 25:
            continue
        haystack = _norm(f"{number or ''} {block}")
        terms = _query_terms(query.exact_phrase or query.text or query.number)
        if terms and not all(term in haystack for term in terms):
            continue
        excluded = _query_terms(query.without_words)
        if excluded and any(term in haystack for term in excluded):
            continue
        rapporteur_match = _RELATOR_RE.search(block)
        origin_match = _ORIGIN_RE.search(block)
        decision_type = "acordao" if re.search(r"AC.RD", block, re.I) else "decisao"
        record_id = (
            "tjal-recursal-"
            + hashlib.sha256(f"{trace.source_url}|{number or index}|{index}".encode()).hexdigest()[
                :24
            ]
        )
        records.append(
            JurisprudenceResult(
                id=record_id,
                source="tjal_turma_recursal_ementario",
                court="TJAL",
                type=decision_type,
                number=number,
                summary=summary,
                full_text=summary,
                rapporteur=(
                    _clean_fragment(rapporteur_match.group("value")) if rapporteur_match else None
                ),
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                raw={
                    "volume_url": trace.source_url,
                    "record_index": index,
                    "origin": _clean_fragment(origin_match.group("value"))
                    if origin_match
                    else None,
                    "source_scope": "Turmas Recursais TJAL",
                },
                degree="recursal",
                instance="turma_recursal",
                branch="state",
                authority="TJAL",
                collection="TJAL_TURMAS_RECURSAIS",
                document_type="acordao_ementa" if decision_type == "acordao" else "decisao",
                source_origin="tjal_recursal_pdf",
                document_url=trace.source_url,
                field_provenance={
                    "degree": {"value": "recursal", "method": "official_scope"},
                    "instance": {
                        "value": "turma_recursal",
                        "method": "official_scope",
                    },
                    "number": {
                        "value": number,
                        "method": "source_process_marker",
                    },
                },
            )
        )
    return records


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJAL Turmas Recursais exige termo, numero ou frase")
    if query.degree and _norm(query.degree) not in {"recursal", "turma recursal", "juizado"}:
        raise QueryRejectedError("TJAL Turmas Recursais suporta somente grau recursal")
    if query.instance and _norm(query.instance) not in {
        "turma recursal",
        "turma_recursal",
        "recursal",
    }:
        raise QueryRejectedError("TJAL Turmas Recursais suporta somente instancia recursal")
    if query.branch and _norm(query.branch) not in {"state", "estadual", "justica estadual"}:
        raise QueryRejectedError("a autoridade pertence ao ramo estadual")
    if query.authority and _norm(query.authority) not in {"tjal", "alagoas"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TJAL")
    if query.collection and _norm(query.collection) not in {
        "tjal turmas recursais",
        "tjal_turmas_recursais",
        "turmas recursais",
    }:
        raise QueryRejectedError("colecao TJAL Turmas Recursais desconhecida")


def _summary_text(value: str) -> str:
    match = _HEADER_RE.search(value)
    value = value[match.end() :] if match else value
    lines = []
    for line in value.splitlines():
        clean = _clean_fragment(line)
        if not clean or _NOISE_RE.match(clean):
            continue
        lines.append(clean)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()[:12000]


def _clean_fragment(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\ufffd", " ")).strip(" -")


def _query_terms(value: str) -> list[str]:
    return [term for term in _norm(value).split() if len(term) >= 3]


def _norm(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


__all__ = [
    "TjalTurmaRecursalEmentarioProvider",
    "parse_tjal_turma_recursal_pdf",
    "parse_tjal_turma_recursal_text",
]
