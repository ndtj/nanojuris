import pytest

from nanojuris import ANALYZER_VERSION, LegalQueryAnalyzer


def test_analyzer_extracts_document_type_and_concept() -> None:
    intent = LegalQueryAnalyzer().analyze("acórdãos sobre divórcio")

    assert intent.analyzer_version == ANALYZER_VERSION
    assert intent.detected_filters["document_type"] == "acordao"
    assert intent.legal_concepts[0].concept_id == "divorcio"
    assert "acordaos" not in intent.normalized_terms
    assert "sobre" not in intent.normalized_terms


def test_analyzer_preserves_compound_legal_concept() -> None:
    intent = LegalQueryAnalyzer().analyze("responsabilidade civil administrativa")

    assert intent.legal_concepts[0].concept_id == "responsabilidade_civil_administrativa"
    assert intent.legal_concepts[0].expansion_weight == 0.4
    assert intent.suggested_filters["legal_area"] == "responsabilidade civil administrativa"


def test_analyzer_prioritizes_exact_cnj_identifier() -> None:
    intent = LegalQueryAnalyzer().analyze("0000000-12.3452.0.20.1234")

    assert intent.is_exact_identifier is True
    assert intent.identifier == "0000000-12.3452.0.20.1234"
    assert intent.required_terms == ("0000000-12.3452.0.20.1234",)
    assert intent.normalized_terms == ()


def test_analyzer_extracts_explicit_filters_and_negative_terms() -> None:
    intent = LegalQueryAnalyzer().analyze("TJSP segundo grau acordão -segredo")

    assert intent.detected_filters["authority"] == "TJSP"
    assert intent.detected_filters["degree"] == "second"
    assert intent.excluded_terms == ("segredo",)


def test_analyzer_keeps_ambiguous_authority_as_suggestion_state() -> None:
    intent = LegalQueryAnalyzer().analyze("TJSP ou TJMG responsabilidade civil")

    assert "authority:TJSP,TJMG" in intent.ambiguous_interpretations
    assert "authority" not in intent.detected_filters


def test_analyzer_can_suppress_an_inferred_filter() -> None:
    intent = LegalQueryAnalyzer().analyze(
        "acórdãos sobre divórcio", ignored_filters={"document_type"}
    )

    assert "document_type" not in intent.detected_filters


@pytest.mark.parametrize(
    "query, concept_id",
    [
        ("responsabilidade civil administrativa", "responsabilidade_civil_administrativa"),
        ("acórdãos sobre divórcio", "divorcio"),
        ("dano moral inscrição indevida", "dano_moral_inscricao_indevida"),
        ("servidor público acumulação de cargos", "acumulacao_cargos"),
        ("prisão preventiva contemporaneidade", "prisao_preventiva_contemporaneidade"),
    ],
)
def test_required_golden_queries_have_conservative_concept_matches(
    query: str, concept_id: str
) -> None:
    intent = LegalQueryAnalyzer().analyze(query)

    assert any(item.concept_id == concept_id for item in intent.legal_concepts)
