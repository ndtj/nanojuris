"""Utilities to evaluate public jurisprudence route candidates."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

import requests
from bs4 import BeautifulSoup

RouteStatus = Literal[
    "live_valid",
    "candidate",
    "partial_response",
    "access_control_or_login",
    "not_found",
    "source_unavailable",
    "invalid_response",
]


DEFAULT_ACCEPT = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7"
)
LEGAL_SIGNAL_PATTERNS = {
    "case_number": r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b",
    "acordao": r"\bac[oó]rd[aã]o\b",
    "ementa": r"\bementa\b",
    "jurisprudencia": r"\bjurisprud[eê]ncia\b",
    "relator": r"\brelator(?:a)?\b",
    "judging_body": r"\b(?:[oó]rg[aã]o julgador|turma|c[aâ]mara|se[cç][aã]o)\b",
    "decision": r"\b(?:decis[aã]o|senten[cç]a|voto)\b",
    "precedent": r"\b(?:tese|tema|s[uú]mula|repercuss[aã]o geral|repetitivo|irdr|iac)\b",
    "full_text": r"\b(?:inteiro teor|documento|pdf|visualizar ac[oó]rd[aã]o)\b",
}
ACCESS_SIGNAL_PATTERNS = {
    "captcha": r"\bcaptcha\b",
    "recaptcha": r"\b(?:recaptcha|g-recaptcha)\b",
    "turnstile": r"\bturnstile\b",
    "cloudflare": r"\bcloudflare\b",
    "login": (
        r"\b(?:fa[cç]a login|login obrigat[oó]rio|entrar no sistema|"
        r"autentica[cç][aã]o requerida|sajcas|cas server)\b"
    ),
    "anti_robot": r"\b(?:antirrob[oô]|anti-rob[oô]|verifica[cç][aã]o automatica)\b",
    "empty_session": r"\b(?:emptysession|sess[aã]o expirada|sess[aã]o inexistente)\b",
    "access_denied": r"\b(?:access denied|acesso negado|forbidden|n[aã]o autorizado)\b",
    "request_blocked": r"\b(?:request blocked|request could not be satisfied)\b",
}
PAGINATION_PATTERNS = (
    r"\bresultados?\s+\d+\s+a\s+\d+\s+de\s+\d+\b",
    r"\bp[aá]gina\s+\d+\b",
    r"\bpr[oó]xima\b",
    r"\btrocaDePagina\b",
    r"\bpage(?:Number)?\b",
)


@dataclass(slots=True)
class RouteProbeResult:
    """Structured diagnostic for a candidate public route."""

    ok: bool
    route_status: RouteStatus
    quality_grade: str
    score: int
    url: str
    final_url: str | None = None
    method: str = "GET"
    status_code: int | None = None
    content_type: str = ""
    title: str = ""
    content_bytes: int = 0
    content_sha256: str | None = None
    elapsed_ms: int | None = None
    time_to_first_byte_ms: int | None = None
    content_length: int | None = None
    response_complete: bool = True
    content_truncated: bool = False
    transport_status: str = "complete"
    expected_texts: dict[str, bool] = field(default_factory=dict)
    access_signals: dict[str, bool] = field(default_factory=dict)
    legal_signals: dict[str, bool] = field(default_factory=dict)
    route_features: dict[str, bool] = field(default_factory=dict)
    recommendation: str = ""
    visible_sample: str = ""
    error_type: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def probe_route(
    url: str,
    *,
    method: str = "GET",
    expected_texts: Sequence[str] = (),
    timeout: float = 30.0,
    connect_timeout: float | None = None,
    read_timeout: float | None = None,
    max_bytes: int = 5_000_000,
    chunk_size: int = 64 * 1024,
    user_agent: str = "NanoJuris/route-probe (+https://github.com/ndtj/nanojuris)",
    data: Mapping[str, str] | None = None,
    json_payload: Any | None = None,
    verify_ssl: bool = True,
) -> RouteProbeResult:
    """Probe a public route with a clean HTTP session and no browser state."""

    if max_bytes <= 0:
        raise ValueError("max_bytes deve ser maior que zero")
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser maior que zero")
    if timeout <= 0:
        raise ValueError("timeout deve ser maior que zero")
    if connect_timeout is not None and connect_timeout <= 0:
        raise ValueError("connect_timeout deve ser maior que zero")
    if read_timeout is not None and read_timeout <= 0:
        raise ValueError("read_timeout deve ser maior que zero")

    session = requests.Session()
    # Route discovery must not silently inherit a broken local proxy or
    # unrelated browser environment; callers can use the browser for HAR
    # capture, but this diagnostic intentionally replays a clean session.
    session.trust_env = False
    session.headers.update({"Accept": DEFAULT_ACCEPT, "User-Agent": user_agent})
    started = time.perf_counter()
    normalized_method = method.upper()
    response: requests.Response | None = None
    response_started_ms: int | None = None
    content_length: int | None = None
    content = bytearray()
    content_truncated = False
    transport_status = "complete"
    transport_error: requests.RequestException | None = None
    final_url: str | None = None
    status_code: int | None = None
    content_type = ""
    try:
        response = session.request(
            normalized_method,
            url,
            data=dict(data or {}),
            json=json_payload,
            timeout=(
                connect_timeout if connect_timeout is not None else min(timeout, 10.0),
                read_timeout if read_timeout is not None else timeout,
            ),
            allow_redirects=True,
            verify=verify_ssl,
            stream=True,
        )
        response_started_ms = int((time.perf_counter() - started) * 1000)
        content_length = _content_length(response.headers.get("Content-Length"))
        final_url = response.url
        status_code = response.status_code
        content_type = response.headers.get("Content-Type", "")
        if content_length is not None and content_length > max_bytes:
            content_truncated = True
        try:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                remaining = max_bytes - len(content)
                if remaining <= 0:
                    content_truncated = True
                    break
                if len(chunk) > remaining:
                    content.extend(chunk[:remaining])
                    content_truncated = True
                    break
                content.extend(chunk)
        except requests.RequestException as exc:
            transport_status = (
                "timeout_after_headers" if _is_read_timeout(exc) else "partial_read_error"
            )
            transport_error = exc
            content_truncated = True
    except requests.RequestException as exc:
        transport_status = _transport_status_for_error(exc)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return RouteProbeResult(
            ok=False,
            route_status="source_unavailable",
            quality_grade="D",
            score=0,
            url=url,
            method=normalized_method,
            elapsed_ms=elapsed_ms,
            response_complete=False,
            transport_status=transport_status,
            expected_texts={item: False for item in expected_texts},
            recommendation=_transport_recommendation(transport_status),
            error_type=type(exc).__name__,
            error=str(exc),
        )
    finally:
        if response is not None:
            response.close()
        session.close()

    assert response is not None
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result = analyze_route_response(
        url=url,
        final_url=final_url or url,
        method=normalized_method,
        status_code=status_code or 0,
        content=bytes(content),
        content_type=content_type,
        expected_texts=expected_texts,
        elapsed_ms=elapsed_ms,
        time_to_first_byte_ms=response_started_ms,
        content_length=content_length,
        response_complete=not content_truncated and transport_error is None,
        content_truncated=content_truncated,
        transport_status=transport_status,
    )
    if transport_error is not None:
        result.route_status = "partial_response"
        result.ok = False
        result.error_type = type(transport_error).__name__
        result.error = str(transport_error)
        result.recommendation = (
            "Resposta parcial analisada; repetir somente com nova evidencia ou "
            "uma estrategia de paginacao/streaming mais especifica."
        )
    elif content_truncated:
        result.error_type = "content_truncated"
        result.error = f"Resposta limitada a {max_bytes} bytes para preservar o probe."
    return result


def analyze_route_response(
    *,
    url: str,
    final_url: str,
    method: str,
    status_code: int,
    content: bytes,
    content_type: str = "",
    expected_texts: Sequence[str] = (),
    elapsed_ms: int | None = None,
    time_to_first_byte_ms: int | None = None,
    content_length: int | None = None,
    response_complete: bool = True,
    content_truncated: bool = False,
    transport_status: str = "complete",
) -> RouteProbeResult:
    """Analyze one already-fetched response for jurisprudence provider viability."""

    text = _decode_content(content, content_type)
    lowered = text.lower()
    visible, title = _visible_text_and_title(text, content_type)
    expected = {item: item in text or item in visible for item in expected_texts}
    access_signals = _access_signals(raw_text=lowered, visible_text=visible.lower())
    legal_signals = _signals(visible.lower() or lowered, LEGAL_SIGNAL_PATTERNS)
    route_features = _route_features(
        content_type=content_type,
        text=text,
        visible=visible,
        legal_signals=legal_signals,
    )
    score = _score_route(
        status_code=status_code,
        expected_texts=expected,
        access_signals=access_signals,
        legal_signals=legal_signals,
        route_features=route_features,
        elapsed_ms=elapsed_ms,
        response_complete=response_complete,
        content_truncated=content_truncated,
        transport_status=transport_status,
    )
    route_status = _route_status(
        status_code=status_code,
        access_signals=access_signals,
        legal_signals=legal_signals,
        expected_texts=expected,
        route_features=route_features,
        response_complete=response_complete,
        content_truncated=content_truncated,
    )
    ok = route_status == "live_valid"
    return RouteProbeResult(
        ok=ok,
        route_status=route_status,
        quality_grade=_quality_grade(score),
        score=score,
        url=url,
        final_url=final_url,
        method=method.upper(),
        status_code=status_code,
        content_type=content_type,
        title=title,
        content_bytes=len(content),
        content_sha256=hashlib.sha256(content).hexdigest(),
        elapsed_ms=elapsed_ms,
        time_to_first_byte_ms=time_to_first_byte_ms,
        content_length=content_length,
        response_complete=response_complete,
        content_truncated=content_truncated,
        transport_status=transport_status,
        expected_texts=expected,
        access_signals=access_signals,
        legal_signals=legal_signals,
        route_features=route_features,
        recommendation=_recommendation(route_status, score),
        visible_sample=visible[:1000],
    )


def parse_key_value_pairs(items: Sequence[str]) -> dict[str, str]:
    """Parse CLI key=value pairs into a stable dictionary."""

    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Parametro deve estar no formato chave=valor: {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Parametro sem chave: {item!r}")
        parsed[key] = value
    return parsed


def parse_json_payload(value: str) -> Any:
    """Parse a CLI JSON object or array used as probe payload."""

    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalido: {exc}") from exc
    if not isinstance(payload, dict | list):
        raise ValueError("O payload JSON do probe deve ser um objeto ou array.")
    return payload


def parse_json_object(value: str) -> dict[str, Any]:
    """Parse a CLI JSON object. Kept for compatibility with older callers."""

    payload = parse_json_payload(value)
    if not isinstance(payload, dict):
        raise ValueError("O payload JSON do probe deve ser um objeto.")
    return payload


def _decode_content(content: bytes, content_type: str) -> str:
    if "application/pdf" in content_type.lower():
        return ""
    for encoding in ("utf-8", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _visible_text_and_title(text: str, content_type: str) -> tuple[str, str]:
    lowered_content_type = content_type.lower()
    if "json" in lowered_content_type:
        return _normalize_spaces(text), ""
    if not text:
        return "", ""
    soup = BeautifulSoup(text, "html.parser")
    for node in soup(["script", "style", "noscript"]):
        node.decompose()
    visible = _normalize_spaces(soup.get_text(" ", strip=True))
    title = soup.title.get_text(strip=True) if soup.title else ""
    return visible, title


def _signals(text: str, patterns: Mapping[str, str]) -> dict[str, bool]:
    return {
        name: bool(re.search(pattern, text, flags=re.IGNORECASE))
        for name, pattern in patterns.items()
    }


def _access_signals(*, raw_text: str, visible_text: str) -> dict[str, bool]:
    signals = _signals(visible_text, ACCESS_SIGNAL_PATTERNS)
    raw_signals = _signals(raw_text, ACCESS_SIGNAL_PATTERNS)
    challenge_visible = bool(
        re.search(
            r"\b(?:enable\s+javascript\s+and\s+cookies|just\s+a\s+moment|"
            r"attention\s+required|cloudflare\s+ray|checking\s+your\s+browser|"
            r"verifica[cç][aã]o\s+humana|managed\s+challenge)\b",
            visible_text,
        )
    )
    signals["turnstile"] = signals["turnstile"] or (raw_signals["turnstile"] and challenge_visible)
    signals["cloudflare"] = signals["cloudflare"] or (
        raw_signals["cloudflare"] and challenge_visible
    )
    for name in ("empty_session", "access_denied", "request_blocked"):
        signals[name] = raw_signals[name]
    signals["captcha"] = signals["captcha"] or bool(
        re.search(r"\b(?:digite\s+os\s+n[uú]meros|informe\s+o\s+c[oó]digo)\b", visible_text)
    )
    signals["captcha"] = signals["captcha"] or (
        "tokendesafio" in raw_text and '"imagem"' in raw_text
    )
    signals["recaptcha"] = signals["recaptcha"] or bool(
        raw_signals["recaptcha"]
        and re.search(
            r"\b(?:captcha|n[aã]o\s+sou\s+um\s+rob[oô]|verifica[cç][aã]o\s+humana)\b",
            visible_text,
        )
    )
    signals["anti_robot"] = signals["anti_robot"] or bool(
        raw_signals["anti_robot"]
        and re.search(r"\b(?:rob[oô]|automatizada|verifica[cç][aã]o)\b", visible_text)
    )
    signals["anti_robot"] = signals["anti_robot"] or "antirrob" in raw_text
    signals["login"] = signals["login"] or bool(
        raw_signals["login"] and re.search(ACCESS_SIGNAL_PATTERNS["login"], visible_text)
    )
    return signals


def _route_features(
    *,
    content_type: str,
    text: str,
    visible: str,
    legal_signals: Mapping[str, bool],
) -> dict[str, bool]:
    lowered_type = content_type.lower()
    haystack = f"{text}\n{visible}".lower()
    has_json = "json" in lowered_type or _looks_like_json(text)
    has_xml = "xml" in lowered_type or text.lstrip().startswith("<?xml")
    return {
        "structured_response": has_json or has_xml,
        "html_response": "html" in lowered_type or "<html" in text.lower(),
        "pdf_response": "application/pdf" in lowered_type or text.startswith("%PDF"),
        "pagination": any(
            re.search(pattern, haystack, flags=re.IGNORECASE) for pattern in PAGINATION_PATTERNS
        ),
        "full_text_link": legal_signals.get("full_text", False),
        "legal_content": any(legal_signals.values()),
    }


def _looks_like_json(text: str) -> bool:
    stripped = text.strip()
    return (stripped.startswith("{") and stripped.endswith("}")) or (
        stripped.startswith("[") and stripped.endswith("]")
    )


def _score_route(
    *,
    status_code: int,
    expected_texts: Mapping[str, bool],
    access_signals: Mapping[str, bool],
    legal_signals: Mapping[str, bool],
    route_features: Mapping[str, bool],
    elapsed_ms: int | None,
    response_complete: bool,
    content_truncated: bool,
    transport_status: str,
) -> int:
    score = 0
    if 200 <= status_code < 300:
        score += 1
    if route_features.get("structured_response"):
        score += 3
    if route_features.get("legal_content"):
        score += 3
    if route_features.get("pagination"):
        score += 2
    if route_features.get("full_text_link") or route_features.get("pdf_response"):
        score += 2
    if expected_texts and all(expected_texts.values()):
        score += 2
    if not any(access_signals.values()):
        score += 1
    if elapsed_ms is not None and elapsed_ms <= 2500:
        score += 1
    if any(access_signals.values()):
        score -= 4
    if status_code == 404:
        score -= 4
    elif status_code >= 400:
        score -= 3
    if not any(legal_signals.values()) and not route_features.get("structured_response"):
        score -= 2
    if not response_complete or content_truncated or transport_status != "complete":
        score -= 3
    return max(score, 0)


def _route_status(
    *,
    status_code: int,
    access_signals: Mapping[str, bool],
    legal_signals: Mapping[str, bool],
    expected_texts: Mapping[str, bool],
    route_features: Mapping[str, bool],
    response_complete: bool,
    content_truncated: bool,
) -> RouteStatus:
    if status_code == 404:
        return "not_found"
    if any(access_signals.values()):
        return "access_control_or_login"
    if status_code >= 400:
        return "source_unavailable"
    if not response_complete or content_truncated:
        return "partial_response"
    if expected_texts and not all(expected_texts.values()):
        return "candidate"
    if any(legal_signals.values()) or route_features.get("structured_response"):
        return "live_valid"
    return "candidate"


def _quality_grade(score: int) -> str:
    if score >= 8:
        return "A"
    if score >= 5:
        return "B"
    if score >= 2:
        return "C"
    return "D"


def _recommendation(route_status: RouteStatus, score: int) -> str:
    if route_status == "live_valid" and score >= 8:
        return "Promover para ficha de contrato e fixture offline antes do provider."
    if route_status == "live_valid":
        return "Manter como candidato forte; aprofundar campos, paginacao e documento."
    if route_status == "candidate":
        return "Investigar contrato com HAR/DevTools e confirmar conteudo juridico objetivo."
    if route_status == "partial_response":
        return (
            "Resposta parcial; preservar sinais encontrados e investigar paginacao, "
            "streaming ou timeout de leitura."
        )
    if route_status == "access_control_or_login":
        return "Documentar bloqueio; nao implementar bypass de captcha, login ou sessao."
    if route_status == "not_found":
        return "Descartar rota ou revisar URL/metodo antes de novo probe."
    return "Registrar indisponibilidade e repetir teste em outra janela."


def _content_length(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _transport_status_for_error(exc: requests.RequestException) -> str:
    if isinstance(exc, requests.exceptions.ConnectTimeout):
        return "timeout_before_headers"
    if _is_read_timeout(exc):
        return "timeout_before_headers"
    return "transport_error"


def _is_read_timeout(exc: requests.RequestException) -> bool:
    """Recognize direct and wrapped urllib3 read-timeout exceptions."""

    current: BaseException | None = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, requests.exceptions.ReadTimeout):
            return True
        current = current.__cause__ or current.__context__
    return "read timed out" in str(exc).lower()


def _transport_recommendation(transport_status: str) -> str:
    if transport_status == "timeout_before_headers":
        return (
            "Nenhum header foi recebido; testar uma rota mais especifica, "
            "paginacao pequena ou captura automatica de rede."
        )
    return (
        "Falha de transporte antes da resposta; preservar o diagnostico e testar "
        "superficie oficial alternativa."
    )


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
