from pytest import approx

from nanojuris import (
    BM25_VERSION,
    BM25Scorer,
    JurisprudenceResult,
    LegalLiveRanker,
    LegalQueryAnalyzer,
    reciprocal_rank_fusion,
)


def _result(identifier: str, summary: str, *, number: str | None = None) -> JurisprudenceResult:
    return JurisprudenceResult(
        id=identifier,
        source="fixture",
        court="TJSP",
        type="acordao",
        number=number,
        summary=summary,
        document_type="acordao",
        degree="second",
        instance="second",
        branch="state",
    )


def test_ranker_prefers_exact_phrase_and_returns_reasons() -> None:
    intent = LegalQueryAnalyzer().analyze('"responsabilidade civil administrativa"')
    rows = LegalLiveRanker().rank(
        intent,
        [
            _result("b", "Responsabilidade administrativa em contrato"),
            _result("a", "Responsabilidade civil administrativa comprovada"),
        ],
    )

    assert rows[0].record.id == "a"
    assert rows[0].relevance_score > rows[1].relevance_score
    assert "Expressão exata no conteúdo" in rows[0].match_reasons


def test_ranker_is_invariant_to_input_permutation() -> None:
    intent = LegalQueryAnalyzer().analyze("dano moral inscrição indevida")
    first = LegalLiveRanker().rank(
        intent, [_result("b", "dano moral"), _result("a", "inscrição indevida")]
    )
    second = LegalLiveRanker().rank(
        intent, [_result("a", "inscrição indevida"), _result("b", "dano moral")]
    )

    assert [item.record.id for item in first] == [item.record.id for item in second]
    assert [item.relevance_score for item in first] == [item.relevance_score for item in second]


def test_exact_cnj_identifier_dominates() -> None:
    intent = LegalQueryAnalyzer().analyze("0000000-12.3452.0.20.1234")
    rows = LegalLiveRanker().rank(
        intent,
        [
            _result("other", "decisão parecida", number="0000000-99.9999.0.99.9999"),
            _result("exact", "decisão", number="0000000-12.3452.0.20.1234"),
        ],
    )

    assert rows[0].record.id == "exact"
    assert rows[0].relevance_score == 99.9
    assert rows[0].match_reasons == ("Identificador exato",)


def test_ranker_deduplicates_same_cnj_as_group_without_merging_republication() -> None:
    intent = LegalQueryAnalyzer().analyze("divorcio")
    rows = LegalLiveRanker().rank(
        intent,
        [
            _result("a", "divórcio", number="0000000-12.3452.0.20.1234"),
            _result("b", "divórcio", number="0000000-12.3452.0.20.1234"),
        ],
    )

    assert rows[0].deduplication_group == rows[1].deduplication_group
    assert rows[0].duplicate_sources == ("fixture",)


def test_ranker_pushes_excluded_terms_to_zero() -> None:
    intent = LegalQueryAnalyzer().analyze("dano moral -segredo")
    rows = LegalLiveRanker().rank(
        intent,
        [
            _result("excluded", "dano moral em segredo de justiÃ§a"),
            _result("allowed", "dano moral por inscriÃ§Ã£o indevida"),
        ],
    )

    assert rows[-1].record.id == "excluded"
    assert rows[-1].relevance_score == 0.0
    assert rows[-1].match_reasons


def test_ranker_penalizes_missing_required_term() -> None:
    intent = LegalQueryAnalyzer().analyze("+responsabilidade +administrativa")
    rows = LegalLiveRanker().rank(
        intent,
        [
            _result("partial", "responsabilidade civil"),
            _result("complete", "responsabilidade administrativa"),
        ],
    )

    assert rows[0].record.id == "complete"
    assert rows[0].relevance_score > rows[1].relevance_score


def test_ranker_accepts_curated_concept_expansion_with_lower_weight() -> None:
    intent = LegalQueryAnalyzer().analyze("divorcio")
    rows = LegalLiveRanker().rank(
        intent,
        [
            _result("literal", "divorcio consensual"),
            _result("expanded", "dissolucao do casamento"),
        ],
    )
    assert rows[0].record.id == "literal"
    assert rows[1].relevance_score > 0


def test_bm25_is_bounded_batch_scoring_and_exposes_version() -> None:
    scorer = BM25Scorer()
    rows = [_result("a", "responsabilidade civil"), _result("b", "divorcio")]

    scores = scorer.score_batch(("responsabilidade", "civil"), rows)

    assert scorer.version == BM25_VERSION
    assert len(scores) == 2
    assert 0.0 <= scores[0] <= 1.0
    assert scores[0] > scores[1] == 0.0


def test_bm25_is_invariant_to_input_permutation() -> None:
    scorer = BM25Scorer()
    rows = [_result("a", "dano moral"), _result("b", "dano moral inscricao indevida")]

    first = dict(
        zip((row.id for row in rows), scorer.score_batch(("dano", "moral"), rows), strict=True)
    )
    reordered = list(reversed(rows))
    second = dict(
        zip(
            (row.id for row in reordered),
            scorer.score_batch(("dano", "moral"), reordered),
            strict=True,
        )
    )

    assert first == second


def test_ranked_result_contains_bm25_annotation() -> None:
    intent = LegalQueryAnalyzer().analyze("responsabilidade civil")
    ranked = LegalLiveRanker().rank(intent, [_result("a", "responsabilidade civil")])

    payload = ranked[0].to_dict()

    assert payload["bm25_version"] == BM25_VERSION
    assert payload["bm25_score"] > 0


def test_reciprocal_rank_fusion_ignores_duplicate_ids_within_one_ranking() -> None:
    fused = reciprocal_rank_fusion([["a", "a", "b"], ["b", "c"]])

    assert list(fused) == ["b", "a", "c"]
    assert fused["b"] == approx((1 / 22) + (1 / 21))
