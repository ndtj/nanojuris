"""Deterministic quality checks for canonical jurisprudence records.

The checks in this module are deliberately local and conservative.  They do
not decide whether a source is authoritative or healthy at runtime; they
validate the shape of a record that an adapter is about to expose and keep
uncertainty explicit.  Network health belongs to the provider live evidence
pipeline, while these invariants are suitable for CI and golden-set tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from nanojuris.models import CanonicalDecision, CanonicalDocument, CanonicalPrecedent

CanonicalRecord = CanonicalDecision | CanonicalDocument | CanonicalPrecedent

_DATE_FIELDS = (
    "judgment_date",
    "publication_date",
    "updated_at",
    "source_updated_at",
    "retrieved_at",
)
_VOLATILE_KEYS = {
    "elapsed_ms",
    "extracted_at",
    "retrieved_at",
}
_HTML_MARKER = re.compile(r"<\s*(?:html|body|script|style|div|table)\b", re.IGNORECASE)
_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
_DIMENSIONS = {
    "degree": {"first", "second", "mixed", "superior", "unknown"},
    "instance": {"first", "second", "mixed", "superior", "unknown"},
    "branch": {
        "state",
        "federal",
        "labor",
        "electoral",
        "military",
        "superior",
        "administrative",
        "unknown",
    },
    "collection": {
        "cjpg",
        "cjsg",
        "sjur",
        "eproc",
        "portal",
        "juris",
        "jurisprudencia",
        "precedent",
    },
}


@dataclass(frozen=True, slots=True)
class QualityIssue:
    """One deterministic quality finding for a canonical record."""

    code: str
    severity: str
    message: str
    field: str | None = None

    def to_dict(self) -> dict[str, str]:
        payload = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.field is not None:
            payload["field"] = self.field
        return payload


def validate_record(record: CanonicalRecord) -> tuple[QualityIssue, ...]:
    """Return quality issues without mutating ``record``.

    Missing legal content and provenance are critical because they make a
    result unsafe to present as jurisprudence.  Optional metadata remains a
    warning so an incomplete public response is distinguishable from a parser
    failure without rejecting every partial source response.
    """

    if not isinstance(record, (CanonicalDecision, CanonicalDocument, CanonicalPrecedent)):
        raise TypeError(f"registro canonico nao suportado: {type(record).__name__}")

    values = record.to_dict()
    issues: list[QualityIssue] = []
    source = str(values.get("source") or "").strip()
    identifier = str(values.get("id") or "").strip()
    if not identifier:
        issues.append(QualityIssue("missing_identity", "critical", "id canonico ausente", "id"))
    if not source:
        issues.append(
            QualityIssue("missing_source", "critical", "source canonico ausente", "source")
        )

    if isinstance(record, CanonicalDecision):
        _require_any(
            values,
            ("case_number", "registry_number", "id"),
            "missing_decision_identity",
            issues,
        )
        _require_any(
            values,
            ("summary", "full_text"),
            "missing_legal_content",
            issues,
        )
        _require_value(values, "court", "missing_authority", issues)
    elif isinstance(record, CanonicalPrecedent):
        _require_value(values, "precedent_type", "missing_precedent_type", issues)
        _require_any(values, ("number", "id"), "missing_precedent_identity", issues)
        _require_any(values, ("question", "thesis"), "missing_legal_content", issues)
        _require_value(values, "court", "missing_authority", issues)
    else:
        _require_value(values, "document_type", "missing_document_type", issues)
        _require_any(values, ("text", "title"), "missing_document_content", issues)

    trace = values.get("source_trace")
    if not isinstance(trace, dict):
        issues.append(
            QualityIssue("missing_provenance", "critical", "SourceTrace ausente", "source_trace")
        )
    else:
        trace_provider = str(trace.get("provider") or "").strip()
        if source and trace_provider and trace_provider != source:
            issues.append(
                QualityIssue(
                    "trace_provider_mismatch",
                    "critical",
                    "provider do SourceTrace difere do source canonico",
                    "source_trace.provider",
                )
            )
        endpoint = str(trace.get("endpoint") or "").strip()
        if not endpoint:
            issues.append(
                QualityIssue(
                    "missing_trace_endpoint",
                    "warning",
                    "endpoint de origem nao preservado",
                    "source_trace.endpoint",
                )
            )
        trace_hash = trace.get("content_sha256")
        if trace_hash is not None and not _SHA256.fullmatch(str(trace_hash)):
            issues.append(
                QualityIssue(
                    "invalid_trace_hash",
                    "critical",
                    "content_sha256 do trace nao e SHA-256",
                    "source_trace.content_sha256",
                )
            )

    for field_name in ("document_url", "url"):
        value = values.get(field_name)
        if value:
            _check_url(str(value), field_name, issues)
    if isinstance(trace, dict):
        for field_name in ("source_url", "final_url"):
            value = trace.get(field_name)
            if value:
                _check_url(str(value), f"source_trace.{field_name}", issues)

    for field_name in _DATE_FIELDS:
        value = values.get(field_name)
        if value and not _valid_date(str(value)):
            issues.append(
                QualityIssue(
                    "invalid_date",
                    "critical",
                    "data deve ser ISO-8601 ou YYYY-MM-DD",
                    field_name,
                )
            )

    # Dimensions are advisory because tribunals use local labels, but an
    # explicitly supplied value must use a documented canonical vocabulary.
    # Unknown/missing values remain valid and are preserved in ``raw``.
    for field_name, allowed in _DIMENSIONS.items():
        value = values.get(field_name)
        if value is None or not str(value).strip():
            continue
        normalized = str(value).strip().casefold()
        if normalized not in allowed:
            issues.append(
                QualityIssue(
                    "unknown_canonical_dimension",
                    "warning",
                    f"valor de {field_name} nao pertence ao vocabulario canonico",
                    field_name,
                )
            )

    for field_name in ("summary", "full_text", "question", "thesis", "text"):
        value = values.get(field_name)
        if isinstance(value, str) and _HTML_MARKER.search(value):
            issues.append(
                QualityIssue(
                    "html_in_canonical_text",
                    "critical",
                    "conteudo canonico contem HTML cru",
                    field_name,
                )
            )

    return tuple(issues)


def duplicate_identity_keys(records: list[CanonicalRecord]) -> dict[str, tuple[int, ...]]:
    """Return repeated canonical identities, preserving input indexes."""

    from nanojuris.identity import canonical_record_identity

    positions: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        identity = canonical_record_identity(record)
        if identity.key is None:
            continue
        positions.setdefault(identity.key, []).append(index)
    return {key: tuple(indexes) for key, indexes in sorted(positions.items()) if len(indexes) > 1}


def compare_golden(expected: Any, actual: Any) -> tuple[str, ...]:
    """Compare JSON-compatible payloads while ignoring volatile timestamps.

    The returned paths are stable and human-readable, making a schema drift a
    failing CI assertion rather than an opaque serialized diff.
    """

    left = _stable_payload(expected)
    right = _stable_payload(actual)
    differences: list[str] = []
    _diff(left, right, "$", differences)
    return tuple(differences)


def _require_value(
    values: dict[str, Any], field_name: str, code: str, issues: list[QualityIssue]
) -> None:
    if not str(values.get(field_name) or "").strip():
        issues.append(
            QualityIssue(code, "critical", f"campo obrigatorio ausente: {field_name}", field_name)
        )


def _require_any(
    values: dict[str, Any], fields: tuple[str, ...], code: str, issues: list[QualityIssue]
) -> None:
    if not any(str(values.get(field_name) or "").strip() for field_name in fields):
        issues.append(
            QualityIssue(
                code,
                "critical",
                "nenhum campo de " + ", ".join(fields) + " foi informado",
                fields[0],
            )
        )


def _check_url(value: str, field_name: str, issues: list[QualityIssue]) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        issues.append(
            QualityIssue("unsafe_url", "critical", "URL deve usar HTTP(S) com host", field_name)
        )
    if parsed.username or parsed.password:
        issues.append(
            QualityIssue(
                "url_contains_credentials",
                "critical",
                "URL nao pode conter credenciais",
                field_name,
            )
        )


def _valid_date(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return True
    try:
        if "T" in candidate or " " in candidate:
            datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        else:
            date.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def _stable_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _stable_payload(item)
            for key, item in sorted(value.items())
            if key not in _VOLATILE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_stable_payload(item) for item in value]
    if hasattr(value, "to_dict"):
        return _stable_payload(value.to_dict())
    return value


def _diff(left: Any, right: Any, path: str, output: list[str]) -> None:
    if type(left) is not type(right):
        output.append(path)
        return
    if isinstance(left, dict):
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}"
            if key not in left or key not in right:
                output.append(child)
            else:
                _diff(left[key], right[key], child, output)
        return
    if isinstance(left, list):
        if len(left) != len(right):
            output.append(path + ".length")
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=False)):
            _diff(left_item, right_item, f"{path}[{index}]", output)
        return
    if left != right:
        output.append(path)


__all__ = [
    "CanonicalRecord",
    "QualityIssue",
    "compare_golden",
    "duplicate_identity_keys",
    "validate_record",
]
