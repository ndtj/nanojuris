"""Shared normalization rules for public jurisprudence records."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from urllib.parse import urldefrag, urljoin

_CNJ_DIGITS = re.compile(r"\d{20}")
_DATE_TOKEN = re.compile(r"\b\d{1,4}[./-]\d{1,2}[./-]\d{2,4}\b")
_PT_MONTHS = {
    "janeiro": "01",
    "fevereiro": "02",
    "março": "03",
    "marco": "03",
    "abril": "04",
    "maio": "05",
    "junho": "06",
    "julho": "07",
    "agosto": "08",
    "setembro": "09",
    "outubro": "10",
    "novembro": "11",
    "dezembro": "12",
}


def normalize_text(value: object, *, preserve_lines: bool = False) -> str | None:
    """Normalize Unicode and whitespace while preserving the original elsewhere."""

    if value is None:
        return None
    text = unicodedata.normalize("NFKC", str(value)).replace("\xa0", " ").strip()
    if not text:
        return None
    if preserve_lines:
        return "\n".join(" ".join(line.split()) for line in text.splitlines()).strip() or None
    return " ".join(text.split()) or None


def first_nonempty(*values: object) -> str | None:
    for value in values:
        normalized = normalize_text(value)
        if normalized:
            return normalized
    return None


def normalize_date_value(value: object) -> str | None:
    """Return an ISO date for formats observed in Brazilian court portals."""

    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = normalize_text(value)
    if not text:
        return None
    lowered = text.casefold()
    for month, number in _PT_MONTHS.items():
        lowered = re.sub(rf"\b{month}\b", number, lowered)
    text = lowered
    text = re.sub(r"\b(\d{1,2})\s+de\s+(\d{1,2})\s+de\s+(\d{4})\b", r"\1/\2/\3", text)
    for parser in (
        lambda item: datetime.fromisoformat(item.replace("Z", "+00:00")).date(),
        lambda item: datetime.strptime(item, "%d/%m/%Y").date(),
        lambda item: datetime.strptime(item, "%d-%m-%Y").date(),
        lambda item: datetime.strptime(item, "%d.%m.%Y").date(),
        lambda item: datetime.strptime(item, "%Y/%m/%d").date(),
        lambda item: date.fromisoformat(item[:10]),
    ):
        try:
            return parser(text).isoformat()
        except (TypeError, ValueError):
            continue
    match = _DATE_TOKEN.search(text)
    if match:
        token = match.group(0).replace(".", "/").replace("-", "/")
        parts = token.split("/")
        if len(parts[-1]) == 2:
            parts[-1] = f"20{parts[-1]}"
        candidates = ("/".join(parts), "/".join(reversed(parts)))
        for candidate in candidates:
            try:
                return datetime.strptime(candidate, "%d/%m/%Y").date().isoformat()
            except ValueError:
                continue
    return None


def normalize_cnj_number(value: object) -> str | None:
    """Format a twenty-digit CNJ number while preserving non-CNJ identifiers."""

    text = normalize_text(value)
    if not text:
        return None
    digits = re.sub(r"\D", "", text)
    if len(digits) != 20:
        return text
    return f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}.{digits[14:16]}.{digits[16:]}"


def normalize_decision_type(value: object) -> str | None:
    text = normalize_text(value)
    if not text:
        return None
    lowered = text.casefold()
    if "acórd" in lowered or "acord" in lowered:
        return "acordao"
    if "senten" in lowered:
        return "sentenca"
    if "monocr" in lowered:
        return "decisao_monocratica"
    if "despacho" in lowered:
        return "despacho"
    if "decis" in lowered:
        return "decisao"
    return lowered


def normalize_url(value: object, *, base_url: str = "") -> str | None:
    text = normalize_text(value)
    if not text:
        return None
    absolute = urljoin(base_url, text)
    return urldefrag(absolute)[0]


__all__ = [
    "first_nonempty",
    "normalize_cnj_number",
    "normalize_date_value",
    "normalize_decision_type",
    "normalize_text",
    "normalize_url",
]
