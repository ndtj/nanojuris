"""TJAC official static Ementario de Jurisprudencia provider.

The TJAC publishes editorial volumes containing appellate ementas.  The
provider treats a volume as a bounded local window: it never claims a remote
total or a complete national corpus, and it does not persist a searchable
document index.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
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
MAX_PAGES = 300
MAX_RESULTS = 100
_OFFICIAL_HOST = "www.tjac.jus.br"
_CNJ_RE = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}\b")
_HEADER_RE = re.compile(r"(?=\bTRIBUNAL\s+(?:PLENO|DE JUSTI[ÇC]A|C[ÂA]MARA))", re.I)
_RELATOR_RE = re.compile(r"Relator(?:a)?\s*:\s*(?P<value>[^\n]+)", re.I)
_DATE_RE = re.compile(r"Julgado\s+em\s+(?P<value>\d{1,2}[./]\d{1,2}[./]\d{4})", re.I)
_FOOTER_RE = re.compile(r"Ement[áa]rio.*?\b\d+\s*/\s*\d+\b", re.I | re.S)
_NOISE_RE = re.compile(r"^(?:EMENTA|DISPOSITIVO|TRIBUNAL DE JUSTI[ÇC]A.*|\d+\s*/\s*\d+)$", re.I)


class TjacEmentarioJurisprudenciaProvider(JurisprudenceProvider):
    """Read the current official TJAC appellate ementario volume."""

    name = "tjac_ementario_jurisprudencia"

    def __init__(
        self,
        config: NanoJurisConfig | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.config = config or NanoJurisConfig()
        self.session = configure_requests_session(session or requests.Session(), self.config)
        host = urlparse(self.volume_url).hostname or _OFFICIAL_HOST
        self.http = SharedHttpClient(
            TransportPolicy(
                allowed_hosts=(host,),
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
        return self.config.tjac_ementario_url

    def search(self, query: JurisprudenceQuery) -> SearchPage:
        _validate_query(query)
        content, trace = self._request_pdf(query)
        records = parse_tjac_ementario_pdf(content, query=query, trace=trace)
        for record in records:
            self._records[record.id] = record
        start = (query.page - 1) * min(query.page_size, MAX_RESULTS)
        page_results = records[start : start + min(query.page_size, MAX_RESULTS)]
        return SearchPage(
            source=self.name,
            total=len(records),
            start=start,
            end=start + len(page_results),
            page=query.page,
            page_size=min(query.page_size, MAX_RESULTS),
            results=page_results,
            source_trace=trace,
            pagination_mode="local_pdf_window",
            is_complete=False,
            completeness_reason=(
                "volume oficial estatico; o TJAC nao publica total pesquisavel "
                "entre volumes e a janela nao representa o acervo integral"
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
            raise SourceUnavailableError("TJAC Ementario exige resultado observado na sessao")
        text = result.full_text or result.summary or ""
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
            raise SourceUnavailableError("TJAC Ementario exige resultado observado na sessao")
        text = result.full_text or result.summary or ""
        return build_canonical_document(
            document_id=document_id,
            source=self.name,
            document_type="acordao_ementa",
            content=text.encode("utf-8"),
            content_type="text/plain",
            title=f"TJAC Ementario {result.number or document_id}",
            text_override=text,
            url=result.document_url,
            source_trace=result.source_trace,
            access_status=AccessStatus.PUBLIC,
            raw_metadata={"volume_only": True, "collection": "TJAC_EMENTARIO"},
            parser="tjac_ementario_jurisprudencia.pdf_text",
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
        return ProviderCapabilities(
            source=self.name,
            display_name="TJAC Ementario de Jurisprudencia",
            source_url="https://www.tjac.jus.br/transparencia/relatorios-e-estatisticas/ementario-jurisprudencial/",
            category="court_jurisprudence",
            search_modes=["text", "exact_phrase", "case_number", "summary", "page"],
            document_types=["acordao_ementa"],
            content_formats=["pdf", "text"],
            canonical_records=["CanonicalDecision", "CanonicalDocument"],
            semantic_discriminator="official TJAC appellate ementario volume",
            extracted_fields=[
                "source_record_id",
                "case_number",
                "case_class",
                "rapporteur",
                "judging_body",
                "judgment_date",
                "summary",
                "full_text",
                "document_url",
                "degree",
                "instance",
                "branch",
                "authority",
                "collection",
            ],
            access_statuses=[AccessStatus.PUBLIC, AccessStatus.SOURCE_UNAVAILABLE],
            endpoints=["GET official TJAC Ementario PDF"],
            supports_full_text=False,
            supports_live_tests=True,
            supports_cli=True,
            supports_mcp=True,
            supports_studio=True,
            supports_unified_search=True,
            opt_in_unified_search=False,
            pagination_mode="local_pdf_window",
            max_remote_page_size=MAX_RESULTS,
            completeness_contract="static_volume_total_unknown",
            full_text_access="summary_only",
            supported_filters=[
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
            ],
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
                **{name: "unsupported" for name in unsupported},
            },
            limitations=[
                "Colecao editorial estatica; nao substitui a busca CJSG online.",
                "O volume nao informa total autoritativo entre edicoes.",
                "O provider nao executa OCR em paginas imagem-only.",
                "O documento individual nao foi publicado como link separado.",
            ],
            responsible_use=[
                "Consultar no maximo um volume por busca e respeitar o rate limit.",
                "Nao tratar ausencia de termo no volume como ausencia nacional.",
                "Nao converter PDF invalido ou indisponivel em resultado vazio.",
            ],
        )

    def _request_pdf(self, query: JurisprudenceQuery) -> tuple[bytes, SourceTrace]:
        parsed = urlparse(self.volume_url)
        if parsed.scheme != "https" or parsed.hostname != _OFFICIAL_HOST:
            raise ParserContractChangedError("TJAC Ementario URL fora da allowlist oficial")
        request = TransportRequest(
            source=self.name,
            operation="tjac_ementario_pdf",
            method="GET",
            url=self.volume_url,
            headers={"Accept": "application/pdf"},
            idempotent=True,
        )
        try:
            response = self.http.request(request)
        except requests.exceptions.Timeout as exc:
            raise SourceUnavailableError("TJAC Ementario timeout") from exc
        except requests.exceptions.SSLError as exc:
            raise SourceUnavailableError("TJAC Ementario TLS negotiation failed") from exc
        except requests.RequestException as exc:
            raise SourceUnavailableError("TJAC Ementario request failed") from exc
        if response.status is not TransportStatus.COMPLETE:
            raise SourceUnavailableError(
                f"TJAC Ementario transport failed: {response.error_type or response.status.value}"
            )
        body = response.body
        final_url = str(response.final_url or self.volume_url)
        self._last_http = {
            "http_status": response.status_code,
            "final_url": final_url,
            "content_type": response.content_type,
            "content_sha256": response.content_sha256 or hashlib.sha256(body).hexdigest(),
            "response_bytes": len(body),
            "elapsed_ms": response.elapsed_ms,
            "retrieval_status": "ok"
            if response.status_code is not None and 200 <= response.status_code < 300
            else "error",
        }
        final_host = urlparse(final_url).hostname
        if final_host != _OFFICIAL_HOST:
            raise ParserContractChangedError("TJAC Ementario redirecionou para host nao oficial")
        status_code = response.status_code
        if status_code is None:
            raise SourceUnavailableError("TJAC Ementario returned no HTTP status")
        if status_code == 429:
            raise RateLimitDetectedError("TJAC Ementario returned HTTP 429")
        if status_code in {401, 403, 407, 451}:
            raise AccessControlRequiredError(f"TJAC Ementario returned HTTP {status_code}")
        if status_code < 200 or status_code >= 300:
            raise SourceUnavailableError(f"TJAC Ementario returned HTTP {status_code}")
        if len(body) > MAX_PDF_BYTES or not body.startswith(b"%PDF-"):
            raise ParserContractChangedError(
                "TJAC Ementario nao retornou PDF valido dentro do limite"
            )
        trace = SourceTrace(
            provider=self.name,
            endpoint="GET /wp-content/uploads/.../Ementario_TJAC_Vol_XXX_2026.pdf",
            query=query.to_dict(),
            source_url=self.volume_url,
            limitations=[
                "Volume semestral oficial; total entre volumes desconhecido.",
                "Ementas textuais; voto integral nao foi publicado no volume.",
            ],
            **self._last_http,
        )
        return body, trace


def parse_tjac_ementario_pdf(
    content: bytes, *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    """Parse a bounded official PDF without creating a local searchable index."""

    try:
        reader = PdfReader(BytesIO(content), strict=False)
    except Exception as exc:  # noqa: BLE001
        raise ParserContractChangedError("TJAC Ementario PDF malformado") from exc
    if len(reader.pages) > MAX_PAGES:
        raise ParserContractChangedError("TJAC Ementario PDF excede o limite de paginas")
    pages = [str(page.extract_text() or "") for page in reader.pages]
    return parse_tjac_ementario_text("\n".join(pages), query=query, trace=trace)


def parse_tjac_ementario_text(
    text: str, *, query: JurisprudenceQuery, trace: SourceTrace
) -> list[JurisprudenceResult]:
    blocks = [block.strip() for block in _HEADER_RE.split(text) if block.strip()]
    records: list[JurisprudenceResult] = []
    record_blocks: list[tuple[int, str]] = []
    for index, block in enumerate(blocks):
        if _CNJ_RE.search(block) is None:
            continue
        continuation: list[str] = []
        for following in blocks[index + 1 :]:
            if _CNJ_RE.search(following) is not None:
                break
            continuation.append(following)
        record_blocks.append((index, "\n".join([block, *continuation])))
    for index, block in record_blocks:
        match = _CNJ_RE.search(block)
        assert match is not None
        case_number = str(match.group(0) or "")
        header = block[: match.start()].strip()
        body = block[match.end() :]
        date_match = _DATE_RE.search(body)
        judgment_date = _parse_date(date_match.group("value")) if date_match else None
        if date_match:
            body = body[date_match.end() :]
        relator_match = _RELATOR_RE.search(block)
        rapporteur = _clean_fragment(relator_match.group("value")) if relator_match else None
        summary = _summary_text(body)
        if not summary:
            continue
        normalized_query = _query_terms(query.exact_phrase or query.text or query.number)
        haystack = _norm(f"{case_number} {header} {summary}")
        if query.number and _norm(query.number) not in haystack:
            continue
        if normalized_query and not all(term in haystack for term in normalized_query):
            continue
        excluded = _query_terms(query.without_words)
        if excluded and any(term in haystack for term in excluded):
            continue
        identity_material = "|".join((str(trace.source_url or ""), case_number, _norm(summary)))
        record_id = (
            "tjac-ementario-" + hashlib.sha256(identity_material.encode("utf-8")).hexdigest()[:24]
        )
        records.append(
            JurisprudenceResult(
                id=record_id,
                source="tjac_ementario_jurisprudencia",
                court="TJAC",
                type="acordao_ementa",
                number=case_number,
                case_class=_clean_fragment(header.splitlines()[-1] if header else "") or None,
                summary=summary,
                full_text=summary,
                rapporteur=rapporteur,
                judgment_date=judgment_date,
                access_status=AccessStatus.PUBLIC,
                extraction_status=ExtractionStatus.COMPLETE,
                source_trace=trace,
                raw={
                    "source_record_id": record_id,
                    "volume_url": trace.source_url,
                    "header": _clean_fragment(header),
                    "record_index": index,
                    "source_scope": "Tribunal Pleno Jurisdicional",
                },
                degree="second",
                instance="second",
                branch="state",
                authority="TJAC",
                collection="TJAC_EMENTARIO",
                document_type="acordao_ementa",
                source_origin="tjac_ementario_pdf",
                document_url=trace.source_url,
                field_provenance={
                    "source_record_id": {
                        "value": record_id,
                        "method": "case_number_summary_volume_fingerprint",
                    },
                    "degree": {"value": "second", "method": "official_tribunal_pleno_scope"},
                    "instance": {"value": "second", "method": "official_tribunal_pleno_scope"},
                    "case_number": {"value": case_number, "method": "cnj_pattern"},
                },
            )
        )
    return records


def _validate_query(query: JurisprudenceQuery) -> None:
    if not any((query.text.strip(), query.number.strip(), query.exact_phrase.strip())):
        raise QueryRejectedError("TJAC Ementario exige termo, numero ou frase exata")
    if query.degree and _norm(query.degree) not in {"second", "segundo", "2", "2g"}:
        raise QueryRejectedError("TJAC Ementario suporta somente segundo grau")
    if query.instance and _norm(query.instance) not in {"second", "segundo", "2", "2g"}:
        raise QueryRejectedError("TJAC Ementario suporta somente instancia de segundo grau")
    if query.branch and _norm(query.branch) not in {"state", "estadual", "justica estadual"}:
        raise QueryRejectedError("TJAC Ementario pertence ao ramo estadual")
    if query.authority and _norm(query.authority) not in {"tjac", "acre"}:
        raise QueryRejectedError("a autoridade solicitada nao corresponde ao TJAC")
    if query.collection and _norm(query.collection) not in {
        "tjac ementario",
        "tjac_ementario",
        "cjsg",
    }:
        raise QueryRejectedError("colecao TJAC Ementario desconhecida")


def _summary_text(value: str) -> str:
    value = _FOOTER_RE.sub(" ", value)
    value = re.split(
        r"\b(?:Dispositivos relevantes citados|Jurisprud[êe]ncia relevante citada)\b",
        value,
        maxsplit=1,
        flags=re.I,
    )[0]
    lines = []
    for line in value.splitlines():
        clean = _clean_fragment(line)
        if not clean or _NOISE_RE.match(clean):
            continue
        if clean.casefold().startswith("ementario semestral"):
            continue
        lines.append(clean)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()[:12000]


def _clean_fragment(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\ufffd", " ")).strip(" -")


def _parse_date(value: str) -> str | None:
    normalized = value.replace("/", ".")
    try:
        return datetime.strptime(normalized, "%d.%m.%Y").date().isoformat()
    except ValueError:
        return None


def _query_terms(value: str) -> list[str]:
    return [term for term in _norm(value).split() if len(term) >= 3]


def _norm(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


__all__ = [
    "TjacEmentarioJurisprudenciaProvider",
    "parse_tjac_ementario_pdf",
    "parse_tjac_ementario_text",
]
