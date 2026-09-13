"""Deterministic legal-query interpretation for live federated search."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from importlib.resources import files
from typing import Any

ANALYZER_VERSION = "legal-intent-v1"
_CNJ_RE = re.compile(r"(?<!\d)(?:\d[.\s-]?){20}(?!\d)")
_TOKEN_RE = re.compile(r"[\wÀ-ÿ]+(?:['’][\wÀ-ÿ]+)?", re.UNICODE)
_NEGATIVE_RE = re.compile(r"-(?:\"[^\"]+\"|\S+)")
_REQUIRED_RE = re.compile(r"\+(?:\"[^\"]+\"|\S+)")


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _clean_spaces(value: str) -> str:
    return " ".join(value.split()).strip()


@dataclass(frozen=True, slots=True)
class LegalConceptMatch:
    """A conservative vocabulary match with bounded expansions."""

    concept_id: str
    label: str
    matched_terms: tuple[str, ...] = ()
    expansions: tuple[str, ...] = ()
    expansion_weight: float = 0.4

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class QueryIntent:
    """Stable, serializable interpretation independent of a provider."""

    original_query: str
    normalized_query: str
    normalized_terms: tuple[str, ...] = ()
    phrases: tuple[str, ...] = ()
    required_terms: tuple[str, ...] = ()
    optional_terms: tuple[str, ...] = ()
    excluded_terms: tuple[str, ...] = ()
    legal_concepts: tuple[LegalConceptMatch, ...] = ()
    detected_filters: dict[str, str] = field(default_factory=dict)
    suggested_filters: dict[str, str] = field(default_factory=dict)
    ambiguous_interpretations: tuple[str, ...] = ()
    identifier: str | None = None
    is_exact_identifier: bool = False
    analyzer_version: str = ANALYZER_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["legal_concepts"] = [item.to_dict() for item in self.legal_concepts]
        return payload


class LegalQueryAnalyzer:
    """Interpret legal queries without network access or probabilistic models."""

    def __init__(self, vocabulary: dict[str, Any] | None = None) -> None:
        self.vocabulary = vocabulary or _load_vocabulary()
        self.version = ANALYZER_VERSION

    def analyze(
        self,
        query: str,
        *,
        ignored_filters: set[str] | tuple[str, ...] | list[str] = (),
    ) -> QueryIntent:
        original = query or ""
        normalized = _clean_spaces(_fold(original))
        identifier = self._find_identifier(original)
        phrases = self._phrases(original)
        excluded = self._marked_terms(original, _NEGATIVE_RE)
        required = self._marked_terms(original, _REQUIRED_RE)
        command_terms = {_fold(item) for item in self.vocabulary.get("command_terms", ())}
        for variants in self.vocabulary.get("document_types", {}).values():
            for variant in variants:
                command_terms.update(_fold(item) for item in variant.split())

        raw_tokens = tuple(_fold(item) for item in _TOKEN_RE.findall(original))
        excluded_set = {_fold(item) for item in excluded}
        required_set = {_fold(item) for item in required}
        terms: list[str] = []
        for token in raw_tokens:
            if token in excluded_set or token in command_terms or token in {"and", "e"}:
                continue
            if token not in terms:
                terms.append(token)

        concepts = self._concept_matches(normalized)
        detected, suggested, ambiguous = self._filters(normalized, original, identifier)
        ignored = {str(item) for item in ignored_filters}
        if ignored:
            detected = {key: value for key, value in detected.items() if key not in ignored}
            suggested = {key: value for key, value in suggested.items() if key not in ignored}
            ambiguous = tuple(item for item in ambiguous if item.split(":", 1)[0] not in ignored)
        if identifier is not None:
            terms = []
            required = (identifier,)
            optional: tuple[str, ...] = ()
        else:
            optional = tuple(item for item in terms if item not in required_set)
        return QueryIntent(
            original_query=original,
            normalized_query=normalized,
            normalized_terms=tuple(terms),
            phrases=phrases,
            required_terms=tuple(required),
            optional_terms=optional,
            excluded_terms=tuple(excluded),
            legal_concepts=concepts,
            detected_filters=detected,
            suggested_filters=suggested,
            ambiguous_interpretations=ambiguous,
            identifier=identifier,
            is_exact_identifier=identifier is not None,
        )

    @staticmethod
    def _find_identifier(query: str) -> str | None:
        match = _CNJ_RE.search(query)
        if not match:
            return None
        digits = re.sub(r"\D", "", match.group(0))
        if len(digits) != 20:
            return None
        return (
            f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}.{digits[14:16]}.{digits[16:]}"
        )

    @staticmethod
    def _phrases(query: str) -> tuple[str, ...]:
        explicit = [_clean_spaces(_fold(item)) for item in re.findall(r'"([^\"]+)"', query)]
        return tuple(dict.fromkeys(item for item in explicit if item))

    @staticmethod
    def _marked_terms(query: str, pattern: re.Pattern[str]) -> tuple[str, ...]:
        values: list[str] = []
        for match in pattern.findall(query):
            cleaned = match.lstrip("+").lstrip("-").strip('"')
            normalized = _clean_spaces(_fold(cleaned))
            if normalized and normalized not in values:
                values.append(normalized)
        return tuple(values)

    def _concept_matches(self, normalized: str) -> tuple[LegalConceptMatch, ...]:
        matches: list[LegalConceptMatch] = []
        for concept in self.vocabulary.get("concepts", ()):
            matched = tuple(term for term in concept.get("terms", ()) if _fold(term) in normalized)
            if not matched:
                continue
            expansions = tuple(_fold(term) for term in concept.get("expansions", ()))
            matches.append(
                LegalConceptMatch(
                    concept_id=str(concept["id"]),
                    label=str(concept.get("label", concept["id"])),
                    matched_terms=matched,
                    expansions=expansions,
                )
            )
        return tuple(matches)

    def _filters(
        self,
        normalized: str,
        original: str,
        identifier: str | None,
    ) -> tuple[dict[str, str], dict[str, str], tuple[str, ...]]:
        detected: dict[str, str] = {}
        suggested: dict[str, str] = {}
        ambiguous: list[str] = []
        if identifier:
            detected["number"] = identifier
        for canonical, variants in self.vocabulary.get("document_types", {}).items():
            if any(_fold(variant) in normalized for variant in variants):
                detected["document_type"] = canonical
                break
        patterns: dict[str, dict[str, tuple[str, ...]]] = {
            "degree": {
                "first": ("primeiro grau", "1o grau", "1 grau"),
                "second": ("segundo grau", "2o grau", "2 grau"),
                "superior": ("tribunal superior", "superiores"),
            },
            "branch": {
                "state": ("estadual", "estaduais"),
                "federal": ("federal", "federais"),
                "labor": ("trabalhista", "trabalho"),
                "electoral": ("eleitoral", "eleitorais"),
                "military": ("militar", "militares"),
            },
        }
        for field_name, options in patterns.items():
            matches = [
                value
                for value, variants in options.items()
                if any(_fold(item) in normalized for item in variants)
            ]
            if len(matches) == 1:
                detected[field_name] = matches[0]
            elif len(matches) > 1:
                ambiguous.append(f"{field_name}:{','.join(matches)}")
        authorities = re.findall(
            r"\b(?:STF|STJ|TST|TSE|STM|TJ[A-Z]{2}|TRF ?[1-6]|TRT ?\d{1,2})\b", original.upper()
        )
        unique_authorities = tuple(dict.fromkeys(item.replace(" ", "") for item in authorities))
        if len(unique_authorities) == 1:
            detected["authority"] = unique_authorities[0]
        elif len(unique_authorities) > 1:
            ambiguous.append("authority:" + ",".join(unique_authorities))
        for collection in ("cjpg", "cjsg", "sjur", "eproc", "projudi"):
            if collection in normalized:
                detected["collection"] = collection.upper()
                break
        if "responsabilidade civil" in normalized and "administrativa" in normalized:
            suggested["legal_area"] = "responsabilidade civil administrativa"
        return detected, suggested, tuple(ambiguous)


def _load_vocabulary() -> dict[str, Any]:
    path = files("nanojuris").joinpath("data/legal-vocabulary-v1.json")
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["ANALYZER_VERSION", "LegalConceptMatch", "LegalQueryAnalyzer", "QueryIntent"]
