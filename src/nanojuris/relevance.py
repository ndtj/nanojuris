"""Deterministic, explainable ranking for live jurisprudence candidates."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import log1p
from typing import Any

from nanojuris.search_intent import QueryIntent

RANKING_VERSION = "legal-live-v1"
BM25_VERSION = "bm25-v1"
BM25_K1 = 1.2
BM25_B = 0.75
RRF_K = 20
_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)
_REPUBLICATION_RE = re.compile(r"republica|retifica|versao", re.IGNORECASE)
_FIELDS: tuple[tuple[str, float], ...] = (
    ("case_number", 10.0),
    ("number", 10.0),
    ("registry_number", 10.0),
    ("question", 5.0),
    ("thesis", 5.0),
    ("subject", 5.0),
    ("title", 5.0),
    ("summary", 4.0),
    ("case_class", 3.0),
    ("document_type", 3.0),
    ("decision_type", 3.0),
    ("judging_body", 2.0),
    ("rapporteur", 2.0),
    ("legal_area", 2.0),
    ("full_text", 1.0),
)
_FIELD_NAMES = {name for name, _ in _FIELDS}
_FIELD_ORDER = tuple(name for name, _ in _FIELDS)
_BM25_RANK_FIELDS: dict[str, float] = {
    "question": 5.0,
    "thesis": 5.0,
    "subject": 5.0,
    "title": 5.0,
    "summary": 4.0,
    "full_text": 1.0,
}
_FIELD_LIMITS: dict[str, int] = {
    "case_number": 128,
    "number": 128,
    "registry_number": 128,
    "question": 2048,
    "thesis": 2048,
    "subject": 2048,
    "title": 2048,
    "summary": 8192,
    "case_class": 512,
    "document_type": 512,
    "decision_type": 512,
    "judging_body": 1024,
    "rapporteur": 1024,
    "legal_area": 1024,
    "full_text": 16384,
}


def _contains_term(text: str, term: str) -> bool:
    """Match a normalized term without rewarding a substring inside another word."""

    normalized = _fold(term).strip()
    if not normalized:
        return False
    escaped = re.escape(normalized)
    return re.search(rf"(?<!\w){escaped}(?!\w)", text, flags=re.UNICODE) is not None


def _contains_projected_term(text: str, tokens: set[str], term: str) -> bool:
    """Match a term against a projected field without recompiling simple regexes."""

    term_text = str(term)
    normalized = term_text.casefold().strip() if term_text.isascii() else _fold(term_text).strip()
    if not normalized:
        return False
    if " " not in normalized:
        return normalized in tokens
    return _contains_term(text, normalized)


def _fold(value: object) -> str:
    text = str(value)
    if not text:
        return ""
    if text.isascii():
        return text.casefold()
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _tokens(value: object) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(_fold(value)))


def _record_value(record: Any, field_name: str) -> object:
    """Read an allowlisted field from either a model or a mapping."""

    if isinstance(record, Mapping):
        return record.get(field_name, "")
    return getattr(record, field_name, "")


def _bounded_field_text(record: Any, field_name: str) -> str:
    """Return bounded text before folding/tokenizing untrusted provider data."""

    value = _record_value(record, field_name)
    if value is None:
        return ""
    return str(value)[: _FIELD_LIMITS.get(field_name, 1024)]


class BM25Scorer:
    """Score a live candidate batch with fielded BM25.

    This is deliberately a *batch scorer*, not an index. Document frequency
    and average field length are calculated from the bounded candidates in the
    current request and discarded afterwards. That keeps the implementation
    deterministic, CPU-only and compatible with the no-persistent-index
    product decision.
    """

    version = BM25_VERSION

    def __init__(
        self,
        *,
        k1: float = BM25_K1,
        b: float = BM25_B,
        field_weights: Mapping[str, float] | None = None,
    ) -> None:
        if k1 <= 0:
            raise ValueError("k1 must be positive")
        if not 0 <= b <= 1:
            raise ValueError("b must be between 0 and 1")
        weights = field_weights or dict(_FIELDS)
        if any(weight < 0 for weight in weights.values()):
            raise ValueError("field weights must be non-negative")
        self.k1 = float(k1)
        self.b = float(b)
        self.field_weights = {
            name: float(weight) for name, weight in weights.items() if name in _FIELD_NAMES
        }

    def score_batch(self, query_terms: Iterable[str], records: Iterable[Any]) -> tuple[float, ...]:
        """Return normalized BM25 scores in input order for one bounded batch."""

        materialized = list(records)
        if not materialized:
            return ()
        projected = [
            {
                field_name: _fold(_bounded_field_text(record, field_name))
                for field_name in self.field_weights
            }
            for record in materialized
        ]
        return self.score_projected_batch(query_terms, projected)

    def score_projected_batch(
        self,
        query_terms: Iterable[str],
        projected_records: Iterable[Mapping[str, str]],
    ) -> tuple[float, ...]:
        """Score already bounded/folded allowlisted fields without re-normalizing."""

        projected = list(projected_records)
        if not projected:
            return ()
        terms = tuple(dict.fromkeys(token for term in query_terms for token in _tokens(term)))
        if not terms:
            return tuple(0.0 for _ in projected)
        documents = [
            {
                field_name: (
                    Counter(_TOKEN_RE.findall(field_text))
                    if any(term in field_text for term in terms)
                    else Counter()
                )
                for field_name in self.field_weights
                for field_text in (str(record.get(field_name, "")),)
            }
            for record in projected
        ]
        count = len(documents)
        average_lengths = {
            field_name: max(
                1.0,
                sum(sum(document[field_name].values()) for document in documents) / count,
            )
            for field_name in self.field_weights
        }
        document_frequency: dict[str, int] = {}
        for document in documents:
            present = {
                term
                for term in terms
                if any(term in field_tokens for field_tokens in document.values())
            }
            for term in present:
                document_frequency[term] = document_frequency.get(term, 0) + 1

        raw_scores: list[float] = []
        for document in documents:
            score = 0.0
            for term in terms:
                frequency = document_frequency.get(term, 0)
                if not frequency:
                    continue
                idf = log1p((count - frequency + 0.5) / (frequency + 0.5))
                for field_name, field_weight in self.field_weights.items():
                    token_counts = document[field_name]
                    term_frequency = token_counts.get(term, 0)
                    if not term_frequency or not field_weight:
                        continue
                    length_norm = (
                        1.0
                        - self.b
                        + self.b * (sum(token_counts.values()) / average_lengths[field_name])
                    )
                    tf = (term_frequency * (self.k1 + 1.0)) / (
                        term_frequency + self.k1 * length_norm
                    )
                    score += field_weight * idf * tf
            raw_scores.append(score)
        maximum = max(raw_scores, default=0.0)
        if maximum <= 0:
            return tuple(0.0 for _ in raw_scores)
        return tuple(max(0.0, min(1.0, score / maximum)) for score in raw_scores)


@dataclass(frozen=True, slots=True)
class RankedResult:
    """A candidate plus only the ranking facts safe to expose."""

    record: Any
    relevance_score: float
    matched_terms: tuple[str, ...] = ()
    matched_concepts: tuple[str, ...] = ()
    match_reasons: tuple[str, ...] = ()
    bm25_score: float = 0.0
    native_rank: int | None = None
    deduplication_group: str | None = None
    duplicate_sources: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = self.record.to_dict() if hasattr(self.record, "to_dict") else self.record
        return {
            "record": payload,
            "relevance_score": self.relevance_score,
            "matched_terms": list(self.matched_terms),
            "matched_concepts": list(self.matched_concepts),
            "match_reasons": list(self.match_reasons),
            "bm25_score": self.bm25_score,
            "bm25_version": BM25_VERSION,
            "native_rank": self.native_rank,
            "deduplication_group": self.deduplication_group,
            "duplicate_sources": list(self.duplicate_sources),
        }


@dataclass(frozen=True, slots=True)
class _Candidate:
    record: Any
    index: int
    score: float
    matched_terms: tuple[str, ...]
    matched_concepts: tuple[str, ...]
    reasons: tuple[str, ...]
    bm25_score: float
    native_rank: int | None
    group: str | None


class LegalLiveRanker:
    """Score a bounded live result set without network, vector or LLM calls."""

    version = RANKING_VERSION

    def rank(
        self,
        intent: QueryIntent,
        records: Iterable[Any],
        *,
        native_ranks: dict[str, int] | None = None,
    ) -> list[RankedResult]:
        materialized = list(records)
        ranks = native_ranks or {}
        terms = tuple(dict.fromkeys(intent.normalized_terms + intent.required_terms))
        projected = [
            {
                field_name: _fold(_bounded_field_text(record, field_name))
                for field_name in _FIELD_ORDER
            }
            for record in materialized
        ]
        bm25_scores = BM25Scorer(field_weights=_BM25_RANK_FIELDS).score_projected_batch(
            terms, projected
        )
        candidates = [
            self._score(
                intent,
                record,
                index=index,
                native_rank=self._native_rank(record, ranks),
                bm25_score=bm25_scores[index],
                projected_values=projected[index],
            )
            for index, record in enumerate(materialized)
        ]
        candidates.sort(key=self._sort_key)
        groups: dict[str, list[_Candidate]] = {}
        for candidate in candidates:
            if candidate.group is not None:
                groups.setdefault(candidate.group, []).append(candidate)
        ranked: list[RankedResult] = []
        for candidate in candidates:
            group_rows = groups.get(candidate.group, []) if candidate.group else []
            sources = tuple(
                sorted(
                    {
                        str(getattr(row.record, "source", ""))
                        for row in group_rows
                        if getattr(row.record, "source", None)
                    }
                )
            )
            ranked.append(
                RankedResult(
                    record=candidate.record,
                    relevance_score=round(candidate.score, 1),
                    matched_terms=candidate.matched_terms,
                    matched_concepts=candidate.matched_concepts,
                    match_reasons=candidate.reasons[:3],
                    bm25_score=round(candidate.bm25_score, 6),
                    native_rank=candidate.native_rank,
                    deduplication_group=candidate.group,
                    duplicate_sources=sources,
                )
            )
        return ranked

    @staticmethod
    def diversify_near_ties(
        ranked: list[RankedResult], *, margin: float = 2.5
    ) -> list[RankedResult]:
        """Avoid adjacent same-source near ties without imposing a quota.

        A swap is made only when an alternative is within ``margin`` points of
        the current item. Exact identifiers and materially stronger results
        therefore retain their position.
        """

        if margin < 0:
            raise ValueError("margin must be non-negative")
        rows = list(ranked)
        for index in range(1, len(rows)):
            previous_source = str(getattr(rows[index - 1].record, "source", ""))
            current = rows[index]
            if str(getattr(current.record, "source", "")) != previous_source:
                continue
            for candidate_index in range(index + 1, len(rows)):
                candidate = rows[candidate_index]
                if current.relevance_score - candidate.relevance_score > margin:
                    break
                if str(getattr(candidate.record, "source", "")) == previous_source:
                    continue
                rows[index], rows[candidate_index] = candidate, current
                break
        return rows

    def _score(
        self,
        intent: QueryIntent,
        record: Any,
        *,
        index: int,
        native_rank: int | None,
        bm25_score: float,
        projected_values: Mapping[str, str] | None = None,
    ) -> _Candidate:
        identifier = str(getattr(record, "number", "") or getattr(record, "case_number", ""))
        if (
            intent.is_exact_identifier
            and intent.identifier
            and _fold(intent.identifier) in _fold(identifier)
        ):
            return _Candidate(
                record,
                index,
                99.9,
                (intent.identifier,),
                (),
                ("Identificador exato",),
                1.0,
                native_rank,
                self._group_key(record),
            )
        values = dict(
            projected_values
            or {name: _fold(_bounded_field_text(record, name)) for name in _FIELD_ORDER}
        )
        all_text = " ".join(value for value in values.values() if value)
        all_tokens = set(_TOKEN_RE.findall(all_text))
        terms = tuple(dict.fromkeys(intent.normalized_terms + intent.required_terms))
        matched = tuple(
            term for term in terms if _contains_projected_term(all_text, all_tokens, term)
        )
        coverage = len(matched) / max(1, len(terms))
        required_matches = tuple(
            term
            for term in intent.required_terms
            if _contains_projected_term(all_text, all_tokens, term)
        )
        required_coverage = len(required_matches) / max(1, len(intent.required_terms))
        excluded_matches = tuple(
            term
            for term in intent.excluded_terms
            if _contains_projected_term(all_text, all_tokens, term)
        )
        exact_phrase = self._phrase_signal(intent, values)
        proximity = self._proximity_signal(terms, all_text)
        concept_matches = tuple(
            concept.concept_id
            for concept in intent.legal_concepts
            if any(
                _contains_projected_term(all_text, all_tokens, term)
                for term in (*concept.matched_terms, *concept.expansions)
            )
        )
        concept_coverage = len(concept_matches) / max(1, len(intent.legal_concepts))
        field_quality = min(
            1.0, sum(bool(values.get(name)) for name in ("summary", "full_text", "subject")) / 3
        )
        filter_consistency = self._filter_consistency(intent, record)
        native_signal = self._native_signal(native_rank)
        lexical = (
            0.25 * coverage
            + 0.10 * bm25_score
            + 0.22 * exact_phrase
            + 0.14 * proximity
            + 0.12 * concept_coverage
            + 0.08 * field_quality
            + 0.06 * filter_consistency
            + 0.03 * native_signal
        )
        penalties = 0.0
        if terms and coverage < 0.5 and not concept_matches:
            penalties += 0.30
        if intent.required_terms and required_coverage < 1.0:
            penalties += 0.45 * (1.0 - required_coverage)
        if excluded_matches:
            # A negative term is a hard exclusion for ranking purposes. Keep
            # the candidate in the diagnostic result set, but ensure it cannot
            # displace a candidate that satisfies the query.
            penalties = 1.0
        if not values.get("summary") and not values.get("full_text"):
            penalties += 0.18
        if intent.detected_filters:
            penalties += 0.20 * (1.0 - filter_consistency)
        score = max(0.0, min(100.0, 100 * (lexical - penalties)))
        reasons = self._reasons(
            intent,
            record,
            matched,
            coverage,
            exact_phrase,
            concept_matches,
            filter_consistency,
            required_matches,
            excluded_matches,
        )
        return _Candidate(
            record,
            index,
            score,
            matched,
            concept_matches,
            reasons,
            bm25_score,
            native_rank,
            self._group_key(record),
        )

    @staticmethod
    def _native_rank(record: Any, ranks: dict[str, int]) -> int | None:
        identifier = str(getattr(record, "id", ""))
        value = ranks.get(identifier)
        if value is None:
            value = getattr(record, "native_rank", None)
        return value if value is not None and value > 0 else None

    @staticmethod
    def _native_signal(rank: int | None) -> float:
        if rank is None:
            return 0.0
        return 1.0 / (20.0 + rank)

    @staticmethod
    def _phrase_signal(intent: QueryIntent, values: dict[str, str]) -> float:
        if not intent.phrases:
            return 0.0
        strongest = 0.0
        for phrase in intent.phrases:
            if phrase in values.get("subject", "") or phrase in values.get("question", ""):
                strongest = max(strongest, 1.0)
            elif phrase in values.get("summary", "") or phrase in values.get("thesis", ""):
                strongest = max(strongest, 1.0)
            elif phrase in values.get("full_text", ""):
                strongest = max(strongest, 0.7)
        return strongest

    @staticmethod
    def _proximity_signal(terms: tuple[str, ...], text: str) -> float:
        if len(terms) < 2:
            return 1.0 if terms and terms[0] in text else 0.0
        # Tokenize once per candidate.  The previous implementation rebuilt
        # the complete token tuple for every term and again for membership,
        # which made the bounded 240-candidate CPU gate unnecessarily noisy.
        positions_by_token: dict[str, int] = {}
        for position, token in enumerate(_TOKEN_RE.findall(text)):
            positions_by_token.setdefault(token, position)
        positions = [positions_by_token[term] for term in terms if term in positions_by_token]
        if len(positions) < 2:
            return 0.0
        window = max(positions) - min(positions) + 1
        return max(0.0, min(1.0, 1.0 - (window - len(positions)) / 50.0))

    @staticmethod
    def _filter_consistency(intent: QueryIntent, record: Any) -> float:
        checks: list[bool] = []
        for field_name, expected in intent.detected_filters.items():
            if field_name in {"number", "authority"}:
                value = (
                    getattr(record, "number", None)
                    if field_name == "number"
                    else getattr(record, "authority", None)
                )
            elif field_name == "document_type":
                value = getattr(record, "document_type", None) or getattr(record, "type", None)
            else:
                value = getattr(record, field_name, None)
            if value:
                checks.append(expected.casefold() in str(value).casefold())
        return sum(checks) / len(checks) if checks else 1.0

    @staticmethod
    def _type_matches(intent: QueryIntent, record: Any) -> bool:
        expected = intent.detected_filters.get("document_type", "")
        value = str(getattr(record, "document_type", None) or getattr(record, "type", ""))
        return expected.casefold() in _fold(value)

    @staticmethod
    def _group_key(record: Any) -> str | None:
        source = str(getattr(record, "source", "")).casefold()
        identifier = str(getattr(record, "id", "")).strip()
        number = str(
            getattr(record, "number", None) or getattr(record, "case_number", None) or ""
        ).strip()
        document = str(getattr(record, "document_url", "") or "").split("#", 1)[0]
        if _REPUBLICATION_RE.search(str(getattr(record, "decision_type", ""))):
            return None
        if number and len(re.sub(r"\D", "", number)) == 20:
            digits = re.sub(r"\D", "", number)
            return f"cnj:{digits}"
        if document:
            return f"document:{_fold(document)}"
        if identifier and source:
            return f"native:{source}:{identifier}"
        return None

    @staticmethod
    def _reasons(
        intent: QueryIntent,
        record: Any,
        matched: tuple[str, ...],
        coverage: float,
        phrase: float,
        concepts: tuple[str, ...],
        filter_consistency: float,
        required_matches: tuple[str, ...],
        excluded_matches: tuple[str, ...],
    ) -> tuple[str, ...]:
        reasons: list[str] = []
        if excluded_matches:
            reasons.append("Contém termo excluído")
        if phrase:
            reasons.append("Expressão exata no conteúdo")
        if matched and coverage >= 0.99:
            reasons.append(f"{len(matched)} de {len(intent.normalized_terms)} termos encontrados")
        elif matched:
            reasons.append(f"{len(matched)} termos da consulta encontrados")
        if concepts:
            reasons.append("Conceito jurídico compatível")
        if required_matches:
            reasons.append(f"{len(required_matches)} termo(s) obrigatório(s) atendido(s)")
        if filter_consistency >= 1.0 and intent.detected_filters:
            reasons.append("Filtros explícitos compatíveis")
        if getattr(record, "full_text", None):
            reasons.append("Inteiro teor disponível")
        return tuple(reasons)

    @staticmethod
    def _sort_key(candidate: _Candidate) -> tuple[Any, ...]:
        record = candidate.record
        return (
            -candidate.score,
            -len(candidate.matched_terms),
            str(getattr(record, "source", "")).casefold(),
            str(getattr(record, "id", "")),
            candidate.index,
        )


def reciprocal_rank_fusion(
    rankings: Iterable[Iterable[str]], *, k: int = RRF_K
) -> dict[str, float]:
    """Fuse provider/variant rankings without comparing native score scales."""

    if k < 1:
        raise ValueError("k must be positive")
    fused: dict[str, float] = {}
    for ranking in rankings:
        seen: set[str] = set()
        unique_position = 0
        for identifier in ranking:
            key = str(identifier)
            if not key or key in seen:
                continue
            seen.add(key)
            unique_position += 1
            fused[key] = fused.get(key, 0.0) + 1.0 / (k + unique_position)
    return dict(sorted(fused.items(), key=lambda item: (-item[1], item[0])))


__all__ = [
    "BM25_B",
    "BM25_K1",
    "BM25_VERSION",
    "BM25Scorer",
    "LegalLiveRanker",
    "RANKING_VERSION",
    "RRF_K",
    "RankedResult",
    "reciprocal_rank_fusion",
]
