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
from dataclasses import asdict, dataclass
from typing import Any, Literal

_CNJ_DIGITS = re.compile(r"^\d{20}$")
_WHITESPACE = re.compile(r"\s+")

LegalRecordKind = Literal["process", "decision", "precedent", "publication", "document", "version"]
IdentityRelation = Literal["same", "distinct", "unknown"]


@dataclass(frozen=True, slots=True)
class IdentityEvidence:
    """Explainable evidence used to derive or compare a legal identity."""

    rule: str
    confidence: Literal["exact", "strong", "weak", "none"]
    fields: tuple[str, ...] = ()
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fields"] = list(self.fields)
        return payload


@dataclass(frozen=True, slots=True)
class LegalIdentity:
    """Conservative identity for a process, decision, precedent or document."""

    kind: LegalRecordKind
    key: str | None
    source: str
    authority: str = ""
    degree: str = ""
    record_type: str = ""
    case_number: str = ""
    native_id: str = ""
    text_sha256: str | None = None
    parent_key: str | None = None
    evidence: IdentityEvidence = IdentityEvidence("unresolved", "none")
    unresolved_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = self.evidence.to_dict()
        return payload


@dataclass(frozen=True, slots=True)
class IdentityMatch:
    """Result of comparing two identities without an irreversible merge."""

    relation: IdentityRelation
    left_key: str | None
    right_key: str | None
    evidence: IdentityEvidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation": self.relation,
            "left_key": self.left_key,
            "right_key": self.right_key,
            "evidence": self.evidence.to_dict(),
        }


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


def resolve_legal_identity(
    *,
    kind: LegalRecordKind,
    source: object,
    authority: object = "",
    degree: object = "",
    native_id: object = "",
    case_number: object = "",
    record_type: object = "",
    event_date: object = "",
    text: object = "",
    parent_key: object = "",
) -> LegalIdentity:
    """Resolve a typed identity using conservative, explainable rules.

    A CNJ number identifies a process, not a decision.  Decisions therefore
    require a native identifier or additional authority/degree/type/date
    evidence; a bare process number produces an unresolved identity.
    """

    source_value = _normalize_component(source)
    authority_value = _normalize_component(authority)
    degree_value = _normalize_component(degree)
    native_value = _normalize_component(native_id)
    number_value = _normalize_number(case_number)
    type_value = _normalize_component(record_type)
    date_value = _normalize_component(event_date)
    parent_value = _normalize_component(parent_key)
    text_hash = _text_hash(text)

    if kind == "process":
        if _is_cnj_number(number_value):
            return LegalIdentity(
                kind=kind,
                key=f"process:cnj:{number_value}",
                source=source_value,
                case_number=number_value,
                evidence=IdentityEvidence("cnj_process_number", "exact", ("case_number",)),
            )
        if native_value:
            return _identity(
                kind=kind,
                key=_scoped_key(kind, source_value, native_value),
                source=source_value,
                native_id=native_value,
                evidence=IdentityEvidence("source_native_id", "exact", ("source", "native_id")),
            )
        if number_value:
            return _identity(
                kind=kind,
                key=_scoped_key(kind, source_value, authority_value, number_value),
                source=source_value,
                authority=authority_value,
                case_number=number_value,
                evidence=IdentityEvidence(
                    "scoped_local_number", "strong", ("source", "authority", "case_number")
                ),
            )
        return _unresolved(kind, source_value, "missing_process_identifier")

    if kind == "decision":
        if native_value:
            return _identity(
                kind=kind,
                key=_scoped_key(kind, source_value, native_value),
                source=source_value,
                authority=authority_value,
                degree=degree_value,
                record_type=type_value,
                case_number=number_value,
                native_id=native_value,
                text_sha256=text_hash,
                parent_key=(
                    f"process:cnj:{number_value}" if _is_cnj_number(number_value) else None
                ),
                evidence=IdentityEvidence("decision_native_id", "exact", ("source", "native_id")),
            )
        required = (authority_value, degree_value, type_value, date_value)
        if all(required) and (number_value or text_hash):
            digest = _digest(
                (
                    source_value,
                    authority_value,
                    degree_value,
                    type_value,
                    date_value,
                    number_value,
                    text_hash or "",
                )
            )
            return _identity(
                kind=kind,
                key=f"decision:derived:{digest}",
                source=source_value,
                authority=authority_value,
                degree=degree_value,
                record_type=type_value,
                case_number=number_value,
                text_sha256=text_hash,
                parent_key=(
                    f"process:cnj:{number_value}" if _is_cnj_number(number_value) else None
                ),
                evidence=IdentityEvidence(
                    "decision_semantic_tuple",
                    "strong",
                    ("authority", "degree", "record_type", "event_date"),
                ),
            )
        return _unresolved(
            kind, source_value, "decision_requires_native_or_semantic_evidence", number_value
        )

    if kind == "precedent":
        if native_value:
            key = _scoped_key(kind, source_value, native_value)
            evidence = IdentityEvidence("precedent_native_id", "exact", ("source", "native_id"))
        elif number_value and type_value:
            key = _scoped_key(kind, source_value, type_value, number_value)
            evidence = IdentityEvidence(
                "precedent_type_and_number", "strong", ("source", "record_type", "case_number")
            )
        else:
            return _unresolved(
                kind, source_value, "precedent_requires_type_and_identifier", number_value
            )
        return _identity(
            kind=kind,
            key=key,
            source=source_value,
            authority=authority_value,
            record_type=type_value,
            case_number=number_value,
            native_id=native_value,
            text_sha256=text_hash,
            evidence=evidence,
        )

    if kind in {"document", "version"}:
        if native_value:
            key = _scoped_key(kind, source_value, native_value)
            evidence = IdentityEvidence("document_native_id", "exact", ("source", "native_id"))
        elif parent_value and text_hash:
            key = _scoped_key(kind, parent_value, text_hash)
            evidence = IdentityEvidence(
                "parent_and_content_hash", "strong", ("parent_key", "text_sha256")
            )
        else:
            return _unresolved(kind, source_value, "document_requires_native_or_parent_hash")
        return _identity(
            kind=kind,
            key=key,
            source=source_value,
            native_id=native_value,
            text_sha256=text_hash,
            parent_key=parent_value or None,
            evidence=evidence,
        )

    if kind == "publication":
        if native_value:
            return _identity(
                kind=kind,
                key=_scoped_key(kind, source_value, native_value),
                source=source_value,
                native_id=native_value,
                evidence=IdentityEvidence(
                    "publication_native_id", "exact", ("source", "native_id")
                ),
            )
        return _unresolved(kind, source_value, "publication_requires_native_identifier")

    raise ValueError(f"kind de identidade invalido: {kind!r}")


def canonical_record_identity(record: object) -> LegalIdentity:
    """Resolve a canonical model without changing its legacy serialization.

    The canonical models intentionally keep their historical fields and
    ``to_dict`` output.  This adapter provides a typed identity projection for
    stores and exporters, using only fields already present in those models
    (and preserving uncertainty when a source did not provide enough evidence).
    ``CanonicalDecision.id``/``CanonicalPrecedent.id``/``CanonicalDocument.id``
    are treated as native IDs because provider adapters are required to map
    source identifiers into ``id``.
    """

    name = type(record).__name__
    if name == "CanonicalDecision":
        raw = getattr(record, "raw", {}) or {}
        case_number = getattr(record, "case_number", None)
        return resolve_legal_identity(
            kind="decision",
            source=getattr(record, "source", ""),
            authority=getattr(record, "court", ""),
            degree=(
                getattr(record, "degree", None)
                or raw.get("degree")
                or raw.get("grau")
                or raw.get("instance")
                or raw.get("instancia")
                or ""
            ),
            native_id=getattr(record, "id", ""),
            case_number=case_number or "",
            record_type=getattr(record, "decision_type", "") or "",
            event_date=getattr(record, "judgment_date", "")
            or getattr(record, "publication_date", "")
            or "",
            text=getattr(record, "full_text", "") or getattr(record, "summary", "") or "",
        )
    if name == "CanonicalPrecedent":
        return resolve_legal_identity(
            kind="precedent",
            source=getattr(record, "source", ""),
            authority=getattr(record, "court", ""),
            native_id=getattr(record, "id", ""),
            case_number=getattr(record, "number", "") or "",
            record_type=getattr(record, "precedent_type", "") or "",
            text=getattr(record, "thesis", "") or getattr(record, "question", "") or "",
        )
    if name == "CanonicalDocument":
        raw_metadata = getattr(record, "raw_metadata", {}) or {}
        return resolve_legal_identity(
            kind="document",
            source=getattr(record, "source", ""),
            native_id=getattr(record, "id", ""),
            parent_key=raw_metadata.get("parent_key") or "",
            text=getattr(record, "text", "") or "",
        )
    raise TypeError(f"registro canonico nao suportado: {name}")


def match_legal_identities(left: LegalIdentity, right: LegalIdentity) -> IdentityMatch:
    """Compare identities and keep uncertain matches explicit."""

    if left.kind != right.kind:
        return IdentityMatch(
            "distinct",
            left.key,
            right.key,
            IdentityEvidence("record_kind_mismatch", "exact", ("kind",)),
        )
    if left.key is None or right.key is None:
        return IdentityMatch(
            "unknown",
            left.key,
            right.key,
            IdentityEvidence("insufficient_identity_evidence", "none"),
        )
    if left.key == right.key:
        return IdentityMatch(
            "same",
            left.key,
            right.key,
            IdentityEvidence("stable_identity_key_equal", "exact", ("key",)),
        )
    if left.kind == "decision" and left.case_number and left.case_number == right.case_number:
        return IdentityMatch(
            "distinct",
            left.key,
            right.key,
            IdentityEvidence(
                "decision_not_merged_by_process_number",
                "exact",
                ("case_number",),
                "decisoes diferentes no mesmo processo permanecem distintas",
            ),
        )
    return IdentityMatch(
        "distinct",
        left.key,
        right.key,
        IdentityEvidence("stable_identity_key_different", "strong", ("key",)),
    )


def _identity(
    *, kind: LegalRecordKind, key: str, source: str, evidence: IdentityEvidence, **fields: Any
) -> LegalIdentity:
    return LegalIdentity(kind=kind, key=key, source=source, evidence=evidence, **fields)


def _unresolved(
    kind: LegalRecordKind, source: str, reason: str, case_number: str = ""
) -> LegalIdentity:
    return LegalIdentity(
        kind=kind,
        key=None,
        source=source,
        case_number=case_number,
        evidence=IdentityEvidence("unresolved", "none"),
        unresolved_reason=reason,
    )


def _scoped_key(kind: LegalRecordKind, *parts: str) -> str:
    return f"{kind}:" + _encoded(tuple(part for part in parts if part))


def _digest(parts: tuple[str, ...]) -> str:
    serialized = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _text_hash(value: object) -> str | None:
    normalized = _normalize_component(value)
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


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


__all__ = [
    "canonical_record_identity",
    "IdentityEvidence",
    "IdentityMatch",
    "LegalIdentity",
    "LegalRecordKind",
    "match_legal_identities",
    "identity_key",
    "resolve_legal_identity",
]
