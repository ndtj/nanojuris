"""Deterministic identity keys used by collection and federated search.

Provider identifiers are not globally unique, while a case number is not
necessarily unique outside its court/source.  Keeping this policy in one
small module prevents the collection and client paths from silently drifting
apart.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

_CNJ_DIGITS = re.compile(r"^\d{20}$")
_WHITESPACE = re.compile(r"\s+")


def identity_key(
    *,
    source: object,
    court: object = "",
    identifier: object = "",
    number: object = "",
    record_type: object = "",
    semantic_fields: dict[str, object] | None = None,
) -> str:
    """Build a stable, source-aware key for a provider result.

    Stable provider IDs take precedence.  CNJ numbers are the only number
    format intentionally shared across sources; local numbers are scoped to
    source, court and record type.  The final fallback is a digest of
    metadata fields and never embeds raw legal text in the key.
    """

    source_value = _normalize_component(source)
    court_value = _normalize_component(court)
    type_value = _normalize_component(record_type)
    identifier_value = _normalize_component(identifier)
    number_value = _normalize_number(number)

    if identifier_value:
        return "id:" + _encoded((source_value, identifier_value))
    if _is_cnj_number(number_value):
        return f"cnj:{number_value}"
    if number_value:
        return "number:" + _encoded((source_value, court_value, type_value, number_value))

    payload = {
        "source": source_value,
        "court": court_value,
        "record_type": type_value,
        "fields": {
            str(name): _fingerprint_value(value)
            for name, value in sorted((semantic_fields or {}).items())
            if value is not None and str(value).strip() != ""
        },
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"fallback:{digest}"


def _normalize_component(value: object) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    return _WHITESPACE.sub(" ", text)


def _normalize_number(value: object) -> str:
    """Normalize punctuation in both CNJ and local numbers."""

    return re.sub(r"[^0-9a-z]", "", _normalize_component(value))


def _is_cnj_number(value: str) -> bool:
    # The shape check deliberately avoids guessing whether a source's local
    # identifier is a CNJ number.  A 20-digit formatted CNJ number is the
    # interoperable identity accepted by the providers' contracts.
    return bool(_CNJ_DIGITS.fullmatch(value))


def _encoded(parts: tuple[str, ...]) -> str:
    """Encode components so delimiters in provider values cannot collide."""

    return json.dumps(parts, ensure_ascii=False, separators=(",", ":"))


def _fingerprint_value(value: object) -> Any:
    if isinstance(value, str):
        normalized = _normalize_component(value)
        return {
            "sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "length": len(normalized),
        }
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_fingerprint_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _fingerprint_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    return _fingerprint_value(str(value))


__all__ = ["identity_key"]
